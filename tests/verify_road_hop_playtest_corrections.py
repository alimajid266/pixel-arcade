from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
js = (root / 'road-hop/game.js').read_text()
html = (root / 'road-hop/index.html').read_text()

# Performance: keep the low-end WebGL path cheap and avoid HUD writes per fixed step.
assert "antialias:false" in js, "WebGL antialiasing is still enabled"
assert re.search(r"setPixelRatio\(Math\.min\(devicePixelRatio,1(?:\.0+)?\)\)", js), "pixel ratio is not capped at 1x"
assert "shadowMap.enabled=false" in js, "expensive realtime shadows remain enabled"
step = js[js.index('function updateStep('):js.index('function update(dt)')]
assert 'updateUI()' not in step, "HUD DOM is still updated inside every simulation substep"
persist = js[js.index('function persist('):js.index('let save=')]
assert 'updateUI()' not in persist, "persist still writes the HUD from fixed-step reward paths"
assert "if(steps)uiDirty=true" in js and "if(uiDirty)updateUI()" in js, "HUD writes are not frame-coalesced"
assert "AHEAD=22" in js, "initial generated world remains larger than the performance budget"

# Framing: terrain must extend beyond the widest supported camera view.
surface = re.search(r"SURFACE_WIDTH=(\d+)", js)
assert surface and int(surface.group(1)) >= 32, "lane surface can expose square side edges"
assert "box(SURFACE_WIDTH" in js, "lane base does not use the extended surface width"
assert "world-underlay" in js, "camera-following underlay is missing"
assert "underlay.position.set(0,-.55,-cameraRow)" in js, "underlay does not follow the camera"
assert "skyDecor" in js, "camera-attached Haunted sky layer is missing"
assert "new THREE.CircleGeometry(.72,16)" in js, "Haunted moon must be a compact flat disc"
assert "moon.position.set(camera.left+1.2,camera.top-1.6,-2)" in js, "Haunted moon overlaps the launcher or clips the near plane"
assert "moon.scale.setScalar(Math.min(1,(camera.right-camera.left)/12))" in js, "Haunted moon is oversized on portrait mobile"
assert "depthTest:false,depthWrite:false,transparent:true,opacity:.62,fog:false" in js, "Haunted moon is still depth- or fog-occluded"
assert "html,body{margin:0;width:100%;height:100%;overflow:hidden" in html
assert ".shell{position:relative;width:100%;height:100%}" in html
assert "#game{display:block;width:100%;height:100%" in html

# Character scale: PIP should be smaller than one lane cell while collisions stay conservative.
assert "PLAYER_VISUAL_SCALE=.72" in js
assert "createCharacter(save.character,PLAYER_VISUAL_SCALE)" in js
assert "(v.width+.56)/2" in js, "collision envelope changed with the cosmetic scale"

# Haunted must have high-contrast supernatural landmarks, not only dim cubes at one edge.
for token in ("haunted-moon", "haunted-ghost", "haunted-lamp", "haunted-grave-cluster", "MeshBasicMaterial"):
    assert token in js, f"missing Haunted redesign element: {token}"
assert "0x090612" in js, "Haunted sky is not deep enough for luminous contrast"
assert "0xb8ffef" in js, "Haunted spectral accent is missing"
assert "Math.abs(x)" in js, "Haunted prop placement still ignores its requested lane-side position"

print('ROAD HOP PLAYTEST CORRECTIONS PASS')
