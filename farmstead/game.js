import * as THREE from '../vendor/three.module.min.js';
import { GLTFLoader } from '../vendor/GLTFLoader.js';
import { mergeGeometries } from '../vendor/BufferGeometryUtils.js';
import { FarmModel, CROPS } from './farm-core.mjs';

const SAVE_KEY = 'pixelArcade.harvestHollow.v1';
const canvas = document.getElementById('game');
const ui = Object.fromEntries([...document.querySelectorAll('[id]')].map(node => [node.id, node]));
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

function loadFarm() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    return raw ? FarmModel.fromSnapshot(JSON.parse(raw)) : new FarmModel();
  } catch {
    return new FarmModel();
  }
}

let farm = loadFarm();
let state = 'MENU';
let selectedTool = 'hoe';
let selectedIndex = 0;
let queuedIndex = null;
let messageTimer = 0;
let completionShown = farm.earnings >= 350;
let audioContext = null;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0x9fd7b5);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9fd7b5);
scene.fog = new THREE.Fog(0x9fd7b5, 24, 46);
const camera = new THREE.OrthographicCamera(-12, 12, 8, -8, 0.1, 100);
camera.position.set(17, 19, 20);
camera.lookAt(0, 0, 1);
scene.add(new THREE.HemisphereLight(0xfff1c9, 0x315f3f, 2.1));
const sun = new THREE.DirectionalLight(0xffe5ad, 2.4);
sun.position.set(-8, 18, 10);
scene.add(sun);

const mats = {
  grass: new THREE.MeshStandardMaterial({ color: 0x78b957, roughness: 1 }),
  grassLight: new THREE.MeshStandardMaterial({ color: 0x91cb66, roughness: 1 }),
  soil: new THREE.MeshStandardMaterial({ color: 0x8b5a3c, roughness: 1 }),
  wetSoil: new THREE.MeshStandardMaterial({ color: 0x594633, roughness: 0.78 }),
  path: new THREE.MeshStandardMaterial({ color: 0xd8b876, roughness: 1 }),
  water: new THREE.MeshStandardMaterial({ color: 0x5db5d5, roughness: 0.25, transparent: true, opacity: 0.88 }),
  wood: new THREE.MeshStandardMaterial({ color: 0x7b4c34, roughness: 1 }),
  cream: new THREE.MeshStandardMaterial({ color: 0xf2dfb2, roughness: 1 }),
  red: new THREE.MeshStandardMaterial({ color: 0xb9503d, roughness: 0.85 }),
  leaf: new THREE.MeshStandardMaterial({ color: 0x4e983d, roughness: 1 }),
  turnip: new THREE.MeshStandardMaterial({ color: 0xf2e8dc, roughness: 0.9 }),
  carrot: new THREE.MeshStandardMaterial({ color: 0xee7b25, roughness: 0.9 }),
  pumpkin: new THREE.MeshStandardMaterial({ color: 0xe96824, roughness: 0.9 }),
  highlight: new THREE.MeshBasicMaterial({ color: 0xffe47a, transparent: true, opacity: 0.72, side: THREE.DoubleSide }),
};
const geometries = {
  tile: new THREE.BoxGeometry(1.42, 0.18, 1.42),
  leaf: new THREE.ConeGeometry(0.11, 0.42, 5),
  turnip: new THREE.SphereGeometry(0.22, 8, 6),
  carrot: new THREE.ConeGeometry(0.16, 0.42, 7),
  pumpkin: new THREE.SphereGeometry(0.27, 10, 6),
};

const world = new THREE.Group();
scene.add(world);
const ground = new THREE.Mesh(new THREE.BoxGeometry(28, 0.8, 22), mats.grass);
ground.position.y = -0.48;
world.add(ground);

function box(w, h, d, material, x, y, z) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  mesh.position.set(x, y, z);
  world.add(mesh);
  return mesh;
}

