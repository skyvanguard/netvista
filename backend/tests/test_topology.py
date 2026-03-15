from topology.categorizer import _categorize_single
from topology.risk import _score_single
from topology.subnet import detect_gateways, group_by_subnet


class TestCategorizer:
    def test_server_with_http(self):
        host = {"ports": [{"port": 80}, {"port": 443}], "os_name": "Linux", "vendor": ""}
        assert _categorize_single(host) == "server"

    def test_workstation_windows(self):
        host = {"ports": [{"port": 3389}, {"port": 445}], "os_name": "Windows 10", "vendor": ""}
        assert _categorize_single(host) == "workstation"

    def test_printer_by_vendor(self):
        host = {"ports": [], "os_name": "", "vendor": "HP Inc"}
        assert _categorize_single(host) == "printer"

    def test_camera_by_vendor(self):
        host = {"ports": [], "os_name": "", "vendor": "Hikvision"}
        assert _categorize_single(host) == "camera"

    def test_network_device_by_vendor(self):
        host = {"ports": [], "os_name": "", "vendor": "Cisco Systems"}
        assert _categorize_single(host) == "network_device"

    def test_unknown_no_info(self):
        host = {"ports": [], "os_name": "", "vendor": ""}
        assert _categorize_single(host) == "unknown"


class TestRiskScoring:
    def test_no_risky_ports(self):
        host = {"ports": [{"port": 80}, {"port": 443}]}
        score, details = _score_single(host)
        assert score == 0.0
        assert details == []

    def test_telnet_high_risk(self):
        host = {"ports": [{"port": 23}]}
        score, details = _score_single(host)
        assert score == 3.0
        assert len(details) == 1

    def test_max_risk_cap(self):
        host = {"ports": [{"port": p} for p in [23, 21, 445, 3389, 6379, 27017, 514, 513, 512]]}
        score, _ = _score_single(host)
        assert score == 10.0

    def test_large_attack_surface(self):
        host = {"ports": [{"port": i} for i in range(1, 22)]}
        score, details = _score_single(host)
        assert any("attack surface" in d for d in details)


class TestSubnetGrouping:
    def test_groups_by_24(self):
        hosts = [
            {"ip": "192.168.1.10"},
            {"ip": "192.168.1.20"},
            {"ip": "192.168.2.5"},
        ]
        subnets = group_by_subnet(hosts)
        assert "192.168.1.0/24" in subnets
        assert "192.168.2.0/24" in subnets
        assert len(subnets["192.168.1.0/24"]) == 2

    def test_gateway_detection(self):
        hosts = [
            {"ip": "192.168.1.10", "subnet": "192.168.1.0/24",
             "traceroute": [{"ip": "10.0.0.1"}, {"ip": "192.168.1.1"}, {"ip": "192.168.1.10"}]},
            {"ip": "192.168.1.20", "subnet": "192.168.1.0/24",
             "traceroute": [{"ip": "10.0.0.1"}, {"ip": "192.168.1.1"}, {"ip": "192.168.1.20"}]},
        ]
        gws = detect_gateways(hosts)
        assert gws.get("192.168.1.0/24") == "192.168.1.1"
