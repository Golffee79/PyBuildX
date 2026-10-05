from pathlib import Path


def init_project():
    config_file = Path("pybuildx.toml")

    if config_file.exists():
        print("pybuildx.toml already exists")
        return

    sections = [
        '[project]\nname = "MyApp"\nentry = "main.py"',
    ]

    if Path("requirements.txt").exists():
        sections.append('[dependencies]\nrequirements = "requirements.txt"')

    sections.append('[build]\nonefile = true\nwindowed = true')
    config_file.write_text("\n\n".join(sections) + "\n", encoding="utf-8")

    print("Created pybuildx.toml")
