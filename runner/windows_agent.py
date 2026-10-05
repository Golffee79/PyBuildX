import json
import shutil
import subprocess
from pathlib import Path


SHARE = Path(r"\\VBOXSVR\gf-2417")
REQUEST = SHARE / "pybuildx" / "runner" / "request.json"

BUILDER = Path(r"C:\pybuildx-builder")
PYTHON = BUILDER / ".venv" / "Scripts" / "python.exe"
WORK = BUILDER / "work"


def main():
    print("PyBuildX Windows Agent")

    with REQUEST.open("r", encoding="utf-8") as f:
        job = json.load(f)

    project_dir = job["project_dir"]
    name = job["name"]
    entry = job["entry"]

    source = SHARE / project_dir
    job_dir = WORK / project_dir

    print(f"Project: {project_dir}")
    print(f"Source: {source}")

    if job_dir.exists():
        shutil.rmtree(job_dir)

    print("Copying project to Windows...")

    shutil.copytree(
        source,
        job_dir,
        ignore=shutil.ignore_patterns(
            "build",
            "dist",
            ".git",
            ".venv",
            "__pycache__",
            "*.spec",
        ),
    )

    print("Building Windows executable...")

    subprocess.run(
        [
            str(PYTHON),
            "-m",
            "PyInstaller",
            "--onefile",
            "--windowed",
            "--name",
            name,
            entry,
        ],
        cwd=job_dir,
        check=True,
    )

    exe = job_dir / "dist" / f"{name}.exe"

    output = source / "dist" / "windows"
    output.mkdir(parents=True, exist_ok=True)

    destination = output / f"{name}.exe"

    shutil.copy2(exe, destination)

    print()
    print("Windows build complete!")
    print(f"Artifact: {destination}")


if __name__ == "__main__":
    main()
