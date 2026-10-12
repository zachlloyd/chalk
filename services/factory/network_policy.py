"""Network policy support for the factory file format.

A factory document and each agent definition may carry an optional
``networkPolicy``. The policy names the hosts a factory or agent may reach
(``allowedHosts``, ``deniedHosts``) and the named policies it extends
(``extends``). The policy is optional in both scopes, and an explicitly empty
policy (``networkPolicy: {}``) is distinct from no policy at all.
"""

import ipaddress
import re
from dataclasses import dataclass
from typing import Any

_POLICY_FIELDS = {"allowedHosts", "deniedHosts", "extends"}

_HOST_LABEL = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?")


class PolicyValidationError(ValueError):
    """Raised when a network policy does not match the factory file format."""


@dataclass
class NetworkPolicy:
    """A parsed ``networkPolicy``.

    A field of ``None`` means the key was omitted; an empty list means the key
    was present but empty. An empty policy is the policy where every field is
    ``None``.
    """

    allowed_hosts: list[str] | None = None
    denied_hosts: list[str] | None = None
    extends: str | list[str] | None = None


def is_valid_host(host: Any) -> bool:
    """Report whether ``host`` is a valid network host name or IP address."""
    if not isinstance(host, str) or not host:
        return False
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    if len(host) > 253:
        return False
    labels = host.split(".")
    if not all(_HOST_LABEL.fullmatch(label) for label in labels):
        return False
    # RFC 1123: an all-numeric top-level label is reserved for IP addresses.
    return not labels[-1].isdigit()


def parse_network_policy(value: Any) -> NetworkPolicy | None:
    """Parse a decoded ``networkPolicy`` value.

    ``None`` — the key is absent — parses to ``None``. An empty mapping parses
    to an empty ``NetworkPolicy``, which is distinct from no policy.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise PolicyValidationError(
            f"networkPolicy must be a mapping, got {type(value).__name__}"
        )
    unknown = [field for field in value if field not in _POLICY_FIELDS]
    if unknown:
        raise PolicyValidationError(f"unknown networkPolicy fields: {unknown}")
    return NetworkPolicy(
        allowed_hosts=_parse_hosts(value, "allowedHosts"),
        denied_hosts=_parse_hosts(value, "deniedHosts"),
        extends=_parse_extends(value),
    )


def parse_factory_policy(document: Any) -> NetworkPolicy | None:
    """Parse the factory-level network policy from a factory document.

    The factory-level policy is a top-level property of the factory. It is
    never read from ``agentDefaults`` and is not merged into agent
    definitions; policies compose, so each scope parses its own.
    """
    if not isinstance(document, dict):
        raise PolicyValidationError("factory document must be a mapping")
    defaults = document.get("agentDefaults")
    if isinstance(defaults, dict) and "networkPolicy" in defaults:
        raise PolicyValidationError(
            "networkPolicy is not valid under agentDefaults; "
            "it is a top-level factory property"
        )
    return parse_network_policy(document.get("networkPolicy"))


def parse_agent_policy(agent: Any) -> NetworkPolicy | None:
    """Parse the network policy of one agent definition."""
    if not isinstance(agent, dict):
        raise PolicyValidationError("agent definition must be a mapping")
    return parse_network_policy(agent.get("networkPolicy"))


def _parse_hosts(policy: dict[str, Any], field: str) -> list[str] | None:
    hosts = policy.get(field)
    if hosts is None:
        return None
    if not isinstance(hosts, list):
        raise PolicyValidationError(f"{field} must be a list of network hosts")
    for host in hosts:
        if not is_valid_host(host):
            raise PolicyValidationError(
                f"{field} contains an invalid network host: {host!r}"
            )
    return list(hosts)


def _parse_extends(policy: dict[str, Any]) -> str | list[str] | None:
    extends = policy.get("extends")
    if extends is None:
        return None
    if isinstance(extends, str):
        return extends
    if isinstance(extends, list) and all(isinstance(item, str) for item in extends):
        return list(extends)
    raise PolicyValidationError("extends must be a string or a list of strings")
