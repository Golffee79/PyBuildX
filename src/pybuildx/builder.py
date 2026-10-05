from pathlib import Path
import sys
import tomllib

from .runners.local import build_local
from .runners.windows import build_windows


def get_host_platform():
    if sys.platform.startswith("linux"):
        return "linux"

    if sys.platform.startswith("win"):
        return "windows"

    if sys.platform == "darwin":
        return "macos"

    return "unknown"


def build(target=None):
    config_path = Path("pybuildx.toml")

    if not config_path.exists():
        print("Error: pybuildx.toml not found")
        print("Run: pybuildx init")
        return

    with config_path.open("rb") as file:
        config = tomllib.load(file)

    project = config["project"]
    dependencies = config.get("dependencies", {})
    build_options = config.get("build", {})

    name = project["name"]
    entry = Path(project["entry"])
    requirements = dependencies.get("requirements")

    if not entry.exists():
        print(f"Error: {entry} not found")
        return

    if requirements and not Path(requirements).exists():
        print(f"Error: requirements file not found: {requirements}")
        return

    host = get_host_platform()

    if target is None:
        target = host

    print(f"Project: {name}")
    print(f"Entry: {entry}")
    print(f"Host: {host}")
    print(f"Target: {target}")

    if target == host:
        build_local(name, entry)
        return

    if host == "linux" and target == "windows":
        build_windows(
            name,
            entry,
            requirements=requirements,
            build_options=build_options,
        )
        return

    print()
    print(f"No runner available for {host} -> {target}")
