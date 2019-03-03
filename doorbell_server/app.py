# import RPi.GPIO as GPIO
import asyncio
import json
import pygame
import tornado.web
import tornado.websocket


with open('../DoorBell/websocket-message-types.json') as file:
    message_types = json.load(file)
    print(message_types)


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


# # GPIO SETUP
# GPIO.setmode(GPIO.BCM)
# BUTTON = 21
# GPIO.setup(BUTTON, GPIO.IN)


pygame.mixer.init()
pygame.mixer.music.load('DBSE.mp3')
pygame.mixer.music.set_volume(1.0)


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
    app.listen(8888)
    # No need to start tornado's ioloop
    # because we already have our own (asyncio).


async def main():
    await asyncio.gather(
        gpio_test_loop(),
        start_websocket_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
