import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.backend import game_icons

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
JPG = b"\xff\xd8\xff" + b"0" * 32


class GameIconTests(unittest.TestCase):
    """Busca de ícones sem rede: ``_get`` responde por um mapa de URLs."""

    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        root = Path(self._directory.name)
        self._paths = patch.multiple(
            game_icons, CACHE_DIR=root / "cache", INDEX=root / "cache" / "index.json",
            KEY_FILE=root / "steamgriddb.key")
        self._paths.start()
        self.calls: list[tuple[str, str]] = []
        self.responses: dict[str, bytes] = {}

    def tearDown(self):
        self._paths.stop()
        self._directory.cleanup()

    def _fake_get(self, url: str, key: str = "") -> bytes:
        self.calls.append((url, key))
        for prefix, body in self.responses.items():
            if url.startswith(prefix):
                return body
        raise OSError(f"sem resposta para {url}")

    def _lookup(self, *names: str) -> dict:
        with patch.object(game_icons, "_get", self._fake_get):
            return game_icons.lookup(list(names))

    def _steam_search(self, *titles: tuple[int, str]) -> None:
        self.responses[game_icons.STEAM_SEARCH] = json.dumps(
            {"items": [{"id": app_id, "name": title} for app_id, title in titles]}).encode()

    def test_steamgriddb_icon_is_used_when_there_is_a_key(self):
        game_icons.KEY_FILE.write_text("abc123\n")
        sgdb = game_icons.SGDB_API
        self.responses.update({
            f"{sgdb}/search/autocomplete/Roblox": json.dumps({"data": [{"id": 42}]}).encode(),
            f"{sgdb}/icons/game/42": json.dumps({"data": [{"url": "https://cdn/roblox.png"}]}).encode(),
            "https://cdn/roblox.png": PNG,
        })
        icon = self._lookup("Roblox")["Roblox"]
        self.assertEqual(icon["kind"], "icon")
        self.assertTrue(icon["file"].endswith(".png"))
        self.assertIn((f"{sgdb}/search/autocomplete/Roblox", "abc123"), self.calls)

    def test_without_a_key_only_an_equivalent_steam_title_counts(self):
        self._steam_search((1, "Minecraft Dungeons"), (730, "Counter-Strike 2"))
        self.responses[f"{game_icons.STEAM_ASSETS}/730/"] = JPG
        found = self._lookup("Minecraft", "Counter-Strike 2")
        self.assertIsNone(found["Minecraft"])
        self.assertEqual(found["Counter-Strike 2"]["kind"], "cover")
        self.assertFalse(any("steamgriddb" in url for url, _ in self.calls))

    def test_found_icons_are_not_fetched_again(self):
        self._steam_search((730, "Counter-Strike 2"))
        self.responses[f"{game_icons.STEAM_ASSETS}/730/"] = JPG
        self._lookup("Counter-Strike 2")
        self.calls.clear()
        self.assertIsNotNone(self._lookup("Counter-Strike 2")["Counter-Strike 2"])
        self.assertEqual(self.calls, [])

    def test_saving_a_key_retries_games_that_had_no_icon(self):
        self._steam_search()
        self.assertIsNone(self._lookup("Roblox")["Roblox"])
        self.calls.clear()
        self._lookup("Roblox")
        self.assertEqual(self.calls, [], "um ausente recente não deve ir à rede de novo")
        game_icons.save_key("abc123")
        self._lookup("Roblox")
        self.assertTrue(any("steamgriddb" in url for url, _ in self.calls))

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg ausente")
    def test_ico_only_games_get_a_png_icon(self):
        """O SteamGridDB só tem .ico de vários jogos (Sea of Thieves, How to
        Fish); recusá-lo os deixava sem ícone por uma semana."""
        with tempfile.TemporaryDirectory() as directory:
            ico = Path(directory) / "jogo.ico"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=red:s=64x64",
                            "-frames:v", "1", str(ico)], check=True)
            game_icons.KEY_FILE.write_text("abc123\n")
            sgdb = game_icons.SGDB_API
            self.responses.update({
                f"{sgdb}/search/autocomplete/Sea": json.dumps({"data": [{"id": 7}]}).encode(),
                f"{sgdb}/icons/game/7": json.dumps({"data": [{"url": "https://cdn/sot.ico"}]}).encode(),
                "https://cdn/sot.ico": ico.read_bytes(),
            })
            icon = self._lookup("Sea of Thieves")["Sea of Thieves"]
        self.assertIsNotNone(icon)
        self.assertEqual(icon["kind"], "icon")
        self.assertTrue(icon["file"].endswith(".png"))
        self.assertTrue((game_icons.CACHE_DIR / icon["file"]).read_bytes().startswith(b"\x89PNG"))

    def test_retry_forgets_only_the_missing_games(self):
        self._steam_search((730, "Counter-Strike 2"))
        self.responses[f"{game_icons.STEAM_ASSETS}/730/"] = JPG
        self._lookup("Counter-Strike 2", "Roblox")
        self.assertEqual(game_icons.forget_missing(), 1)
        self.calls.clear()
        self._lookup("Counter-Strike 2", "Roblox")
        searched = [url for url, _ in self.calls if url.startswith(game_icons.STEAM_SEARCH)]
        self.assertEqual(len(searched), 1, "só o jogo sem ícone deveria ir à rede de novo")
        self.assertIn("Roblox", searched[0])

    def test_only_generated_file_names_are_served(self):
        self.assertIsNone(game_icons.cached_file("../steamgriddb.key"))
        self.assertIsNone(game_icons.cached_file("index.json"))


if __name__ == "__main__":
    unittest.main()
