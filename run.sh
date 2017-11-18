#!/bin/bash

# TODO: Remove this file after https://github.com/resin-os/resinos/issues/199 is fixed

echo "Attaching hci0..."

if ! /usr/bin/hciattach /dev/ttyAMA0 bcm43xx 921600 noflow -; then
    echo "First try failed. Let's try another time."
    /usr/bin/hciattach /dev/ttyAMA0 bcm43xx 921600 noflow -
fi

echo "Bring hci0 up..."
hciconfig hci0 up

# Move this as a docker entrypoint
python3 desk.py
