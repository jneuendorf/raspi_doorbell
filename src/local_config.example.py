cookie_secret = "some really secure string"
# Generate as described here: https://github.com/hynek/argon2-cffi
password_hash = "$argon2id$v=19$m=102400,t=2,p=8$tSm+JOWigOgPZx/g44K5fQ$WDyus6py50bVFIPkjA28lQ"  # NOQA

port = 8888

notifications = {
    "recipients": ["my.name@gmx.de", "some.other.name@gmx.de"],
    "addr_from": "my.name@gmx.de",
    "smtp_server": "mail.gmx.net",
    "smtp_user": "my.name@gmx.de",
    "smtp_pass": "my.password",
    "max_volume": 0.05,
}

do_not_disturb = {
    "begin": [20, 30],
    "end": [8, 30],
}
