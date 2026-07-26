from pathlib import Path
import json
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8770'

zombie_source = (ROOT / 'zombie-defense/index.html').read_text()
flappy_source = (ROOT / 'flappy/index.html').read_text()

source_checks = {
    'countdown_copy_removed': 'THE HORDE RESUMES IN 1.5 SECONDS' not in zombie_source,
    'hint_lowered': '#hint{position:absolute;left:18px;top:-25px' in zombie_source.replace(' ', ''),
    'bomber_impact_audio': 'game.audio.explosion()' in zombie_source and 'explosion(){' in zombie_source,
    'preview_uses_live_grid': 'pathCells[row*COLS+col]' in zombie_source,
    'sky_run_removed': '8-BIT SKY RUN' not in flappy_source and 'DECORATIVE SUBTITLE' not in flappy_source,
    'ghost_persistence': "getBoolean('ghostEnabled', true)" in flappy_source and "setBoolean('ghostEnabled'" in flappy_source,
}

options = Options()
options.add_argument('-headless')
options.binary_location = '/snap/firefox/current/usr/lib/firefox/firefox'
driver = webdriver.Firefox(options=options, service=Service('/snap/bin/firefox.geckodriver'))
try:
    driver.get(BASE + '/zombie-defense/')
    time.sleep(0.6)
    zombie = driver.execute_script("""
      const L = __internals.MENU_LAYOUT;
      const utility = {
        instructionsLeft: L.instructions.x,
        soundLeft: L.sound.x,
        soundRight: L.sound.x + L.sound.w,
        gap: L.sound.x - (L.instructions.x + L.instructions.w)
      };
      const map = L.previewMap || null;
      const previewSignatures = [];
      for (let index = 0; index < 3; index++) {
        __game.mapIndex = index;
        __game.cycleMap(0);
        __game.state.draw(__game.ctx);
        const pixels = __game.ctx.getImageData(map.x, map.y, map.w, map.h).data;
        let signature = 2166136261;
        for (let i = 0; i < pixels.length; i += 7) {
          signature ^= pixels[i];
          signature = Math.imul(signature, 16777619);
        }
        previewSignatures.push(signature >>> 0);
      }
      let explosionCalls = 0;
      const weapon = __internals.WEAPONS[2];
      const target = new __internals.Zombie('brute', 1);
      target.x = 100; target.y = 100; target.drawX = 100; target.drawY = 100;
      const projectile = new __internals.Projectile(100, 100, target, weapon, weapon.damage);
      projectile.update(.1, {
        enemies: [target], effects: [], scorches: [],
        audio: { explosion(){ explosionCalls += 1; } }
      });
      const audio = __game.audio;
      const saved = {ctx:audio.ctx, bus:audio.sfxBus, muted:audio.sfxMuted};
      let oscillators = 0;
      const param = {setValueAtTime(){}, exponentialRampToValueAtTime(){}};
      audio.ctx = {
        currentTime: 0,
        createOscillator(){ oscillators += 1; return {type:'',frequency:param,connect(){},start(){},stop(){}}; },
        createGain(){ return {gain:param,connect(){}}; }
      };
      audio.sfxBus = {};
      audio.sfxMuted = false;
      audio.explosion();
      const audibleOscillators = oscillators;
      audio.sfxMuted = true;
      audio.explosion();
      const mutedOscillators = oscillators - audibleOscillators;
      audio.ctx = saved.ctx; audio.sfxBus = saved.bus; audio.sfxMuted = saved.muted;
      return {
        utility,
        previewMap: map,
        previewAspect: map ? map.w / map.h : 0,
        expectedAspect: 20 / 12,
        previewSignatures,
        explosionCalls,
        audibleOscillators,
        mutedOscillators,
        errors: __errors.slice()
      };
    """)

    driver.get(BASE + '/flappy/')
    time.sleep(0.7)
    ghost = driver.execute_script("""
      __game.returnToMenu();
      const initial = __game.ghostEnabled;
      __game.handleCanvasAction(10, 540);
      const afterOutsideClick = __game.ghostEnabled;
      __game.handleCanvasAction(200, 540);
      const afterClick = __game.ghostEnabled;
      const storedAfterClick = localStorage.getItem('flappyCanvas.ghostEnabled');
      __game.username = '';
      window.dispatchEvent(new KeyboardEvent('keydown', {code:'KeyG', key:'g', bubbles:true}));
      const usernameAfterG = __game.username;
      const ghostAfterNameEntry = __game.ghostEnabled;
      __game.machine.set('PLAYING', __game.playing);
      __game.currentGhostCount = 0;
      __game.bird.y = 222;
      __game.recordGhostSample();
      const recordsWhileHidden = __game.currentGhostCount === 1 && __game.currentGhost[0] === 222;
      __game.previousGhost[0] = 210;
      __game.previousGhostCount = 1;
      __game.ghostPlaybackTime = 0;
      let drawsOff = 0;
      const original = __game.bird.drawGhost;
      __game.bird.drawGhost = function(){ drawsOff += 1; };
      __game.drawWorld(__game.ctx, true);
      __game.ghostEnabled = true;
      let drawsOn = 0;
      __game.bird.drawGhost = function(){ drawsOn += 1; };
      __game.drawWorld(__game.ctx, true);
      __game.bird.drawGhost = original;
      return {initial, afterOutsideClick, afterClick, storedAfterClick, usernameAfterG,
        ghostAfterNameEntry, recordsWhileHidden, drawsOff, drawsOn, errors:__errors.slice()};
    """)
    driver.refresh()
    time.sleep(0.5)
    ghost['afterReload'] = driver.execute_script("return __game.ghostEnabled")
finally:
    driver.quit()

failures = []
for name, passed in source_checks.items():
    if not passed:
        failures.append(name)
if not (zombie['utility']['instructionsLeft'] <= 592 and
        zombie['utility']['soundLeft'] <= 716 and
        zombie['utility']['soundRight'] <= 754 and
        zombie['utility']['gap'] >= 8):
    failures.append('zombie_menu_utilities_shifted_left')
if not (zombie['previewMap'] and abs(zombie['previewAspect'] - zombie['expectedAspect']) < 0.01):
    failures.append('aspect_correct_preview_map')
if len(set(zombie['previewSignatures'])) != 3:
    failures.append('distinct_current_map_previews')
if zombie['explosionCalls'] != 1:
    failures.append('bomber_explosion_called_once')
if zombie['audibleOscillators'] != 2 or zombie['mutedOscillators'] != 0:
    failures.append('bomber_audio_respects_sfx_mute')
if zombie['errors']:
    failures.append('zombie_runtime_errors')
if not (ghost['initial'] is True and ghost['afterOutsideClick'] is True and
        ghost['afterClick'] is False and ghost['storedAfterClick'] == 'false' and
        ghost['usernameAfterG'] == 'G' and ghost['ghostAfterNameEntry'] is False and
        ghost['recordsWhileHidden'] is True and ghost['drawsOff'] == 0 and
        ghost['drawsOn'] == 1 and ghost['afterReload'] is False):
    failures.append('persistent_ghost_toggle_and_render_gate')
if ghost['errors']:
    failures.append('flappy_runtime_errors')

assert not failures, json.dumps({'failures': failures, 'source': source_checks, 'zombie': zombie, 'ghost': ghost}, indent=2)
print('LATEST FEEDBACK PASS:', json.dumps({'source': source_checks, 'zombie': zombie, 'ghost': ghost}, sort_keys=True))
