class ServerConfig:
    host = "localhost"
    port = 8888
    notifications = {
        "max_volume": 0.05,
    }
    do_not_disturb = {
        "begin": [19, 30],
        "end": [7, 30]
    }
    audio_file = "DBSE.ogg"

    def __init__(self, *,
                 debug,
                 host=None, port=None, do_not_disturb=None, audio_file=None,
                 notifications=None):
        if debug:
            self.host = "localhost"
        elif host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if do_not_disturb is not None:
            self.do_not_disturb = do_not_disturb
        if audio_file is not None:
            self.audio_file = audio_file

        if notifications is None:
            notifications = {}
        self.notifications = {
            **self.notifications,
            **notifications,
        }

    def sanitized_dict(self):
        return {
            "host": self.host,
            "port": self.port,
            "do_not_disturb": self.do_not_disturb,
            "audio_file": self.audio_file,
            "notifications": {
                **self.notifications,
                "smtp_user": "••••••••••••••",
                "smtp_pass": "••••••••",
            },
        }
