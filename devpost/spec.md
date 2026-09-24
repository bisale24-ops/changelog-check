---
name: spec
status: approved
---

# Spec — Changelog Check

## Shape

Python 3.11, standard library, and the `git` binary that is already there. No dependencies, no
network, no key. A judge clones the repo and runs it against their own project in one command.

```
src/changelogcheck/
  history.py    the range between two tags: commits, files, issue numbers, churn
  notes.py      a release note cut into claims: bullets and sentences, headings dropped
  match.py      claim against commits, on evidence rather than vocabulary
  report.py     three blocks, terminal and HTML, and the exit code
  cli.py        the command
evals/
  cases.json    public repositories, tag pairs, and what the verdict must be
  run_evals.py  clone shallowly to a cache, run, compare
```

## What counts as evidence

A claim is supported when at least one commit in the range shares a **concrete token** with it:

- a file path or a file stem (`retrieve.py`, `settle`),
- an identifier: a function, class or flag spelled the same way in the diff,
- an issue or PR number (`#412`) present in the commit message,
- a quoted string that appears in the diff.

Shared ordinary words are not evidence. "fixes the timesheet export" and a commit called
"tidy exports" match only if a path or an identifier ties them together. This will miss real
matches; missing them is the acceptable failure, claiming them is not.

## The model's place

The matching above is deterministic and runs with no model at all. A model is used for one
narrow job, behind `--explain`: turning an established match into a sentence a human reads
("this line is backed by three commits that change `export.py` and add the `--csv` flag"). It
never decides a verdict. If the model is unavailable the report still prints, with the evidence
shown raw.

That boundary is the lesson carried over from the previous project, where the arithmetic was
taken away from the model after it corrected a right answer into a wrong one.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | every claim supported, nothing important unmentioned |
| 1 | at least one claim with no evidence |
| 2 | claims all supported, but a change shipped that no line mentions, and `--strict` was given |
| 3 | the range or the repository could not be read |

## Testing

`evals/cases.json` pins real releases of public repositories and the verdict each must produce,
including one case where a line was edited to claim something the diff does not contain. The
suite clones shallowly into a cache directory, so it is reproducible and costs nothing.

The number to beat is trivial to state: no false "supported" on the planted claims, across every
case in the set.
