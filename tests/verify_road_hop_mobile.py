from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time

URL="http://127.0.0.1:8770/road-hop/"
options=Options();options.add_argument('-headless');options.binary_location='/snap/firefox/current/usr/lib/firefox/firefox';options.enable_bidi=True
d=webdriver.Firefox(options=options,service=Service('/snap/bin/firefox.geckodriver'))
try:
    d.get(URL)
    d.browsing_context.set_viewport(context=d.current_window_handle,viewport={'width':390,'height':844})
    for _ in range(30):
        if d.execute_script("return __game&&__game.ready"):break
        time.sleep(.1)
    mobile=d.execute_script("""
      const c=document.getElementById('game'),r=c.getBoundingClientRect();
      return [innerWidth,innerHeight,document.documentElement.scrollWidth,r.width,r.height,c.width,c.height,__errors.slice()];
    """)
    assert mobile[2] <= mobile[0] and mobile[3:5] == mobile[0:2], mobile
    assert mobile[5] >= mobile[3] and mobile[6] >= mobile[4] and mobile[7] == [], mobile

    haunted_mobile = d.execute_script("""
      __game.setBiome('haunted');__game.start();
      const props=[];__game.world.traverse(o=>{
        if(['haunted-jack-o-lantern','haunted-path-lantern','haunted-candle-cluster','haunted-bat'].includes(o.name)){
          const p=o.getWorldPosition(o.position.clone());props.push([o.name,p.x,p.z]);
        }
      });
      const blocked=[...new Set(__game.lanes.flatMap(l=>[...l.blockers]))];
      return [props,blocked,__game.renderer.getPixelRatio(),getComputedStyle(document.body).fontFamily];
    """)
    assert {p[0] for p in haunted_mobile[0]} == {
        'haunted-jack-o-lantern','haunted-path-lantern','haunted-candle-cluster','haunted-bat'
    }, haunted_mobile
    assert any(abs(p[1]) <= 4 for p in haunted_mobile[0]), haunted_mobile
    assert 3 in haunted_mobile[1] or -3 in haunted_mobile[1], haunted_mobile
    assert haunted_mobile[2] <= 1.5 and 'Road Hop Arcade' in haunted_mobile[3], haunted_mobile

    prop_footprints=d.execute_script("""
      const failures=[];let checked=0;
      for(const lane of __game.lanes.filter(l=>l.type==='grass'&&l.group.getObjectByName('haunted-grave-cluster'))){
        const cluster=lane.group.getObjectByName('haunted-grave-cluster');let min=Infinity,max=-Infinity;
        cluster.updateWorldMatrix(true,true);cluster.traverse(mesh=>{if(!mesh.geometry)return;mesh.geometry.computeBoundingBox();const box=mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);min=Math.min(min,box.min.x);max=Math.max(max,box.max.x)});
        for(let cell=Math.ceil(min);cell<=Math.floor(max);cell++){checked++;if(!lane.blockers.has(cell))failures.push([lane.row,cell,min,max,[...lane.blockers]])}
      }
      return {checked,failures};
    """)
    assert prop_footprints['checked'] >= 2, prop_footprints
    assert prop_footprints['failures'] == [], prop_footprints

    cancelled=d.execute_script("""
      __game.start();const c=document.getElementById('game');
      c.dispatchEvent(new PointerEvent('pointerdown',{pointerId:7,clientX:190,clientY:500,bubbles:true}));
      c.dispatchEvent(new PointerEvent('pointercancel',{pointerId:7,bubbles:true}));
      c.dispatchEvent(new PointerEvent('pointerup',{pointerId:7,clientX:190,clientY:390,bubbles:true}));
      __game.debug.advance(.25);
      return [__game.player.row,__game.score];
    """)
    assert cancelled == [0,0], cancelled

    pointer_identity=d.execute_script("""
      __game.start();const c=document.getElementById('game');
      c.dispatchEvent(new PointerEvent('pointerdown',{pointerId:9,clientX:190,clientY:500,bubbles:true}));
      c.dispatchEvent(new PointerEvent('pointerup',{pointerId:10,clientX:190,clientY:390,bubbles:true}));
      c.dispatchEvent(new PointerEvent('pointercancel',{pointerId:10,bubbles:true}));
      c.dispatchEvent(new PointerEvent('pointerup',{pointerId:9,clientX:190,clientY:390,bubbles:true}));
      __game.debug.advance(.25);
      return [__game.player.row,__game.score];
    """)
    assert pointer_identity == [1,1], pointer_identity

    swipe=d.execute_script("""
      __game.start();const c=document.getElementById('game');
      c.dispatchEvent(new PointerEvent('pointerdown',{clientX:190,clientY:500,bubbles:true}));
      c.dispatchEvent(new PointerEvent('pointerup',{clientX:190,clientY:390,bubbles:true}));
      __game.debug.advance(.25);
      return [__game.player.row,__game.score];
    """)
    assert swipe == [1,1], swipe

    pause_button=d.find_element('id','pause-toggle')
    pause_rect=pause_button.rect
    assert pause_rect['width'] >= 44 and pause_rect['height'] >= 44, pause_rect
    pause_button.click()
    pause=d.execute_script("""
      const panel=document.getElementById('pause');
      return [__game.state,!!panel,panel&&panel.classList.contains('hidden')];
    """)
    assert pause == ['PAUSED',True,False], pause
    d.save_screenshot('/tmp/road-hop-mobile-paused.png')
    d.find_element('id','resume').click()
    assert d.execute_script("return __game.state") == 'PLAYING'

    d.execute_script("__game.debug.forceCrash();__game.debug.advance(.02)")
    d.refresh()
    for _ in range(30):
        if d.execute_script("return __game&&__game.ready"):break
        time.sleep(.1)
    persisted=d.execute_script("return [__game.best,document.getElementById('best').textContent,__errors.slice()]")
    assert persisted == [1,'1',[]], persisted
    print('ROAD HOP MOBILE PASS',mobile,cancelled,pointer_identity,swipe,pause_rect,pause,persisted)
finally:d.quit()
