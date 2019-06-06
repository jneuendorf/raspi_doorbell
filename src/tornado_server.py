import json
import logging
import os

import pygame
import tornado.web
import tornado.websocket

import utils


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


connections = set()
logger = logging.getLogger("doorbell")


def initialize(self, config, message_types):
    self.config = config
    self.message_types = message_types


def with_config_and_message_types(cls):
    cls.initialize = initialize
    return cls


@with_config_and_message_types
class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        logger.info("got a connection...")
        connections.add(self)

    def on_message(self, message):
        message = json.loads(message)
        logger.info('message', message)
        message_type = message['type']
        if message_type == self.message_types['request_volume']:
            self.write_message({
                "type": self.message_types['receive_volume'],
                "volume": pygame.mixer.music.get_volume(),
            })
        elif message_type == self.message_types['update_volume']:
            new_volume = message['volume']
            logger.info('new volume =', new_volume)
            pygame.mixer.music.set_volume(new_volume)
            for client in connections:
                if client is not self:
                    client.write_message({
                        "type": self.message_types['receive_volume'],
                        "volume": new_volume,
                    })

    def on_close(self):
        connections.remove(self)

    # @override
    def write_message(self, message):
        super().write_message(json.dumps(message))


@with_config_and_message_types
class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        template_context = dict(
            message_types=self.message_types,
            bell_log=self._get_logs(),
            do_not_disturb_mode_is_on=utils.do_not_disturb_now(self.config),
            websocket_url="/websocket",
        )
        self.render(
            os.path.join(BASE_DIR, "template/status.html"),
            **template_context,
        )

    # TODO: Make this efficient for large log files!
    #       See https://stackoverflow.com/questions/7167008/
    def _get_logs(self, limit=40):
        return []
        # try:
        #     with open(os.path.join(BASE_DIR, "app.log")) as file:
        #         lines = file.readlines()
        # except OSError:
        #     lines = []
        # return reversed(lines[:-limit])


def start(config, message_types):
    initialization_kwargs = dict(
        config=config,
        message_types=message_types,
    )
    app = tornado.web.Application(
        [
            (r"/status", StatusHandler, initialization_kwargs),
            (r"/websocket", WebSocketHandler, initialization_kwargs),
        ],
        static_path=os.path.join(BASE_DIR, 'static'),
        static_url_prefix='/static/',
    )
    app.listen(config.port)
    print(app, config.port, message_types)
