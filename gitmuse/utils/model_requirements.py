"""
This module defines the requirements for different AI models and provides
functions to determine which models are supported based on the system's hardware.
"""

from typing import Dict, List, Any

# Define model requirements
MODEL_REQUIREMENTS = {
    "gemma2:27b": {
        "min_ram": 32,  # GB
        "min_gpu_ram": 24,  # GB
        "cuda_required": True,
    },
    "llama3.2": {
        "min_ram": 16,  # GB
        "min_gpu_ram": 16,  # GB
        "cuda_required": True,
    },
    "gpt-3.5-turbo": {
        "min_ram": 8,  # GB
        "cuda_required": False,
    },
    "gpt-4": {
        "min_ram": 16,  # GB
        "cuda_required": False,
    },
    # Add more models and their requirements as needed
}

def get_supported_models(hardware_report: Dict[str, Any]) -> List[str]:
    """
    Determine which models are supported based on the hardware report.

    :param hardware_report: A dictionary containing hardware information
    :return: A list of supported model names
    """
    supported_models = []

    for model, requirements in MODEL_REQUIREMENTS.items():
        if meets_requirements(hardware_report, requirements):
            supported_models.append(model)

    return supported_models

def meets_requirements(hardware_report: Dict[str, Any], requirements: Dict[str, Any]) -> bool:
    """
    Check if the system meets the requirements for a specific model.

    :param hardware_report: A dictionary containing hardware information
    :param requirements: A dictionary containing model requirements
    :return: True if the system meets the requirements, False otherwise
    """
    # Check RAM
    system_ram = float(hardware_report["RAM Total"].split()[0])
    if system_ram < requirements.get("min_ram", 0):
        return False

    # Check CUDA availability if required
    if requirements.get("cuda_required", False) and not hardware_report["CUDA Available"]:
        return False

    # Check GPU RAM if required
    if "min_gpu_ram" in requirements:
        if not hardware_report["CUDA Available"]:
            return False
        gpu_ram = float(hardware_report["GPU Memory"].split()[0])
        if gpu_ram < requirements["min_gpu_ram"]:
            return False

    return True
