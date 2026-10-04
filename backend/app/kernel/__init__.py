"""
NexPath Career Operating System Kernel Package.
Permanent UI-independent source of truth for candidate career state.
"""

from app.kernel.state import KernelState
from app.kernel.manager import kernel_manager, KernelManager

__all__ = [
    "KernelState",
    "kernel_manager",
    "KernelManager"
]
