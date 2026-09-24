from changelogcheck import history


def test_the_range_excludes_the_starting_point(repo):
    repo.commit("first", {"a.py": "x = 1\n"})
    repo.tag("v1")
    second = repo.commit("second", {"a.py": "x = 2\n"})
    commits = history.collect(repo.path, "v1", "HEAD")
    assert [c.sha for c in commits] == [second]


def test_churn_and_noise_are_recorded(repo):
    repo.commit("first", {"a.py": "x = 1\n"})
    repo.tag("v1")
    repo.commit("lock", {"package-lock.json": "{}\n"})
    commit = history.collect(repo.path, "v1", "HEAD")[0]
    assert commit.noisy and commit.insertions == 1


def test_an_unknown_ref_is_an_error(repo):
    repo.commit("first", {"a.py": "x = 1\n"})
    try:
        history.collect(repo.path, "v9", "HEAD")
    except history.GitError as e:
        assert "v9" in str(e)
    else:
        raise AssertionError("expected GitError")
