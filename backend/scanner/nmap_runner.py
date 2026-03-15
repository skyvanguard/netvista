from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from config import NMAP_PATH
from scanner.parser import parse_nmap_xml
from scanner.profiles import get_profile_flags


async def run_nmap_scan(
    target: str,
    profile: str,
    on_progress: Callable[[float, str], Awaitable[None]] | None = None,
) -> list[dict[str, Any]]:
    """Run nmap scan and return parsed host list."""
    flags = get_profile_flags(profile)

    with tempfile.TemporaryDirectory() as tmpdir:
        xml_path = os.path.join(tmpdir, "scan.xml")
        cmd = [NMAP_PATH, *flags, "-oX", xml_path, target]

        if on_progress:
            await on_progress(0.0, f"Starting {profile} scan on {target}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Read output for progress hints
        stdout_data = b""
        if process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                stdout_data += line
                decoded = line.decode(errors="replace").strip()
                # nmap prints progress like "About 45.00% done"
                if "% done" in decoded and on_progress:
                    try:
                        pct = float(decoded.split("%")[0].split()[-1]) / 100.0
                        await on_progress(pct, decoded)
                    except (ValueError, IndexError):
                        pass

        _, stderr_data = await process.communicate()

        if process.returncode != 0 and not Path(xml_path).exists():
            error_msg = stderr_data.decode(errors="replace").strip()
            raise RuntimeError(f"nmap failed (code {process.returncode}): {error_msg}")

        if on_progress:
            await on_progress(0.9, "Parsing scan results...")

        if not Path(xml_path).exists():
            return []

        hosts = parse_nmap_xml(xml_path)

        if on_progress:
            await on_progress(1.0, f"Scan complete — {len(hosts)} hosts found")

        return hosts
