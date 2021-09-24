"""High-level exceptions."""
from __future__ import annotations

from runway.cfngin.exceptions import CfnginError


class CfnginOnlyLookupError(CfnginError):
    """Attempted to use a CFNgin lookup outside of CFNgin."""

    lookup_name: str

    def __init__(self, lookup_name: str) -> None:
        """Instantiate class."""
        self.lookup_name = lookup_name
        self.message = (
            f"attempted to use CFNgin only lookup {lookup_name} outside of CFNgin"
        )
        super().__init__()
