import os
from pathlib import Path

STARTUP_DIR = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
VENV_PYTHONW = Path(r"D:\projects\whatsapp-agent\venv\Scripts\pythonw.exe")
WATCH_SCRIPT = Path(r"D:\projects\whatsapp-agent\watch_wispr.py")
VBS_PATH = STARTUP_DIR / "WisprCloudSync.vbs"

vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\\projects\\whatsapp-agent"
WshShell.Run chr(34) & "{VENV_PYTHONW}" & chr(34) & " " & chr(34) & "{WATCH_SCRIPT}" & chr(34), 0, False
'''

def install():
    VBS_PATH.write_text(vbs_content, encoding="utf-8")
    print(f"SUCCESS: Auto-sync watcher written to:\n{VBS_PATH}")

if __name__ == "__main__":
    install()
