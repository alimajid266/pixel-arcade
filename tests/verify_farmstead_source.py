from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "farmstead"
VOXEL = GAME / "assets" / "voxel"

required = [
    GAME / "index.html",
    GAME / "game.js",
    GAME / "farm-core.mjs",
    GAME / "ASSET-LICENSES.md",
    GAME / "assets" / "fonts" / "LilitaOne-Regular.ttf",
    GAME / "assets" / "fonts" / "OFL.txt",
    VOXEL / "character-a.glb",
    VOXEL / "Textures" / "texture-a.png",
    VOXEL / "building-type-n.glb",
    VOXEL / "fence-1x4.glb",
    VOXEL / "tree-large.glb",
    VOXEL / "tree-small.glb",
    VOXEL / "path-stones-long.glb",
    VOXEL / "planter.glb",
    VOXEL / "Textures" / "colormap.png",
    VOXEL / "Textures" / "housemap.png",
    ROOT / "vendor" / "GLTFLoader.js",
]
for path in required:
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"

html = (GAME / "index.html").read_text()
source = (GAME / "game.js").read_text()
home = (ROOT / "index.html").read_text()
licenses = (GAME / "ASSET-LICENSES.md").read_text()
vercel_ignore = (ROOT / ".vercelignore").read_text()

for control in [
    "start", "pause-toggle", "resume", "end-day", "sell-all", "deliver-order",
    "tool-hoe", "tool-water", "tool-turnip", "tool-carrot", "tool-pumpkin", "tool-harvest",
    "guide-open", "field-guide", "tutorial", "tutorial-next",
    "buy-energy", "night-transition",
]:
    assert f'id="{control}"' in html, control

assert "user-scalable=no" not in html
assert "maximum-scale" not in html
assert "window.__errors=[]" in html
assert 'data-aesthetic="voxel-farm"' in html
assert "font-family:'Lilita One'" in html
assert "url('./assets/fonts/LilitaOne-Regular.ttf')" in html
assert "font-display:swap" in html
assert "../vendor/three.module.min.js" in source
assert "../vendor/GLTFLoader.js" in source
assert "http://" not in source and "https://" not in source
assert "eval(" not in source and ".innerHTML" not in source
assert "window.__game" in source
assert "VOXEL_WORLD" in source
assert "const RENDER_SCALE = 1;" in source
assert "antialias: true" in source
assert "InstancedMesh" in source
assert "voxel('character-a')" in source
assert "voxel('building-type-n')" in source
assert "kenney('character-archer')" not in source
assert 'id="play-farmstead"' in home
assert 'href="/farmstead/"' in home
assert "Kenney Blocky Characters" in licenses
assert "Kenney City Kit (Suburban)" in licenses
assert "Lilita One" in licenses
assert "SIL Open Font License 1.1" in licenses
assert "!farmstead/assets/voxel/Textures/*.png" in vercel_ignore
assert 'id="complete"' not in html
assert "RESTORE THE MILL" not in html
assert "checkCompletion" not in source
assert "START WITH 6 TURNIP SEEDS" in html
assert "RAIN WATERS EVERY PLANTED CROP" in html
assert "TURNIP · 1 DAY · SELLS 18" in html
assert "MATURE CROPS ROT" in html

expected_hashes = {
    "character-a.glb": "8ee5dae167ec589863f6bba222467eb90ace8be357a4c5abfcab289290181616",
    "Textures/texture-a.png": "257e944c582ce7cda206fbd8ceb717be648f9721756baf377a36478c11c0059a",
    "building-type-n.glb": "2a371632ed4a50a5c9c7b4b7087e41f0c0989457c20481b4106291ab05603e62",
    "fence-1x4.glb": "f63d17e1bb8f83416cffefdc0a90615ddd5b2cb69d8ea721cebdd663f9b2c4fc",
    "tree-large.glb": "16d1f95c149bc727a953a473cf20bf21de9bf1a88747c4f9d2eeb4ac7d43e291",
    "tree-small.glb": "5f63359e5f392609d7617cc98070855ca1ffd4f4b4bc3978a5ff56ece88a58d6",
    "path-stones-long.glb": "cbd73ca5746f2290f44a2e1fc6f0759076c2c5fcdb3cb3f1e3acd74d5751d114",
    "planter.glb": "a876e87d908f0397dcaf94b7705835447825c4c5b39195319535415386542c17",
    "Textures/colormap.png": "9b5de86078c25ef02351a80d35ff3c978693a1044565b73eedd9ae9b5b80665d",
    "Textures/housemap.png": "7fb6ea5325d93e5f3f8567a397b7b6dd09d7e43ceeff1fc071076b615f781f86",
}
for relative, expected in expected_hashes.items():
    actual = hashlib.sha256((VOXEL / relative).read_bytes()).hexdigest()
    assert actual == expected, (relative, actual)
font_hashes = {
    "LilitaOne-Regular.ttf": "f5b641c45c69d772ee4eda687bc9fda411d5cad6b0b45371491da4580cbc8d59",
    "OFL.txt": "9c14147639ea90cfa41b0645c77b4fa642494d11696e2a9f5cd2d9b5843c1a6e",
}
for filename, expected in font_hashes.items():
    actual = hashlib.sha256((GAME / "assets" / "fonts" / filename).read_bytes()).hexdigest()
    assert actual == expected, (filename, actual)
print("FARMSTEAD SOURCE CONTRACT PASS")
