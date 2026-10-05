import subprocess
import sys


def build_local(name, entry):
    print("Building locally...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--name",
            name,
            str(entry),
        ],
        check=True,
    )

    print("Local build complete!")
