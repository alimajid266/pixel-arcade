from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8770/panic-button/"


def force_instruction(page, instruction, elapsed_ms=0):
    page.evaluate(
        """({instruction, elapsedMs}) => {
          const game = window.__game;
          clearTimeout(game.nextTimer);
          game.events.reset();
          game.state.running = true;
          game.state.instruction = instruction;
          game.state.input = [];
          game.state.locked = false;
          game.state.truth = true;
          game.instructionStartedAt = performance.now() - elapsedMs;
          game.deadline = performance.now() + instruction.duration * 1000 - elapsedMs;
        }""",
        {"instruction": instruction, "elapsedMs": elapsed_ms},
    )


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    console_errors = []
    requested_hosts = set()
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    page.on("request", lambda request: requested_hosts.add(request.url.split("/")[2]))

    response = page.goto(URL, wait_until="networkidle")
    assert response.status == 200
    assert page.title() == "PANIC BUTTON // CONTROL STATION 04"
    assert page.evaluate("window.__game.audio.ctx") is None
    assert page.locator(".button-module").count() == 4
    assert page.locator(".brand").get_attribute("href") == "/"
    assert page.locator("#guide-dialog").count() == 1
    assert page.locator(".guide-example").count() >= 7
    assert page.locator("#guide-button").count() == 1
    assert page.locator("#pressure-segments span").count() == 8
    assert page.locator("text=MASTER KEY").count() == 0
    assert page.locator("text=LOAD").count() == 0
    page.locator("#boot-guide").click()
    assert page.locator("#guide-dialog").evaluate("dialog => dialog.open") is True
    guide_text = page.locator("#guide-dialog").inner_text()
    assert "NO INPUT" in guide_text and "INTEGRITY" in guide_text and "CHANNEL" in guide_text
    for protocol in ("PROTOCOL 01 — CALIBRATION", "PROTOCOL 02 — COMPOUND", "PROTOCOL 03 — BREACH", "PROTOCOL 04 — BLACKOUT", "PROTOCOL 05 — COLLAPSE"):
        assert protocol in guide_text
    page.screenshot(path="/tmp/panic-button-guide.png")
    page.locator("#close-guide").click()
    assert page.locator("#guide-dialog").evaluate("dialog => dialog.open") is False
    protocol_label = page.evaluate("""() => {
      window.__game.state.phase = 4;
      window.__game.ui.update(window.__game.state, 0);
      return document.querySelector('#phase-label').textContent;
    }""")
    assert "BLACKOUT" in protocol_label
    page.wait_for_function("document.fonts.check('16px \\\"Press Start 2P\\\"') && document.fonts.check('16px VT323')")
    assert requested_hosts == {"127.0.0.1:8770"}, requested_hosts
    page.screenshot(path="/tmp/panic-button-menu.png", full_page=True)

    page.locator("#start").click()
    page.wait_for_timeout(900)
    assert page.locator("#system-status").inner_text() == "ACTIVE"
    assert page.evaluate("window.__game.audio.ctx !== null") is True

    # The in-game field manual pauses an active directive instead of causing a timeout.
    force_instruction(page, {"kind": "press", "expected": ["RED"], "duration": 0.15, "speaker": "COMPUTER"})
    page.locator("#guide-button").click()
    page.wait_for_timeout(280)
    assert page.evaluate("window.__game.state.locked") is False
    page.locator("#close-guide").click()

    # Opening the guide during the between-order delay pauses that delay too.
    intermission_round = page.evaluate("""() => {
      const game = window.__game;
      clearTimeout(game.nextTimer);
      game.state.locked = true;
      game.nextInstruction(180);
      return game.state.round;
    }""")
    page.locator("#guide-button").click()
    page.wait_for_timeout(260)
    assert page.evaluate("window.__game.state.round") == intermission_round
    page.locator("#close-guide").click()
    page.wait_for_timeout(70)
    assert page.evaluate("window.__game.state.round") == intermission_round
    page.wait_for_timeout(150)
    assert page.evaluate("window.__game.state.round") == intermission_round + 1

    # Verify cannot revive an order that has already reached its deadline.
    expired_verify = page.evaluate("""instruction => {
      const game = window.__game;
      clearTimeout(game.nextTimer);
      game.state.instruction = instruction;
      game.state.locked = false;
      game.verifierUsed = false;
      game.deadline = performance.now();
      const before = game.state.actualMistakes;
      game.verifyOrder();
      clearTimeout(game.nextTimer);
      return {before, after: game.state.actualMistakes, locked: game.state.locked, used: game.verifierUsed};
    }""", {"kind": "press", "expected": ["RED"], "duration": 5, "speaker": "COMPUTER"})
    assert expired_verify["after"] == expired_verify["before"] + 1
    assert expired_verify["locked"] is True and expired_verify["used"] is False

    mistakes = page.evaluate("window.__game.state.actualMistakes")
    press = {"kind": "press", "expected": ["RED"], "duration": 5, "speaker": "COMPUTER"}

    # Training teaches timeouts without damaging the player.
    training_result = page.evaluate("""instruction => {
      const game = window.__game;
      clearTimeout(game.nextTimer);
      game.state.instruction = instruction;
      game.state.locked = false;
      const before = [game.state.integrity, game.state.actualMistakes];
      game.resolve(false);
      clearTimeout(game.nextTimer);
      return {before, after: [game.state.integrity, game.state.actualMistakes]};
    }""", {**press, "training": True, "text": "PRESS RED", "color": "RED", "authorized": True})
    assert training_result["after"] == training_result["before"], training_result

    force_instruction(page, press)
    page.locator('[data-color="RED"] button').click()
    page.wait_for_timeout(80)
    assert page.evaluate("window.__game.state.locked") is True
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes

    force_instruction(page, {**press, "expected": ["BLUE"]})
    page.locator('[data-color="RED"] button').click()
    page.wait_for_timeout(80)
    mistakes += 1
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes

    # Mechanical success/failure feedback must always match actual integrity.
    force_instruction(page, press)
    feedback = page.evaluate("""() => {
      const game = window.__game;
      game.state.truth = false;
      game.resolve(false);
      clearTimeout(game.nextTimer);
      return {className: game.ui.subtext.className, message: game.ui.subtext.textContent};
    }""")
    mistakes += 1
    assert "bad" in feedback["className"] and "FAIL" in feedback["message"], feedback

    # Native keyboard activation must complete press directives without pointer events.
    force_instruction(page, press)
    page.locator('[data-color="RED"] button').focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(80)
    assert page.evaluate("window.__game.state.locked") is True

    force_instruction(page, {**press, "expected": ["BLUE"]})
    page.locator('[data-color="BLUE"] button').focus()
    page.keyboard.press("Space")
    page.wait_for_timeout(80)
    assert page.evaluate("window.__game.state.locked") is True

    # A gesture begun under an old directive must not be applied to a newer one.
    force_instruction(page, press)
    red = page.locator('[data-color="RED"] button')
    box = red.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.evaluate("""instruction => {
      const game = window.__game;
      game.__testCreate = game.instructions.create;
      game.__testMaybe = game.events.maybe;
      game.instructions.create = () => instruction;
      game.events.maybe = () => {};
      game.nextInstruction(0);
    }""", {**press, "text": "PRESS RED", "color": "RED"})
    page.wait_for_timeout(40)
    page.locator('[data-color="RED"] button').focus()
    page.keyboard.down("Enter")
    page.mouse.up()
    page.wait_for_timeout(80)
    assert page.evaluate("window.__game.state.locked") is False
    page.keyboard.up("Enter")
    page.wait_for_timeout(80)
    stale_locked = page.evaluate("""() => {
      const game = window.__game;
      game.instructions.create = game.__testCreate;
      game.events.maybe = game.__testMaybe;
      return game.state.locked;
    }""")
    assert stale_locked is True

    double = {"kind": "double", "expected": ["YELLOW", "YELLOW"], "duration": 5, "speaker": "COMPUTER"}
    force_instruction(page, double)
    page.locator('[data-color="YELLOW"] button').click()
    assert page.evaluate("[window.__game.state.locked, window.__game.state.input]") == [False, ["YELLOW"]]
    page.locator('[data-color="YELLOW"] button').click()
    assert page.evaluate("window.__game.state.locked") is True

    sequence = {"kind": "sequence", "expected": ["GREEN", "BLUE"], "duration": 5, "speaker": "SUPERVISOR"}
    force_instruction(page, sequence)
    page.locator('[data-color="GREEN"] button').click()
    assert page.evaluate("window.__game.state.locked") is False
    page.locator('[data-color="BLUE"] button').click()
    assert page.evaluate("window.__game.state.locked") is True

    hold = {"kind": "hold", "expected": ["GREEN"], "duration": 5, "speaker": "COMPUTER"}
    force_instruction(page, hold)
    green = page.locator('[data-color="GREEN"] button')
    box = green.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(700)
    page.mouse.up()
    assert page.evaluate("window.__game.state.locked") is True

    # Label restoration must not replace a control while it owns pointer capture.
    force_instruction(page, hold)
    page.evaluate("window.__game.events.trigger('labels', window.__game.state.instruction)")
    page.wait_for_timeout(1800)
    green = page.locator('[data-color="GREEN"] button')
    box = green.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(700)
    page.mouse.up()
    assert page.evaluate("window.__game.state.locked") is True

    delayed = {"kind": "delayed", "expected": ["BLUE"], "duration": 7, "unlockAt": 3, "speaker": "EMERGENCY"}
    force_instruction(page, delayed, 2500)
    page.locator('[data-color="BLUE"] button').click()
    mistakes += 1
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes
    force_instruction(page, delayed, 3050)
    page.locator('[data-color="BLUE"] button').click()
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes

    passive = {"kind": "wait", "expected": [], "duration": 0.15, "speaker": "UNKNOWN"}
    integrity_before_wait = page.evaluate("window.__game.state.integrity")
    force_instruction(page, passive)
    page.wait_for_timeout(280)
    assert page.evaluate("window.__game.state.locked") is True
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes
    assert page.evaluate("window.__game.state.integrity") >= integrity_before_wait

    avoid = {"kind": "avoid", "expected": [], "duration": 0.15, "speaker": "SUPERVISOR"}
    integrity_before_avoid = page.evaluate("window.__game.state.integrity")
    force_instruction(page, avoid)
    page.wait_for_timeout(280)
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes
    assert page.evaluate("window.__game.state.integrity") >= integrity_before_avoid

    forged_timeout = {**press, "duration": 0.15, "authorized": False}
    integrity_before_forged = page.evaluate("window.__game.state.integrity")
    force_instruction(page, forged_timeout)
    page.wait_for_timeout(280)
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes
    assert page.evaluate("window.__game.state.integrity") >= integrity_before_forged

    force_instruction(page, {**press, "duration": 0.15})
    page.wait_for_timeout(280)
    mistakes += 1
    assert page.evaluate("window.__game.state.actualMistakes") == mistakes

    # Completion exactly on the deadline is expired: orders must finish before it.
    exact_deadline = page.evaluate("""instruction => {
      const game = window.__game;
      clearTimeout(game.nextTimer);
      game.events.reset();
      game.state.running = true;
      game.state.instruction = instruction;
      game.state.input = [];
      game.state.locked = false;
      game.instructionStartedAt = performance.now();
      game.deadline = game.instructionStartedAt + 100;
      const before = game.state.actualMistakes;
      game.action({type: 'down', color: 'RED', gestureId: 'exact', time: game.deadline - 10});
      game.action({type: 'press', color: 'RED', gestureId: 'exact', duration: 10, time: game.deadline});
      clearTimeout(game.nextTimer);
      return {before, after: game.state.actualMistakes, locked: game.state.locked};
    }""", press)
    mistakes += 1
    assert exact_deadline == {"before": mistakes - 1, "after": mistakes, "locked": True}, exact_deadline

    # An input completed after the deadline must use the timeout outcome even
    # when it reaches the handler before the next animation frame.
    late_result = page.evaluate("""instruction => {
      const game = window.__game;
      clearTimeout(game.nextTimer);
      game.events.reset();
      game.state.running = true;
      game.state.instruction = instruction;
      game.state.input = [];
      game.state.locked = false;
      game.state.truth = true;
      game.instructionStartedAt = performance.now() - 5001;
      game.deadline = performance.now() - 1;
      const before = game.state.actualMistakes;
      game.action({type: 'down', color: 'RED', gestureId: 'late', time: performance.now()});
      game.action({type: 'press', color: 'RED', gestureId: 'late', duration: 20, time: performance.now()});
      return {before, after: game.state.actualMistakes, locked: game.state.locked};
    }""", press)
    mistakes += 1
    assert late_result == {"before": mistakes - 1, "after": mistakes, "locked": True}, late_result

    force_instruction(page, sequence)
    page.evaluate("window.__game.events.trigger('disabled', window.__game.state.instruction)")
    disabled = page.evaluate("[...document.querySelectorAll('.mechanical:disabled')].map(button => button.closest('.button-module').dataset.color)")
    assert len(disabled) == 1 and disabled[0] in ["RED", "YELLOW"], disabled

    # A safe disabled color from one order must be restored before the next order can require it.
    page.evaluate("""() => {
      const game = window.__game;
      clearTimeout(game.nextTimer);
      game.buttons.disable('BLUE', 1600);
      window.__originalInstructionCreate = game.instructions.create.bind(game.instructions);
      game.instructions.create = () => ({
        kind: 'press', text: 'PRESS BLUE', expected: ['BLUE'], duration: 5, speaker: 'COMPUTER',
        color: 'BLUE', authorized: true, authVisible: true, phase: 1,
        responseHint: 'YOUR INPUT: PRESS BLUE ONCE'
      });
      game.state.phase = 1;
      game.nextInstruction(0);
    }""")
    page.wait_for_timeout(80)
    assert page.locator('[data-color="BLUE"] button').is_disabled() is False
    page.evaluate("() => { window.__game.instructions.create = window.__originalInstructionCreate; return true; }")

    page.evaluate("window.__game.events.trigger('alarm', window.__game.state.instruction)")
    alarm_state = page.locator("#flash").evaluate("element => ({text: element.textContent, shown: element.classList.contains('show')})")
    assert alarm_state == {"text": "SYSTEM ALARM — PANEL LIGHTS UNRELIABLE", "shown": True}, alarm_state

    forged = {**press, "authorized": False, "authVisible": False, "responseHint": "YOUR INPUT: PRESS RED ONCE"}
    force_instruction(page, forged)
    page.evaluate("window.__game.verifierUsed = false")
    integrity_before = page.evaluate("window.__game.state.integrity")
    page.locator("#panic-button").click()
    assert page.evaluate("window.__game.state.integrity") == integrity_before
    assert page.locator("#signal").inner_text() == "AUTH: INVALID"
    assert "NO INPUT" in page.locator("#response-hint").inner_text()
    assert page.locator("#panic-status").inner_text() == "USED"
    assert page.evaluate("window.__game.authorizationRevealed") is True
    assert page.evaluate("window.__game.instructions.authorization(5, 'EMERGENCY')") is True

    triple_sequence = {"kind": "sequence", "expected": ["RED", "BLUE", "GREEN"], "duration": 4.5, "speaker": "EMERGENCY", "authorized": True}
    force_instruction(page, triple_sequence)
    penalty_result = page.evaluate("""() => {
      const game = window.__game;
      const before = game.state.integrity;
      game.resolve(false, 'timeout');
      clearTimeout(game.nextTimer);
      return {before, after: game.state.integrity, message: game.ui.subtext.textContent};
    }""")
    assert penalty_result["before"] - penalty_result["after"] == 12
    assert "-12" in penalty_result["message"]

    page.evaluate("""() => {
      const game=window.__game;
      clearTimeout(game.nextTimer);
      game.state.phase=4;
      game.effects.setPhase(4);
      game.narrator.say('UNKNOWN','SEQUENCE: RED / BLUE','SIGNAL SOURCE UNVERIFIED');
    }""")
    page.wait_for_timeout(1800)
    runtime_errors = page.evaluate("window.__game.debug().errors")
    assert runtime_errors == [], runtime_errors
    page.screenshot(path="/tmp/panic-button-gameplay.png", full_page=True)

    mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    mobile.goto(URL, wait_until="networkidle")
    mobile.locator("#start").click()
    mobile.wait_for_timeout(1000)
    metrics = mobile.evaluate("""() => ({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
      controls: [...document.querySelectorAll('.mechanical')].map(button => {
        const rect=button.getBoundingClientRect(); return [rect.width,rect.height];
      }),
      errors: window.__game.debug().errors,
      brand: document.querySelector('.brand').getBoundingClientRect().width
    })""")
    assert metrics["scrollWidth"] <= metrics["viewportWidth"]
    assert all(width >= 60 and height >= 60 for width, height in metrics["controls"])
    assert metrics["brand"] > 70
    assert metrics["errors"] == []
    mobile.screenshot(path="/tmp/panic-button-mobile.png", full_page=True)

    force_instruction(page, press)
    low_integrity_result = page.evaluate("""() => {
      const game = window.__game;
      game.state.integrity = 5;
      game.resolve(false, 'timeout');
      clearTimeout(game.nextTimer);
      return {integrity: game.state.integrity, message: game.ui.subtext.textContent};
    }""")
    assert low_integrity_result == {"integrity": 0, "message": "ORDER SKIPPED — ACTIVE ORDER FAILED — INTEGRITY -5"}, low_integrity_result

    assert console_errors == [], console_errors
    browser.close()
    print("PANIC BUTTON BROWSER PASS:", {
        "mechanics": ["press", "incorrect", "double", "sequence", "hold", "delayed", "wait", "timeout"],
        "fair_disabled": disabled,
        "actual_mistakes": mistakes,
        "mobile": metrics,
        "external_requests": sorted(requested_hosts),
    })
