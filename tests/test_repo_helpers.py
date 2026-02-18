import os
import sys
import unittest


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import repo_helpers  # noqa: E402


class RepoHelpersTests(unittest.TestCase):
    def test_normalize_repo_slug_accepts_slug_ssh_and_https(self) -> None:
        self.assertEqual(repo_helpers.normalize_repo_slug("owner/repo"), "owner/repo")
        self.assertEqual(repo_helpers.normalize_repo_slug("git@github.com:owner/repo.git"), "owner/repo")
        self.assertEqual(repo_helpers.normalize_repo_slug("https://github.com/owner/repo"), "owner/repo")

    def test_normalize_repo_slug_rejects_invalid_values(self) -> None:
        self.assertIsNone(repo_helpers.normalize_repo_slug(""))
        self.assertIsNone(repo_helpers.normalize_repo_slug("https://example.com/owner/repo"))
        self.assertIsNone(repo_helpers.normalize_repo_slug("owner"))

    def test_pages_url_from_slug_handles_user_pages_repo(self) -> None:
        self.assertEqual(repo_helpers.pages_url_from_slug("octocat/octocat.github.io"), "https://octocat.github.io/")
        self.assertEqual(repo_helpers.pages_url_from_slug("octocat/my-dashboard"), "https://octocat.github.io/my-dashboard/")

    def test_normalize_dashboard_url_accepts_host_and_keeps_query(self) -> None:
        self.assertEqual(repo_helpers.normalize_dashboard_url("example.com"), "https://example.com/")
        self.assertEqual(
            repo_helpers.normalize_dashboard_url("https://example.com/foo?x=1"),
            "https://example.com/foo?x=1",
        )

    def test_normalize_dashboard_url_rejects_non_http_schemes(self) -> None:
        self.assertEqual(repo_helpers.normalize_dashboard_url("ftp://example.com"), "")

    def test_choose_repo_slug_from_env_prefers_dashboard_repo_by_default(self) -> None:
        self.assertEqual(
            repo_helpers.choose_repo_slug_from_env(
                "owner/custom-fork",
                "owner/current-repo",
                "",
            ),
            "owner/custom-fork",
        )

    def test_choose_repo_slug_from_env_prefers_github_repository_on_actions_mismatch(self) -> None:
        renamed_repo = "owner/custom-renamed-repo"
        self.assertEqual(
            repo_helpers.choose_repo_slug_from_env(
                "owner/git-sweaty",
                renamed_repo,
                "true",
            ),
            renamed_repo,
        )

    def test_choose_repo_slug_from_env_prefers_dashboard_repo_when_not_actions(self) -> None:
        self.assertEqual(
            repo_helpers.choose_repo_slug_from_env(
                "owner/custom-fork",
                "owner/current-repo",
                "false",
            ),
            "owner/custom-fork",
        )

    def test_choose_repo_slug_from_env_uses_github_repository_when_dashboard_repo_invalid(self) -> None:
        renamed_repo = "owner/custom-renamed-repo"
        self.assertEqual(
            repo_helpers.choose_repo_slug_from_env(
                "not-a-slug",
                renamed_repo,
                "true",
            ),
            renamed_repo,
        )

    def test_choose_repo_slug_from_env_uses_dashboard_repo_when_github_repository_missing(self) -> None:
        custom_repo = "owner/custom-renamed-repo"
        self.assertEqual(
            repo_helpers.choose_repo_slug_from_env(
                custom_repo,
                "",
                "true",
            ),
            custom_repo,
        )


if __name__ == "__main__":
    unittest.main()
