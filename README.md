# Pixel Arcade

[![Production](https://img.shields.io/badge/production-live-8bc34a)](https://pixel-arcade-pied.vercel.app)
[![Architecture](https://img.shields.io/badge/architecture-static%20HTML5%20Canvas-6c3fc5)](#technical-architecture)

**Pixel Arcade** is a small browser arcade that puts two complete games behind one launcher and one public URL:

- **Flappy Canvas** — a reflex-based endless flying game.
- **Zombie Defense: Last Outpost** — a 12-wave tactical tower-defense campaign.

Play it at **https://pixel-arcade-pied.vercel.app**.

## Contents

- [Non-technical overview](#non-technical-overview)
- [Project and game scope](#project-and-game-scope)
- [How to play](#how-to-play)
- [Technical architecture](#technical-architecture)
- [Flappy Canvas specification](#flappy-canvas-specification)
- [Zombie Defense specification](#zombie-defense-specification)
- [Zombie Defense difficulty model](#zombie-defense-difficulty-model)
- [Design decisions](#design-decisions)
- [Repository structure](#repository-structure)
- [Local development](#local-development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Known boundaries and future work](#known-boundaries-and-future-work)

---

## Non-technical overview

### Pixel Arcade

Pixel Arcade is the shared front door for the games. A player opens one website, chooses a game, and can switch between games through the launcher or the in-game arcade rail. The visual style is intentionally colorful, pixel-inspired, and self-contained.

No account is required. The games run directly in the browser and store preferences and scores on that browser only.

### Flappy Canvas

Flappy Canvas is an endless score-chasing game. The player taps or presses Space to keep a bird in the air while flying through pipe gaps. Passing a pipe adds one point. The game gradually becomes faster and the gaps become narrower.

It includes:

- keyboard, mouse, and touch controls;
- three visual biomes: City, Sunset, and Night;
- clear or rainy weather;
- pause and three-second resume countdown;
- local high score and local top-player board;
- an optional translucent replay ghost of the previous run;
- independent music and sound-effect controls.

### Zombie Defense: Last Outpost

Zombie Defense is a compact strategy game. The player spends limited money to place defenses around a road and must survive 12 increasingly difficult waves. Different weapons can attack different zombie classes, so one tower type cannot solve the whole campaign.

It includes:

- three maps with different routes and build spaces;
- four defenses with different costs, ranges, fire rates, footprints, and valid targets;
- seven enemy archetypes, including regenerating, burrowing, armored, fast, and boss enemies;
- tower selection, Level 2 upgrades, and selling;
- overlapping waves when the player chooses to start early;
- wave rewards, escape penalties, lives, victory, and defeat;
- pause, instructions, map previews, and independent audio controls.

---

## Project and game scope

### Pixel Arcade scope

**In scope**

- One static launcher at `/`.
- Two playable games at `/flappy/` and `/zombie-defense/`.
- Same-origin navigation and a shared in-game arcade rail.
- Responsive desktop and landscape-mobile presentation.
- A portrait orientation gate at widths up to 736 px where the fixed-resolution game UI would be too small to use safely.
- Local browser persistence for preferences and records.
- Static deployment through one GitHub repository and one Vercel project.

**Out of scope**

- User accounts, authentication, cloud saves, and cross-device synchronization.
- A server-authoritative leaderboard.
- Multiplayer, matchmaking, social features, or payments.
- A runtime API, database, WebSocket connection, or server-side simulation.
- A downloadable native mobile or desktop application.
- A general-purpose game engine or plugin system.

### Flappy Canvas scope

**In scope**

- One endless mode with progressively faster pipes and smaller gaps.
- Local score, best score, leaderboard (up to five stored and the top three displayed), and previous-run ghost.
- Three cosmetic biomes and two weather modes.
- Menu, Playing, Paused, Countdown, and Game Over states.
- Space, keyboard shortcuts, pointer, and touch input.

**Out of scope**

- Levels, campaign progression, power-ups, enemies, or alternative birds.
- Online/global leaderboard validation.
- Deterministic seeded runs or competitive anti-cheat.
- Physics customization or selectable difficulty modes.

### Zombie Defense scope

**In scope**

- A fixed 12-wave campaign ending with the Grave Titan.
- Three selectable maps.
- Four tower types, each with Level 1 and Level 2 only.
- Horizontal `2×1` footprints for Bomber and Sniper; no rotation.
- Selling at a partial refund.
- Hard weapon/enemy compatibility rules.
- Early start of the next wave after the current wave finishes deploying.
- Per-wave accounting for overlapping waves.
- One starting difficulty curve shared by all maps.

**Out of scope**

- Endless mode, procedural waves, multiple difficulty presets, or meta-progression.
- Tower rotation, branching upgrade trees, active abilities, or tower status effects.
- Map-specific enemy statistics or map-specific economy.
- Save/resume of an active campaign.
- Backend analytics or telemetry-based automatic balancing.

---

## How to play

### Shared arcade controls

- Use the left arcade rail to switch games or return to Pixel Arcade.
- The `↗` control opens a game in a new tab.
- Music and sound effects can be enabled independently.
- On narrow portrait screens, rotate the device to landscape.

### Flappy Canvas controls

| Action | Input |
|---|---|
| Start / flap / retry | Space, click, or tap |
| Pause / resume | `P`, `Escape`, or the pause control |
| Return to menu | Enter from Game Over, or the menu control in Pause/Game Over |
| Change biome | Left/Right arrows on the menu |
| Change weather | `W` on the menu |
| Toggle previous-run ghost | Ghost row on the menu |
| Toggle all audio | `M` or the Canvas mute control |
| Edit player name | Letter/number keys on the menu; Backspace deletes |

### Zombie Defense controls

| Action | Input |
|---|---|
| Choose a weapon | Shop card or number keys `1`–`4` |
| Leave build mode | Click the selected weapon again |
| Place tower | Click a legal battlefield cell |
| Select tower | Click an existing tower |
| Upgrade or sell | Use the selected-tower HUD controls |
| Start next wave | Click the wave control once the queue is ready |
| Pause / resume | `Escape` or the pause control |
| Change map | Left/Right arrows or the map selector while in Menu |
| Read instructions | Instructions control in Menu or Pause |

The next-wave control becomes available after the current wave's **last queued zombie has entered the map**. Existing zombies do not need to be dead, so starting early creates overlapping pressure.

Zombie Defense uses a `1.5s` resume countdown. Flappy Canvas uses a three-second `3 → 2 → 1` resume countdown.

---

## Technical architecture

### Runtime model

Pixel Arcade is a static web application:

```text
Browser
├── /                       → index.html
├── /flappy/                → flappy/index.html
└── /zombie-defense/        → zombie-defense/index.html
```

After the HTML files are delivered, gameplay runs entirely in the browser:

- no framework;
- no package bundle;
- no runtime backend;
- no API or database;
- no externally hosted game assets;
- no server-side game state.

Each game is a self-contained HTML file containing its markup, CSS, Canvas renderer, state machine, input handling, procedural graphics, procedural Web Audio, and persistence wrapper.

### Main implementation patterns

- **Animation:** `requestAnimationFrame` with delta time capped at `0.1s` to limit large tab-switch jumps.
- **Rendering:** HTML5 Canvas with fixed logical coordinates and responsive CSS display sizing.
- **Input mapping:** pointer coordinates are converted from the displayed Canvas rectangle into logical game coordinates.
- **State management:** explicit Menu/Playing/Pause/End states prevent gameplay from advancing behind overlays.
- **Persistence:** guarded `localStorage` access; failures fall back safely rather than breaking the game.
- **Audio:** Web Audio contexts are created/unlocked only after a user gesture.
- **Navigation:** same-origin route paths avoid coupling games to separate hosts or ports.
- **Diagnostics:** `window.__errors`, `window.__game`, and selected internals support deterministic browser regression tests.

### Responsive model

The games preserve fixed logical worlds while scaling their displayed Canvas:

| Game | Logical size |
|---|---:|
| Flappy Canvas | `400 × 600` |
| Zombie Defense | `800 × 650` |

Zombie Defense uses a `20 × 12` battlefield grid with `40px` logical cells. Its top `480px` is the build grid, `500px` is the playable world area, and the remaining space is the HUD.

At narrow portrait widths (`≤736px`), the game DOM and global gameplay inputs are gated and a landscape-required notice is shown. This is an intentional scope decision: shrinking the fixed Canvas further made internal text and controls too small even when geometry did not overlap.

### Local storage

Stored data is local to the current browser origin and is not trusted or synchronized.

Flappy Canvas uses the `flappyCanvas.` prefix for:

- best score;
- player name;
- local leaderboard;
- biome and weather;
- previous-run ghost visibility;
- music/SFX preferences.

Zombie Defense stores:

- best wave;
- selected map;
- music/SFX preferences.

Changing domains/origins does not migrate browser storage automatically.

---

## Flappy Canvas specification

### Physics and obstacle progression

| Property | Value |
|---|---:|
| Bird start position | `(100, 250)` |
| Flap vertical velocity | `-420 px/s` |
| Gravity | `1400 px/s²` |
| Maximum fall velocity | `600 px/s` |
| Pipe width | `60px` |
| Pipe spacing | `220px` |
| Starting pipe speed | `180 px/s` |
| Maximum pipe speed | `300 px/s` |
| Starting gap | `150px` |
| Minimum gap | `110px` |

After each passed pipe:

```text
pipe speed = min(300, current speed + 4)
gap height = max(110, current gap height - 2)
score = score + 1
```

Each pipe snapshots its gap height when created, so already-visible pipes do not resize when the score changes. Consecutive gap centers are also constrained to avoid impossible vertical jumps.

### Gameplay design

- The bird uses continuous physics but rounded draw positions for a crisp retro appearance.
- Circle-versus-rectangle collision is used for pipes.
- Background speed follows pipe speed, reinforcing the increasing pace.
- Pause freezes gameplay; resuming uses a `3 → 2 → 1` countdown.
- The previous run is sampled into fixed typed arrays and, when enabled, rendered as a translucent ghost. Ghost visibility is stored locally and defaults to on.
- Biome/weather choices are cosmetic and do not change collision or difficulty.

---

## Zombie Defense specification

### Battlefield and campaign

| Property | Value |
|---|---:|
| Logical Canvas | `800 × 650` |
| Build grid | `20 × 12` |
| Cell size | `40px` |
| Starting money | `$190` |
| Starting lives | `8` |
| Campaign length | `12 waves` |
| Maps | Last Outpost, Fog Marsh, Bone Ridge |

Map routes and props are data-driven. Route cells and prop cells are converted into occupancy masks whenever the selected map changes. Towers cannot be placed on the road, props, occupied cells, outside the grid, or without enough money.

| Map | Route length | Wave-1 Walker traversal | Wave-12 Walker traversal |
|---|---:|---:|---:|
| Last Outpost | `1,240px` | `20.17s` | `16.01s` |
| Fog Marsh | `1,560px` | `25.37s` | `20.15s` |
| Bone Ridge | `1,920px` | `31.23s` | `24.80s` |

Traversal values are route length divided by the production Walker speed for that wave. A longer route usually provides more attack time, but route length alone does not determine map difficulty: tower coverage overlap, corners, blocked cells, footprint capacity, and where target-compatible towers can be placed also matter.

### Towers

| Tower | Cost | Footprint | Range | Level 1 damage | Fire interval | Valid targets |
|---|---:|---:|---:|---:|---:|---|
| Rifle | `$45` | `1×1` | `112` | `14` | `0.30s` | Walker, Runner, Toxic, Burrower |
| Shotgun | `$80` | `1×1` | `92` | `28` | `0.88s` | Walker, Runner, Burrower |
| Bomber | `$120` | horizontal `2×1` | `132` | `52` | `1.25s` | Brute, Armored, Burrower, Boss |
| Sniper | `$165` | horizontal `2×1` | `220` | `86` | `1.55s` | Brute, Armored, Toxic, Boss |

Upgrade and sale formulas:

```text
Level 2 damage = Level 1 damage × 1.60
upgrade price  = round(base tower cost × 0.60)
sale refund    = floor(total invested money × 0.50)
```

Level 2 changes damage only. Tower range and firing interval remain unchanged.

Targeting chooses the valid, non-buried enemy with the greatest path progress inside range.

### Enemies

| Enemy | Base HP | Base speed | Base reward | Leak damage | Special behavior |
|---|---:|---:|---:|---:|---|
| Walker | 55 | 58 | `$6` | 1 | Baseline enemy |
| Runner | 38 | 94 | `$7` | 1 | Fast and fragile |
| Brute | 150 | 42 | `$15` | 2 | High health |
| Armored | 240 | 35 | `$20` | 2 | Very high health; restricted counters |
| Toxic | 125 | 50 | `$17` | 1 | Regenerates `14 HP/s` |
| Burrower | 105 | 55 | `$19` | 1 | Untargetable underground; surfaces at 25–45% route progress |
| Grave Titan | 1500 | 29 | `$175` | 5 | Final boss after Wave 12's regular queue |

Normal enemy HP at spawn is:

```text
maxHP(enemy, wave) = round((baseHP + 8 × wave) × thresholdMultiplier)
```

where:

| Waves | HP multiplier |
|---|---:|
| 1–4 | `1.00×` |
| 5–8 | `1.30×` |
| 9–11 | `1.65×` |
| 12 | `2.15×` |

The Grave Titan uses its fixed `1500 HP` boss value.

Enemy speed is:

```text
speed(enemy, wave) = baseSpeed × (1.06 + min(0.275, (wave - 1) × 0.025))
```

This produces `1.06×` speed in Wave 1 and `1.335×` speed in Wave 12.

### Weapon behavior

- **Rifle:** fast single-target projectile.
- **Shotgun:** damages all compatible enemies inside a short cone.
- **Bomber:** full damage to its direct target; compatible secondary targets inside a `90px` blast receive `8% × (1 - distance / 90)` of the direct damage. It also creates a `58px` scorch zone for `1.6s` that deals `1.5 damage/s` to compatible enemies.
- **Sniper:** immediate long-range heavy hit.

Weapon/enemy compatibility is deliberately hard rather than a soft resistance multiplier. This guarantees that mixed late waves require mixed defenses and makes target information strategically meaningful.

### Economy and wave settlement

Kill reward:

```text
reward = base reward + floor((wave - 1) / 6)
```

Perfect-wave bonus for Waves 1–11:

```text
perfect bonus = 12 + 5 × wave
```

Failed-wave penalty:

```text
penalty = min(current money, escaped enemies × 6 + lives lost × 4)
```

Each enemy owns the number of the wave that spawned it. Every wave has an independent settlement record containing remaining enemies, escapes, lost lives, boss state, and settlement state. This is necessary because the player may start the next wave while earlier enemies remain alive.

Settlement is idempotent: rewards, penalties, victory, and defeat cannot be applied twice. Killed-enemy bounty is credited before settlement fines. Terminal transitions stop the active enemy loop, clamp lives to zero, and clear remaining enemies/projectiles.

---

## Zombie Defense difficulty model

### How the current difficulty was determined

The current campaign uses a **hybrid authored/formula model**:

1. **Handcrafted composition** — each wave introduces or combines enemy archetypes intentionally.
2. **Threshold HP scaling** — clear jumps at Waves 5, 9, and 12.
3. **Continuous tempo scaling** — enemies become faster and spawn closer together every wave.
4. **Economy scaling** — kills and perfect-wave bonuses fund stronger defenses and upgrades.
5. **Counter pressure** — late waves mix target categories, regeneration, burrowing, armor, and a boss.
6. **Consequence scaling** — stronger enemies remove more lives when they escape.

The values were selected using tower-defense design heuristics. Mechanics and state/accounting contracts are covered by `tests/verify_zombie_strategy.py` and the broader browser regression suite; those tests do not prove end-to-end balance or campaign viability for representative builds. The values were **not** fitted from production telemetry, a large player sample, documented full-campaign playtests, or an automated optimal-play solver. Therefore, the campaign has an intentional and testable mechanical curve, but it should not be described as statistically calibrated.

### Implemented wave curve

The following table is calculated from the production formulas. “Total HP” and “Kill rewards” include the delayed Grave Titan in Wave 12, while “Queue deployment” covers only Wave 12's 26 regular enemies because the boss appears after those regular enemies are resolved. “Max life loss” is the theoretical result if every enemy escapes; the actual run ends when the player reaches zero lives.

| Wave | Enemies | Total HP | Speed | Spawn interval | Queue deployment | Kill rewards | Perfect bonus | Max life loss |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7 | 441 | `1.060×` | `0.745s` | `4.52s` | `$42` | `$17` | 7 |
| 2 | 9 | 571 | `1.085×` | `0.710s` | `5.73s` | `$58` | `$22` | 9 |
| 3 | 11 | 974 | `1.110×` | `0.675s` | `6.80s` | `$89` | `$27` | 13 |
| 4 | 13 | 1,886 | `1.135×` | `0.640s` | `7.73s` | `$152` | `$32` | 19 |
| 5 | 14 | 2,640 | `1.160×` | `0.605s` | `7.92s` | `$167` | `$37` | 18 |
| 6 | 16 | 3,545 | `1.185×` | `0.570s` | `8.60s` | `$206` | `$42` | 23 |
| 7 | 18 | 3,893 | `1.210×` | `0.535s` | `9.15s` | `$247` | `$47` | 24 |
| 8 | 19 | 4,603 | `1.235×` | `0.500s` | `9.05s` | `$277` | `$52` | 27 |
| 9 | 20 | 6,608 | `1.260×` | `0.465s` | `8.88s` | `$298` | `$57` | 29 |
| 10 | 21 | 7,367 | `1.285×` | `0.430s` | `8.65s` | `$325` | `$62` | 31 |
| 11 | 22 | 8,514 | `1.310×` | `0.395s` | `8.35s` | `$359` | `$67` | 34 |
| 12 | 27 | 14,261 | `1.335×` | `0.360s` | `9.05s` | `$584` | — | 43 |

The difficulty increase is not just “more HP.” Later waves also increase density, movement speed, composition complexity, counter requirements, regeneration pressure, untargetable travel time, and leak severity.

### Should difficulty be formulated more rigorously?

**Yes.** The existing formulas are a good implementation baseline, but future balancing should use a documented model plus player data.

A rigorous calculation must first name a scenario:

```text
scenario P = {
  map,
  tower positions and levels,
  targeting policy,
  upgrade/sell decisions,
  decision timing,
  next-wave overlap schedule,
  simulator timestep and event-order rules,
  seeds for every gameplay-relevant random source
}
```

Without those assumptions, regeneration, range coverage, compatible damage, and escape probability are not single fixed values. The balancing model should keep the following measurements separate instead of hiding them inside one arbitrary “difficulty score”:

1. **Spawn workload**

   ```text
   spawnHP(i,w) = production HP formula for enemy i in wave w
   regeneratedHP(i,P) = integral of actual Toxic regeneration while 0 < HP < maxHP
   damageWork(i,P) = spawnHP(i,w) + regeneratedHP(i,P)
   ```

   `regeneratedHP` depends on the named build and targeting policy. Burrowing is **not** extra health; it affects targetable time and must remain a separate measurement.

2. **Arrival workload and density**

   For a regular queue with `N > 1`:

   ```text
   scheduledInterarrivalSpan(w) = (N - 1) × spawnInterval(w)
   spawnHPArrivalRate(w) = sum(spawnHP of regular queue) / scheduledInterarrivalSpan(w)
   combatRegenRate(w,P) = sum(regeneratedHP during combat) / measured combat duration
   ```

   The initial `0.05s` delay is startup latency, not an interarrival interval. “Scheduled” is deliberate: frame-quantized browser updates can make observed spacing slightly longer because timer overshoot is not preserved. Spawn HP and regeneration are reported separately because Toxic HP is created during combat rather than arriving with the queue. The Grave Titan is evaluated as a separate boss phase because it spawns only after Wave 12's regular enemies resolve. Peak enemies alive and peak compatible workload should also be measured over time; an average alone can hide dangerous bursts.

3. **Traversal time and actual targetable exposure**

   ```text
   traversalTime(i,map) = routeLength(map) / speed(i,w)
   targetableTime(i,P) = time alive, surfaced, compatible, in range, and not already dead
   ```

   Traversal time is only a coarse route-duration proxy. Actual targetable exposure depends on legal build cells, route bends, tower ranges and footprints, overlapping coverage, compatibility, and the selected build.

4. **Incremental affordability**

   Evaluate liquid cash, realizable sale value, and existing compatible tower capacity against the **additional** investment required for a viable counter configuration. Report any cash shortfall by map and strategy archetype rather than using total income alone.

5. **Leak and failure distributions**

   Do not invent escape probabilities. Estimate lives remaining, leaks, and failure rate from deterministic seeded simulations or documented playtests. For Burrowers, enumerate or sample their 25–45% surfacing positions and report distributions or quantiles.

The project should therefore use a metrics dashboard—not one multiplicative scalar—with at least:

- total regular-queue spawn HP and policy-conditioned regenerated HP;
- regular spawn-HP arrival rate and measured combat regeneration rate;
- boss workload as a separate phase;
- traversal and targetable seconds by enemy type;
- peak compatible DPS demand and peak enemies alive;
- economy shortfall for each build archetype;
- leaks, lives remaining, clear time, and failure/no-leak rates.

A simulator should run representative legal builds on all three maps and report:

- enemies leaked and lives remaining;
- cash before and after each wave;
- damage by tower type;
- target downtime caused by compatibility, range coverage, or burrowing;
- peak enemies alive;
- time to clear each wave;
- whether at least two or three distinct opening strategies remain viable.

### What tower-defense games normally do

Tower-defense games commonly combine several of the following; automated simulation and telemetry are most typical in larger or data-mature projects rather than universal requirements for every small game:

- **enemy threat costs:** every enemy type receives a budget value based on HP, speed, abilities, and leak damage;
- **wave budgets:** a curve controls how much total threat each wave may contain;
- **authored milestones:** new enemy types, bosses, and counter checks appear at planned waves;
- **stat curves:** HP/speed/reward multipliers rise gradually or at explicit tiers;
- **economy models:** expected income is compared with the cost of required defenses;
- **map modifiers:** route length, overlapping coverage, and buildable area affect expected difficulty;
- **simulation:** automated runs detect impossible or trivial waves;
- **playtesting/telemetry:** completion rate, leak rate, tower pick rate, sell rate, and failure wave are measured;
- **difficulty targets:** for example, a first-time-player completion target and a higher expert no-leak target.

The recommended next balancing phase for this project is:

1. define beginner, typical, and optimized build archetypes before assigning targets;
2. calculate route duration and legal tower-coverage geometry for all three maps;
3. add a deterministic combat/economy simulator with explicit timestep/event-order rules and fixed seeds for every random source, or enumerate Burrower surfacing positions;
4. model projectile travel, compatibility, splash/scorch, targeting, upgrades, selling, player-controlled overlap, and delayed boss timing;
5. validate simulator outcomes against browser runs;
6. set explicit completion, no-leak, economy, and failure-wave targets for each map/build archetype;
7. collect anonymous aggregate playtest results only if analytics is explicitly added to project scope;
8. tune wave composition and economy from those results while publishing assumptions/seeds and keeping formulas, documentation, and tests synchronized.

---

## Design decisions

| Decision | Reason and tradeoff |
|---|---|
| One repository and one production origin | Simplifies navigation, deployment, and ownership. Old-origin browser saves cannot migrate automatically. |
| Self-contained HTML files | Games run without a build step or runtime packages. The files are larger and less modular than a bundled multi-file application. |
| Canvas instead of DOM entities | Gives deterministic drawing and a cohesive retro style. Accessibility and responsive text require extra care. |
| Procedural graphics and audio | Avoids asset hosting/licensing dependencies and keeps deployment static. Art/audio variety is intentionally limited. |
| Explicit state machines | Prevents gameplay from continuing behind pause/end screens and makes browser tests deterministic. |
| Fixed logical resolution with responsive scaling | Keeps gameplay geometry stable. Narrow portrait play is gated because internal Canvas controls become too small. |
| Local-only persistence | Works without accounts or a backend. Scores and preferences are not portable or authoritative. |
| Four differentiated Zombie defenses | Produces understandable tactical roles without overloading a small HUD. |
| Hard target compatibility | Forces mixed defenses and makes enemy composition meaningful. It is less forgiving than resistance-based damage. |
| Two tower levels only | Keeps upgrade decisions visible and scoped. No branching specialization is provided. |
| Horizontal `2×1` heavy towers | Adds placement pressure while keeping click mapping and validation deterministic. Rotation is intentionally excluded. |
| 50% sale refund | Allows correction and repositioning without enabling free tower movement. |
| Early next-wave start | Gives skilled players control over pacing and income timing. It required per-wave enemy ownership and settlement records. |
| Handcrafted waves plus formulas | Supports intentional enemy introductions while retaining predictable scaling. It still needs telemetry/simulation for statistical calibration. |
| Data-driven maps | Routes, palettes, props, occupancy, and previews can change without rewriting combat systems. |
| Exposed debug handles | Enables deterministic Selenium tests for Canvas-only state. These handles do not provide server access or trusted state. |

---

## Repository structure

```text
pixel-arcade/
├── index.html                         # Pixel Arcade launcher
├── flappy/
│   └── index.html                     # Flappy Canvas
├── zombie-defense/
│   └── index.html                     # Zombie Defense
├── tests/
│   ├── verify_source_contract.py      # Same-origin/source invariants
│   ├── verify_flappy_feedback.py      # Flappy behavior and rendering checks
│   ├── verify_gameplay_feedback.py    # Cross-game gameplay feedback checks
│   ├── verify_zombie_strategy.py      # Strategy, accounting, input, responsive tests
│   ├── verify_combined_arcade.py      # Launcher/game integration
│   └── verify_production.py           # Production browser smoke test
└── README.md
```

---

## Local development

No build is required.

```bash
git clone git@github.com:alimajid266/pixel-arcade.git
cd pixel-arcade
python3 -m http.server 8770 --bind 127.0.0.1
```

Open:

- Launcher: http://127.0.0.1:8770/
- Flappy Canvas: http://127.0.0.1:8770/flappy/
- Zombie Defense: http://127.0.0.1:8770/zombie-defense/

Do not use the development server as a public production server.

---

## Testing

Browser regressions use Python, Selenium, Firefox, and geckodriver. The committed browser tests currently point to the verified Linux Snap paths:

- Firefox: `/snap/firefox/current/usr/lib/firefox/firefox`
- geckodriver: `/snap/bin/firefox.geckodriver`

Installing Selenium alone is insufficient if those browser/driver paths do not exist. On another operating system, either provide equivalent binaries at those paths or update the test configuration deliberately. In this repository's verified Linux environment:

```bash
python3 -m venv .venv
.venv/bin/pip install selenium
python3 -m http.server 8770 --bind 127.0.0.1
```

In another terminal:

```bash
.venv/bin/python tests/verify_source_contract.py
.venv/bin/python tests/verify_flappy_feedback.py
.venv/bin/python tests/verify_gameplay_feedback.py
.venv/bin/python tests/verify_zombie_strategy.py
.venv/bin/python tests/verify_combined_arcade.py
```

Production smoke test:

```bash
.venv/bin/python tests/verify_production.py
```

The regression suite covers, among other behavior:

- launcher and same-origin navigation;
- Canvas runtime errors and initial states;
- Flappy scoring, pacing, ghost orientation/visibility, pause, and menu geometry;
- tower placement rejection and `2×1` footprints;
- upgrades, selling, compatibility, and unaffordable previews;
- overlapping-wave ownership and settlement;
- bounty/fine ordering, lethal escapes, final-wave boss flow, and terminal cleanup;
- map preview and utility-control geometry;
- sidebar separation, Canvas aspect ratio, scaled input, and portrait gates.

---

## Deployment

Production is deployed as one static Vercel project connected to the repository's `main` branch:

- Repository: https://github.com/alimajid266/pixel-arcade
- Production: https://pixel-arcade-pied.vercel.app

Vercel configuration:

- Framework preset: **Other**
- Build command: none
- Output directory: none
- Runtime: static files only

A release is considered verified only after:

1. local regression suites pass;
2. the intended files are committed and pushed;
3. Vercel reports a successful deployment for the exact Git commit;
4. the stable production alias points to that deployment;
5. production browser smoke tests pass.

---

## Known boundaries and future work

The current release is a complete small arcade, not a live-service platform. Reasonable extensions include:

- a formal Zombie Defense wave-budget/simulation tool;
- playtest-derived difficulty presets;
- additional games behind the shared launcher;
- accessible DOM mirrors for important Canvas-only status text;
- optional cloud accounts and server-validated leaderboards;
- active-run save/resume for Zombie Defense;
- more tower upgrade paths, maps, enemy mechanics, and campaign modes.

Those features are intentionally outside the current scope and should be introduced only with matching tests, updated formulas, and a clear persistence/backend design.
