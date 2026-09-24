from changelogcheck import notes

SAMPLE = """# Changelog

## [1.4.0] - 2026-09-20

### Added
- `--strict` fails the build when a change ships unmentioned
- Support for shallow clones

```python
print("not a claim")
```

### Fixed
- Crash when the refs are identical (#412) by @someone

[1.4.0]: https://example.com/compare/v1.3.0...v1.4.0
"""


def test_headings_fences_and_links_are_not_claims():
    found = [claim for _, claim in notes.claims(SAMPLE)]
    assert found == ["--strict fails the build when a change ships unmentioned",
                     "Support for shallow clones",
                     "Crash when the refs are identical (#412)"]


def test_prose_without_bullets_still_counts():
    found = [claim for _, claim in notes.claims("This release rewrites the export pipeline.")]
    assert found == ["This release rewrites the export pipeline."]


def test_a_bare_version_line_is_not_a_claim():
    assert notes.claims("## 2.0.0\n\nv2.0.0\n1.9.3 - 2026-01-02\n") == []
