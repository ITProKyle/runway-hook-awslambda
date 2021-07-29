"""Base classes."""
from __future__ import annotations

from typing import Any

from runway.compat import cached_property

from ...base_classes import DependencyManager


class PythonDependencyManager(DependencyManager):
    """Python dependency manager."""

    @cached_property
    def version(self) -> str:
        """Get executable version."""
        raise NotImplementedError

    def export(self, **_kwargs: Any) -> None:
        """Export."""
        raise NotImplementedError
