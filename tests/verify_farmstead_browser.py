from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/farmstead/"


def click_tile(page, index):
    point = page.evaluate(
        """index => {
          const canvas = document.getElementById('game');
          let tile = null;
          __game.scene.traverse(o => { if (o.userData && o.userData.tileIndex === index) tile = o; });
          if (!tile) throw new Error('tile mesh not found');
          const p = tile.position.clone();
          tile.getWorldPosition(p);
          p.project(__game.camera);
          const r = canvas.getBoundingClientRect();
          return {x:r.left+(p.x+1)*r.width/2,y:r.top+(-p.y+1)*r.height/2};
        }""",
        index,
    )
    page.mouse.click(point["x"], point["y"])


def covered_tile_centers(page):
    return page.evaluate("""() => {
      const canvas=document.getElementById('game'), rect=canvas.getBoundingClientRect(), covered=[];
      for (let index=0; index<30; index++) {
        let tile;
        __game.scene.traverse(node => { if (node.userData?.tileIndex === index) tile=node; });
        const point=tile.getWorldPosition(tile.position.clone()).project(__game.camera);
        const x=rect.left+(point.x+1)*rect.width/2, y=rect.top+(-point.y+1)*rect.height/2;
        if (document.elementFromPoint(x,y) !== canvas) covered.push(index);
      }
      return covered;
    }""")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    page.goto(URL)
    page.wait_for_function("__game.ready && __game.assets.farmer && __game.assets.farmhouse && __game.assets.scenery")
    assert page.evaluate("[document.title,__game.state,__game.farm.tiles.length,__errors.slice()]") == [
        "Harvest Hollow", "MENU", 30, []
    ]
    assert page.evaluate("[document.body.dataset.aesthetic,__game.aesthetic,__game.renderScale]") == [
        "voxel-farm", "voxel-farm", 1
    ]
    page.wait_for_function("document.fonts.check('16px \\\"Lilita One\\\"')")
    assert "Lilita One" in page.evaluate("getComputedStyle(document.body).fontFamily")
    assert page.evaluate("__game.assets.treeCount") >= 30
    assert page.evaluate("[__game.windmillBlades,__game.renderer.getContext().getContextAttributes().antialias]") == [4, True]
    weather_art = page.evaluate("""() => {
      const rain=__game.scene.getObjectByName('rain-visuals');
      const hat=__game.scene.getObjectByName('straw-hat');
      return {rainCount:rain?.count,rainVisible:rain?.visible,hatParent:hat?.parent?.name};
    }""")
    assert weather_art == {"rainCount": 96, "rainVisible": False, "hatParent": "head"}, weather_art
    voxel_contract = page.evaluate("""() => {
      const grass=__game.scene.getObjectByName('voxel-grass-grid');
      const path=__game.scene.getObjectByName('voxel-path-blocks');
      const pond=__game.scene.getObjectByName('voxel-pond');
      return {grass:grass?.children.reduce((n,m)=>n+m.count,0),grassLayers:grass?.children.length,
        path:path?.count,pond:pond?.count,
        grassInstanced:grass?.children.every(m=>m.isInstancedMesh),pathInstanced:path?.isInstancedMesh,pondInstanced:pond?.isInstancedMesh};
    }""")
    assert voxel_contract == {
        "grass": 1760, "grassLayers": 4, "path": 14, "pond": 16,
        "grassInstanced": True, "pathInstanced": True, "pondInstanced": True,
    }, voxel_contract
    rendering = page.evaluate("""() => ({
      cssWidth: document.getElementById('game').clientWidth,
      bufferWidth: document.getElementById('game').width,
      layout: __game.layout
    })""")
    assert rendering["bufferWidth"] == rendering["cssWidth"], rendering
    overlap = page.evaluate("""() => {
      const hit=(a,b)=>a.minX<b.maxX&&a.maxX>b.minX&&a.minZ<b.maxZ&&a.maxZ>b.minZ;
      return {
        buildingPath:Object.values(__game.layout.buildings).some(b=>__game.layout.paths.some(p=>hit(b,p))),
        fieldPath:__game.layout.paths.some(p=>hit(__game.layout.field,p)),
        houseField:hit(__game.layout.buildings.farmhouse,__game.layout.field)
      };
    }""")
    assert overlap == {"buildingPath": False, "fieldPath": False, "houseField": False}, (overlap, rendering)
    clearance = page.evaluate("""() => ({
      pathRoutes: __game.layout.paths.length,
      marketRemoved: !('market' in __game.layout.buildings),
      houseToField: __game.layout.field.minZ - __game.layout.buildings.farmhouse.maxZ,
      pathToField: __game.layout.field.minZ - Math.max(...__game.layout.paths.map(path => path.maxZ))
    })""")
    assert clearance["pathRoutes"] == 1, clearance
    assert clearance["marketRemoved"] is True, clearance
    assert clearance["houseToField"] >= 1.5, clearance
    assert clearance["pathToField"] >= 1.5, clearance

    page.locator("#guide-open").click()
    assert page.locator("#field-guide").is_visible()
    guide_text = page.locator("#field-guide").inner_text()
    assert "RAIN: AUTO-WATERS CROPS + NEW SEEDS" in page.locator("#quest-card").inner_text()
    for explanation in ["START WITH 6 TURNIP SEEDS", "START WITH 20 PLOTS", "BUY ANOTHER PLOT FOR 60 COINS", "TURNIP · 1 DAY · SELLS 18", "RAIN WATERS", "MATURE CROPS ROT", "up to 25"]:
        assert explanation in guide_text, guide_text
    page.locator("#guide-close").click()

    page.locator("#new-game").click()
    assert page.evaluate("__game.state") == "PLAYING"
    assert page.locator("#tutorial").is_visible()
    assert "PLOW" in page.locator("#tutorial").inner_text()
    assert page.locator("#tool-hoe").inner_text().startswith("PLOW")
    page.locator("#tutorial-skip").click()
    assert covered_tile_centers(page) == []
    plot_access = page.evaluate("""() => ({
      count: __game.farm.unlockedPlots,
      unlocked: [...Array(30).keys()].filter(index => __game.farm.isPlotUnlocked(index)),
      lockedVisuals: __game.tileGroups.map(group => group.userData.locked)
    })""")
    assert plot_access["count"] == 20, plot_access
    assert plot_access["unlocked"] == [1,2,3,4,7,8,9,10,13,14,15,16,19,20,21,22,25,26,27,28], plot_access
    assert [index for index, locked in enumerate(plot_access["lockedVisuals"]) if locked] == [0,5,6,11,12,17,18,23,24,29], plot_access
    page.evaluate("__game.actTile(0)")
    page.wait_for_timeout(100)
    assert page.evaluate("[__game.farm.energy,document.getElementById('message').textContent]") == [14,"Buy this plot first"]
    page.evaluate("__game.farm.coins=60; __game.refresh()")
    page.locator("#buy-plot").click()
    assert page.evaluate("[__game.farm.coins,__game.farm.unlockedPlots,__game.farm.isPlotUnlocked(0),__game.tileGroups[0].userData.locked]") == [0,21,True,False]
    assert "21/30" in page.locator("#buy-plot").inner_text()

    # The visible Harvest Board control must work through an actual pointer click.
    page.evaluate("__game.farm.produce.turnip=3; __game.refresh()")
    page.locator("#deliver-order").click(timeout=2000)
    assert page.evaluate("[__game.farm.orderIndex,__game.farm.earnings,__game.farm.produce.turnip]") == [1, 35, 0]
    page.evaluate("__game.farm.coins=80; __game.refresh()")
    page.locator("#buy-energy").click()
    assert page.evaluate("[__game.farm.coins,__game.farm.energy,__game.farm.maxEnergy]") == [0, 15, 15]
    page.evaluate("__game.farm.coins=80; __game.farm.maxEnergy=24; __game.farm.energy=24; __game.refresh()")
    page.locator("#buy-energy").click()
    assert page.evaluate("[__game.farm.coins,__game.farm.energy,__game.farm.maxEnergy,document.getElementById('buy-energy').disabled]") == [0,25,25,True]

    # A queued action from an abandoned run must never mutate a newly reset farm.
    page.evaluate("__game.actTile(28)")
    page.locator("#pause-toggle").click()
    page.locator("#pause .menu-return").click()
    page.locator("#new-game").click()
    page.wait_for_timeout(3000)
    assert page.evaluate("[__game.farm.energy,__game.farm.tiles[28].state,__game.selectedTool]") == [14, "grass", "hoe"]

    # Sleeping must cancel movement queued on the previous day.
    page.evaluate("__game.farm.coins=500; __game.farm.produce.turnip=3; __game.refresh(); __game.actTile(28); __game.endDay()")
    assert page.evaluate("[__game.transitioning,document.getElementById('night-transition').classList.contains('show')]") == [True, True]
    blocked_before = page.evaluate("[JSON.stringify(__game.farm.snapshot()),__game.selectedTool]")
    page.evaluate("""() => {
      for (const id of ['buy-turnip','buy-carrot','buy-pumpkin','buy-energy','buy-plot','sell-all','deliver-order','tool-water']) document.getElementById(id).click();
      dispatchEvent(new KeyboardEvent('keydown',{key:'2'}));
      __game.actTile(0);
    }""")
    blocked_after = page.evaluate("[JSON.stringify(__game.farm.snapshot()),__game.selectedTool]")
    assert blocked_after == blocked_before, (blocked_before, blocked_after)
    page.wait_for_timeout(3000)
    assert page.evaluate("[__game.transitioning,document.getElementById('night-transition').classList.contains('show')]") == [False, False]
    assert page.evaluate("[__game.farm.day,__game.farm.energy,__game.farm.tiles[28].state]") == [2, 14, "grass"]
    page.locator("#pause-toggle").click()
    page.locator("#pause .menu-return").click()
    page.locator("#new-game").click()
    page.locator("#tutorial-skip").click()

    # A queued action keeps the tool selected when the plot was clicked.
    page.evaluate("__game.selectTool('hoe'); __game.actTile(27); __game.selectTool('water')")
    page.wait_for_function("__game.farm.tiles[27].state === 'tilled'", timeout=5000)
    queued_result = page.evaluate("[__game.farm.tiles[27].state,__game.farm.energy]")
    assert queued_result == ["tilled", 13], queued_result
    page.locator("#pause-toggle").click()
    page.locator("#pause .menu-return").click()
    page.locator("#new-game").click()
    page.locator("#tutorial-skip").click()

    # Planting through ordinary controls on a rainy day must auto-water the seed.
    page.evaluate("__game.farm.day=3; __game.refresh()")
    assert page.evaluate("__game.scene.getObjectByName('rain-visuals').visible") is True
    click_tile(page, 26)
    page.wait_for_function("__game.farm.tiles[26].state === 'tilled'")
    page.locator("#tool-turnip").click()
    click_tile(page, 26)
    page.wait_for_function("__game.farm.tiles[26].crop === 'turnip'")
    assert page.evaluate("__game.farm.tiles[26].watered") is True
    page.locator("#pause-toggle").click()
    page.locator("#pause .menu-return").click()
    page.locator("#new-game").click()
    page.locator("#tutorial-skip").click()

    # Rot must be prominent and Harvest must show ready crops, not a static keyboard shortcut.
    page.evaluate("""() => { Object.assign(__game.farm.tiles[0], {state:'planted',crop:'turnip',growth:1,watered:false,ready:true,readyDays:1,dryDays:0}); __game.refresh(); }""")
    assert page.locator("#ready-count").inner_text() == "1"
    page.evaluate("__game.endDay()")
    assert "1 CROP ROTTED" in page.locator("#night-transition").inner_text()
    assert page.locator("#ready-count").inner_text() == "0"
    page.wait_for_function("!__game.transitioning")
    page.locator("#pause-toggle").click()
    page.locator("#pause .menu-return").click()
    page.locator("#new-game").click()
    page.locator("#tutorial-skip").click()

    page.wait_for_timeout(200)
    assert page.evaluate("__game.renderer.info.render.calls") < 80
    animation_before = page.evaluate("""() => {
      const farmer=__game.scene.getObjectByName('farmer-avatar');
      const leg=__game.scene.getObjectByName('leg-left');
      return {x:farmer.position.x,z:farmer.position.z,q:leg.quaternion.toArray()};
    }""")
    click_tile(page, 1)
    page.wait_for_timeout(180)
    animation_after = page.evaluate("""() => {
      const farmer=__game.scene.getObjectByName('farmer-avatar');
      const leg=__game.scene.getObjectByName('leg-left');
      return {x:farmer.position.x,z:farmer.position.z,q:leg.quaternion.toArray()};
    }""")
    assert (animation_after["x"], animation_after["z"]) != (animation_before["x"], animation_before["z"])
    assert animation_after["q"] != animation_before["q"], (animation_before, animation_after)
    page.wait_for_function("__game.farm.tiles[1].state === 'tilled'")
    hat_samples = []
    for _ in range(6):
        hat_samples.append(page.evaluate("""() => { const root=__game.scene.getObjectByName('farmer-avatar'),hat=__game.scene.getObjectByName('straw-hat'),point=hat.getWorldPosition(hat.position.clone()); return root.worldToLocal(point).toArray(); }"""))
        page.wait_for_timeout(60)
    assert len({tuple(round(value, 3) for value in sample) for sample in hat_samples}) > 1, hat_samples
    assert page.evaluate("__game.farm.energy") == 13

    page.locator("#tool-turnip").click()
    click_tile(page, 1)
    page.wait_for_function("__game.farm.tiles[1].crop === 'turnip'")
    page.locator("#tool-water").click()
    click_tile(page, 1)
    page.wait_for_function("__game.farm.tiles[1].watered === true")
    page.locator("#end-day").click()
    assert page.evaluate("[__game.farm.day,__game.farm.tiles[1].ready]") == [2, True]
    page.wait_for_function("!__game.transitioning")

    page.locator("#tool-harvest").click()
    click_tile(page, 1)
    page.wait_for_function("__game.farm.produce.turnip === 1")
    page.locator("#sell-all").click()
    assert page.evaluate("[__game.farm.coins,__game.farm.earnings,__game.farm.produce.turnip]") == [78, 18, 0]

    page.locator("#pause-toggle").click()
    assert page.evaluate("__game.state") == "PAUSED"
    page.locator("#resume").click()
    assert page.evaluate("__game.state") == "PLAYING"
    page.evaluate("""() => {
      const samples = [
        {state:'planted',crop:'turnip',growth:1,watered:false,ready:true},
        {state:'planted',crop:'carrot',growth:1,watered:true,ready:false},
        {state:'planted',crop:'pumpkin',growth:2,watered:false,ready:false}
      ];
      samples.forEach((sample, i) => Object.assign(__game.farm.tiles[i], sample));
      __game.refresh();
    }""")
    page.wait_for_timeout(200)
    assert page.evaluate("__game.renderer.info.render.calls") < 80
    page.screenshot(path="/tmp/harvest-hollow-desktop.png")

    page.reload()
    page.wait_for_function("__game.ready && __game.assets.farmer && __game.assets.farmhouse && __game.assets.scenery")
    assert page.evaluate("[__game.farm.day,__game.farm.coins,__game.farm.earnings,__errors.slice()]") == [2, 78, 18, []]

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(URL)
    page.wait_for_function("__game.ready && __game.assets.farmer && __game.assets.farmhouse && __game.assets.scenery")
    page.locator("#start").click()
    assert page.evaluate("__game.state") == "PLAYING"
    assert covered_tile_centers(page) == []
    click_tile(page, 14)
    page.wait_for_function("__game.farm.tiles[14].state === 'tilled'", timeout=5000)
    page.locator("#guide-open").click()
    assert page.locator("#field-guide").is_visible()
    page.locator("#guide-close").click()
    assert page.evaluate("__game.state") == "PLAYING"
    mobile = page.evaluate("""() => {
      const ids=['tool-hoe','tool-water','tool-turnip','tool-carrot','tool-pumpkin','tool-harvest','buy-turnip','buy-carrot','buy-pumpkin','buy-energy','buy-plot','sell-all','end-day'];
      const boxes=ids.map(id => {const b=document.getElementById(id).getBoundingClientRect();return [id,b.left,b.right,b.width,b.height];});
      return {width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,boxes,errors:__errors.slice()};
    }""")
    assert mobile["scrollWidth"] <= mobile["width"], mobile
    for _, left, right, width, height in mobile["boxes"]:
        assert left >= 0 and right <= mobile["width"] and width >= 44 and height >= 44, mobile
    assert mobile["errors"] == [], mobile
    page.screenshot(path="/tmp/harvest-hollow-mobile.png")

    page.goto("http://127.0.0.1:8770/")
    launcher = page.evaluate("""() => ({
      errors: __errors.slice(),
      cards: [...document.querySelectorAll('.game-card')].map(card => {
        const b=card.getBoundingClientRect();return [card.id,b.left,b.right,b.width,b.height];
      })
    })""")
    assert launcher["errors"] == [] and len(launcher["cards"]) == 4, launcher
    for _, left, right, width, height in launcher["cards"]:
        assert left >= 0 and right <= 390 and width >= 300 and height >= 200, launcher
    page.screenshot(path="/tmp/pixel-arcade-home-390-full.png", full_page=True)
    page.locator("#play-farmstead").click()
    page.wait_for_function("document.title === 'Harvest Hollow' && __game.ready")
    print("FARMSTEAD BROWSER PASS", mobile)
    browser.close()
