"""Base collector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DataPoint:
    timestamp: datetime
    source: str
    data_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    @abstractmethod
    async def collect(self) -> List[DataPoint]:
        """Collect data from source."""
        pass

    @abstractmethod
    async def collect_one(self, symbol: str) -> Optional[DataPoint]:
        """Collect data for a single symbol."""
        pass

    def format_for_llm(self, data: List[DataPoint]) -> str:
        """Format collected data for LLM analysis."""
        lines = []
        for dp in data:
            lines.append(f"[{dp.timestamp.isoformat()}] {dp.source}: {dp.data_type}")
            for key, value in dp.content.items():
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
