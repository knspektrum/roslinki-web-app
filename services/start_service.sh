#!/bin/bash
cd /home/<username>/roslinki-web-app

for i in {1..15}; do
    ping -c 1 github.com > /dev/null 2>&1 && break
    sleep 1
done

git fetch origin rpi-service_LostyGuy_version

git checkout origin/rpi-service_LostyGuy_version -- services/rpi_service.py

python3 services/rpi_service.py
 