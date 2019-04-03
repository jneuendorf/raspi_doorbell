import asyncio
from concurrent.futures import CancelledError
import json
import logging
import signal
import sys

# 3rd party
import RPi.GPIO as GPIO
import pygame

# local
import notifications
import tornado_server


if sys.version_info[0:2] != (3, 5):
    raise RuntimeError('Python 3.5 required but got ' + sys.version)


###############################################################################
# HELPERS

def handle_ring(channel):
    logger.info("bell is ringing!")
    for client in tornado_server.connections:
        client.write_message({
            'type': message_types['receive_bell'],
        })
    pygame.mixer.music.play()
    notifications.send(server_config['notifications'])


async def gpio_loop():
    while True:
        await asyncio.sleep(0.200)


async def start_server():
    tornado_server.start(server_config['port'])

###############################################################################
# SETUP

# SETUP LOGGING
logger = logging.getLogger("doorbell")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(asctime)s,%(msecs)d] %(levelname)s %(message)s'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# SETUP GPIO
GPIO.setmode(GPIO.BCM)
BUTTON = 21
GPIO.setup(BUTTON, GPIO.IN)
# See https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
GPIO.add_event_detect(BUTTON, GPIO.FALLING,
                      callback=handle_ring, bouncetime=10000)


# SETUP SOUND PLAYBACK LIB
pygame.mixer.init()
pygame.mixer.music.load('DBSE.ogg')
pygame.mixer.music.set_volume(0.6)


with open('../websocket-message-types.json') as file:
    message_types = json.load(file)
    logger.info(message_types)
with open('../server-config.json') as file:
    server_config = json.load(file)
    logger.info(server_config)


###############################################################################
# MAIN PROGRAM

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    future = asyncio.gather(
        gpio_loop(),
        start_server(),
    )

    cleaning_up = False

    # Cleanup handler, e.g. for when Ctrl+C is pressed.
    def cleanup(sig, frame):
        cleaning_up = True

        pygame.mixer.quit()
        GPIO.cleanup()
        # 'stop' only affects 'loop.run_forever' but not
        # 'loop.run_until_complete'. Thus we just cancel the Future object.
        # See https://docs.python.org/3.5/library/asyncio-eventloop.html#asyncio.AbstractEventLoop.stop
        future.cancel()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        loop.run_until_complete(future)
    except CancelledError as e:
        if not cleaning_up:
            logger.error(str(e))
    finally:
        loop.close()
