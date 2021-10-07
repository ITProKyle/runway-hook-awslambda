"""This type stub file was generated by pyright."""
# pylint: disable=C,E,W,R
from __future__ import annotations

from docker.types.containers import (
    ContainerConfig,
    DeviceRequest,
    HostConfig,
    LogConfig,
    Ulimit,
)
from docker.types.daemon import CancellableStream
from docker.types.healthcheck import Healthcheck
from docker.types.networks import EndpointConfig, IPAMConfig, IPAMPool, NetworkingConfig
from docker.types.services import (
    ConfigReference,
    ContainerSpec,
    DNSConfig,
    DriverConfig,
    EndpointSpec,
    Mount,
    NetworkAttachmentConfig,
    Placement,
    PlacementPreference,
    Privileges,
    Resources,
    RestartPolicy,
    RollbackConfig,
    SecretReference,
    ServiceMode,
    TaskTemplate,
    UpdateConfig,
)
from docker.types.swarm import SwarmExternalCA, SwarmSpec

__all__ = [
    "CancellableStream",
    "ConfigReference",
    "ContainerConfig",
    "ContainerSpec",
    "DNSConfig",
    "DeviceRequest",
    "DriverConfig",
    "EndpointConfig",
    "EndpointSpec",
    "Healthcheck",
    "HostConfig",
    "IPAMConfig",
    "IPAMPool",
    "LogConfig",
    "Mount",
    "NetworkAttachmentConfig",
    "NetworkingConfig",
    "Placement",
    "PlacementPreference",
    "Privileges",
    "Resources",
    "RestartPolicy",
    "RollbackConfig",
    "SecretReference",
    "ServiceMode",
    "SwarmExternalCA",
    "SwarmSpec",
    "TaskTemplate",
    "Ulimit",
    "UpdateConfig",
]
