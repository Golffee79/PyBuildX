import json
import os
import time
import uuid
from pathlib import Path

from .virtualbox import start_vm


RUNNER_DIR = Path(
    os.environ.get(
        "PYBUILDX_HOST_RUNNER_DIR",
        str(Path.home() / "pybuildx" / "runner"),
    )
)
REQUEST = RUNNER_DIR / "request.json"
STATUS = RUNNER_DIR / "status.json"


def build_windows(name, entry, requirements=None, build_options=None, release=False):
    print("Preparing Windows runner...")

    vm_name = os.environ.get("PYBUILDX_WINDOWS_VM", "D365")
    start_vm(vm_name)

    project_path = Path.cwd().resolve()

    try:
        project_dir = project_path.relative_to(Path.home()).as_posix()
    except ValueError:
        raise RuntimeError(
            "Project must currently be located inside your home directory."
        )

    RUNNER_DIR.mkdir(parents=True, exist_ok=True)

    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "project_dir": project_dir,
        "name": name,
        "entry": str(entry),
        "requirements": requirements,
        "build": build_options or {},
        "release": release,
    }

    STATUS.unlink(missing_ok=True)
    temp_request = REQUEST.with_suffix(".tmp")
    temp_request.write_text(json.dumps(job, indent=2), encoding="utf-8")
    temp_request.replace(REQUEST)

    print(f"Job: {job_id}")
    print("Waiting for Windows build...")

    deadline = time.monotonic() + 1800
    last_message = None

    while time.monotonic() < deadline:
        if not STATUS.exists():
            time.sleep(1)
            continue

        try:
            status = json.loads(STATUS.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            time.sleep(1)
            continue

        if status.get("job_id") != job_id:
            time.sleep(1)
            continue

        message = status.get("message")
        if message and message != last_message:
            print(message)
            last_message = message

        state = status.get("state")
        if state == "building":
            time.sleep(1)
            continue
        if state == "success":
            print("Windows build complete!")
            print(f"Artifact: {status['artifact']}")
            return
        if state == "failed":
            raise RuntimeError(
                f"Windows build failed: {status.get('error')}"
            )

        time.sleep(1)

    raise TimeoutError("Timed out waiting for Windows build.")
