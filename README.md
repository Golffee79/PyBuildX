# PyBuildX

PyBuildX is a small build orchestrator for Python desktop applications. It lets a Linux workstation build Linux artifacts locally and hand Windows builds to a real Windows VM running PyInstaller.

## Status

Current milestone: M1.2 prototype.

Working flow:

```text
Linux host
  -> pybuildx build --target windows
  -> starts a VirtualBox Windows VM if needed
  -> writes a build job to the shared folder
  -> Windows agent syncs the project
  -> cached per-project venv installs dependencies only when requirements change
  -> PyInstaller builds on Windows
  -> artifact is copied back to the Linux project
```

## Install for development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Project configuration

Create `pybuildx.toml` in the application root:

```toml
[project]
name = "MyApp"
entry = "main.py"

[dependencies]
requirements = "requirements.txt"

[build]
onefile = true
windowed = true
collect_submodules = ["UI", "LIB"]
collect_all = ["dash_ag_grid"]
add_data = ["RPT/*.lrxml:RPT"]
```

## Build modes

Fast development build (Windows uses `onedir` and preserves the PyInstaller build cache):

```bash
pybuildx build --target windows
```

Release build (uses the project's `onefile` setting, defaulting to `true`):

```bash
pybuildx build --target windows --release
```

Linux builds use the same dev/release mode selection.

## Windows runner

The current prototype uses VirtualBox and a Windows agent. The Linux side defaults to VM name `D365`; override it with:

```bash
export PYBUILDX_WINDOWS_VM="YourWindowsVM"
```

The Windows agent supports these environment variables:

- `PYBUILDX_SHARE` - VirtualBox shared-folder root visible in Windows.
- `PYBUILDX_RUNNER_DIR` - directory containing `request.json` and `status.json`.
- `PYBUILDX_BUILDER_ROOT` - Windows cache root (default `C:\pybuildx-builder`).

The prototype defaults are currently tailored to the original development machine, so set these values for another host.

## Caching

PyBuildX keeps two independent caches on Windows:

1. Dependency cache: one virtual environment per project, invalidated by the SHA-256 of the requirements file.
2. Build cache: separate `dev` and `release` working trees preserve PyInstaller's `build/` and `dist/` state between runs.

Project files are mirrored into the cached working tree while generated build directories are preserved.

## Current limitations

- Windows runner currently assumes VirtualBox.
- Job transport uses one shared `request.json` / `status.json` slot, so concurrent builds are not supported yet.
- Runner setup is still machine-level configuration rather than a first-class PyBuildX config command.
- macOS is not implemented.

## License

No license has been selected yet.
