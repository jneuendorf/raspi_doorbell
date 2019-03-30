import RPi.GPIO as GPIO
import asyncio
import json
import pygame
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


# GPIO SETUP
GPIO.setmode(GPIO.BCM)
BUTTON = 21
GPIO.setup(BUTTON, GPIO.IN)


pygame.mixer.init()
pygame.mixer.music.load('DBSE.ogg')
pygame.mixer.music.set_volume(0.3)


async def play_sound():
    pygame.mixer.music.play()
    # Estimated duration of MP3 file.
    await asyncio.sleep(1.8)


async def handle_ring():
    print("bell is ringing!")
    for client in connections:
        client.write_message({
            'type': message_types['receive_bell'],
        })
    await play_sound()


async def gpio_loop():
    while True:
        if not GPIO.input(BUTTON):
            handle_ring()
        await asyncio.sleep(0.150)


async def gpio_test_loop():
    while True:
        timer = asyncio.sleep(10.000)
        await handle_ring()
        await timer


async def start_websocket_server():
    app = make_app()
    app.listen(server_config['port'])
    # No need to start tornado's ioloop
    # because we already have our own (asyncio).


if __name__ == "__main__":
    # Python 3.5
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(
            gpio_loop(),
            start_websocket_server(),
        )
    )
    loop.close()

    # Python 3.7+
    # asyncio.run(asyncio.gather(
    #     gpio_test_loop(),
    #     start_websocket_server(),
    # ))
