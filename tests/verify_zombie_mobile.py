import json
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

BASE = 'http://127.0.0.1:8770/zombie-defense/'
options = Options()
options.add_argument('-headless')
options.binary_location = '/snap/firefox/current/usr/lib/firefox/firefox'
options.enable_bidi = True

driver = webdriver.Firefox(options=options, service=Service('/snap/bin/firefox.geckodriver'))
results = []
try:
    for width, height in ((667, 375), (844, 414), (932, 430)):
        driver.get(BASE)
        driver.browsing_context.set_viewport(
            context=driver.current_window_handle,
            viewport={'width': width, 'height': height},
        )
        time.sleep(0.45)
        result = driver.execute_script("""
          const canvas=document.getElementById('game');
          const shell=document.getElementById('shell');
          const rail=document.querySelector('.game-rail');
          const c=canvas.getBoundingClientRect(),s=shell.getBoundingClientRect(),r=rail.getBoundingClientRect();
          const future=document.querySelector('.game-tile.future');
          const visible=el=>getComputedStyle(el).display!=='none'&&el.getClientRects().length>0;
          const targets=[...rail.querySelectorAll('.rail-brand,.game-tile,.audio-toggle')].filter(visible).map(el=>{const b=el.getBoundingClientRect();return {label:el.textContent.trim(),width:b.width,height:b.height}});
          const captures=[];
          const original=__game.ctx.fillText;
          __game.ctx.fillText=function(text,x,y){captures.push({text:String(text),font:parseFloat((this.font.match(/[0-9.]+px/)||['0'])[0]),x,width:this.measureText(String(text)).width,align:this.textAlign});return original.apply(this,arguments)};
          __game.state.draw(__game.ctx);
          __game.ctx.fillText=original;
          const lookup=prefix=>{const hit=captures.find(item=>item.text.startsWith(prefix));return hit?hit.font*c.width/800:0};
          return {
            requested:[arguments[0],arguments[1]],viewport:[innerWidth,innerHeight],
            canvas:{left:c.left,top:c.top,width:c.width,height:c.height,right:c.right,bottom:c.bottom},
            shell:{left:s.left,top:s.top,width:s.width,height:s.height,right:s.right,bottom:s.bottom},
            rail:{left:r.left,top:r.top,width:r.width,height:r.height,right:r.right,bottom:r.bottom},
            scale:c.width/800,gap:s.left-r.right,
            futureVisible:getComputedStyle(future).display!=='none',
            targets,
            menuFonts:{description:lookup('MIX GUN'),mood:lookup(__game.maps[__game.mapIndex].mood),grid:lookup('20 x 12'),footer:lookup('SURVIVE 12')},
            document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight],errors:__errors.slice()
          };
        """, width, height)
        result['playingFonts'] = driver.execute_script("""
          __game.startGame();
          const c=document.getElementById('game').getBoundingClientRect(),captures=[];
          const original=__game.ctx.fillText;
          __game.ctx.fillText=function(text,x,y){captures.push({text:String(text),font:parseFloat((this.font.match(/[0-9.]+px/)||['0'])[0]),x,width:this.measureText(String(text)).width,align:this.textAlign});return original.apply(this,arguments)};
          __game.state.draw(__game.ctx);
          __game.ctx.fillText=original;
          const lookup=prefix=>{const hit=captures.find(item=>item.text.startsWith(prefix));return hit?hit.font*c.width/800:0};
          const hits=captures.find(item=>item.text.startsWith('HITS:'));
          return {money:lookup('$190'),wave:lookup('WAVE 0'),next:lookup('NEXT:'),rifle:lookup('1 RIFLE'),description:lookup('FAST / PRECISE'),start:lookup('START WAVE'),selectedFits:!!hits&&hits.x+hits.width<=610};
        """)
        result['instructionFonts'] = driver.execute_script("""
          __game.goMainMenu();__game.instructionsOpen=true;
          const c=document.getElementById('game').getBoundingClientRect(),captures=[];
          const original=__game.ctx.fillText;
          __game.ctx.fillText=function(text,x,y){captures.push({text:String(text),font:parseFloat((this.font.match(/[0-9.]+px/)||['0'])[0]),x,width:this.measureText(String(text)).width,align:this.textAlign});return original.apply(this,arguments)};
          __game.state.draw(__game.ctx);
          __game.ctx.fillText=original;
          const lookup=prefix=>{const hit=captures.find(item=>item.text.startsWith(prefix));return hit?hit.font*c.width/800:0};
          const detailLines=captures.filter(item=>item.text.includes('LIFE')||item.text.startsWith('REGEN')||item.text.startsWith('TOUGH')||item.text.startsWith('HEAVY'));
          return {heading:lookup('THE HORDE'),type:lookup('WALKER'),detail:lookup('BALANCED'),stats:lookup('HP 55'),button:lookup('CLOSE'),detailsFit:detailLines.every(item=>item.x+item.width<=730)};
        """)
        results.append(result)
    driver.get(BASE)
    driver.browsing_context.set_viewport(
        context=driver.current_window_handle,
        viewport={'width': 1280, 'height': 500},
    )
    time.sleep(.35)
    desktop_short = driver.execute_script("""
      __game.goMainMenu();__game.instructionsOpen=true;__game.instructionsPage=0;
      const copy=[],old=__game.ctx.fillText;
      __game.ctx.fillText=function(text,x,y){copy.push(String(text));return old.apply(this,arguments)};
      __game.state.draw(__game.ctx);__game.ctx.fillText=old;
      return {compact:mobileLandscape(),future:getComputedStyle(document.querySelector('.game-tile.future')).display,rail:getComputedStyle(document.querySelector('.game-rail')).position,full:copy.includes('TUNNELS, SURFACES 25–45% • 1 LIFE'),abbreviated:copy.includes('SURFACES 25–45% • 1 LIFE'),errors:__errors.slice()};
    """)
