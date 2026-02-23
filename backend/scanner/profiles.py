from __future__ import annotations

SCAN_PROFILES: dict[str, dict] = {
    "quick": {
        "name": "Quick Discovery",
        "flags": ["-sn", "-PE", "-PP", "-PS21,22,80,443"],
        "description": "Ping sweep only — fast host discovery, no port scan",
        "estimated_time": "~30 seconds for /24",
    },
    "standard": {
        "name": "Standard",
        "flags": [
            "-sS", "-sV", "--top-ports", "1000",
            "-O", "--traceroute", "-T4",
        ],
        "description": "SYN scan, top 1000 ports, OS detection, traceroute",
        "estimated_time": "~15 minutes for /24",
    },
    "deep": {
        "name": "Deep",
        "flags": [
            "-sS", "-sV", "-sC", "-O",
            "-p-", "--traceroute", "-T3",
        ],
        "description": "Full port scan with scripts, OS detection, traceroute",
        "estimated_time": "~45 minutes for /24",
    },
}


def get_profile_flags(profile: str) -> list[str]:
    if profile not in SCAN_PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    return SCAN_PROFILES[profile]["flags"]
