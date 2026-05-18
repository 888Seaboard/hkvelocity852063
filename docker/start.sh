#!/bin/sh
set -e

export DISPLAY=:99
export VNC_PASSWORD="${VNC_PASSWORD:-1234}"

mkdir -p ~/.vnc
x11vnc -storepasswd "$VNC_PASSWORD" ~/.vnc/passwd

Xvfb :99 -screen 0 1280x720x24 -ac &
fluxbox &

x11vnc -display :99 -rfbauth ~/.vnc/passwd -forever -shared -repeat -rfbport 5900 &
websockify --web=/usr/share/novnc 6080 localhost:5900 &

google-chrome --no-sandbox --disable-dev-shm-usage --user-data-dir=/tmp/chrome --window-size=1280,720 about:blank &

wait