box(3.2, 0.12, 17, mats.path, -6.1, 0.01, 0.8);
box(12, 0.1, 2.2, mats.path, -0.4, 0.02, -6.5);
const pond = new THREE.Mesh(new THREE.CylinderGeometry(2.15, 2.4, 0.12, 18), mats.water);
pond.position.set(8.7, 0.02, 5.7);
world.add(pond);
for (let i = 0; i < 13; i++) {
  const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(0.22 + (i % 3) * 0.07, 0), new THREE.MeshStandardMaterial({ color: i % 2 ? 0x819173 : 0x718169, roughness: 1 }));
  const angle = i / 13 * Math.PI * 2;
  rock.position.set(8.7 + Math.cos(angle) * 2.35, 0.12, 5.7 + Math.sin(angle) * 2.35);
  rock.scale.y = 0.65;
  world.add(rock);
}

const tileGroups = [];
const tileHitMeshes = [];
const FIELD_COLS = 6;
const FIELD_ROWS = 5;
const TILE = 1.55;
const FIELD_X = 1.0;
const FIELD_Z = 1.0;
for (let row = 0; row < FIELD_ROWS; row++) {
  for (let col = 0; col < FIELD_COLS; col++) {
    const index = row * FIELD_COLS + col;
    const group = new THREE.Group();
    group.position.set(FIELD_X + (col - 2.5) * TILE, 0, FIELD_Z + (row - 2) * TILE);
    const base = new THREE.Mesh(geometries.tile, mats.grassLight);
    base.position.y = 0.05;
    base.userData.tileIndex = index;
    group.add(base);
    world.add(group);
    tileGroups.push(group);
    tileHitMeshes.push(base);
  }
}

const selection = new THREE.Mesh(new THREE.RingGeometry(0.68, 0.79, 4), mats.highlight);
selection.rotation.x = -Math.PI / 2;
selection.rotation.z = Math.PI / 4;
selection.position.y = 0.18;
world.add(selection);

function addLeaves(group, height, scale = 1) {
  for (let i = 0; i < 3; i++) {
    const leaf = new THREE.Mesh(geometries.leaf, mats.leaf);
    leaf.position.set(Math.cos(i * 2.094) * 0.09, height, Math.sin(i * 2.094) * 0.09);
    leaf.rotation.z = (i - 1) * 0.35;
    leaf.scale.setScalar(scale);
    group.add(leaf);
  }
}

function buildCrop(tile, group) {
  const ratio = clamp(tile.growth / CROPS[tile.crop].growDays, 0, 1);
  const scale = 0.46 + ratio * 0.54;
  const crop = new THREE.Group();
  crop.userData.cropVisual = true;
  if (tile.crop === 'turnip') {
    const bulb = new THREE.Mesh(geometries.turnip, mats.turnip);
    bulb.position.y = 0.25;
    bulb.scale.set(1, 0.9, 1);
    crop.add(bulb);
    addLeaves(crop, 0.54, 0.8);
  } else if (tile.crop === 'carrot') {
    const root = new THREE.Mesh(geometries.carrot, mats.carrot);
    root.position.y = 0.33;
    root.rotation.x = Math.PI;
    crop.add(root);
    addLeaves(crop, 0.55, 0.7);
  } else {
    const fruit = new THREE.Mesh(geometries.pumpkin, mats.pumpkin);
    fruit.position.y = 0.27;
    fruit.scale.y = 0.72;
    crop.add(fruit);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.055, 0.2, 5), mats.leaf);
    stem.position.y = 0.5;
    crop.add(stem);
  }
  crop.scale.setScalar(scale);
  if (tile.ready) {
    const glow = new THREE.Mesh(new THREE.RingGeometry(0.34, 0.4, 16), new THREE.MeshBasicMaterial({ color: 0xffe36e, transparent: true, opacity: 0.8, side: THREE.DoubleSide }));
    glow.rotation.x = -Math.PI / 2;
    glow.position.y = 0.2;
    glow.userData.readyGlow = true;
    crop.add(glow);
  }
  group.add(crop);
}

