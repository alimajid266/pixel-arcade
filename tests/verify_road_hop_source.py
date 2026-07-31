from pathlib import Path

root = Path(__file__).resolve().parents[1]
home = (root / "index.html").read_text()
game_path = root / "road-hop" / "index.html"
script_path = root / "road-hop" / "game.js"

assert 'id="play-road-hop"' in home
assert 'href="/road-hop/"' in home
assert game_path.exists() and script_path.exists()

game = game_path.read_text()
script = script_path.read_text()
assert "<title>Road Hop</title>" in game
assert "import * as THREE from '../vendor/three.module.min.js'" in script
assert "https://" not in game and "http://" not in game
assert 'window.__errors' in game
assert 'window.__game' in game
print("ROAD HOP SOURCE PASS")
