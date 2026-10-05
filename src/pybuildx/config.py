from pathlib import Path


def init_project():
    config_file = Path("pybuildx.toml")

    if config_file.exists():
        print("pybuildx.toml already exists")
        return

    content = """[project]
name = "MyApp"
entry = "main.py"
"""

    config_file.write_text(content)

    print("Created pybuildx.toml")
