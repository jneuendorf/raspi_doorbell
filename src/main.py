#!/usr/bin/env bash

import sys

from app import App


if sys.version_info[0:2] != (3, 5):
    raise RuntimeError('Python 3.5 required but got ' + sys.version)


if __name__ == "__main__":
    args = sys.argv[1:]
    app = App(
        debug=(True if args and args[0] == "--debug" else False),
    )
    app.start()
