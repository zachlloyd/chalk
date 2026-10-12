"""Regression tests for factory file format network policies."""

import pytest

from services.factory.network_policy import (
    NetworkPolicy,
    PolicyValidationError,
    is_valid_host,
    parse_agent_policy,
    parse_factory_policy,
    parse_network_policy,
)


class TestParseNetworkPolicy:
    def test_absent_policy_parses_to_none(self):
        assert parse_network_policy(None) is None

    def test_empty_policy_is_distinct_from_absent(self):
        policy = parse_network_policy({})
        assert policy is not None
        assert policy == NetworkPolicy()
        assert policy.allowed_hosts is None
        assert policy.denied_hosts is None
        assert policy.extends is None

    def test_full_policy(self):
        policy = parse_network_policy(
            {
                "allowedHosts": ["myapp.internal.acme.com", "1.1.1.1"],
                "deniedHosts": ["gitlab.com"],
                "extends": "warp/package-managers@latest",
            }
        )
        assert policy == NetworkPolicy(
            allowed_hosts=["myapp.internal.acme.com", "1.1.1.1"],
            denied_hosts=["gitlab.com"],
            extends="warp/package-managers@latest",
        )

    def test_extends_accepts_a_list_of_strings(self):
        policy = parse_network_policy({"extends": ["warp/package-managers@latest", "warp/web@1"]})
        assert policy.extends == ["warp/package-managers@latest", "warp/web@1"]

    def test_empty_host_lists_are_preserved_as_empty(self):
        policy = parse_network_policy({"allowedHosts": [], "deniedHosts": []})
        assert policy.allowed_hosts == []
        assert policy.denied_hosts == []
        assert parse_network_policy({}).allowed_hosts is None

    def test_non_mapping_policy_raises(self):
        with pytest.raises(PolicyValidationError, match="must be a mapping"):
            parse_network_policy("default")

    def test_unknown_policy_field_raises(self):
        with pytest.raises(PolicyValidationError, match="unknown networkPolicy fields"):
            parse_network_policy({"allowedHostz": ["gitlab.com"]})

    def test_hosts_must_be_lists(self):
        with pytest.raises(PolicyValidationError, match="allowedHosts must be a list"):
            parse_network_policy({"allowedHosts": "gitlab.com"})

    def test_invalid_host_in_list_raises(self):
        with pytest.raises(PolicyValidationError, match="invalid network host"):
            parse_network_policy({"deniedHosts": ["gitlab..com"]})

    def test_non_string_host_raises(self):
        with pytest.raises(PolicyValidationError, match="invalid network host"):
            parse_network_policy({"allowedHosts": [1]})

    def test_extends_must_be_string_or_string_list(self):
        with pytest.raises(PolicyValidationError, match="extends must be a string"):
            parse_network_policy({"extends": 3})
        with pytest.raises(PolicyValidationError, match="extends must be a string"):
            parse_network_policy({"extends": ["warp/a", 2]})


class TestIsValidHost:
    @pytest.mark.parametrize(
        "host",
        [
            "myapp.internal.acme.com",
            "gitlab.com",
            "localhost",
            "GitLab.com",
            "1.1.1.1",
            "::1",
        ],
    )
    def test_accepts(self, host):
        assert is_valid_host(host)

    @pytest.mark.parametrize(
        "host",
        [
            "",
            "git lab.com",
            "gitlab..com",
            "-gitlab.com",
            "gitlab.com-",
            "a" * 64 + ".com",
            "999.999.999.999",
            None,
            5,
        ],
    )
    def test_rejects(self, host):
        assert not is_valid_host(host)


class TestScopes:
    def test_factory_policy_is_top_level(self):
        document = {
            "name": "Example",
            "networkPolicy": {"deniedHosts": ["gitlab.com"]},
            "agentDefaults": {"model": "auto"},
        }
        assert parse_factory_policy(document) == NetworkPolicy(denied_hosts=["gitlab.com"])

    def test_factory_policy_under_agent_defaults_is_rejected(self):
        document = {"agentDefaults": {"networkPolicy": {"deniedHosts": ["gitlab.com"]}}}
        with pytest.raises(PolicyValidationError, match="top-level factory property"):
            parse_factory_policy(document)

    def test_empty_factory_policy_is_distinct_from_absent(self):
        assert parse_factory_policy({"networkPolicy": {}}) == NetworkPolicy()
        assert parse_factory_policy({"name": "Example"}) is None

    def test_agent_policy_is_not_merged_from_factory_scope(self):
        document = {"networkPolicy": {"deniedHosts": ["gitlab.com"]}}
        agent = {"name": "builder"}
        assert parse_factory_policy(document) == NetworkPolicy(denied_hosts=["gitlab.com"])
        assert parse_agent_policy(agent) is None

    def test_agent_policy_is_parsed_from_the_agent_definition(self):
        agent = {"name": "builder", "networkPolicy": {"allowedHosts": ["1.1.1.1"]}}
        assert parse_agent_policy(agent) == NetworkPolicy(allowed_hosts=["1.1.1.1"])

    def test_non_mapping_scopes_raise(self):
        with pytest.raises(PolicyValidationError, match="agent definition"):
            parse_agent_policy("builder")
        with pytest.raises(PolicyValidationError, match="factory document"):
            parse_factory_policy(None)
