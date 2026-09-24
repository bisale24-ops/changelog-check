from changelogcheck import check, report


def test_unmentioned_change_is_listed_and_strict_fails(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("quietly change the pricing table",
                {"pricing.py": "\n".join(f"RATE_{n} = {n}" for n in range(30))})
    repo.commit("document the flag", {"cli.py": "parser.add_argument('--strict')\n"})
    result = check.run(repo.path, "v1", "HEAD", "- New --strict flag")
    silent = {commit.subject for commit in result["unmentioned"]}
    assert "quietly change the pricing table" in silent
    assert report.exit_code(result) == report.EXIT_OK
    assert report.exit_code(result, strict=True) == report.EXIT_UNMENTIONED


def test_an_unsupported_claim_fails_without_strict(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("small tweak", {"a.py": "x = 2\n"})
    result = check.run(repo.path, "v1", "HEAD", "- Added Kubernetes autoscaling")
    assert report.exit_code(result) == report.EXIT_UNSUPPORTED


def test_lockfile_churn_is_not_reported_as_unmentioned(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("bump dependencies", {"uv.lock": "\n".join(f"line {n}" for n in range(200))})
    result = check.run(repo.path, "v1", "HEAD", "- Nothing user visible")
    assert result["unmentioned"] == []


def test_html_report_contains_every_claim(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("touch the parser", {"parser.py": "def parse():\n    return 1\n"})
    result = check.run(repo.path, "v1", "HEAD", "- parser.py learns to parse\n- Invented thing")
    page = report.render_html(result)
    assert "parser.py learns to parse" in page and "Invented thing" in page
