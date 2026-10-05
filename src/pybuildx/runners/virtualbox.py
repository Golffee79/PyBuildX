import subprocess


def get_vm_state(vm_name):
    result = subprocess.run(
        [
            "VBoxManage",
            "showvminfo",
            vm_name,
            "--machinereadable",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in result.stdout.splitlines():
        if line.startswith("VMState="):
            return line.split("=", 1)[1].strip('"')

    return "unknown"


def start_vm(vm_name):
    state = get_vm_state(vm_name)

    print(f"Windows VM: {vm_name}")
    print(f"VM state: {state}")

    if state == "running":
        print("VM already running.")
        return

    print("Starting VM...")

    subprocess.run(
        [
            "VBoxManage",
            "startvm",
            vm_name,
            "--type",
            "headless",
        ],
        check=True,
    )

    print("VM started.")
