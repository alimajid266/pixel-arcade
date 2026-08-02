from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "farmstead"

required = [
    GAME / "index.html",
    GAME / "game.js",
    GAME / "farm-core.mjs",
    GAME / "ASSET-LICENSES.md",
    GAME / "assets" / "farmer.glb",
    GAME / "assets" / "farm.glb",
    ROOT / "vendor" / "GLTFLoader.js",
]
for path in required:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

html = (GAME / "index.html").read_text()
source = (GAME / "game.js").read_text()
home = (ROOT / "index.html").read_text()
licenses = (GAME / "ASSET-LICENSES.md").read_text()

for control in [
    "start", "pause-toggle", "resume", "end-day", "sell-all", "deliver-order",
    "tool-hoe", "tool-water", "tool-turnip", "tool-carrot", "tool-pumpkin", "tool-harvest",
]:
    assert f'id="{control}"' in html, control

assert "user-scalable=no" not in html
assert "maximum-scale" not in html
assert "window.__errors=[]" in html
assert "../vendor/three.module.min.js" in source
assert "../vendor/GLTFLoader.js" in source
assert "http://" not in source and "https://" not in source
assert "eval(" not in source and ".innerHTML" not in source
assert "window.__game" in source
assert 'id="play-farmstead"' in home
assert 'href="/farmstead/"' in home
assert "Quaternius" in licenses and "Poly by Google" in licenses
expected_hashes = {
    "farmer.glb": "f7ae6e2596c6521d296fa5948783f1dac717807456ce5355e48719e81d15e9a6",
    "farm.glb": "a01fa134bd97ece0684615583420eb36ea14935d206cd99f60e1c7aa6ab28c33",
}
for filename, expected in expected_hashes.items():
    actual = hashlib.sha256((GAME / "assets" / filename).read_bytes()).hexdigest()
    assert actual == expected, (filename, actual)
print("FARMSTEAD SOURCE CONTRACT PASS")
