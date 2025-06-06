from dataclasses import dataclass
from typing import List, Optional, Dict, ClassVar
from enum import Enum

class Vendor(Enum):
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    UNKNOWN = "UNKNOWN"

@dataclass
class AvailableGPU:
    id: str
    display_name: str
    memory_in_gb: int

    # Class variable to store all GPU instances
    _all_gpus: ClassVar[Dict[str, 'AvailableGPU']] = {}

    def __post_init__(self):
        # Validate memory
        if not self.memory_in_gb > 0:
            raise ValueError("Memory must be non-negative")

        AvailableGPU._all_gpus[self.id] = self

    @property
    def vendor(self) -> Vendor:
        if self.id.startswith("NVIDIA"):
            return Vendor.NVIDIA
        elif self.id.startswith("AMD"):
            return Vendor.AMD
        return Vendor.UNKNOWN

    @classmethod
    def from_dict(cls, data: dict) -> 'AvailableGPU':
        return cls(
            id=data['id'],
            display_name=data['displayName'],
            memory_in_gb=data['memoryInGb']
        )

    @classmethod
    def from_list(cls, gpu_list: List[dict]) -> List['AvailableGPU']:
        all_gpus = []
        for gpu_data in gpu_list:
            if gpu_data['memoryInGb'] < 1:
                continue
            gpu = cls.from_dict(gpu_data)
            all_gpus.append(gpu)
        return all_gpus

    @classmethod
    def get_by_id(cls, gpu_id: str) -> Optional['AvailableGPU']:
        """Retrieve a GPU instance by its ID"""
        return cls._all_gpus.get(gpu_id)

    @classmethod
    def get_gpu_closest_to_memory(cls, memory_in_gb: int, limit: int = 5) -> List['AvailableGPU']:
        """Get the top N GPUs with memory closest to the specified amount

        Args:
            memory_in_gb: Target memory amount in GB
            limit: Maximum number of GPUs to return

        Returns:
            List of GPUs ordered by how close their memory is to the target amount
        """
        if not cls._all_gpus:
            return []

        # Sort GPUs by absolute difference from target memory
        sorted_gpus = sorted(
            cls._all_gpus.values(),
            key=lambda gpu: abs(gpu.memory_in_gb - memory_in_gb)
        )

        # Return up to limit GPUs
        return sorted_gpus[:limit]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.memory_in_gb}GB). ID: {self.id}"