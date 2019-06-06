#!/usr/bin/env bash


ssh raspi 'cd Developer/raspi_doorbell && git reset HEAD --hard && git checkout master && git pull'

npx parcel build --out-dir static/dist static/status.js
scp static/dist/status.js raspi:Developer/raspi_doorbell/static/dist/status.js
scp static/dist/status.js.map raspi:Developer/raspi_doorbell/static/dist/status.js.map

scp src/local_config.py raspi:Developer/raspi_doorbell/src/local_config.py
