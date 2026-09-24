---
name: prd
status: approved
---

# PRD — Changelog Check

## How it is used

A terminal command first, because that is where a release is cut:

```
changelog-check --repo . --from v1.2.0 --to v1.3.0 --notes CHANGELOG.md
```

and the same thing as one line in CI, failing the job when a note claims something that did not
ship.

## What it prints

Three blocks, always in this order, always all three, even when one is empty — an empty block is
information too.

**Supported.** Each note line with the commits that back it, shortest evidence first: commit
subject, short hash, and the files that carry the change.

**Shipped without a mention.** Each commit or file group that no line covers, with a one-line
description of what it touched. Ordered by how much it changed, because a big silent change is
the dangerous one.

**No evidence found.** Each note line that nothing supports, with what was searched for. This is
the block that decides the exit code.

## Behaviour that matters

- A line is never marked supported by a commit whose message merely shares a word with it. The
  match must rest on a file path, a symbol, or an issue number that appears in both.
- Merge commits are followed into their parents; a squashed history still works, with less
  evidence per line, and the report says so rather than pretending.
- Version bumps, lockfile churn and generated files are collected but grouped, so they do not
  drown the report.
- Nothing is sent anywhere. The evidence comes from `git` on the machine running it.

## Visual style

Terminal-first and quiet: the three blocks separated by their headings, evidence indented under
each line, colour used only for the verdict (green, amber, plain). An optional `--html` writes
the same report as one self-contained page for attaching to a release.

## Edge cases

| Case | Behaviour |
|---|---|
| The two tags are the same, or the range is empty | Says so and exits zero, rather than reporting everything as unsupported |
| Notes contain headings, bullets and prose | Only bullet and sentence lines are treated as claims; headings are structure |
| A line describes something invisible to git, like "improved performance" | Reported as no evidence, with a note that it may be true but is not checkable here |
| The repository is shallow-cloned | Detected, with the one command that fixes it |

## Now and later

**Now:** the three-block report, git evidence, HTML output, the exit code, and the eval set that
proves it on public repositories.

**Later:** reading release notes straight from the GitHub API, matching against tests rather than
commits, and a mode that suggests the missing lines.
