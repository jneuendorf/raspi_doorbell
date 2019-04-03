import pygame
import tornado.web
import tornado.websocket


connections = set()


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        # logger.info("got a connection...")
        connections.add(self)

    def on_message(self, message):
        message = json.loads(message)
        # logger.info('message', message)
        message_type = message['type']
        if message_type == message_types['request_volume']:
            self.write_message({
                "type": message_types['receive_volume'],
                "volume": pygame.mixer.music.get_volume(),
            })
        elif message_type == message_types['update_volume']:
            new_volume = message['volume']
            # logger.info('new volume =', new_volume)
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


async def start(port):
    app = tornado.web.Application([
        # (r"/", MainHandler),
        (r"/websocket", WebSocketHandler),
    ])
    app.listen(port)
    # No need to start tornado's ioloop
    # because we already have our own (asyncio).
