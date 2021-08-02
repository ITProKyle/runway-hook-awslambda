"""Source code."""
from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Optional, Union

import igittigitt
from runway.compat import cached_property

if TYPE_CHECKING:
    from os import PathLike

LOGGER = logging.getLogger(f"runway.{__name__}")


class SourceCode:
    """Source code iterable.

    Attributes:
        gitignore_filter: Filter to use when zipping dependencies.
            If file/folder matches the filter, it should be ignored.
        root_directory: The root directory containing the source code.

    """

    gitignore_filter: igittigitt.IgnoreParser
    root_directory: Path

    def __init__(
        self,
        root_directory: PathLike[str],
        *,
        gitignore_filter: Optional[igittigitt.IgnoreParser] = None,
    ) -> None:
        """Instantiate class.

        Args:
            root_directory: The root directory containing the source code.
            gitignore_filter: Object that has been pre-populated with
                rules/patterns to determine if a file should be ignored.

        """
        self.gitignore_filter = gitignore_filter or igittigitt.IgnoreParser()
        self.root_directory = (
            root_directory if isinstance(root_directory, Path) else Path(root_directory)
        )

        if not gitignore_filter:
            self.gitignore_filter.parse_rule_files(self.root_directory)
            self.gitignore_filter.add_rule(".git/", self.root_directory)
            self.gitignore_filter.add_rule(".gitignore", self.root_directory)
            # TODO remove once fixed in lib
            self.gitignore_filter.add_rule(  # fix incorrectly handled synlinks
                "**/bin/python*", "/"
            )

    @cached_property
    def md5_hash(self) -> str:
        """Calculate the md5 hash of the directory contents.

        This can be resource intensive depending on the size of the project.
        The implimentation tries to conserve memory as much as possible.

        """
        file_hash = hashlib.md5()
        read_size = 1024 * 10_000_000  # 10mb - number of bytes in each read operation
        for source_file in self.sorted():
            file_hash.update(
                (str(source_file.relative_to(self.root_directory)) + "\0").encode()
            )
            with open(source_file, "rb") as buf:
                # python 3.7 compatable version of `while chunk := buf.read(read_size):`
                chunk = buf.read(read_size)  # seed chunk with initial value
                while chunk:
                    file_hash.update(chunk)
                    chunk = buf.read(read_size)  # read in new chunk
                file_hash.update("\0".encode())  # end of file contents
        return file_hash.hexdigest()

    def add_filter_rule(self, pattern: str) -> None:
        """Add rule to ignore filter.

        Args:
            pattern: The gitignore pattern to add to the filter.

        """
        self.gitignore_filter.add_rule(pattern=pattern, base_path=self.root_directory)

    def copy(self, destination_directory: PathLike[str]) -> SourceCode:
        """Copy source code to a new directory.

        Files that match the ignore filter are not copied.

        Args:
            destination_directory: Directory where source code should be
                copied to.

        Returns:
            New instance of :class:`SourceCode` using the destination directory
            as the root directory.

        """
        return SourceCode(
            shutil.copytree(
                self.root_directory,
                destination_directory,
                ignore=self.gitignore_filter.shutil_ignore,
                dirs_exist_ok=True,  # TODO remove to support python 3.7
            )
        )

    def sorted(self, *, reverse: bool = False) -> List[Path]:
        """Sorted list of source code files.

        Args:
            reverse: Sort the list in reverse.

        Returns:
            Sorted list of source code files excluding those that match the
            ignore filter.

        """
        return sorted(self, reverse=reverse)

    def __eq__(self, other: object) -> bool:
        """Compare if self is equal to another object."""
        if isinstance(other, SourceCode):
            return self.root_directory == other.root_directory
        if isinstance(other, Path):
            return self.root_directory == other
        return False

    def __fspath__(self) -> Union[str, bytes]:
        """Return the file system path representation of the object."""
        return str(self.root_directory)

    def __iter__(self) -> Iterator[Path]:
        """Iterate over the source code files.

        Yields:
            Files that do not match the ignore filter. Order in arbitrary.

        """
        for child in self.root_directory.rglob("*"):
            if child.is_dir():
                continue  # ignore directories
            if self.gitignore_filter.match(child):
                continue  # ignore files that match the filter
            yield child

    def __str__(self) -> str:
        """Return the string representation of the object."""
        return str(self.root_directory)

    def __truediv__(self, other: Union[PathLike[str], str]) -> Path:
        """Create a new path object from source code's root directory."""
        return self.root_directory / other
