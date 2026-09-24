"""Synthetic repositories: a handful of commits built on the spot, so the tests need no network
and no fixtures checked into the tree, and every assertion is about history we wrote ourselves."""
import subprocess

import pytest


class Repo:
    def __init__(self, path):
        self.path = path
        self._run("init", "-q", "-b", "main")
        self._run("config", "user.email", "test@example.com")
        self._run("config", "user.name", "Test")

    def _run(self, *args):
        return subprocess.run(["git", "-C", str(self.path), *args],
                              capture_output=True, text=True, check=True).stdout

    def commit(self, subject, files, body=""):
        for name, content in files.items():
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        self._run("add", "-A")
        self._run("commit", "-q", "-m", subject if not body else f"{subject}\n\n{body}")
        return self._run("rev-parse", "HEAD").strip()

    def tag(self, name):
        self._run("tag", name)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)
