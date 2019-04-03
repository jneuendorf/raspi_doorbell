import asyncio
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


RECIPIENTS = ['jim.neuendorf@gmx.de', 'visel@gmx.net']


with open('../websocket-message-types.json') as file:
    message_types = json.load(file)
    logger.info(message_types)
with open('../server-config.json') as file:
    server_config = json.load(file)
    logger.info(server_config)


###############################################################################
# MAIN PROGRAM

if __name__ == "__main__":
    # Python 3.5
    loop = asyncio.get_event_loop()
    future = asyncio.gather(
        gpio_loop(),
        start_server(),
    )

    # Cleanup handler, e.g. for when Ctrl+C is pressed.
    def cleanup(sig, frame):
        future.cancel()
        loop.stop()
        loop.close()
        pygame.mixer.quit()
        GPIO.cleanup()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    loop.run_until_complete(future)
    loop.close()
