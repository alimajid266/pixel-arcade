# Harvest Hollow asset licenses

Harvest Hollow vendors its runtime dependencies and selected game assets locally so the deployed game has no CDN or third-party runtime dependency.

## Kenney Blocky Characters 2.0

- **Creator:** Kenney
- **Source:** https://kenney.nl/assets/blocky-characters
- **License:** Creative Commons Zero 1.0 Universal (CC0)
- **License deed:** https://creativecommons.org/publicdomain/zero/1.0/
- **Use in Harvest Hollow:** blocky farmer character; a separately authored voxel straw hat and hoe are attached at runtime
- **Runtime treatment:** nearest-neighbor texture filtering, role-appropriate scale, and procedural limb animation using the model's authored limb nodes

| Local file | SHA-256 |
|---|---|
| `assets/voxel/character-a.glb` | `8ee5dae167ec589863f6bba222467eb90ace8be357a4c5abfcab289290181616` |
| `assets/voxel/Textures/texture-a.png` | `257e944c582ce7cda206fbd8ceb717be648f9721756baf377a36478c11c0059a` |

## Kenney City Kit (Suburban) 2.0

- **Creator:** Kenney
- **Source:** https://kenney.nl/assets/city-kit-suburban
- **License:** Creative Commons Zero 1.0 Universal (CC0)
- **License deed:** https://creativecommons.org/publicdomain/zero/1.0/
- **Use in Harvest Hollow:** farmhouse, fences, trees, path stones, and planters
- **Runtime treatment:** models are normalized, positioned in the authored farm layout, rendered with nearest-neighbor texture filtering, and repeated scenery is merged by material to limit draw calls
- **Farmhouse color derivative:** `housemap.png` is a local derivative of Kenney's `colormap.png`. Green roof pixels were remapped to a coral/red palette for visual separation from the grass. The building GLB's equal-length external texture URI was changed from `Textures/colormap.png` to `Textures/housemap.png`; geometry and UVs are unchanged.

| Local file | SHA-256 |
|---|---|
| `assets/voxel/building-type-n.glb` | `2a371632ed4a50a5c9c7b4b7087e41f0c0989457c20481b4106291ab05603e62` |
| `assets/voxel/fence-1x4.glb` | `f63d17e1bb8f83416cffefdc0a90615ddd5b2cb69d8ea721cebdd663f9b2c4fc` |
| `assets/voxel/tree-large.glb` | `16d1f95c149bc727a953a473cf20bf21de9bf1a88747c4f9d2eeb4ac7d43e291` |
| `assets/voxel/tree-small.glb` | `5f63359e5f392609d7617cc98070855ca1ffd4f4b4bc3978a5ff56ece88a58d6` |
| `assets/voxel/path-stones-long.glb` | `cbd73ca5746f2290f44a2e1fc6f0759076c2c5fcdb3cb3f1e3acd74d5751d114` |
| `assets/voxel/planter.glb` | `a876e87d908f0397dcaf94b7705835447825c4c5b39195319535415386542c17` |
| `assets/voxel/Textures/colormap.png` | `9b5de86078c25ef02351a80d35ff3c978693a1044565b73eedd9ae9b5b80665d` |
| `assets/voxel/Textures/housemap.png` | `7fb6ea5325d93e5f3f8567a397b7b6dd09d7e43ceeff1fc071076b615f781f86` |

## Lilita One font

- **Designer:** Juan Montoreano
- **Distribution:** Google Fonts
- **Source:** https://github.com/google/fonts/tree/main/ofl/lilitaone
- **License:** SIL Open Font License 1.1
- **Use in Harvest Hollow:** locally vendored game-style UI typography for headings, buttons, HUD labels, tutorial text, and the Field Guide
- **Runtime treatment:** loaded from the same origin through CSS `@font-face`; the system sans-serif stack remains the loading fallback

| Local file | SHA-256 |
|---|---|
| `assets/fonts/LilitaOne-Regular.ttf` | `f5b641c45c69d772ee4eda687bc9fda411d5cad6b0b45371491da4580cbc8d59` |
| `assets/fonts/OFL.txt` | `9c14147639ea90cfa41b0645c77b4fa642494d11696e2a9f5cd2d9b5843c1a6e` |

## Three.js

- **Project:** Three.js r170
- **Source:** https://github.com/mrdoob/three.js/tree/r170
- **License:** MIT
- **Local files:** `../vendor/three.module.min.js`, `../vendor/GLTFLoader.js`, and `../vendor/BufferGeometryUtils.js`

### MIT License notice

Copyright © 2010-2024 Three.js Authors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Original Harvest Hollow art

The checkerboard voxel terrain, 30 plot blocks, crop growth meshes, voxel pond, path blocks, market stall, windmill assembly, farmer straw hat, and farmer hoe were authored specifically for Harvest Hollow. The visual direction uses broad qualities of colorful voxel games; no protected models, textures, characters, maps, names, code, branding, or exact designs were copied from Crossy Road, Stardew Valley, or another farming game.
