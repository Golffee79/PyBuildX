import subprocess
import sys


def build_local(name, entry, build_options=None):
    options = build_options or {}
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm"]

    command.append("--onefile" if options.get("onefile", True) else "--onedir")
    command.append("--windowed" if options.get("windowed", False) else "--console")
    command += ["--name", name, str(entry)]

    print("Building locally...")
    subprocess.run(command, check=True)
    print("Local build complete!")