function refreshTiles() {
  tileGroups.forEach((group, index) => {
    const tile = farm.tiles[index];
    const base = group.children[0];
    base.material = tile.state === 'grass' ? mats.grassLight : (tile.watered ? mats.wetSoil : mats.soil);
    for (let i = group.children.length - 1; i > 0; i--) group.remove(group.children[i]);
    if (tile.state === 'planted') buildCrop(tile, group);
  });
  const position = tileGroups[selectedIndex].position;
  selection.position.set(position.x, 0.2, position.z);
}

const windmill = new THREE.Group();
windmill.position.set(-8.4, 0, 4.8);
const tower = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.45, 4.2, 8), mats.cream);
tower.position.y = 2.1;
windmill.add(tower);
const roof = new THREE.Mesh(new THREE.ConeGeometry(1.35, 1.5, 8), mats.red);
roof.position.y = 4.55;
windmill.add(roof);
const hub = new THREE.Group();
hub.position.set(0, 3.45, 1.18);
hub.rotation.y = Math.PI;
for (let i = 0; i < 4; i++) {
  const sail = new THREE.Mesh(new THREE.BoxGeometry(0.28, 2.6, 0.12), mats.wood);
  sail.position.y = 1.2;
  const arm = new THREE.Group();
  arm.rotation.z = i * Math.PI / 2;
  arm.add(sail);
  hub.add(arm);
}
windmill.add(hub);
world.add(windmill);

const farmerRoot = new THREE.Group();
farmerRoot.position.set(-1.5, 0.1, -3.8);
world.add(farmerRoot);
let farmerModel = null;
let mixer = null;
let idleAction = null;
let walkAction = null;
let interactAction = null;
const assets = { farmer: false, farm: false };

function normalizedModel(sceneRoot, targetHeight) {
  const bounds = new THREE.Box3().setFromObject(sceneRoot);
  const size = bounds.getSize(new THREE.Vector3());
  const scale = targetHeight / Math.max(size.y, 0.001);
  sceneRoot.scale.setScalar(scale);
  const scaled = new THREE.Box3().setFromObject(sceneRoot);
  const center = scaled.getCenter(new THREE.Vector3());
  sceneRoot.position.x -= center.x;
  sceneRoot.position.z -= center.z;
  sceneRoot.position.y -= scaled.min.y;
  return sceneRoot;
}

function flattenStaticModel(root) {
  root.updateMatrixWorld(true);
  const buckets = new Map();
  const sourceGeometries = new Set();
  root.traverse(node => {
    if (!node.isMesh || node.isSkinnedMesh || Array.isArray(node.material)) return;
    const geometry = node.geometry.clone();
    geometry.applyMatrix4(node.matrixWorld);
    const key = node.material.uuid;
    if (!buckets.has(key)) buckets.set(key, { material: node.material, geometries: [] });
    buckets.get(key).geometries.push(geometry);
    sourceGeometries.add(node.geometry);
  });

  const flattened = new THREE.Group();
  for (const { material, geometries } of buckets.values()) {
    const merged = mergeGeometries(geometries, false);
    if (merged) flattened.add(new THREE.Mesh(merged, material));
    geometries.forEach(geometry => geometry.dispose());
  }
  sourceGeometries.forEach(geometry => geometry.dispose());
  return flattened;
}

const loader = new GLTFLoader();
loader.load('./assets/farmer.glb', gltf => {
  farmerModel = normalizedModel(gltf.scene, 1.7);
  farmerRoot.add(farmerModel);
  mixer = new THREE.AnimationMixer(farmerModel);
  const findClip = name => gltf.animations.find(clip => clip.name.endsWith(`|${name}`));
  const idle = findClip('Idle') || findClip('Idle_Neutral');
  const walk = findClip('Walk') || findClip('Run');
  const interact = findClip('Interact');
  if (idle) idleAction = mixer.clipAction(idle).play();
  if (walk) walkAction = mixer.clipAction(walk);
  if (interact) {
    interactAction = mixer.clipAction(interact);
    interactAction.setLoop(THREE.LoopOnce, 1);
    interactAction.clampWhenFinished = true;
  }
  assets.farmer = true;
  updateDebug();
}, undefined, error => {
  window.__errors.push(`Farmer asset: ${error.message || error}`);
});

