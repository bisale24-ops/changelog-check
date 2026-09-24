from changelogcheck import check, history, match


def test_shared_english_is_not_evidence(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("tidy up the exports", {"a.py": "x = 2\n"})
    result = check.run(repo.path, "v1", "HEAD", "- improves the export experience")
    assert not result["claims"][0]["verdict"]["supported"]


def test_a_named_file_is_evidence(repo):
    repo.commit("initial", {"pkg/hours.py": "def total():\n    return 0\n"})
    repo.tag("v1")
    repo.commit("count the seventh day", {"pkg/hours.py": "def total():\n    return 1\n"})
    result = check.run(repo.path, "v1", "HEAD", "- hours.py now counts the seventh day")
    assert result["claims"][0]["verdict"]["supported"]
    kinds = {kind for _, found in result["claims"][0]["verdict"]["hits"] for kind, _ in found}
    assert "file" in kinds


def test_an_issue_number_is_evidence(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("stop the loop from spinning", {"a.py": "x = 2\n"}, body="Closes #412")
    result = check.run(repo.path, "v1", "HEAD", "- Fixed the spinning loop (#412)")
    assert result["claims"][0]["verdict"]["supported"]


def test_an_invented_claim_is_not_supported(repo):
    repo.commit("initial", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("adjust the retry delay", {"a.py": "x = 2\n"})
    result = check.run(repo.path, "v1", "HEAD",
                       "- Rewrote the billing engine to use double-entry bookkeeping")
    assert not result["claims"][0]["verdict"]["supported"]


def test_a_flag_in_the_note_matches_the_flag_in_the_diff(repo):
    repo.commit("initial", {"cli.py": "import sys\n"})
    repo.tag("v1")
    repo.commit("add the strict switch",
                {"cli.py": "import sys\nparser.add_argument('--strict')\n"})
    result = check.run(repo.path, "v1", "HEAD", "- New `--strict` flag")
    assert result["claims"][0]["verdict"]["supported"]
