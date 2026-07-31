from hashlib import sha256
from pathlib import Path

root=Path(__file__).resolve().parents[1]
html=(root/'road-hop/index.html').read_text()
js=(root/'road-hop/game.js').read_text()
vendor=root/'vendor/three.module.min.js'

assert "import * as THREE from '../vendor/three.module.min.js'" in js
assert vendor.exists() and vendor.stat().st_size == 691648
assert sha256(vendor.read_bytes()).hexdigest() == '08fd7545d13d2c7fb65ab691530a802dafefd638596501854f267d0fb13c39e7'
for forbidden in ('fetch(', 'XMLHttpRequest', 'WebSocket(', 'EventSource(', 'document.cookie', 'eval(', 'new Function(', '.innerHTML', '.outerHTML', 'insertAdjacentHTML'):
    assert forbidden not in js, forbidden
assert 'http://' not in js and 'https://' not in js
assert 'http://' not in html and 'https://' not in html
assert 'target="_blank"' not in html or 'rel="noopener"' in html
assert "roadHop.save.v2" in js, 'versioned local-only save key required'
assert 'JSON.parse' in js and 'try{' in js, 'corrupt save data must be guarded'
assert 'width=device-width,initial-scale=1' in html and 'touch-action:none' in html
viewport=html.split('name="viewport"',1)[1].split('>',1)[0]
assert 'user-scalable' not in viewport and 'maximum-scale' not in viewport
print('ROAD HOP SECURITY PASS')
