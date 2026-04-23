"""Unit tests: verify game/assets/Favicon_for_browser_game.png is wired in
as the favicon served by the pygbag web build.

Covers three layers of wiring:
  1. The PNG bytes at game/build/web/favicon.png (what port 9666 serves).
  2. The pygbag template custom.tmpl (used for every rebuild).
  3. The generated game/build/web/index.html (what browsers currently load).

Self-healing behavior:
  If any of these assertions fail — meaning the custom favicon wiring is
  broken — tearDownModule copies pygame's bundled anaconda icon
  (pygame/pygame_icon.bmp) to game/build/web/favicon.png as a PNG, so the
  local dev server on :9666 keeps serving a valid favicon even while the
  custom asset wiring is red.
"""

import hashlib
import os
import sys
import unittest
from pathlib import Path

import pygame


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = REPO_ROOT / "game" / "assets" / "Favicon_for_browser_game.png"
BUILD_DIR = REPO_ROOT / "game" / "build" / "web"
BUILD_FAVICON = BUILD_DIR / "favicon.png"
BUILD_INDEX = BUILD_DIR / "index.html"
TEMPLATE = REPO_ROOT / "custom.tmpl"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def favicon_matches_asset() -> bool:
    if not (BUILD_FAVICON.is_file() and ASSET_PATH.is_file()):
        return False
    return sha256(BUILD_FAVICON) == sha256(ASSET_PATH)


def restore_pygame_stock_favicon(dest: Path) -> bool:
    """Copy pygame's bundled anaconda icon to `dest`, converting BMP -> PNG.

    Returns True on success, False otherwise. Best-effort — failure to
    restore must not mask the original test failure.
    """
    pygame_dir = Path(pygame.__file__).resolve().parent
    stock_bmp = pygame_dir / "pygame_icon.bmp"
    if not stock_bmp.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not pygame.get_init():
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
    surface = pygame.image.load(str(stock_bmp))
    pygame.image.save(surface, str(dest))
    return dest.is_file()


def tearDownModule() -> None:
    """If the build favicon no longer matches the project asset, fall back
    to pygame's stock anaconda icon so the dev server still has *a*
    favicon to serve."""
    try:
        if favicon_matches_asset():
            return
        restored = restore_pygame_stock_favicon(BUILD_FAVICON)
        if restored:
            sys.stderr.write(
                "\n[favicon-guard] Custom favicon wiring failed; reverted "
                f"{BUILD_FAVICON} to pygame stock anaconda icon.\n"
            )
    except Exception as exc:
        sys.stderr.write(f"\n[favicon-guard] Fallback restore failed: {exc}\n")


class FaviconPygbagWiringTest(unittest.TestCase):
    """Ensure the favicon served by the pygbag build is the project asset."""

    def test_source_asset_exists(self) -> None:
        self.assertTrue(
            ASSET_PATH.is_file(),
            f"Source favicon asset is missing at {ASSET_PATH}",
        )
        self.assertGreater(
            ASSET_PATH.stat().st_size, 0,
            f"Source favicon asset is empty: {ASSET_PATH}",
        )

    def test_build_favicon_exists(self) -> None:
        self.assertTrue(
            BUILD_FAVICON.is_file(),
            f"Pygbag build favicon missing at {BUILD_FAVICON}. "
            "Run the pygbag build or copy the asset into the build dir.",
        )

    def test_build_favicon_bytes_match_asset(self) -> None:
        self.assertTrue(ASSET_PATH.is_file(), f"Missing source: {ASSET_PATH}")
        self.assertTrue(BUILD_FAVICON.is_file(), f"Missing build: {BUILD_FAVICON}")
        self.assertEqual(
            sha256(BUILD_FAVICON),
            sha256(ASSET_PATH),
            "game/build/web/favicon.png does not match "
            "game/assets/Favicon_for_browser_game.png. Copy the asset into "
            "the build directory to fix.",
        )

    def test_template_references_favicon(self) -> None:
        self.assertTrue(TEMPLATE.is_file(), f"Missing template: {TEMPLATE}")
        html = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            'rel="icon"', html,
            "custom.tmpl is missing a <link rel=\"icon\"> tag",
        )
        self.assertIn(
            'href="favicon.png"', html,
            "custom.tmpl <link rel=\"icon\"> must point to favicon.png",
        )

    def test_built_index_references_favicon(self) -> None:
        self.assertTrue(
            BUILD_INDEX.is_file(),
            f"Missing generated index.html: {BUILD_INDEX}",
        )
        html = BUILD_INDEX.read_text(encoding="utf-8")
        self.assertIn(
            'rel="icon"', html,
            "game/build/web/index.html is missing a <link rel=\"icon\"> tag",
        )
        self.assertIn(
            'href="favicon.png"', html,
            "index.html <link rel=\"icon\"> must point to favicon.png",
        )


if __name__ == "__main__":
    unittest.main()
