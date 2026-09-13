from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union
from uuid import UUID

from app.pipeline.contracts import NormalizedSonarFrame


class BaseDeviceAdapter(ABC):
    """Abstract interface for side-scan sonar format ingest adapters."""

    @abstractmethod
    def parse(
        self,
        source: Union[str, Path, bytes],
        survey_id: UUID,
        sss_file_id: Union[UUID, None] = None,
        **kwargs,
    ) -> List[NormalizedSonarFrame]:
        """
        Parses raw sonar binary or image into a list of NormalizedSonarFrame instances.
        Each frame contains along-track waterfall lines and navigation metadata.
        """
        pass
