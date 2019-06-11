#!/usr/bin/env python3

import sys

from argon2 import PasswordHasher


ph = PasswordHasher()
hash = ph.hash(sys.argv[1])
print(hash)
