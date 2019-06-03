import asyncio
from concurrent.futures import CancelledError
from datetime import datetime, time
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


class App:
    DEFAULT_SERVER_CONFIG = {
        'notifications': {
            'max_volume': 0.05,
        },
        'do_not_disturb_mode': {
            'begin': [19, 30],
            'end': [7, 30]
        },
        'audio_file': 'DBSE.ogg',
    }

    logger = None
    server_config = None
    message_types = None
    cleaning_up = False
    future = None

    def __init__(self, debug=False):
        self.debug = debug
        self.init_logger()
        self.load_configs()
        self.init_mixer()
        self.init_gpio()

    def init_logger(self):
        # TODO: Use dict config: logging.config.dictConfig()
        # logging.config.dictConfig({
        #     "version": 1,
        #     "disable_existing_loggers": True,
        #     "formatters": {
        #         "console": {
        #             "format": "\033[1;31m%(levelname)s\033[1;0m %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        #         },
        #         "verbose": {
        #             "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        #         },
        #         "simple": {
        #             "format": "%(levelname)s %(message)s"
        #         },
        #     },
        #     "handlers": {
        #         "console": {
        #             "class": "logging.StreamHandler",
        #             "formatter": "console",
        #         },
        #         "slack_info": {
        #             "()": SlackHandler,
        #             "webhook_urls": [
        #                 "https://hooks.slack.com/services/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",
        #             ],
        #             "formatter": "simple",
        #             "level": "INFO",
        #         },
        #         "slack_warning": {
        #             "()": SlackHandler,
        #             "webhook_urls": [
        #                 "https://hooks.slack.com/services/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",
        #             ],
        #             "formatter": "simple",
        #             "level": "WARNING",
        #         },
        #     },
        #     "loggers": {
        #         "__main__": {
        #             "handlers": ["console", "slack"],
        #             "level": "DEBUG",
        #             "propagate": True,
        #         },
        #         # "slack": {
        #         #     "handlers": ["slack"],
        #         #     "level": "INFO",
        #         #     "propagate": True,
        #         # },
        #     },
        # })
        logger = logging.getLogger('doorbell')

        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(asctime)s,%(msecs)d] %(levelname)s %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        self.logger = logger

    def load_configs(self):
        with open('websocket-message-types.json') as file:
            self.message_types = json.load(file)
            self.logger.info(self.message_types)
        with open('server-config.json') as file:
            server_config = json.load(file)
            self.server_config = {
                **self.DEFAULT_SERVER_CONFIG,
                **server_config,
                # Deep merge some deep dicts.
                'notifications': {
                    **self.DEFAULT_SERVER_CONFIG['notifications'],
                    **server_config['notifications'],
                },
            }
            sanitized_config = {
                **self.server_config,
                'notifications': {
                    **self.server_config['notifications'],
                    'smtp_user': '••••••••••••••',
                    'smtp_pass': '••••••••',
                },
            }
            self.logger.info(sanitized_config)

    def init_mixer(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.server_config['audio_file'])
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
            notifications.send(self.server_config['notifications'])
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
        tornado_server.start(self.server_config['port'], self.message_types)

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
        do_not_disturb_mode = self.server_config['do_not_disturb_mode']
        now = datetime.now().time()
        begin = time(*do_not_disturb_mode['begin'])
        end = time(*do_not_disturb_mode['end'])
        return not utils.is_time_between(begin, end, now)

    def _should_send_notification(self):
        return (
            pygame.mixer.music.get_volume()
            <= self.server_config['notifications']['max_volume']
        )
