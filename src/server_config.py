class ServerConfig:
    port = 8888
    notifications = {
        "max_volume": 0.05,
    }
    do_not_disturb = {
        "begin": [19, 30],
        "end": [7, 30]
    }
    audio_file = "DBSE.ogg"

    cookie_secret = None
    password_hash = None

    def __init__(self, *,
                 debug, cookie_secret, password_hash,
                 port=None, do_not_disturb=None, audio_file=None,
                 notifications=None):
        self.debug = debug
        self.cookie_secret = cookie_secret
        self.password_hash = password_hash

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
            "debug": self.debug,
            "cookie_secret": "••••••••••••••••••••••••••••••••••••••••••••••••",
            "password_hash": self.password_hash,
            "port": self.port,
            "do_not_disturb": self.do_not_disturb,
            "audio_file": self.audio_file,
            "notifications": {
                **self.notifications,
                "smtp_user": "••••••••••••••",
                "smtp_pass": "••••••••",
            },
        }
