# raspi_doorbell

Attach your raspberry pi to your doorbell and get notified on your phone.

This repository contains the code for a raspberry pi attached to your doorbell
(GPIO) as well as the code for a mobile app (iOS, Android) that receives a
message whenever the bell is rung.


## Commands

`npx parcel watch --out-dir static/dist static/status.js`
`npx parcel build --out-dir static/dist static/status.js`

`python3 src/main.py --debug`

pipenv does not work, but python3 -m venv venv

sudo apt-get install git
sudo apt-get install python3-pip python3-venv
sudo apt-get install libsdl1.2-dev
sudo apt-get install libsdl-mixer1.2
