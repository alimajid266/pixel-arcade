import json
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

BASE = 'http://127.0.0.1:8770'

options = Options()
options.add_argument('-headless')
options.binary_location = '/snap/firefox/current/usr/lib/firefox/firefox'
options.enable_bidi = True

driver = webdriver.Firefox(options=options, service=Service('/snap/bin/firefox.geckodriver'))
results = []
try:
    for width, height in ((390, 844), (360, 800), (430, 932)):
        driver.get(BASE + '/flappy/')
        driver.browsing_context.set_viewport(
            context=driver.current_window_handle,
            viewport={'width': width, 'height': height},
        )
        time.sleep(0.5)
        result = driver.execute_script("""
          const canvas = document.getElementById('game');
          const rail = document.querySelector('.game-rail');
          const notice = document.querySelector('.rotate-notice');
          const c = canvas.getBoundingClientRect();
          const r = rail.getBoundingClientRect();
          const visible = el => !!el && getComputedStyle(el).display !== 'none' && el.getClientRects().length > 0;
          const targets = [...rail.querySelectorAll('.rail-brand,.game-tile,.audio-toggle')]
            .filter(visible)
            .map(el => { const b=el.getBoundingClientRect(); return {label:el.textContent.trim(),width:b.width,height:b.height}; });
          const overlaps = !(c.right <= r.left || r.right <= c.left || c.bottom <= r.top || r.bottom <= c.top);
          const before = __game.machine.name;
          const touch = new Event('touchstart', {bubbles:true,cancelable:true});
          Object.defineProperty(touch,'touches',{value:[{clientX:c.left+c.width/2,clientY:c.top+c.height*.55}]});
          canvas.dispatchEvent(touch);
          const after = __game.machine.name;
          return {
            requested: [arguments[0], arguments[1]],
            viewport: [innerWidth, innerHeight],
            canvas: {left:c.left, top:c.top, width:c.width, height:c.height, right:c.right, bottom:c.bottom},
            rail: {left:r.left, top:r.top, width:r.width, height:r.height, right:r.right, bottom:r.bottom},
            targets,
            noticeVisible: visible(notice),
            overlap: overlaps,
            scale: c.width / 400,
            effectiveSmallText: 10 * c.width / 400,
            documentWidth: document.documentElement.scrollWidth,
            documentHeight: document.documentElement.scrollHeight,
            before,
            after,
            errors: __errors.slice()
          };
        """, width, height)
        results.append(result)

    driver.get(BASE + '/flappy/')
    driver.browsing_context.set_viewport(
        context=driver.current_window_handle,
        viewport={'width': 844, 'height': 414},
    )
    time.sleep(0.3)
    driver.execute_script("""
      const c=document.getElementById('game'),r=c.getBoundingClientRect();
      const touch=new Event('touchstart',{bubbles:true,cancelable:true});
      Object.defineProperty(touch,'touches',{value:[{clientX:r.left+r.width/2,clientY:r.top+r.height*.55}]});
      c.dispatchEvent(touch);
    """)
    driver.browsing_context.set_viewport(
        context=driver.current_window_handle,
        viewport={'width': 390, 'height': 844},
    )
    time.sleep(0.2)
    rotation = driver.execute_script("""
      const c=document.getElementById('game'),r=c.getBoundingClientRect();
      __game.bird.vy=100;
      const touch=new Event('touchstart',{bubbles:true,cancelable:true});
      Object.defineProperty(touch,'touches',{value:[{clientX:r.left+r.width/2,clientY:r.top+r.height*.55}]});
      c.dispatchEvent(touch);
      return {state:__game.machine.name,velocity:__game.bird.vy,canvas:[r.left,r.top,r.width,r.height],errors:__errors.slice()};
    """)

    driver.get(BASE + '/zombie-defense/')
    driver.browsing_context.set_viewport(
        context=driver.current_window_handle,
        viewport={'width': 390, 'height': 844},
    )
    time.sleep(0.4)
    zombie = driver.execute_script("""
      const notice=document.querySelector('.rotate-notice');
      const shell=document.getElementById('shell');
      return {
        noticeVisible:getComputedStyle(notice).display!=='none',
        shellVisible:shell.getClientRects().length>0,
        state:__game.state.current,
        errors:__errors.slice()
      };
    """)
finally:
    driver.quit()

failures = []
for item in results:
    width, height = item['requested']
    if item['viewport'] != [width, height]: failures.append(f'viewport_{width}')
    if item['noticeVisible']: failures.append(f'flappy_gate_{width}')
    if item['overlap']: failures.append(f'rail_overlap_{width}')
    if any(target['width'] < 40 or target['height'] < 44 for target in item['targets']): failures.append(f'toolbar_touch_targets_{width}')
    if item['canvas']['left'] < 0 or item['canvas']['right'] > width: failures.append(f'canvas_horizontal_{width}')
    if item['canvas']['top'] < item['rail']['bottom'] or item['canvas']['bottom'] > height: failures.append(f'canvas_vertical_{width}')
    if abs(item['canvas']['left'] - (width - item['canvas']['width']) / 2) > 1: failures.append(f'canvas_not_centered_{width}')
    if item['canvas']['top'] - item['rail']['bottom'] > 16: failures.append(f'canvas_toolbar_gap_{width}')
    if width == 390 and item['canvas']['width'] < 360: failures.append('canvas_too_narrow_390')
    if item['scale'] < 0.84: failures.append(f'scale_too_small_{width}')
    if item['effectiveSmallText'] < 8.4: failures.append(f'text_too_small_{width}')
    if item['documentWidth'] > width or item['documentHeight'] > height: failures.append(f'overflow_{width}')
    if [item['before'], item['after']] != ['MENU', 'PLAYING']: failures.append(f'portrait_pointer_blocked_{width}')
    if item['errors']: failures.append(f'runtime_{width}')
if zombie != {'noticeVisible': True, 'shellVisible': False, 'state': 'MENU', 'errors': []}:
    failures.append('zombie_portrait_gate_changed')
if (rotation['state'] != 'PLAYING' or rotation['velocity'] >= 0 or
        rotation['canvas'] != [8, 76, 374, 561] or rotation['errors']):
    failures.append('landscape_to_portrait_rotation')

assert not failures, json.dumps({'failures': failures, 'flappy': results, 'rotation': rotation, 'zombie': zombie}, indent=2)
print('FLAPPY MOBILE PORTRAIT PASS:', json.dumps({'flappy': results, 'rotation': rotation, 'zombie': zombie}, sort_keys=True))
