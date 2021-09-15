"""Test runway.cfngin.hooks.awslambda.source_code."""
# pylint: disable=no-self-use,protected-access,redefined-outer-name
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from mock import Mock, call

from awslambda.source_code import SourceCode

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

MODULE = "awslambda.source_code"


class TestSourceCode:
    """Test SourceCode."""

    def test___eq___other(self, tmp_path: Path) -> None:
        """Test __eq__."""
        assert SourceCode(tmp_path) != tmp_path
        assert SourceCode(tmp_path) != str(tmp_path)

    def test___eq___source_code(self, tmp_path: Path) -> None:
        """Test __eq__."""
        assert SourceCode(tmp_path) == SourceCode(tmp_path)
        assert SourceCode(tmp_path) == SourceCode(str(tmp_path))
        assert SourceCode(tmp_path) != SourceCode(tmp_path / "foo")

    def test___fspath__(self, tmp_path: Path) -> None:
        """Test __fspath__."""
        assert SourceCode(tmp_path).__fspath__() == str(tmp_path)

    def test___init__(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test __init__."""
        gitignore_filter = mocker.patch("igittigitt.IgnoreParser", Mock())
        gitignore_filter.return_value = gitignore_filter

        obj = SourceCode(tmp_path)
        assert obj._include_files_in_hash == []
        assert obj.gitignore_filter == gitignore_filter
        gitignore_filter.assert_called_once_with()
        assert obj.root_directory == tmp_path
        gitignore_filter.parse_rule_files.assert_called_once_with(tmp_path)
        gitignore_filter.add_rule.assert_has_calls(
            [
                call(".git/", tmp_path),
                call(".gitignore", tmp_path),
                call("**/bin/python*", "/"),
            ]
        )

    def test___init___gitignore_filter_provided(self, tmp_path: Path) -> None:
        """Test __init__ gitignore_filter provided."""
        gitignore_filter = Mock()
        obj = SourceCode(
            tmp_path,
            gitignore_filter=gitignore_filter,
            include_files_in_hash=[tmp_path],
        )
        assert obj._include_files_in_hash == [tmp_path]
        assert obj.gitignore_filter == gitignore_filter
        gitignore_filter.parse_rule_files.assert_not_called()
        gitignore_filter.add_rule.assert_not_called()

    def test___init___handle_str(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test __init__ root_directory provided as str."""
        gitignore_filter = mocker.patch("igittigitt.IgnoreParser", Mock())
        gitignore_filter.return_value = gitignore_filter

        obj = SourceCode(str(tmp_path))
        assert obj.root_directory == tmp_path
        assert isinstance(obj.root_directory, Path)

    def test___iter__(self, tmp_path: Path) -> None:
        """Test __iter__."""
        file0 = tmp_path / "foo0.txt"
        file0.touch()
        file1 = tmp_path / "foo1.txt"
        file1.touch()
        (tmp_path / "dir").mkdir()

        gitignore_filter = Mock(match=Mock(side_effect=[False, True]))
        assert (
            len(list(iter(SourceCode(tmp_path, gitignore_filter=gitignore_filter))))
            == 1
        )
        gitignore_filter.match.assert_has_calls(
            [call(file0), call(file1)], any_order=True
        )

    def test___str__(self, tmp_path: Path) -> None:
        """Test __str__."""
        assert str(SourceCode(tmp_path)) == str(tmp_path)

    def test___truediv__(self, tmp_path: Path) -> None:
        """Test __truediv__."""
        assert SourceCode(tmp_path) / "foo" == tmp_path / "foo"

    def test_add_filter_rule(self, tmp_path: Path) -> None:
        """Test add_filter_rule."""
        gitignore_filter = Mock()
        pattern = "foobar/"
        obj = SourceCode(tmp_path, gitignore_filter=gitignore_filter)
        assert not obj.add_filter_rule(pattern)
        gitignore_filter.add_rule.assert_called_once_with(
            pattern=pattern, base_path=tmp_path
        )

    def test_copy(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test copy."""
        dest_path = tmp_path / "dest"
        mock_copytree = mocker.patch("shutil.copytree", return_value=dest_path)
        obj = SourceCode(tmp_path)
        result = obj.copy(dest_path)
        assert result.root_directory == dest_path
        mock_copytree.assert_called_once_with(
            tmp_path,
            dest_path,
            ignore=obj.gitignore_filter.shutil_ignore,
            dirs_exist_ok=True,
        )

    def test_md5_hash(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Test md5_hash."""
        file_hash = Mock(hexdigest="success")
        mock_file_hash_class = mocker.patch(
            f"{MODULE}.FileHash", return_value=file_hash
        )
        mock_md5 = mocker.patch("hashlib.md5")
        test_file = tmp_path / "test.txt"
        assert (
            SourceCode(
                tmp_path, gitignore_filter=Mock(), include_files_in_hash=[test_file]
            ).md5_hash
            == file_hash.hexdigest
        )
        mock_file_hash_class.assert_called_once_with(mock_md5.return_value)
        file_hash.add_files.assert_called_once_with([test_file], relative_to=tmp_path)

    @pytest.mark.parametrize("reverse", [False, True])
    def test_sorted(self, mocker: MockerFixture, reverse: bool, tmp_path: Path) -> None:
        """Test sorted."""
        mock_sorted = mocker.patch(f"{MODULE}.sorted", return_value="success")
        obj = SourceCode(tmp_path)
        assert obj.sorted(reverse=reverse)
        mock_sorted.assert_called_once_with(obj, reverse=reverse)
