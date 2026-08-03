from pathlib import Path
root=Path(__file__).resolve().parents[1]
home=(root/'index.html').read_text()
flappy=(root/'flappy/index.html').read_text()
zombie=(root/'zombie-defense/index.html').read_text()
crossy=(root/'road-hop/index.html').read_text()
panic=(root/'panic-button/index.html').read_text()
assert 'href="/flappy/"' in home and 'href="/zombie-defense/"' in home and 'href="/road-hop/"' in home and 'href="/farmstead/"' in home and 'href="/panic-button/"' in home
assert 'class="brand" href="/"' in panic
assert 'fonts.googleapis.com' not in panic and 'fonts.gstatic.com' not in panic
assert "url('assets/fonts/PressStart2P-Regular.ttf')" in (root/'panic-button/styles.css').read_text()
assert (root/'panic-button/assets/fonts/OFL-PressStart2P.txt').is_file()
assert (root/'panic-button/assets/fonts/OFL-VT323.txt').is_file()
for name,text in [('flappy',flappy),('zombie',zombie)]:
    compact=text.replace(' ','')
    assert "constflappyUrl='/flappy/';" in compact,name
    assert "constzombieUrl='/zombie-defense/';" in compact,name
    assert "constroadHopUrl='/road-hop/';" in compact,name
    assert "constfarmsteadUrl='/farmstead/';" in compact,name
    assert 'id="road-hop-game-link"' in text,name
    assert 'id="farmstead-game-link"' in text,name
    assert 'class="rail-brand" href="/"' in text,name
    assert 'flappy-canvas.vercel.app' not in text,name
    assert 'zombie-defense-alimajid266s-projects.vercel.app' not in text,name
print('MONOREPO SOURCE CONTRACT PASS')
