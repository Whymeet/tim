#!/usr/bin/env python3
"""
Скрипт для быстрого включения/отключения прокси
Использование:
    python proxy_toggle.py on    - включить прокси
    python proxy_toggle.py off   - отключить прокси
    python proxy_toggle.py       - показать текущий статус
"""

import sys
import re
import os

def get_current_proxy_status():
    """Читает текущий статус прокси из config.py"""
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Ищем строку USE_PROXY = True/False
        match = re.search(r'USE_PROXY\s*=\s*(True|False)', content)
        if match:
            return match.group(1) == 'True'
        return False
    except FileNotFoundError:
        print("❌ Файл config.py не найден!")
        return False

def set_proxy_status(enabled):
    """Устанавливает статус прокси в config.py"""
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Заменяем USE_PROXY = True/False
        new_value = 'True' if enabled else 'False'
        new_content = re.sub(
            r'USE_PROXY\s*=\s*(True|False)', 
            f'USE_PROXY = {new_value}', 
            content
        )
        
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
    except Exception as e:
        print(f"❌ Ошибка при изменении config.py: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        # Показываем текущий статус
        current = get_current_proxy_status()
        status = "включен ✅" if current else "отключен ❌"
        print(f"🌐 Прокси {status}")
        print("\nИспользование:")
        print("  python proxy_toggle.py on   - включить прокси")
        print("  python proxy_toggle.py off  - отключить прокси")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'on':
        if set_proxy_status(True):
            print("✅ Прокси включен")
        else:
            print("❌ Не удалось включить прокси")
    elif command == 'off':
        if set_proxy_status(False):
            print("✅ Прокси отключен")
        else:
            print("❌ Не удалось отключить прокси")
    else:
        print("❌ Неизвестная команда. Используйте 'on' или 'off'")

if __name__ == "__main__":
    main()
