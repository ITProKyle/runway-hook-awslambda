"""This type stub file was generated by pyright."""
# pylint: disable=C,E,W,R
from __future__ import annotations

from .base import DictType

class LogConfigTypesEnum:
    _values = ...

class LogConfig(DictType):
    types = LogConfigTypesEnum
    def __init__(self, **kwargs) -> None: ...
    @property
    def type(self): ...
    @type.setter
    def type(self, value): ...
    @property
    def config(self): ...
    def set_config_value(self, key, value): ...
    def unset_config(self, key): ...

class Ulimit(DictType):
    def __init__(self, **kwargs) -> None: ...
    @property
    def name(self): ...
    @name.setter
    def name(self, value): ...
    @property
    def soft(self): ...
    @soft.setter
    def soft(self, value): ...
    @property
    def hard(self): ...
    @hard.setter
    def hard(self, value): ...

class DeviceRequest(DictType):
    def __init__(self, **kwargs) -> None: ...
    @property
    def driver(self): ...
    @driver.setter
    def driver(self, value): ...
    @property
    def count(self): ...
    @count.setter
    def count(self, value): ...
    @property
    def device_ids(self): ...
    @device_ids.setter
    def device_ids(self, value): ...
    @property
    def capabilities(self): ...
    @capabilities.setter
    def capabilities(self, value): ...
    @property
    def options(self): ...
    @options.setter
    def options(self, value): ...

class HostConfig(dict):
    def __init__(
        self,
        version,
        binds=...,
        port_bindings=...,
        lxc_conf=...,
        publish_all_ports=...,
        links=...,
        privileged=...,
        dns=...,
        dns_search=...,
        volumes_from=...,
        network_mode=...,
        restart_policy=...,
        cap_add=...,
        cap_drop=...,
        devices=...,
        extra_hosts=...,
        read_only=...,
        pid_mode=...,
        ipc_mode=...,
        security_opt=...,
        ulimits=...,
        log_config=...,
        mem_limit=...,
        memswap_limit=...,
        mem_reservation=...,
        kernel_memory=...,
        mem_swappiness=...,
        cgroup_parent=...,
        group_add=...,
        cpu_quota=...,
        cpu_period=...,
        blkio_weight=...,
        blkio_weight_device=...,
        device_read_bps=...,
        device_write_bps=...,
        device_read_iops=...,
        device_write_iops=...,
        oom_kill_disable=...,
        shm_size=...,
        sysctls=...,
        tmpfs=...,
        oom_score_adj=...,
        dns_opt=...,
        cpu_shares=...,
        cpuset_cpus=...,
        userns_mode=...,
        uts_mode=...,
        pids_limit=...,
        isolation=...,
        auto_remove=...,
        storage_opt=...,
        init=...,
        init_path=...,
        volume_driver=...,
        cpu_count=...,
        cpu_percent=...,
        nano_cpus=...,
        cpuset_mems=...,
        runtime=...,
        mounts=...,
        cpu_rt_period=...,
        cpu_rt_runtime=...,
        device_cgroup_rules=...,
        device_requests=...,
    ) -> None: ...

def host_config_type_error(param, param_value, expected): ...
def host_config_version_error(param, version, less_than=...): ...
def host_config_value_error(param, param_value): ...
def host_config_incompatible_error(param, param_value, incompatible_param): ...

class ContainerConfig(dict):
    def __init__(
        self,
        version,
        image,
        command,
        hostname=...,
        user=...,
        detach=...,
        stdin_open=...,
        tty=...,
        ports=...,
        environment=...,
        volumes=...,
        network_disabled=...,
        entrypoint=...,
        working_dir=...,
        domainname=...,
        host_config=...,
        mac_address=...,
        labels=...,
        stop_signal=...,
        networking_config=...,
        healthcheck=...,
        stop_timeout=...,
        runtime=...,
    ) -> None: ...
