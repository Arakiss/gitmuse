"""
This module is a fork of the hardware check functionality from the RedWheel project.
Original source: https://github.com/Arakiss/redwheel/blob/main/redwheel/core/hardware_check.py

It has been adapted and extended for use in the GitMuse project.
"""

import torch
import psutil  # type: ignore
import platform
import os
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .model_requirements import get_supported_models

console = Console()


def is_wsl():
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except IOError:
        return False


def get_wsl_host_memory():
    try:
        # Intenta obtener la memoria total del host
        cmd_total = 'powershell.exe -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"'
        total_bytes = int(
            subprocess.check_output(cmd_total, shell=True, stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
        total_gb = total_bytes / (1024**3)

        # Intenta obtener la memoria disponible
        try:
            cmd_available = "powershell.exe -Command \"(Get-Counter '\\Memory\\Available Bytes').CounterSamples.CookedValue\""
            available_bytes = int(
                float(
                    subprocess.check_output(
                        cmd_available, shell=True, stderr=subprocess.DEVNULL
                    )
                    .decode()
                    .strip()
                )
            )
        except subprocess.CalledProcessError:
            # Si falla, usa la información de /proc/meminfo
            with open("/proc/meminfo", "r") as f:
                mem_info = f.read()
            available_kb = int(
                [line for line in mem_info.split("\n") if "MemAvailable" in line][
                    0
                ].split()[1]
            )
            available_bytes = available_kb * 1024

        available_gb = available_bytes / (1024**3)
        used_percent = ((total_bytes - available_bytes) / total_bytes) * 100

        return {
            "total": total_gb,
            "available": available_gb,
            "used_percent": used_percent,
        }
    except Exception as e:
        console.print(
            f"[yellow]Warning: Unable to get host memory information. Error: {e}"
        )
        return {"total": 0, "available": 0, "used_percent": 0}


def get_cpu_info():
    if platform.system() == "Windows":
        return platform.processor()
    elif platform.system() == "Darwin":
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + "/usr/sbin"
        command = "sysctl -n machdep.cpu.brand_string"
        return subprocess.check_output(command).strip().decode()
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo"
        all_info = subprocess.check_output(command, shell=True).strip().decode()
        for line in all_info.split("\n"):
            if "model name" in line:
                return line.split(":")[1].strip()
    return platform.processor()


def get_os_info():
    system = platform.system()
    release = platform.release()
    if system == "Linux":
        try:
            with open("/etc/os-release") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=")[1].strip().strip('"')
        except IOError:
            pass
    return f"{system} {release}"


def check_hardware():
    report = {}

    # Get username
    try:
        report["Username"] = os.getlogin()
    except OSError:
        try:
            import pwd
            report["Username"] = pwd.getpwuid(os.getuid())[0]
        except ImportError:
            report["Username"] = "User"

    # Check CUDA availability and details
    try:
        report["CUDA Available"] = torch.cuda.is_available()
        if report["CUDA Available"]:
            report["CUDA Version"] = torch.version.cuda
            report["GPU Name"] = torch.cuda.get_device_name(0)
            report["GPU Memory"] = (
                f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
            )
        else:
            report["CUDA Version"] = "N/A"
            report["GPU Name"] = "N/A"
            report["GPU Memory"] = "N/A"
    except Exception as e:
        report["CUDA Available"] = False
        report["CUDA Version"] = f"Error: {e}"
        report["GPU Name"] = f"Error: {e}"
        report["GPU Memory"] = "N/A"

    # Check RAM
    vm = psutil.virtual_memory()
    report["RAM Total"] = f"{vm.total / (1024**3):.2f} GB"
    report["RAM Available"] = f"{vm.available / (1024**3):.2f} GB"
    report["RAM Usage"] = f"{vm.percent}%"

    # Check if running in WSL
    if is_wsl():
        wsl_host_memory = get_wsl_host_memory()
        report["WSL Warning"] = (
            "Warning: Running in WSL. Host RAM information may be limited."
        )
        report["Host RAM Total"] = f"{wsl_host_memory['total']:.2f} GB"
        report["Host RAM Available"] = f"{wsl_host_memory['available']:.2f} GB"
        report["Host RAM Usage"] = f"{wsl_host_memory['used_percent']:.1f}%"

        if wsl_host_memory["total"] == 0:
            report["WSL Warning"] += " Unable to retrieve host RAM information."
    else:
        report["WSL Warning"] = None

    # Additional system info
    report["OS"] = get_os_info()
    report["CPU"] = get_cpu_info()
    report["CPU Cores"] = psutil.cpu_count(logical=False)
    report["CPU Threads"] = psutil.cpu_count(logical=True)
    report["CPU Usage"] = f"{psutil.cpu_percent()}%"

    return report


def display_hardware_report(report):
    table = Table(title="System Information", expand=True)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Details", style="magenta")

    table.add_row("OS", report["OS"])
    table.add_row("CPU", report["CPU"])
    table.add_row(
        "CPU Details", f"{report['CPU Cores']} cores, {report['CPU Threads']} threads"
    )
    table.add_row("CPU Usage", report["CPU Usage"])

    if report.get("WSL Warning"):
        if float(report["Host RAM Total"].split()[0]) > 0:
            table.add_row(
                "RAM (Host)",
                f"Total: {report['Host RAM Total']} ({report['Host RAM Usage']} used)",
            )
            table.add_row("RAM Available (Host)", report["Host RAM Available"])
        table.add_row(
            "RAM (WSL)", f"Total: {report['RAM Total']} ({report['RAM Usage']} used)"
        )
        table.add_row("RAM Available (WSL)", report["RAM Available"])
    else:
        table.add_row(
            "RAM", f"Total: {report['RAM Total']} ({report['RAM Usage']} used)"
        )
        table.add_row("RAM Available", report["RAM Available"])

    table.add_row(
        "GPU", f"{'Available' if report['CUDA Available'] else 'Not Available'}"
    )
    if report["CUDA Available"]:
        table.add_row(
            "GPU Details",
            f"{report['GPU Name']}, Memory: {report['GPU Memory']}, CUDA: {report['CUDA Version']}",
        )

    console.print(
        Panel(table, title=f"Hardware Report for {report['Username']}", expand=False)
    )


def check_minimum_requirements():
    report = check_hardware()
    supported_models = get_supported_models(report)
    return len(supported_models) > 0, supported_models


def print_system_summary(report, supported_models):
    summary = Table(title="System Summary", expand=True)
    summary.add_column("Metric", style="cyan")
    summary.add_column("Status", style="magenta")

    summary.add_row(
        "CPU",
        f"{report['CPU']} ({report['CPU Cores']} cores, {report['CPU Usage']} usage)",
    )

    if report.get("WSL Warning"):
        if float(report["Host RAM Total"].split()[0]) > 0:
            summary.add_row(
                "RAM (Host)",
                f"Total: {report['Host RAM Total']} ({report['Host RAM Usage']} used)",
            )
            summary.add_row("RAM Available (Host)", report["Host RAM Available"])
        summary.add_row(
            "RAM (WSL)",
            f"{report['RAM Total']} total, {report['RAM Usage']} used, {report['RAM Available']} available",
        )
    else:
        summary.add_row(
            "RAM",
            f"{report['RAM Total']} total, {report['RAM Usage']} used, {report['RAM Available']} available",
        )

    summary.add_row(
        "GPU", f"{'Available' if report['CUDA Available'] else 'Not Available'}"
    )
    if report["CUDA Available"]:
        summary.add_row(
            "GPU Details", f"{report['GPU Name']}, {report['GPU Memory']} Memory"
        )
    summary.add_row(
        "Supported Models", ", ".join(supported_models) if supported_models else "None"
    )

    console.print(
        Panel(summary, title=f"System Overview for {report['Username']}", expand=False)
    )


if __name__ == "__main__":
    hardware_report = check_hardware()
    display_hardware_report(hardware_report)
    meets_requirements, supported_models = check_minimum_requirements()
    username = hardware_report["Username"]
    print(f"\nWelcome, {username}!")
    print(f"Meets minimum requirements: {meets_requirements}")
    if meets_requirements:
        print("Supported models:")
        for model in supported_models:
            print(f"- {model}")
    print_system_summary(hardware_report, supported_models)