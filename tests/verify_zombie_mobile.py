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
          const lookup=prefix=>{const hit=captures.find(item=>item.text.startsWith(prefix));return hit?hit.font*c.height/650:0};
          return {
            requested:[arguments[0],arguments[1]],viewport:[innerWidth,innerHeight],
            canvas:{left:c.left,top:c.top,width:c.width,height:c.height,right:c.right,bottom:c.bottom},
            shell:{left:s.left,top:s.top,width:s.width,height:s.height,right:s.right,bottom:s.bottom},
            rail:{left:r.left,top:r.top,width:r.width,height:r.height,right:r.right,bottom:r.bottom},
            scale:c.height/650,widthScale:c.width/800,gap:s.left-r.right,
            railVisible:visible(rail),
            futureVisible:visible(future),
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
          const lookup=prefix=>{const hit=captures.find(item=>item.text.startsWith(prefix));return hit?hit.font*c.height/650:0};
          const hits=captures.find(item=>item.text.startsWith('HIT'));
          return {money:lookup('$190'),wave:lookup('WAVE 0'),next:lookup('NEXT:'),rifle:lookup('1 RIFLE'),description:lookup('FAST / PRECISE'),start:lookup('START WAVE'),selectedFits:!!hits&&hits.x+hits.width<=610};
        """)
        result['instructionFonts'] = driver.execute_script("""
          __game.goMainMenu();__game.instructionsOpen=true;
          const c=document.getElementById('game').getBoundingClientRect(),captures=[];
          const original=__game.ctx.fillText;
          __game.ctx.fillText=function(text,x,y){captures.push({text:String(text),font:parseFloat((this.font.match(/[0-9.]+px/)||['0'])[0]),x,width:this.measureText(String(text)).width,align:this.textAlign});return original.apply(this,arguments)};
          __game.state.draw(__game.ctx);
          __game.ctx.fillText=original;
          const lookup=prefix=>{const hit=captures.find(item=>item.text.startsWith(prefix));return hit?hit.font*c.height/650:0};
          const detailLines=captures.filter(item=>item.text.includes('LIFE')||item.text.startsWith('REGEN')||item.text.startsWith('TOUGH')||item.text.startsWith('HEAVY'));
          return {heading:lookup('THE HORDE'),type:lookup('WALKER'),detail:lookup('BALANCED'),stats:lookup('HP 55'),button:lookup('CLOSE'),detailsFit:detailLines.every(item=>item.x+item.width<=730)};
        """)
        result['instructionPages'] = driver.execute_script("""
          const inspect=page=>{
            __game.instructionsOpen=true;__game.instructionsPage=page;
            const captures=[],ctx=__game.ctx,original=ctx.fillText;
            ctx.fillText=function(text,x,y){
              const width=this.measureText(String(text)).width,align=this.textAlign;
              captures.push({text:String(text),x,y,width,align});
              return original.apply(this,arguments);
            };
            __game.state.draw(ctx);ctx.fillText=original;
            const bounds=item=>item.align==='center'?[item.x-item.width/2,item.x+item.width/2]:item.align==='right'?[item.x-item.width,item.x]:[item.x,item.x+item.width];
            const overflow=captures.filter(item=>item.text!=='♪'&&(()=>{const [left,right]=bounds(item);return left<70||right>730;})()).map(item=>item.text);
            return {overflow,contradiction:captures.some(item=>item.text.includes('Any leak on Wave 12 means defeat'))};
          };
          return {weapons:inspect(1),rules:inspect(2)};
        """)
        result['mappedInput'] = driver.execute_script("""
          __game.instructionsOpen=false;__game.startGame();__game.selected=0;
          const canvas=document.getElementById('game'),c=canvas.getBoundingClientRect();
          const tap=(x,y)=>canvas.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,clientX:c.left+x/800*c.width,clientY:c.top+y/650*c.height,pointerId:1,pointerType:'touch',isPrimary:true}));
          tap(67,590);const deselected=__game.selected===-1;
          tap(67,590);const reselected=__game.selected===0;
          return {deselected,reselected,state:__game.state.current,errors:__errors.slice()};
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
    if item['railVisible']: failures.append(f'rail_wastes_game_space_{width}')
    if item['canvas']['left'] > 5 or item['canvas']['right'] < width-5: failures.append(f'horizontal_space_wasted_{width}')
    if item['canvas']['top'] > 5 or item['canvas']['bottom'] < height-5: failures.append(f'vertical_space_wasted_{width}')
    if item['futureVisible']: failures.append(f'future_tile_wastes_space_{width}')
    if item['document'] != [width,height]: failures.append(f'overflow_{width}')
    if min(item['menuFonts'].values()) < 9.0: failures.append(f'menu_text_too_small_{width}')
    if min(value for key,value in item['playingFonts'].items() if key != 'selectedFits') < 9.0: failures.append(f'hud_text_too_small_{width}')
    if min(value for key,value in item['instructionFonts'].items() if key != 'detailsFit') < 9.0: failures.append(f'instruction_text_too_small_{width}')
    if not item['playingFonts']['selectedFits']: failures.append(f'selected_text_overflow_{width}')
    if not item['instructionFonts']['detailsFit']: failures.append(f'instruction_text_overflow_{width}')
    if item['instructionPages']['weapons']['overflow']: failures.append(f'weapon_instructions_overflow_{width}')
    if item['instructionPages']['rules']['overflow']: failures.append(f'rules_instructions_overflow_{width}')
    if item['instructionPages']['rules']['contradiction']: failures.append(f'stale_wave_12_defeat_copy_{width}')
    if item['mappedInput'] != {'deselected':True,'reselected':True,'state':'PLAYING','errors':[]}: failures.append(f'mapped_input_{width}')
    if item['errors']: failures.append(f'runtime_{width}')
assert not failures,json.dumps({'failures':failures,'results':results},indent=2)
assert desktop_short == {'compact':False,'future':'block','rail':'fixed','full':True,'abbreviated':False,'errors':[]},desktop_short
print('ZOMBIE MOBILE LANDSCAPE PASS:',json.dumps(results,sort_keys=True))
print('ZOMBIE SHORT DESKTOP PASS:',json.dumps(desktop_short,sort_keys=True))
