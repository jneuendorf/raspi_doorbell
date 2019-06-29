#!/usr/bin/env bash

echo "amixer set PCM -- '$1%'"
amixer set PCM -- "$1%"
