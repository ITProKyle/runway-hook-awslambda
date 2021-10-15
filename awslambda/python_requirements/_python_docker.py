"""Docker logic for python."""
from __future__ import annotations

import logging
import re
import shlex
from typing import TYPE_CHECKING, Dict, List, Optional

from docker.types.services import Mount
from runway.compat import cached_property

from ..docker import DockerDependencyInstaller
from ..utils import Version

if TYPE_CHECKING:
    from ._python_project import PythonProject  # noqa

# TODO add support for cache directory


class PythonDockerDependencyInstaller(DockerDependencyInstaller["PythonProject"]):
    """Docker dependency installer for Python."""

    @cached_property
    def bind_mounts(self) -> List[Mount]:
        """Bind mounts that will be used by the container."""
        return [
            *super().bind_mounts,
            Mount(
                target=f"/var/task/{self.project.requirements_txt.name}",
                source=str(self.project.requirements_txt),
                type="bind",
            ),
        ]

    @cached_property
    def environmet_variables(self) -> Dict[str, str]:
        """Environment variables to pass to the docker container.

        This is a subset of the environment variables stored in the context
        object as some will cause issues if they are passed.

        """
        docker_env_vars = super().environmet_variables
        pip_env_vars = {
            k: v for k, v in self.ctx.env.vars.items() if k.startswith("PIP")
        }
        return {**docker_env_vars, **pip_env_vars}

    @cached_property
    def install_commands(self) -> List[str]:
        """Commands to run to install dependencies."""
        return [
            shlex.join(
                self.project.pip.generate_install_command(
                    cache_dir=self.CACHE_DIR if self.project.cache_dir else None,
                    no_cache_dir=not self.project.args.use_cache,
                    requirements=f"/var/task/{self.project.requirements_txt.name}",
                    target=self.DEPENDENCY_DIR,
                )
            )
        ]

    @cached_property
    def python_version(self) -> Optional[Version]:
        """Version of Python installed in the docker container."""
        match = re.search(
            r"Python (?P<version>\S*)",
            "\n".join(self.run_command("python --version", level=logging.DEBUG)),
        )
        if not match:
            return None
        return Version(match.group("version"))

    @cached_property
    def runtime(self) -> Optional[str]:
        """AWS Lambda runtime determined from the docker container's Python version."""
        if not self.python_version:
            return None
        return f"python{self.python_version.major}.{self.python_version.minor}"