loader.load('./assets/farm.glb', gltf => {
  const source = normalizedModel(gltf.scene, 3.8);
  source.position.x += -6.6;
  source.position.z += -4.8;
  source.rotation.y = Math.PI * 0.12;
  const farmArt = flattenStaticModel(source);
  world.add(farmArt);
  assets.farm = true;
  updateDebug();
}, undefined, error => {
  window.__errors.push(`Farm asset: ${error.message || error}`);
});

function updateWindmill() {
  const progress = clamp(farm.earnings / 350, 0, 1);
  tower.material = mats.cream;
  roof.visible = true;
  hub.visible = true;
  hub.children.forEach((arm, index) => { arm.visible = index === 0 || progress >= (index + 1) / 4; });
  windmill.scale.setScalar(0.92 + progress * 0.08);
}

function weatherForDay(day) {
  return day % 3 === 0 ? 'RAIN' : day % 5 === 0 ? 'BREEZY' : 'SUNNY';
}

function applyRain() {
  if (weatherForDay(farm.day) !== 'RAIN') return;
  for (const tile of farm.tiles) if (tile.state === 'planted') tile.watered = true;
}

function save() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(farm.snapshot())); } catch {}
}

function totalProduce() {
  return Object.values(farm.produce).reduce((sum, value) => sum + value, 0);
}

function updateHud() {
  ui.day.textContent = farm.day;
  ui.weather.textContent = weatherForDay(farm.day);
  ui.coins.textContent = farm.coins;
  ui.energy.textContent = farm.energy;
  ui.earnings.textContent = farm.earnings;
  ui['goal-progress'].style.width = `${clamp(farm.earnings / 350, 0, 1) * 100}%`;
  ui['turnip-count'].textContent = farm.seeds.turnip;
  ui['carrot-count'].textContent = farm.seeds.carrot;
  ui['pumpkin-count'].textContent = farm.seeds.pumpkin;
  const order = farm.order;
  ui['order-text'].textContent = `${order.count} ${CROPS[order.crop].name.toLowerCase()}s → ${order.reward} coins`;
  ui['buy-carrot'].textContent = farm.day >= 2 ? 'BUY CARROT · 14' : 'CARROT · DAY 2';
  ui['buy-pumpkin'].textContent = farm.day >= 4 ? 'BUY PUMPKIN · 24' : 'PUMPKIN · DAY 4';
  ui['buy-carrot'].disabled = farm.day < 2;
  ui['buy-pumpkin'].disabled = farm.day < 4;
  ui['sell-all'].textContent = totalProduce() ? `SELL BASKET · ${totalProduce()}` : 'SELL BASKET';
  for (const button of document.querySelectorAll('.tool')) button.classList.toggle('active', button.dataset.tool === selectedTool);
  refreshTiles();
  updateWindmill();
  updateDebug();
}

function toast(text, good = false) {
  ui.message.textContent = text;
  ui.message.style.borderColor = good ? '#8bd450' : '#ffd166';
  ui.message.classList.add('show');
  messageTimer = 2.1;
}

function unlockAudio() {
  if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
  if (audioContext.state === 'suspended') audioContext.resume();
}

function sound(kind) {
  if (!audioContext) return;
  const osc = audioContext.createOscillator();
  const gain = audioContext.createGain();
  const now = audioContext.currentTime;
  osc.type = kind === 'coin' ? 'triangle' : 'sine';
  osc.frequency.setValueAtTime(kind === 'coin' ? 520 : kind === 'water' ? 220 : 150, now);
  osc.frequency.exponentialRampToValueAtTime(kind === 'coin' ? 880 : 95, now + 0.12);
  gain.gain.setValueAtTime(0.055, now);
  gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
  osc.connect(gain).connect(audioContext.destination);
  osc.start(now); osc.stop(now + 0.17);
}

