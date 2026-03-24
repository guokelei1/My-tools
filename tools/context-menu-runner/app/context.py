from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class InvocationContext:
    invocation_type: str
    target_path: Path
    working_directory: Path
    install_root: Path
    timestamp: str
    raw_args: list[str] = field(default_factory=list)
    selected_paths: list[Path] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        invocation_type: str,
        target_path: str,
        install_root: Path,
        raw_args: list[str] | None = None,
    ) -> 'InvocationContext':
        resolved_target = Path(target_path).expanduser().resolve(strict=False)

        if invocation_type == 'background' or resolved_target.is_dir():
            working_directory = resolved_target
        else:
            working_directory = resolved_target.parent

        return cls(
            invocation_type=invocation_type,
            target_path=resolved_target,
            working_directory=working_directory,
            install_root=install_root.resolve(strict=False),
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_args=list(raw_args or []),
        )

    def to_environment(self) -> dict[str, str]:
        return {
            'CMR_INVOCATION_TYPE': self.invocation_type,
            'CMR_TARGET_PATH': str(self.target_path),
            'CMR_WORKING_DIRECTORY': str(self.working_directory),
            'CMR_INSTALL_ROOT': str(self.install_root),
            'CMR_TIMESTAMP': self.timestamp,
        }
