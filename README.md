# Changelog Check

Every tool in this space writes release notes *from* the diff. This one reads the notes you
already have and asks what evidence supports each line.

```bash
./run.sh --repo . --from v1.2.0 --to v1.3.0 --notes CHANGELOG.md
```

Three answers, and all three are printed every time:

- **supported** — these commits and these files do what the line says;
- **shipped without a mention** — this change went out and no line covers it, which is how a
  breaking change reaches users quietly;
- **no evidence found** — this line claims something the diff does not contain.

The command exits non-zero on the third, so it can sit in CI as one line and fail the release
before the notes are published.

No dependencies, no network, no API key: the evidence is `git` on the machine running it.
Python 3.11 and the standard library.

## On a real release

`httpx` 0.27.2 → 0.28.0, checked against the project's own changelog section:

```
SUPPORTED  12 of 16 claims
SHIPPED WITHOUT A MENTION  4 commits
NO EVIDENCE FOUND  4 claims
```

That is not an accusation against httpx — it is what a careful, human-written changelog looks
like when you ask a machine for receipts. Some of those four lines describe behaviour git cannot
see, and the report says so rather than calling them false.

## What counts as evidence

A claim is supported when something **concrete** ties it to a commit:

| Evidence | Strength | Example |
|---|---|---|
| issue or PR number | strong | the line says `(#412)` and a commit closes #412 |
| command-line flag | strong | `--strict` in the line and in the diff |
| filename | strong | the line names `hours.py`, the commit touches it |
| identifier | medium | a symbol the diff defines, or a code-like token in the commit subject such as `verify=False` |
| path fragment | weak | the line mentions "export", the commit touches `export/` |

Shared ordinary English is **not** evidence. "improves the export" and a commit called "tidy up
exports" have a word in common and prove nothing. That rule misses real matches; missing them is
the acceptable failure, because the cost of a false *supported* is a release note nobody checks
again.

## Where the model is, and is not

The matching above is deterministic and runs with no model at all. A model is used for one
narrow job, behind `--explain`: turning an established match into a sentence a person reads. It
never decides a verdict, and with no key the report still prints, with the evidence raw.

That boundary comes from a measurement, not a preference: in an earlier project the model was
asked to do arithmetic and "corrected" a right answer into a wrong one inside a single reply.

## Usage

```bash
./run.sh --repo . --from v1.2.0 --to HEAD               # CHANGELOG.md by default
./run.sh --from v1.2.0 --to v1.3.0 --section 1.3.0      # just that version's block
gh release view v1.3.0 --json body -q .body | ./run.sh --from v1.2.0 --to v1.3.0 --notes -
./run.sh --from v1.2.0 --to v1.3.0 --strict             # also fail on silent changes
./run.sh --from v1.2.0 --to v1.3.0 --html report.html   # the same report as a page
```

| Exit code | Meaning |
|---|---|
| 0 | every claim supported |
| 1 | a claim with no evidence |
| 2 | a substantial change shipped unmentioned, with `--strict` |
| 3 | the repository or the range could not be read |

## Tests

```bash
PYTHONPATH=src python -m pytest tests -q      # 15 tests, no network
```

They build small git repositories on the spot and assert on history written by the test itself:
that shared English is not evidence, that a named file is, that an invented line is caught, and
that lockfile churn is not reported as a silent change.

CI runs the suite and then runs the tool against this repository's own release notes.

## What is not "shipped without a mention"

Three kinds of commit ship and do not belong in a changelog, and reporting them would turn a
correct changelog into a list of complaints — the failure that makes the whole report ignorable:

- a dependency bump (`Bump the python-packages group with 11 updates`);
- a commit that touches only tests;
- a commit that edited the release notes themselves, which by definition did not skip them.

All three were found by running this against httpx's own history and checking each finding by
hand. Lockfile churn was already excluded.

## Honest limits

- It reasons about lines and commits, not behaviour. "Fixed the crash on startup" is matched
  against commits that touch startup, not against a test proving the crash is gone.
- A squashed history gives less evidence per line. The report says when that is what it is
  looking at.
- Weak path matches can attach a plausible-looking commit to an unrelated line. They are ranked
  last and labelled, so the reader can see the difference.

MIT licensed. Planned with the Devpost Learn skill pack; `devpost/` holds the scope, PRD and spec
written before the code.
