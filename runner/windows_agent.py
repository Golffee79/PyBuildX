import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


SHARE = Path(os.environ.get("PYBUILDX_SHARE", r"\\VBOXSVR\gf-2417"))
RUNNER_DIR = Path(
    os.environ.get("PYBUILDX_RUNNER_DIR", str(SHARE / "pybuildx" / "runner"))
)
REQUEST = RUNNER_DIR / "request.json"
STATUS = RUNNER_DIR / "status.json"

BUILDER = Path(os.environ.get("PYBUILDX_BUILDER_ROOT", r"C:\pybuildx-builder"))
BOOTSTRAP_PYTHON = BUILDER / ".venv" / "Scripts" / "python.exe"
WORK = BUILDER / "work"
ENVS = BUILDER / "envs"

IGNORED_DIRS = {"build", "dist", ".git", ".venv", "__pycache__"}


def write_status(job_id, state="building", message=None, **extra):
    data = {"job_id": job_id, "state": state}
    if message:
        data["message"] = message
    data.update(extra)
    STATUS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def requirements_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_env_key(project_dir):
    digest = hashlib.sha256(project_dir.encode("utf-8")).hexdigest()[:12]
    name = Path(project_dir).name.replace(" ", "-")
    return f"{name}-{digest}"


def ensure_environment(job_id, project_dir, job_dir, requirements):
    env_dir = ENVS / project_env_key(project_dir)
    python = env_dir / "Scripts" / "python.exe"
    stamp = env_dir / ".requirements.sha256"

    if requirements:
        requirements_path = job_dir / requirements
        if not requirements_path.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements}")
        digest = requirements_digest(requirements_path)
    else:
        requirements_path = None
        digest = "no-requirements"

    cached_digest = stamp.read_text(encoding="utf-8").strip() if stamp.exists() else None

    if python.exists() and cached_digest == digest:
        write_status(job_id, message="Dependencies unchanged; using cached Windows environment...")
        return python

    if env_dir.exists():
        write_status(job_id, message="Dependencies changed; rebuilding Windows environment...")
        shutil.rmtree(env_dir)
    else:
        write_status(job_id, message="Creating Windows build environment...")

    ENVS.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(BOOTSTRAP_PYTHON), "-m", "venv", str(env_dir)], check=True)

    install = [str(python), "-m", "pip", "install", "PyInstaller"]
    if requirements_path:
        install += ["-r", str(requirements_path)]

    write_status(job_id, message="Installing Windows dependencies (first build may take a while)...")
    subprocess.run(install, check=True)
    stamp.write_text(digest, encoding="utf-8")
    return python


def ignored(relative_path):
    if any(part in IGNORED_DIRS for part in relative_path.parts):
        return True
    return relative_path.suffix == ".spec"


def sync_project(source, destination):
    """Mirror source while preserving PyInstaller build/dist caches."""
    destination.mkdir(parents=True, exist_ok=True)
    source_files = set()

    for src in source.rglob("*"):
        relative = src.relative_to(source)
        if ignored(relative):
            continue
        target = destination / relative
        if src.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        source_files.add(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)

    for target in sorted(destination.rglob("*"), reverse=True):
        relative = target.relative_to(destination)
        if not relative.parts:
            continue
        if relative.parts[0] in {"build", "dist"} or relative.suffix == ".spec":
            continue
        if target.is_file() and relative not in source_files:
            target.unlink()
        elif target.is_dir():
            try:
                target.rmdir()
            except OSError:
                pass


def pyinstaller_command(python, name, entry, options):
    command = [str(python), "-m", "PyInstaller", "--noconfirm"]
    command.append("--onefile" if options.get("onefile", True) else "--onedir")
    command.append("--windowed" if options.get("windowed", True) else "--console")
    command += ["--name", name]

    for module in options.get("collect_submodules", []):
        command += ["--collect-submodules", module]
    for package in options.get("collect_all", []):
        command += ["--collect-all", package]
    for hidden_import in options.get("hidden_imports", []):
        command += ["--hidden-import", hidden_import]
    for data in options.get("add_data", []):
        command += ["--add-data", data]

    command.append(entry)
    return command


def build_job(job):
    job_id = job.get("job_id", "unknown")
    project_dir = job["project_dir"]
    name = job["name"]
    entry = job["entry"]
    requirements = job.get("requirements")
    options = job.get("build", {})
    release = bool(job.get("release", False))

    source = SHARE / project_dir
    mode = "release" if release else "dev"
    job_dir = WORK / project_dir / mode

    print()
    print(f"Project: {project_dir}")
    print(f"Mode: {mode}")
    print(f"Source: {source}")

    write_status(job_id, message="Syncing project to Windows build cache...")
    sync_project(source, job_dir)

    python = ensure_environment(job_id, project_dir, job_dir, requirements)

    write_status(job_id, message="Building Windows executable with PyInstaller cache...")
    subprocess.run(
        pyinstaller_command(python, name, entry, options),
        cwd=job_dir,
        check=True,
    )

    artifact = job_dir / "dist" / (f"{name}.exe" if options.get("onefile", True) else name)
    output = source / "dist" / "windows"
    output.mkdir(parents=True, exist_ok=True)
    destination = output / artifact.name

    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    if artifact.is_dir():
        shutil.copytree(artifact, destination)
    else:
        shutil.copy2(artifact, destination)

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
        write_status(job_id, message="Windows agent accepted build job...")

        try:
            artifact = build_job(job)
            write_status(
                job_id,
                state="success",
                message="Windows build finished.",
                artifact=str(artifact),
            )
            print()
            print("Windows build complete!")
            print(f"Artifact: {artifact}")
            print("Waiting for next job...")
        except Exception as error:
            write_status(job_id, state="failed", error=str(error))
            print(f"Build failed: {error}")
            print("Waiting for next job...")
        finally:
            REQUEST.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
