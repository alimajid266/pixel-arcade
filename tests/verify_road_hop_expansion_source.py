from pathlib import Path

root=Path(__file__).resolve().parents[1]
js=(root/'road-hop/game.js').read_text()
html=(root/'road-hop/index.html').read_text()
readme=(root/'README.md').read_text()

for token in ('BIOMES','CHARACTERS','MISSIONS','RACE_LENGTH','SAVE_KEY','dailySeed','nearMiss','postcards'):
    assert token in js, f'missing expansion contract: {token}'
for biome in ('meadow','wetlands','autumn','haunted'):
    assert biome in js.lower(), f'missing biome: {biome}'
for name,price in [('PIP',0),('BOUNCE',75),('RUSTY',175),('BOLT',300),('JACK',500),('WISP',750)]:
    assert name in js and str(price) in js, f'missing roster contract: {name}/{price}'
for control in ('mode-select','biome-select','daily-toggle','shop-open','gallery-open','missions','coins'):
    assert f'id="{control}"' in html, f'missing DOM control: {control}'
assert 'Road Rally' in html and '50' in js
assert 'Road Hop expansion' in readme
assert "roadHop.save.v2" in js
assert "function changeCoins(" in js
assert "save.coins+=" not in js and "save.coins-=" not in js
print('ROAD HOP EXPANSION SOURCE PASS')