function setAnimation(next) {
  if (!mixer) return;
  const target = next === 'walk' ? walkAction : idleAction;
  if (target && !target.isRunning()) {
    for (const action of [idleAction, walkAction]) if (action && action !== target) action.fadeOut(0.12);
    target.reset().fadeIn(0.12).play();
  }
}

function performAction(index) {
  const tool = ['turnip', 'carrot', 'pumpkin'].includes(selectedTool) ? 'seed' : selectedTool;
  const crop = tool === 'seed' ? selectedTool : null;
  const result = farm.act(index, tool, crop);
  if (result.ok) {
    if (interactAction) interactAction.reset().fadeIn(0.08).play();
    sound(tool === 'water' ? 'water' : 'action');
    toast(tool === 'harvest' ? 'Harvested into your basket.' : 'Farm work done.', true);
    save();
  } else {
    toast(result.reason);
  }
  updateHud();
}

function queueAction(index) {
  if (state !== 'PLAYING' || queuedIndex !== null) return;
  selectedIndex = clamp(index, 0, farm.tiles.length - 1);
  queuedIndex = selectedIndex;
  updateHud();
}

function selectTool(tool) {
  selectedTool = tool;
  updateHud();
}

function changeState(next) {
  state = next;
  document.body.classList.toggle('menu-mode', next === 'MENU');
  ui.menu.classList.toggle('hidden', next !== 'MENU');
  ui.pause.classList.toggle('hidden', next !== 'PAUSED');
  ui.complete.classList.toggle('hidden', next !== 'COMPLETE');
  ui['pause-toggle'].classList.toggle('hidden', next !== 'PLAYING');
  updateDebug();
}

function startGame() {
  unlockAudio();
  applyRain();
  changeState('PLAYING');
  updateHud();
  toast('Select a tool, then tap a field plot.');
}

function resetInteractionState() {
  queuedIndex = null;
  selectedIndex = 0;
  selectedTool = 'hoe';
  farmerRoot.position.set(-1.5, 0.1, -3.8);
  farmerRoot.rotation.set(0, 0, 0);
  messageTimer = 0;
  ui.message.classList.remove('show');
  setAnimation('idle');
}

function endDay() {
  const before = farm.day;
  farm.endDay();
  applyRain();
  save();
  updateHud();
  sound('coin');
  toast(`Day ${before} complete. Day ${farm.day} is ${weatherForDay(farm.day).toLowerCase()}.`, true);
}

function checkCompletion(beforeEarnings) {
  if (beforeEarnings < 350 && farm.earnings >= 350 && !completionShown) {
    completionShown = true;
    changeState('COMPLETE');
  }
}

for (const button of document.querySelectorAll('.tool')) button.addEventListener('click', () => {
  unlockAudio();
  selectTool(button.dataset.tool);
});
ui.start.addEventListener('click', startGame);
ui['new-game'].addEventListener('click', () => {
  unlockAudio();
  resetInteractionState();
  farm = new FarmModel();
  completionShown = false;
  save();
  startGame();
});
ui['pause-toggle'].addEventListener('click', () => changeState('PAUSED'));
ui.resume.addEventListener('click', () => changeState('PLAYING'));
ui.continue.addEventListener('click', () => changeState('PLAYING'));
for (const button of document.querySelectorAll('.menu-return')) button.addEventListener('click', () => changeState('MENU'));
ui['end-day'].addEventListener('click', () => { if (state === 'PLAYING') endDay(); });
ui['sell-all'].addEventListener('click', () => {
  if (state !== 'PLAYING') return;
  unlockAudio();
  const before = farm.earnings;
  const result = farm.sellAll();
  if (result.ok) { sound('coin'); toast(`Sold ${result.items} crops for ${result.coins} coins.`, true); save(); }
  else toast(result.reason);
  updateHud(); checkCompletion(before);
});
ui['deliver-order'].addEventListener('click', () => {
  if (state !== 'PLAYING') return;
  unlockAudio();
  const before = farm.earnings;
  const result = farm.deliverOrder();
  if (result.ok) { sound('coin'); toast(`Order delivered! +${result.reward} coins.`, true); save(); }
  else toast(result.reason);
  updateHud(); checkCompletion(before);
});
for (const crop of Object.keys(CROPS)) {
  ui[`buy-${crop}`].addEventListener('click', () => {
    if (state !== 'PLAYING') return;
    unlockAudio();
    const result = farm.buySeeds(crop);
    if (result.ok) { sound('coin'); toast(`Bought 1 ${CROPS[crop].name.toLowerCase()} seed.`, true); save(); }
    else toast(result.reason);
    updateHud();
  });
}

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
canvas.addEventListener('pointerdown', event => {
  if (state !== 'PLAYING') return;
  unlockAudio();
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(tileHitMeshes, false)[0];
  if (hit) queueAction(hit.object.userData.tileIndex);
});

