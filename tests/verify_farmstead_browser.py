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


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    page.goto(URL)
    page.wait_for_function("__game.ready && __game.assets.farmer && __game.assets.farm")
    assert page.evaluate("[document.title,__game.state,__game.farm.tiles.length,__errors.slice()]") == [
        "Harvest Hollow", "MENU", 30, []
    ]

    page.locator("#new-game").click()
    assert page.evaluate("__game.state") == "PLAYING"

    # A queued action from an abandoned run must never mutate a newly reset farm.
    page.evaluate("__game.actTile(29)")
    page.locator("#pause-toggle").click()
    page.locator("#pause .menu-return").click()
    page.locator("#new-game").click()
    page.wait_for_timeout(3000)
    assert page.evaluate("[__game.farm.energy,__game.farm.tiles[29].state,__game.selectedTool]") == [14, "grass", "hoe"]

    page.wait_for_timeout(200)
    assert page.evaluate("__game.renderer.info.render.calls") < 80
    click_tile(page, 0)
    page.wait_for_function("__game.farm.tiles[0].state === 'tilled'")
    assert page.evaluate("__game.farm.energy") == 13

    page.locator("#tool-turnip").click()
    click_tile(page, 0)
    page.wait_for_function("__game.farm.tiles[0].crop === 'turnip'")
    page.locator("#tool-water").click()
    click_tile(page, 0)
    page.wait_for_function("__game.farm.tiles[0].watered === true")
    page.locator("#end-day").click()
    assert page.evaluate("[__game.farm.day,__game.farm.tiles[0].ready]") == [2, True]

    page.locator("#tool-harvest").click()
    click_tile(page, 0)
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
    page.screenshot(path="/tmp/harvest-hollow-desktop.png")

    page.reload()
    page.wait_for_function("__game.ready && __game.assets.farmer && __game.assets.farm")
    assert page.evaluate("[__game.farm.day,__game.farm.coins,__game.farm.earnings,__errors.slice()]") == [2, 78, 18, []]

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(URL)
    page.wait_for_function("__game.ready && __game.assets.farmer && __game.assets.farm")
    page.locator("#start").click()
    assert page.evaluate("__game.state") == "PLAYING"
    mobile = page.evaluate("""() => {
      const ids=['tool-hoe','tool-water','tool-turnip','tool-carrot','tool-pumpkin','tool-harvest'];
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
