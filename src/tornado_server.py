import json
import logging
import os

import pygame
import tornado.web
import tornado.websocket


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


connections = set()
logger = logging.getLogger("doorbell")
message_types = {}


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        logger.info("got a connection...")
        connections.add(self)

    def on_message(self, message):
        message = json.loads(message)
        logger.info('message', message)
        message_type = message['type']
        if message_type == message_types['request_volume']:
            self.write_message({
                "type": message_types['receive_volume'],
                "volume": pygame.mixer.music.get_volume(),
            })
        elif message_type == message_types['update_volume']:
            new_volume = message['volume']
            logger.info('new volume =', new_volume)
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


class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            os.path.join(BASE_DIR, "template/status2.html"),
            # template context
            bell_log=self._get_logs(),
            do_not_disturb_mode_is_on=False,
            pid_file_exists=True,
            # TODO: localhost <=> debug
            # websocket_url="ws://192.168.2.169:8888/websocket",
            websocket_url="ws://localhost:8888/websocket",
        )

    def _get_logs(self, limit=40):
        try:
            with open(os.path.join(BASE_DIR, "app.log")) as file:
                lines = file.readlines()
        except OSError:
            lines = []
        return reversed(lines[:-limit])


def start(port, _message_types):
    global message_types
    message_types = _message_types
    app = tornado.web.Application(
        [
            (r"/status", StatusHandler),
            (r"/websocket", WebSocketHandler),
        ],
        static_path=os.path.join(BASE_DIR, 'static'),
        static_url_prefix='/static/',
    )
    app.listen(port)
    print(app, port, message_types)