addEventListener('keydown', event => {
  if (event.target instanceof HTMLButtonElement) return;
  if (event.key === 'Escape' || event.key.toLowerCase() === 'p') {
    if (state === 'PLAYING') changeState('PAUSED');
    else if (state === 'PAUSED') changeState('PLAYING');
    return;
  }
  if (state !== 'PLAYING') return;
  const tools = ['hoe', 'water', 'turnip', 'carrot', 'pumpkin', 'harvest'];
  if (/^[1-6]$/.test(event.key)) { selectTool(tools[Number(event.key) - 1]); return; }
  let row = Math.floor(selectedIndex / FIELD_COLS);
  let col = selectedIndex % FIELD_COLS;
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') col--;
  else if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') col++;
  else if (event.key === 'ArrowUp' || event.key.toLowerCase() === 'w') row--;
  else if (event.key === 'ArrowDown' || event.key.toLowerCase() === 's') row++;
  else if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); queueAction(selectedIndex); return; }
  else return;
  event.preventDefault();
  selectedIndex = clamp(row, 0, FIELD_ROWS - 1) * FIELD_COLS + clamp(col, 0, FIELD_COLS - 1);
  updateHud();
});

function resize() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  renderer.setSize(width, height, false);
  const aspect = width / Math.max(height, 1);
  const viewHeight = width < 700 ? 20 : 17;
  camera.left = -viewHeight * aspect / 2;
  camera.right = viewHeight * aspect / 2;
  camera.top = viewHeight / 2;
  camera.bottom = -viewHeight / 2;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
resize();

function updateDebug() {
  window.__game = {
    ready: true,
    get state() { return state; },
    get farm() { return farm; },
    get selectedTool() { return selectedTool; },
    assets,
    renderer,
    scene,
    camera,
    selectTool,
    actTile: queueAction,
    endDay,
    save,
    refresh: updateHud
  };
}

let last = performance.now();
function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;
  if (state === 'PLAYING') {
    if (mixer) mixer.update(dt);
    if (queuedIndex !== null) {
      const destination = tileGroups[queuedIndex].position;
      const dx = destination.x - farmerRoot.position.x;
      const dz = destination.z - farmerRoot.position.z;
      const distance = Math.hypot(dx, dz);
      if (distance < 0.18) {
        farmerRoot.position.set(destination.x, 0.1, destination.z - 0.46);
        const actionIndex = queuedIndex;
        queuedIndex = null;
        setAnimation('idle');
        performAction(actionIndex);
      } else {
        const step = Math.min(distance, dt * 5.2);
        farmerRoot.position.x += dx / distance * step;
        farmerRoot.position.z += dz / distance * step;
        farmerRoot.rotation.y = Math.atan2(dx, dz);
        setAnimation('walk');
      }
    } else {
      setAnimation('idle');
    }
    if (hub.visible) hub.rotation.z -= dt * 0.55;
  }
  if (messageTimer > 0) {
    messageTimer -= dt;
    if (messageTimer <= 0) ui.message.classList.remove('show');
  }
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}

refreshTiles();
updateHud();
updateDebug();
requestAnimationFrame(frame);
