from __future__ import annotations

import pytest
from pydantic import ValidationError

from models import ScanCreate


@pytest.mark.parametrize(
    "target",
    [
        "192.168.1.0/24",
        "10.0.0.5",
        "172.16.0.0/16",
        "example.com",
        "scanme.nmap.org",
        "host-1.sub.example.org",
    ],
)
def test_valid_targets_are_accepted(target):
    assert ScanCreate(target=target).target == target


def test_target_is_stripped():
    assert ScanCreate(target="  192.168.1.1  ").target == "192.168.1.1"


@pytest.mark.parametrize(
    "target",
    [
        "--script=vuln",          # nmap flag injection
        "-oN /tmp/out",           # output redirection flag
        "; rm -rf /",             # shell metacharacters
        "10.0.0.1 --top-ports 1", # extra argument smuggled in
        "",                       # empty
        "-",                      # lone dash
        "bad host name",          # spaces
    ],
)
def test_injection_targets_are_rejected(target):
    with pytest.raises(ValidationError):
        ScanCreate(target=target)


@pytest.mark.parametrize("profile", ["quick", "standard", "deep"])
def test_valid_profiles(profile):
    assert ScanCreate(target="10.0.0.1", profile=profile).profile == profile


def test_invalid_profile_rejected():
    with pytest.raises(ValidationError):
        ScanCreate(target="10.0.0.1", profile="aggressive")


def test_profile_defaults_to_standard():
    assert ScanCreate(target="10.0.0.1").profile == "standard"
