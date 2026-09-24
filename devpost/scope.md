---
name: scope
status: approved
---

# Scope — Does the release note tell the truth?

## The idea in one line

Point it at a repository and two tags, and it says which lines of the release notes are backed by
the commits, which changes shipped without being mentioned, and which claims have nothing behind
them at all.

## Why this and not another summariser

Every tool in this space writes release notes *from* the diff. That is the easy direction, and it
is the one nobody checks: a generated note is trusted because a machine made it, and a
hand-written note is trusted because a person made it. Neither is verified against what actually
shipped.

The interesting direction is backwards. Take the note that exists — written by a person, by a
bot, by a model — and ask what evidence supports each line. Three answers are useful:

- **supported**: these commits and these files do what the line says;
- **unmentioned**: this change shipped and no line covers it, which is how a breaking change
  reaches users quietly;
- **unsupported**: this line claims something the diff does not contain, which is how a release
  note becomes marketing.

Same posture as the last project: the tool is only as good as its refusal to bless what it
cannot show.

## Who it is for

Anyone who tags a release and writes notes: a solo maintainer, a small team, or a CI job that
wants to fail a release whose notes are wrong. In the demo it is run against a well-known public
repository, where the judges can check the verdict against the real history themselves.

## The core loop

1. Two tags, a repository path, and the release note text (from `CHANGELOG.md`, a GitHub release
   or stdin).
2. Collect what actually changed between the tags: commits, files, additions and deletions,
   and any issue or PR numbers referenced.
3. For each line of the note, find the commits that could support it, and decide.
4. Report three lists, with the evidence attached to each entry, and exit non-zero when the note
   has an unsupported claim.

## What "done" means for the proof of concept

- Runs on any local git repository with no network and no API key for the evidence collection.
- On a repository where the notes are honest, no line is marked unsupported.
- On a note with a deliberately invented line, that line is caught.
- Every unmentioned change is traceable to the commit that made it.
- Exits non-zero on failure, so it can sit in CI as one line.

## Deliberately out of scope

- Writing release notes. This is the checker, not the generator.
- Semantic versioning advice, changelog formatting, conventional-commit linting.
- Anything that needs a hosted service or an account.

## Why it is a proof of concept

It reasons about lines and commits, not about behaviour: a note that says "fixed the crash on
startup" is matched against commits that touch startup and mention a crash, not against a test
that proves the crash is gone. That boundary is stated in the output rather than hidden.
