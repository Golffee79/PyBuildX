import json
import shutil
import subprocess
import time
from pathlib import Path


SHARE = Path(r"\\VBOXSVR\gf-2417")

RUNNER_DIR = SHARE / "pybuildx" / "runner"
REQUEST = RUNNER_DIR / "request.json"
STATUS = RUNNER_DIR / "status.json"

BUILDER = Path(r"C:\pybuildx-builder")
PYTHON = BUILDER / ".venv" / "Scripts" / "python.exe"
WORK = BUILDER / "work"


def write_status(data):
    STATUS.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def build_job(job):
    project_dir = job["project_dir"]
    name = job["name"]
    entry = job["entry"]

    source = SHARE / project_dir
    job_dir = WORK / project_dir

    print()
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

    return destination


def main():
    print("PyBuildX Windows Agent")
    print("Waiting for jobs...")

    while True:
        if not REQUEST.exists():
            time.sleep(1)
            continue

        try:
            with REQUEST.open("r", encoding="utf-8") as file:
                job = json.load(file)
        except (OSError, json.JSONDecodeError):
            time.sleep(1)
            continue

        job_id = job.get("job_id", "unknown")

        write_status({
            "job_id": job_id,
            "state": "building",
        })

        try:
            artifact = build_job(job)

            write_status({
                "job_id": job_id,
                "state": "success",
                "artifact": str(artifact),
            })

            print()
            print("Windows build complete!")
            print(f"Artifact: {artifact}")
            print("Waiting for next job...")

        except Exception as error:
            write_status({
                "job_id": job_id,
                "state": "failed",
                "error": str(error),
            })

            print(f"Build failed: {error}")
            print("Waiting for next job...")

        finally:
            REQUEST.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
