@echo off
chcp 65001 >nul
title VK Ads Proxy Toggle

echo ==========================================
echo        VK Ads Report - Proxy Toggle
echo ==========================================
echo.

if "%1"=="on" (
    python proxy_toggle.py on
    goto end
)

if "%1"=="off" (
    python proxy_toggle.py off
    goto end
)

echo Выберите действие:
echo 1 - Включить прокси
echo 2 - Отключить прокси
echo 3 - Показать текущий статус
echo 0 - Выход
echo.

set /p choice="Ваш выбор (1-3): "

if "%choice%"=="1" (
    python proxy_toggle.py on
) else if "%choice%"=="2" (
    python proxy_toggle.py off
) else if "%choice%"=="3" (
    python proxy_toggle.py
) else if "%choice%"=="0" (
    exit
) else (
    echo Неверный выбор!
    pause
    goto start
)

:end
echo.
pause
