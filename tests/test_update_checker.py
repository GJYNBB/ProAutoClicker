import unittest
from unittest.mock import Mock, patch

from autoclicker.update_checker import fetch_latest_release, is_newer_version


class UpdateCheckerTests(unittest.TestCase):
    def test_is_newer_version_compares_semver_like_tags(self) -> None:
        self.assertTrue(is_newer_version("v1.2.0", "1.1.9"))
        self.assertFalse(is_newer_version("v1.1.0", "1.1.0"))
        self.assertFalse(is_newer_version("v1.0.9", "1.1.0"))

    def test_fetch_latest_release_parses_github_payload(self) -> None:
        response = Mock()
        response.json.return_value = {
            "tag_name": "v9.9.9",
            "html_url": "https://example.test/release",
            "name": "v9.9.9",
        }
        response.raise_for_status.return_value = None

        with patch("autoclicker.update_checker.requests.get", return_value=response) as get:
            release = fetch_latest_release()

        self.assertEqual(release.version, "v9.9.9")
        self.assertEqual(release.url, "https://example.test/release")
        get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
