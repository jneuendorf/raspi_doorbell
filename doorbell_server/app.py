# import RPi.GPIO as GPIO
import asyncio
import pygame
import tornado.gen
import tornado.ioloop
import tornado.web
import tornado.websocket


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


connections = set()


class SimpleWebSocket(tornado.websocket.WebSocketHandler):

    def open(self):
        print("got a connection...")
        connections.add(self)

    def on_message(self, message):
        print('new volume =', message)
        pygame.mixer.music.set_volume(float(message))
        for client in connections:
            if client is not self:
                client.write_message(f'{{"volume": {message}}}')

    def on_close(self):
        connections.remove(self)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", SimpleWebSocket),
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
    await tornado.gen.sleep(1.8)


async def handle_ring():
    print("bell is ringing!")
    # play_sound()
    await play_sound()
    for client in connections:
        client.write_message("someone's at the door!")


async def gpio_loop():
    while True:
        if not GPIO.input(BUTTON):
            handle_ring()
        await tornado.gen.sleep(0.150)


async def gpio_test_loop():
    while True:
        # print("bell is ringing!")
        timer = tornado.gen.sleep(10.000)
        await handle_ring()
        await timer


async def start_websocket_server():
    app = make_app()
    app.listen(8888)
    # No need to start tornado's loop because we already have our own.


async def main():
    await asyncio.gather(
        gpio_test_loop(),
        start_websocket_server(),
    )

if __name__ == "__main__":
    asyncio.run(main())