finally:
    driver.quit()

failures=[]
for item in results:
    width,height=item['requested']
    minimum_scale=0.55 if width==667 else 0.62
    if item['viewport'] != [width,height]: failures.append(f'viewport_{width}')
    if item['scale'] < minimum_scale: failures.append(f'game_too_small_{width}')
    if item['rail']['width'] > 70: failures.append(f'rail_too_wide_{width}')
    if item['gap'] < 0 or item['gap'] > 12: failures.append(f'wasted_rail_gap_{width}')
    cluster_left=item['rail']['left'];cluster_right=item['shell']['right']
    if abs(cluster_left-(width-cluster_right)) > 12: failures.append(f'cluster_not_centered_{width}')
    if item['canvas']['top'] > 6 or item['canvas']['bottom'] < height-6: failures.append(f'vertical_space_wasted_{width}')
    if item['futureVisible']: failures.append(f'future_tile_wastes_space_{width}')
    if any(target['width'] < 40 or target['height'] < 44 for target in item['targets']): failures.append(f'rail_touch_targets_{width}')
    if item['document'] != [width,height]: failures.append(f'overflow_{width}')
    if min(item['menuFonts'].values()) < 7.8: failures.append(f'menu_text_too_small_{width}')
    if min(value for key,value in item['playingFonts'].items() if key != 'selectedFits') < 7.8: failures.append(f'hud_text_too_small_{width}')
    if min(value for key,value in item['instructionFonts'].items() if key != 'detailsFit') < 7.8: failures.append(f'instruction_text_too_small_{width}')
    if not item['playingFonts']['selectedFits']: failures.append(f'selected_text_overflow_{width}')
    if not item['instructionFonts']['detailsFit']: failures.append(f'instruction_text_overflow_{width}')
    if item['errors']: failures.append(f'runtime_{width}')
assert not failures,json.dumps({'failures':failures,'results':results},indent=2)
assert desktop_short == {'compact':False,'future':'block','rail':'fixed','full':True,'abbreviated':False,'errors':[]},desktop_short
print('ZOMBIE MOBILE LANDSCAPE PASS:',json.dumps(results,sort_keys=True))
print('ZOMBIE SHORT DESKTOP PASS:',json.dumps(desktop_short,sort_keys=True))
