from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
js = (root / 'road-hop/game.js').read_text()
html = (root / 'road-hop/index.html').read_text()

# Definition: use a modest high-resolution/antialiasing path without uncapped DPR.
assert "antialias:true" in js, "WebGL antialiasing is not enabled"
assert re.search(r"setPixelRatio\(Math\.min\(devicePixelRatio,1\.5\)\)", js), "pixel ratio is not capped at 1.5x"
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
assert "#game{position:absolute;top:0;display:block;width:100%;height:100%" in html
assert "w=Math.min(innerWidth,h*2)" in js and "calc(50vw - ${w/2}px)" in js

# Character scale: PIP should be smaller than one lane cell while collisions stay conservative.
assert "PLAYER_VISUAL_SCALE=.72" in js
assert "createCharacter(save.character,PLAYER_VISUAL_SCALE)" in js
assert "(v.width+.56)/2" in js, "collision envelope changed with the cosmetic scale"

# Haunted must have high-contrast supernatural landmarks, not only dim cubes at one edge.
for token in ("haunted-moon", "haunted-ghost", "haunted-lamp", "haunted-grave-cluster", "MeshBasicMaterial"):
    assert token in js, f"missing Haunted redesign element: {token}"
for token in ("haunted-jack-o-lantern", "haunted-path-lantern", "haunted-candle-cluster", "haunted-bat"):
    assert token in js, f"missing Halloween detail: {token}"
assert "sky:0x170b32" in js, "Halloween sky lacks saturated violet contrast"
assert "0xb8ffef" in js, "Haunted spectral accent is missing"
assert "Math.abs(x)" in js, "Haunted prop placement still ignores its requested lane-side position"

# The local chunky display face must replace generic system monospace.
font = root / 'road-hop/assets/fonts/LilitaOne-Regular.ttf'
license_file = root / 'road-hop/assets/fonts/OFL.txt'
assert font.exists() and license_file.exists(), "local Road Hop font or license is missing"
assert "font-family:'Road Hop Arcade'" in html
assert "font-family:ui-monospace" not in html
assert "try{await document.fonts.load" in js and "catch{}" in js, "font failure can block game startup"
assert "bridgeSequences" not in js, "bridge route state must stay bounded during endless play"
assert "while(blockers.has(x))" not in js and "openBlockerCell" in js, "blocker placement can hang on duplicate edge cells"

print('ROAD HOP PLAYTEST CORRECTIONS PASS')
