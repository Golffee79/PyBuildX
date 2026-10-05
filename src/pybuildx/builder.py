from pathlib import Path
import subprocess
import sys
import tomllib


def build():
    config_path = Path("pybuildx.toml")

    if not config_path.exists():
        print("Error: pybuildx.toml not found")
        print("Run: pybuildx init")
        return

    with config_path.open("rb") as file:
        config = tomllib.load(file)

    project = config["project"]

    name = project["name"]
    entry = Path(project["entry"])

    if not entry.exists():
        print(f"Error: {entry} not found")
        return

    print(f"Project: {name}")
    print(f"Entry: {entry}")
    print("Building...")

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

    print("Build complete!")
