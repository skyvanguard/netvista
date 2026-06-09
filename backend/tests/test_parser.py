from __future__ import annotations

from scanner.parser import parse_nmap_xml

# A trimmed-down but representative nmap XML output: one host up with MAC/vendor,
# hostname, OS match, an open and a closed port, and a traceroute; plus one host
# that is down (must be skipped).
SAMPLE_XML = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="192.168.1.10" addrtype="ipv4"/>
    <address addr="AA:BB:CC:DD:EE:FF" addrtype="mac" vendor="Cisco Systems"/>
    <hostnames>
      <hostname name="router.local" type="PTR"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.9"/>
      </port>
      <port protocol="tcp" portid="23">
        <state state="closed"/>
        <service name="telnet"/>
      </port>
    </ports>
    <os>
      <osmatch name="Linux 5.x" accuracy="96"/>
    </os>
    <trace>
      <hop ttl="1" ipaddr="192.168.1.1" rtt="1.20" host="gw.local"/>
      <hop ttl="2" ipaddr="192.168.1.10" rtt="2.50"/>
    </trace>
  </host>
  <host>
    <status state="down"/>
    <address addr="192.168.1.99" addrtype="ipv4"/>
  </host>
</nmaprun>
"""


def _parse(tmp_path, xml: str):
    path = tmp_path / "scan.xml"
    path.write_text(xml, encoding="utf-8")
    return parse_nmap_xml(str(path))


def test_only_up_hosts_are_returned(tmp_path):
    hosts = _parse(tmp_path, SAMPLE_XML)
    assert len(hosts) == 1
    assert hosts[0]["ip"] == "192.168.1.10"


def test_host_metadata_is_parsed(tmp_path):
    host = _parse(tmp_path, SAMPLE_XML)[0]
    assert host["hostname"] == "router.local"
    assert host["mac"] == "AA:BB:CC:DD:EE:FF"
    assert host["vendor"] == "Cisco Systems"
    assert host["os_name"] == "Linux 5.x"
    assert host["os_accuracy"] == 96
    assert host["state"] == "up"


def test_only_open_ports_are_kept_with_version(tmp_path):
    host = _parse(tmp_path, SAMPLE_XML)[0]
    assert len(host["ports"]) == 1
    port = host["ports"][0]
    assert port["port"] == 22
    assert port["protocol"] == "tcp"
    assert port["state"] == "open"
    assert port["service"] == "ssh"
    assert port["version"] == "OpenSSH 8.9"


def test_traceroute_hops_are_parsed(tmp_path):
    host = _parse(tmp_path, SAMPLE_XML)[0]
    assert [h["hop"] for h in host["traceroute"]] == [1, 2]
    assert host["traceroute"][0]["ip"] == "192.168.1.1"
    assert host["traceroute"][0]["rtt"] == 1.2


def test_host_without_ipv4_is_skipped(tmp_path):
    xml = """<?xml version="1.0"?>
    <nmaprun>
      <host>
        <status state="up"/>
        <address addr="fe80::1" addrtype="ipv6"/>
      </host>
    </nmaprun>"""
    assert _parse(tmp_path, xml) == []


def test_empty_run_returns_empty_list(tmp_path):
    assert _parse(tmp_path, '<?xml version="1.0"?><nmaprun></nmaprun>') == []
