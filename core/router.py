"""
Router - Automatic engine routing for file conversions.

Routes files to the appropriate engine based on file type.
"""

from pathlib import Path
from typing import Optional, List, Any

from core.engines.pillow import PillowEngine


class Router:
    """Routes files to appropriate conversion engines."""

    def __init__(self):
        """Initialize the router with available engines."""
        self._engines: List[Any] = []
        self._register_default_engines()

    def _register_default_engines(self):
        """Register default engines."""
        # Register PillowEngine for image files
        self.register_engine(PillowEngine())

    def register_engine(self, engine: Any) -> None:
        """
        Register an engine for routing.

        Args:
            engine: An engine instance with a `supports` method.
        """
        self._engines.append(engine)

    def get_engine(self, file_path: Path) -> Optional[Any]:
        """
        Get the appropriate engine for a given file.

        Args:
            file_path: Path to the file.

        Returns:
            The appropriate engine, or None if no engine supports the file.
        """
        for engine in self._engines:
            if engine.supports(file_path):
                return engine
        return None

    def route(self, file_path: Path) -> Optional[Any]:
        """
        Route a file to the appropriate engine.

        Args:
            file_path: Path to the file.

        Returns:
            The appropriate engine, or None if no engine supports the file.
        """
        return self.get_engine(file_path)

    def supports(self, file_path: Path) -> bool:
        """
        Check if any registered engine supports the file.

        Args:
            file_path: Path to the file.

        Returns:
            True if at least one engine supports the file.
        """
        return self.get_engine(file_path) is not None
