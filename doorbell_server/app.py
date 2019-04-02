import RPi.GPIO as GPIO
import asyncio
import json
import pygame
import signal
import sys
import tornado.web
import tornado.websocket


if sys.version_info[0:2] != (3, 5):
    raise RuntimeError('Python 3.5 required but got ' + sys.version)


with open('../websocket-message-types.json') as file:
    message_types = json.load(file)
    print(message_types)
with open('../server-config.json') as file:
    server_config = json.load(file)
    print(server_config)


connections = set()


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        print("got a connection...")
        connections.add(self)

    def on_message(self, message):
        message = json.loads(message)
        print('message', message)
        message_type = message['type']
        if message_type == message_types['request_volume']:
            self.write_message({
                "type": message_types['receive_volume'],
                "volume": pygame.mixer.music.get_volume(),
            })
        elif message_type == message_types['update_volume']:
            new_volume = message['volume']
            # print('new volume =', new_volume)
            pygame.mixer.music.set_volume(new_volume)
            for client in connections:
                if client is not self:
                    client.write_message({
                        "type": message_types['receive_volume'],
                        "volume": new_volume,
                    })

    def on_close(self):
        connections.remove(self)

    # @override
    def write_message(self, message):
        super().write_message(json.dumps(message))


# class MainHandler(tornado.web.RequestHandler):
#     def get(self):
#         self.render("index.html")


def make_app():
    return tornado.web.Application([
        # (r"/", MainHandler),
        (r"/websocket", WebSocketHandler),
    ])


def handle_ring(channel):
    print("bell is ringing!")
    for client in connections:
        client.write_message({
            'type': message_types['receive_bell'],
        })
    pygame.mixer.music.play()


async def gpio_loop():
    while True:
        # See https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
        # if GPIO.event_detected(BUTTON):
        #     await handle_ring()
        await asyncio.sleep(0.200)


async def start_websocket_server():
    app = make_app()
    app.listen(server_config['port'])
    # No need to start tornado's ioloop
    # because we already have our own (asyncio).


###############################################################################
# MAIN PROGRAM

# SETUP GPIO
GPIO.setmode(GPIO.BCM)
BUTTON = 21
GPIO.setup(BUTTON, GPIO.IN)
GPIO.add_event_detect(BUTTON, GPIO.FALLING,
                      callback=handle_ring, bouncetime=5000)

# SETUP SOUND PLAYBACK LIB
pygame.mixer.init()
pygame.mixer.music.load('DBSE.ogg')
pygame.mixer.music.set_volume(0.3)


if __name__ == "__main__":
    # Python 3.5
    loop = asyncio.get_event_loop()
    future = asyncio.gather(
        gpio_loop(),
        start_websocket_server(),
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

    # Python 3.7+
    # asyncio.run(asyncio.gather(
    #     gpio_loop(),
    #     start_websocket_server(),
    # ))
