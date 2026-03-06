#!/bin/bash
set -e

MODE="${1:-main}"

if [ "$MODE" = "auth" ]; then
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 &
    sleep 1
    x11vnc -display :99 -forever -passwd "${VNC_PASSWORD:-admin}" &
    websockify --web /usr/share/novnc 6080 localhost:5900 &
    sleep 1
    echo ""
    echo "========================================="
    echo " noVNC: http://localhost:6080/vnc.html"
    echo "========================================="
    echo ""
    echo "Откройте ссылку выше в браузере."
    echo "Авторизуйтесь в VK, затем нажмите Enter здесь."
    echo ""
    python vk_ads_auth.py
else
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 &
    sleep 1
    x11vnc -display :99 -forever -passwd "${VNC_PASSWORD:-admin}" &
    websockify --web /usr/share/novnc 6080 localhost:5900 &
    sleep 1
    echo ""
    echo "========================================="
    echo " noVNC: http://localhost:6080/vnc.html"
    echo "========================================="
    echo ""
    python main.py
fi
