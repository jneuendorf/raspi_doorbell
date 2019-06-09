import asyncio
from concurrent.futures import CancelledError
import json
import logging
import logging.config
from select import select
import signal
import sys

# 3rd party
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None
import pygame

# local
import notifications
import tornado_server
import utils
from server_config import ServerConfig
import local_config


class App:
    logger = None
    server_config = None
    message_types = {
        "request_volume": "volume:request",
        "receive_volume": "volume:receive",
        "update_volume": "volume:update",
        "receive_bell": "bell:receive",
    }

    cleaning_up = False
    future = None

    def __init__(self, debug=False):
        self.debug = debug
        self.init_logger()
        self.load_config()
        self.init_mixer()
        self.init_gpio()

    def init_logger(self):
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "console": {
                    "format": "\033[1;31m%(levelname)s\033[1;0m %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
                },
                "verbose": {
                    "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
                },
                "simple": {
                    "format": "%(levelname)s %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": "app.log",
                    "formatter": "verbose",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": True,
                },
            },
        })
        self.logger = logging.getLogger('doorbell')

    def load_config(self):
        config_kwargs = {
            name: getattr(local_config, name)
            for name in dir(local_config)
            if not name.startswith("_")
        }
        self.server_config = ServerConfig(
            debug=self.debug,
            **config_kwargs
        )
        self.logger.info(self.server_config.sanitized_dict())

    def init_mixer(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.server_config.audio_file)
        pygame.mixer.music.set_volume(0.6)

    def init_gpio(self):
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            BUTTON = 21
            GPIO.setup(BUTTON, GPIO.IN)
            # See https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
            GPIO.add_event_detect(
                BUTTON,
                GPIO.FALLING,
                callback=self.handle_ring,
                bouncetime=10000,
            )

    def handle_ring(self, channel=None):
        self.logger.info('bell is ringing!')
        for client in tornado_server.connections:
            client.write_message({'type': self.message_types['receive_bell']})
        if self._should_play_sound():
            pygame.mixer.music.play()
        else:
            self.logger.debug('Not playing sound because in do-not-disturb-mode.')
        if self._should_send_notification():
            notifications.send(self.server_config.notifications)
        else:
            self.logger.debug('Not sending notifications because volume is too high.')

    def start(self):
        loop = asyncio.get_event_loop()
        self.future = asyncio.gather(
            self.start_web_server(),
            self.gpio_loop(),
        )

        self.cleaning_up = False

        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

        try:
            loop.run_until_complete(self.future)
        except CancelledError as e:
            if not self.cleaning_up:
                logger.error(str(e))
        finally:
            loop.close()

    async def gpio_loop(self):
        timeout_sec = 1
        while True:
            if self.debug:
                # See https://stackoverflow.com/a/3471853/6928824
                ready_to_read, _, _ = select([sys.stdin], [], [], timeout_sec)
                if ready_to_read:
                    user_input = sys.stdin.read(2)
                    if user_input == "r\n":
                        print("fake bell!")
                        self.handle_ring()
            await asyncio.sleep(0.200)

    async def start_web_server(self):
        tornado_server.start(self.server_config, self.message_types)

    def cleanup(self, sig, frame):
        """
        Cleanup handler, e.g. for when Ctrl+C is pressed.
        """
        self.cleaning_up = True

        pygame.mixer.quit()
        if GPIO:
            GPIO.cleanup()
        # 'stop' only affects 'loop.run_forever' but not
        # 'loop.run_until_complete'. Thus we just cancel the Future object.
        # See https://docs.python.org/3.5/library/asyncio-eventloop.html#asyncio.AbstractEventLoop.stop
        self.future.cancel()

        sys.exit(0)

    ###########################################################################
    # PRIVATE

    def _should_play_sound(self):
        return not utils.do_not_disturb_now(self.server_config)

    def _should_send_notification(self):
        return (
            pygame.mixer.music.get_volume()
            <= self.server_config.notifications['max_volume']
        )
