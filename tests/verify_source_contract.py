from pathlib import Path
root=Path(__file__).resolve().parents[1]
home=(root/'index.html').read_text()
flappy=(root/'flappy/index.html').read_text()
zombie=(root/'zombie-defense/index.html').read_text()
assert 'href="/flappy/"' in home and 'href="/zombie-defense/"' in home
for name,text in [('flappy',flappy),('zombie',zombie)]:
    compact=text.replace(' ','')
    assert "constflappyUrl='/flappy/';" in compact,name
    assert "constzombieUrl='/zombie-defense/';" in compact,name
    assert 'class="rail-brand" href="/"' in text,name
    assert 'flappy-canvas.vercel.app' not in text,name
    assert 'zombie-defense-alimajid266s-projects.vercel.app' not in text,name
print('MONOREPO SOURCE CONTRACT PASS')
