# Changelog

## 0.1.0 - 2026-09-25

### Added
- `history.py` collects the range between two refs: commits, files, churn and issue numbers
- `notes.py` cuts a release note into claims, dropping headings, fences and link definitions
- `match.py` decides a claim on evidence — issue numbers, flags, filenames, identifiers — and
  refuses to treat shared English as proof
- `report.py` prints three blocks and returns an exit code CI can act on, and writes the same
  report as a self-contained page with `--html`
- `--strict` fails the build when a substantial change ships unmentioned
- 15 tests that build git repositories on the spot, with no network
