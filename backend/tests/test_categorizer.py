from __future__ import annotations

from topology.categorizer import categorize_hosts, _categorize_single


def host(*, ports=(), os_name="", vendor=""):
    return {
        "ports": [{"port": p} for p in ports],
        "os_name": os_name,
        "vendor": vendor,
    }


def test_vendor_takes_precedence_over_ports():
    # A camera vendor wins even though port 9100 alone would read as a printer.
    h = host(ports=(9100,), vendor="Hikvision Digital")
    assert _categorize_single(h) == "camera"


def test_network_vendor_wins_over_server_ports():
    h = host(ports=(22, 443), vendor="MikroTik")
    assert _categorize_single(h) == "network_device"


def test_printer_by_port():
    assert _categorize_single(host(ports=(9100,))) == "printer"


def test_camera_by_rtsp_port():
    assert _categorize_single(host(ports=(554,))) == "camera"


def test_iot_by_mqtt_port():
    assert _categorize_single(host(ports=(1883,))) == "iot"


def test_windows_with_workstation_ports_is_workstation():
    h = host(ports=(3389, 445), os_name="Microsoft Windows 11")
    assert _categorize_single(h) == "workstation"


def test_server_by_ports():
    assert _categorize_single(host(ports=(80, 443, 3306))) == "server"


def test_linux_without_ports_is_server():
    assert _categorize_single(host(os_name="Linux 5.x")) == "server"


def test_unknown_when_no_signal():
    assert _categorize_single(host()) == "unknown"


def test_categorize_hosts_mutates_in_place():
    hosts = [host(ports=(9100,)), host(os_name="Linux")]
    categorize_hosts(hosts)
    assert hosts[0]["node_type"] == "printer"
    assert hosts[1]["node_type"] == "server"
