# Changelog

All notable changes to NetVista are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-06-09

A hardening, robustness, observability and quality pass over the initial
implementation. No breaking changes to the public API — new controls are
opt-in and default to the previous behavior.

### Added
- Optional API-key authentication (`API_KEY`): when set, every `/api` route
  except `/api/health` requires the key via the `X-API-Key` header or
  `api_key` query param (export links and the WebSocket). Empty = open API.
- Scan concurrency limit (`MAX_CONCURRENT_SCANS`, default 2); queued scans
  stay `pending` until a slot frees up.
- Scan target size guard (`MAX_TARGET_ADDRESSES`, default 65536 = a /16).
- Structured logging (`LOG_LEVEL`, default INFO) across startup, the scan
  lifecycle, and the exact nmap command.
- WebSocket auto-reconnect with exponential backoff.
- Backend test suite (pytest, 62 tests) and frontend test suite (Vitest, 19).
- Linting: `ruff` (backend) and ESLint (frontend).
- GitHub Actions CI running ruff/pytest and eslint/vitest/build on push & PR.

### Changed
- Topology view is code-split: initial bundle ~720 kB → ~190 kB (Cytoscape
  now loads on demand).
- Host loading uses a fixed number of queries instead of N+1.
- Scan result inserts are batched via `executemany`.
- `hosts_found` is `null` while a scan runs instead of a misleading `0`.
- Topology search input is debounced.

### Fixed
- nmap argument injection through the scan target (input validation).
- Invalid CORS configuration (credentials with a wildcard origin).
- Scans left `running` after a restart are now marked `failed` on startup.
- Deleting a scan cancels the running task and its nmap subprocess.
- nmap progress is now emitted during scans (`--stats-every`).
- Resolved 5 npm advisories (4 high, incl. a picomatch ReDoS).

### Removed
- Unused dependencies (`networkx`, `python-multipart`) and dead code
  (`ScanDetail` model, unused `banner` column and imports).

## [0.1.0]

- Initial NetVista implementation — network topology auto-mapper.
