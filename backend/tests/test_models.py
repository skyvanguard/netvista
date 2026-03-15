import pytest
from pydantic import ValidationError
from models import ScanCreate


class TestScanCreateValidation:
    def test_valid_cidr(self):
        s = ScanCreate(target="192.168.1.0/24")
        assert s.target == "192.168.1.0/24"

    def test_valid_ip(self):
        s = ScanCreate(target="10.0.0.1")
        assert s.target == "10.0.0.1"

    def test_valid_hostname(self):
        s = ScanCreate(target="example.com")
        assert s.target == "example.com"

    def test_valid_subdomain(self):
        s = ScanCreate(target="sub.example.com")
        assert s.target == "sub.example.com"

    def test_strips_whitespace(self):
        s = ScanCreate(target="  10.0.0.1  ")
        assert s.target == "10.0.0.1"

    def test_rejects_command_injection(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="192.168.1.0/24; rm -rf /")

    def test_rejects_pipe(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="10.0.0.1 | cat /etc/passwd")

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="")

    def test_rejects_backtick(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="`whoami`")

    def test_default_profile(self):
        s = ScanCreate(target="10.0.0.1")
        assert s.profile == "standard"

    def test_valid_profiles(self):
        for p in ("quick", "standard", "deep"):
            s = ScanCreate(target="10.0.0.1", profile=p)
            assert s.profile == p

    def test_invalid_profile(self):
        with pytest.raises(ValidationError):
            ScanCreate(target="10.0.0.1", profile="ultra")
