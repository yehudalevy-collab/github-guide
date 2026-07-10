from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse


ROOT = Path(__file__).resolve().parents[1]


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.meta_refresh_targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src"):
            value = values.get(key)
            if value:
                self.links.append(value)
        if tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            content = values.get("content") or ""
            match = re.search(r"url=([^;]+)", content, flags=re.IGNORECASE)
            if match:
                self.meta_refresh_targets.append(match.group(1).strip())


def local_target_exists(target: str) -> bool:
    clean_target = urldefrag(target)[0]
    if not clean_target:
        return True
    parsed = urlparse(clean_target)
    if parsed.scheme or parsed.netloc or clean_target.startswith("mailto:"):
        return True
    return (ROOT / clean_target).exists()


class StaticGuideTests(unittest.TestCase):
    def test_root_page_redirects_to_single_file_guide(self) -> None:
        parser = LinkCollector()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))

        self.assertIn("github-mastery-guide.html", parser.meta_refresh_targets)
        self.assertIn("github-mastery-guide.html", parser.links)

    def test_readme_local_links_point_to_tracked_files(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)

        missing = [target for target in targets if not local_target_exists(target)]
        self.assertEqual(missing, [])

    def test_guide_keeps_expected_level_structure(self) -> None:
        html = (ROOT / "github-mastery-guide.html").read_text(encoding="utf-8")

        for label in ("Basic", "Intermediate", "Advanced"):
            self.assertIn(label, html)
        self.assertIn("GitHub Mastery Guide", html)


if __name__ == "__main__":
    unittest.main()
