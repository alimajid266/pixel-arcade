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
let queuedTool = null;
let messageTimer = 0;
let transitioning = false;
let audioContext = null;
const VOXEL_WORLD = true;
const RENDER_SCALE = 1;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0x65d9ff);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x65d9ff);
scene.fog = new THREE.Fog(0x65d9ff, 42, 68);
const camera = new THREE.OrthographicCamera(-12, 12, 8, -8, 0.1, 100);
camera.position.set(18, 21, 22);
camera.lookAt(0, 0, 0);
const skyLight = new THREE.HemisphereLight(0xffffff, 0x245080, 0.9);
scene.add(skyLight);
const sun = new THREE.DirectionalLight(0xffe1a8, 1.18);
sun.position.set(-8, 18, 10);
scene.add(sun);

const mats = {
  grass: new THREE.MeshLambertMaterial({ color: 0x51d957, flatShading: true }),
  grassLight: new THREE.MeshLambertMaterial({ color: 0x72ef65, flatShading: true }),
  soil: new THREE.MeshLambertMaterial({ color: 0xb95d43, flatShading: true }),
  wetSoil: new THREE.MeshLambertMaterial({ color: 0x713b41, flatShading: true }),
  path: new THREE.MeshLambertMaterial({ color: 0xffcc55, flatShading: true }),
  water: new THREE.MeshLambertMaterial({ color: 0x2fcbd5, transparent: true, opacity: 0.94, flatShading: true }),
  wood: new THREE.MeshLambertMaterial({ color: 0x70415a, flatShading: true }),
  cream: new THREE.MeshLambertMaterial({ color: 0xffe4a8, flatShading: true }),
  red: new THREE.MeshLambertMaterial({ color: 0xf04f61, flatShading: true }),
  leaf: new THREE.MeshLambertMaterial({ color: 0x168f62, flatShading: true }),
  turnip: new THREE.MeshLambertMaterial({ color: 0xf7efff, flatShading: true }),
  carrot: new THREE.MeshLambertMaterial({ color: 0xff7a35, flatShading: true }),
  pumpkin: new THREE.MeshLambertMaterial({ color: 0xff9f2f, flatShading: true }),
  highlight: new THREE.MeshBasicMaterial({ color: 0xffe47a, transparent: true, opacity: 0.72, side: THREE.DoubleSide }),
};
const geometries = {
  tile: new THREE.BoxGeometry(1.42, 0.18, 1.42),
  leaf: new THREE.BoxGeometry(0.12, 0.4, 0.1),
  turnip: new THREE.BoxGeometry(0.4, 0.32, 0.4),
  carrot: new THREE.BoxGeometry(0.24, 0.46, 0.24),
  pumpkin: new THREE.BoxGeometry(0.52, 0.38, 0.52),
};

const world = new THREE.Group();
scene.add(world);
const rainState = Array.from({ length: 96 }, (_, index) => ({
  x: ((index * 47) % 260) / 10 - 13,
  y: 2 + ((index * 31) % 100) / 10,
  z: ((index * 73) % 220) / 10 - 11,
}));
const rainVisuals = new THREE.InstancedMesh(
  new THREE.BoxGeometry(0.045, 0.72, 0.045),
  new THREE.MeshBasicMaterial({ color: 0x9eeeff, transparent: true, opacity: 0.78, depthWrite: false }),
  rainState.length
);
rainVisuals.name = 'rain-visuals';
rainVisuals.visible = false;
scene.add(rainVisuals);
const ground = new THREE.Mesh(new THREE.BoxGeometry(60, 0.8, 50), new THREE.MeshLambertMaterial({ color: 0x258c4d }));
ground.position.y = -0.62;
world.add(ground);

const grassGeometry = new THREE.BoxGeometry(1.02, 0.26, 1.02);
const grassGrid = new THREE.Group();
grassGrid.name = 'voxel-grass-grid';
const voxelMatrix = new THREE.Matrix4();
const grassPalette = [0x48d95b, 0x62ef69, 0x39c95c, 0x79f47a];
const grassPositions = grassPalette.map(() => []);
for (let z = -20; z < 20; z++) {
  for (let x = -22; x < 22; x++) {
    const colorIndex = Math.abs((x * 13 + z * 7 + x * z) % grassPalette.length);
    grassPositions[colorIndex].push([x + 0.5, -0.15, z + 0.5]);
  }
}
grassPositions.forEach((positions, colorIndex) => {
  const mesh = new THREE.InstancedMesh(grassGeometry, new THREE.MeshBasicMaterial({ color: grassPalette[colorIndex] }), positions.length);
  mesh.name = `voxel-grass-color-${colorIndex}`;
  positions.forEach(([x, y, z], index) => {
    voxelMatrix.makeTranslation(x, y, z);
    mesh.setMatrixAt(index, voxelMatrix);
  });
  mesh.instanceMatrix.needsUpdate = true;
  grassGrid.add(mesh);
});
world.add(grassGrid);

function box(w, h, d, material, x, y, z) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  mesh.position.set(x, y, z);
  world.add(mesh);
  return mesh;
}

const pathCells = [];
for (let index = 0; index < 14; index++) pathCells.push([-5.8 + index * 0.96, -4.0]);
const pathBlocks = new THREE.InstancedMesh(new THREE.BoxGeometry(1.04, 0.22, 1.04), mats.path, pathCells.length);
pathBlocks.name = 'voxel-path-blocks';
pathCells.forEach(([x, z], index) => {
  voxelMatrix.makeTranslation(x, 0.08 + (index % 2) * 0.012, z);
  pathBlocks.setMatrixAt(index, voxelMatrix);
});
pathBlocks.instanceMatrix.needsUpdate = true;
world.add(pathBlocks);
const layout = Object.freeze({
  buildings: Object.freeze({
    farmhouse: Object.freeze({ minX: -10.65, maxX: -6.4, minZ: -8.4, maxZ: -4.0 }),
    windmill: Object.freeze({ minX: 7.25, maxX: 10.45, minZ: -4.2, maxZ: -0.2 }),
  }),
  paths: Object.freeze([
    Object.freeze({ minX: -6.32, maxX: 7.2, minZ: -4.52, maxZ: -3.48 }),
  ]),
  field: Object.freeze({ minX: -3.09, maxX: 6.09, minZ: -1.91, maxZ: 5.71 }),
});
const waterCells = [];
for (let z = 4; z <= 7; z++) for (let x = -10; x <= -6; x++) if (!((x === -10 || x === -6) && (z === 4 || z === 7))) waterCells.push([x, z]);
const voxelPond = new THREE.InstancedMesh(new THREE.BoxGeometry(1.02, 0.12, 1.02), mats.water, waterCells.length);
voxelPond.name = 'voxel-pond';
waterCells.forEach(([x, z], index) => {
  voxelMatrix.makeTranslation(x, 0.05, z);
  voxelPond.setMatrixAt(index, voxelMatrix);
});
voxelPond.instanceMatrix.needsUpdate = true;
world.add(voxelPond);

const tileGroups = [];
const tileHitMeshes = [];
const FIELD_COLS = 6;
const FIELD_ROWS = 5;
const TILE = 1.55;
const FIELD_X = 1.5;
const FIELD_Z = 1.9;
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
    leaf.rotation.z = (i - 1) * 0.55;
    leaf.rotation.y = i * 2.094;
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
    crop.add(root);
    addLeaves(crop, 0.55, 0.7);
  } else {
    const fruit = new THREE.Mesh(geometries.pumpkin, mats.pumpkin);
    fruit.position.y = 0.27;
    crop.add(fruit);
    const stem = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.2, 0.08), mats.leaf);
    stem.position.y = 0.5;
    crop.add(stem);
  }
  crop.scale.setScalar(scale);
  if (tile.ready) {
    const glow = new THREE.Mesh(new THREE.RingGeometry(0.34, 0.43, 4), new THREE.MeshBasicMaterial({ color: 0xffe36e, transparent: true, opacity: 0.9, side: THREE.DoubleSide }));
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
windmill.position.set(8.8, 0, -2.25);
const tower = new THREE.Mesh(new THREE.BoxGeometry(2.4, 3.5, 2.35), mats.cream);
tower.position.y = 1.75;
windmill.add(tower);
const roof = new THREE.Mesh(new THREE.BoxGeometry(2.75, 0.72, 2.7), mats.red);
roof.position.y = 3.86;
windmill.add(roof);
const millDoor = new THREE.Mesh(new THREE.BoxGeometry(0.72, 1.25, 0.16), mats.wood);
millDoor.position.set(-0.48, 0.7, 1.24);
windmill.add(millDoor);
const millWindow = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.58, 0.17), new THREE.MeshLambertMaterial({ color: 0x32cbd8 }));
millWindow.position.set(0.52, 2.1, 1.25);
windmill.add(millWindow);
const hub = new THREE.Group();
hub.position.set(0, 2.95, 1.35);
hub.rotation.y = Math.PI;
const hubCap = new THREE.Mesh(new THREE.BoxGeometry(0.58, 0.58, 0.32), new THREE.MeshLambertMaterial({ color: 0xffc83d }));
hub.add(hubCap);
for (let i = 0; i < 4; i++) {
  const sail = new THREE.Mesh(new THREE.BoxGeometry(0.34, 2.25, 0.16), i % 2 ? mats.wood : mats.red);
  sail.position.y = 1.02;
  const arm = new THREE.Group();
  arm.rotation.z = i * Math.PI / 2;
  arm.add(sail);
  hub.add(arm);
}
windmill.add(hub);
world.add(windmill);

const farmerRoot = new THREE.Group();
farmerRoot.name = 'farmer-avatar';
farmerRoot.position.set(-1.5, 0.1, -3.8);
farmerRoot.rotation.y = Math.PI;
world.add(farmerRoot);
const hatBrimGeometry = new THREE.BoxGeometry(0.82, 0.09, 0.72);
const hatCrownGeometry = new THREE.BoxGeometry(0.48, 0.25, 0.46);
hatCrownGeometry.translate(0, 0.16, 0);
const strawHat = new THREE.Mesh(mergeGeometries([hatBrimGeometry, hatCrownGeometry]), new THREE.MeshLambertMaterial({ color: 0xffc83d, flatShading: true }));
strawHat.name = 'straw-hat';
hatBrimGeometry.dispose();
hatCrownGeometry.dispose();
strawHat.position.y = 1.67;
farmerRoot.add(strawHat);
let farmerModel = null;
let mixer = null;
let idleAction = null;
let walkAction = null;
let interactAction = null;
let voxelLegLeft = null;
let voxelLegRight = null;
let voxelArmLeft = null;
let voxelArmRight = null;
let voxelWalkPhase = 0;
const assets = { farmer: false, farmhouse: false, scenery: false, treeCount: 0 };

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

const loader = new GLTFLoader();
const voxel = name => `./assets/voxel/${name}.glb`;
const staticArt = new THREE.Group();
world.add(staticArt);

function voxelMaterials(root) {
  root.traverse(node => {
    if (!node.isMesh) return;
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of materials) {
      if (material.map) {
        material.map.magFilter = THREE.LinearFilter;
        material.map.minFilter = THREE.LinearMipmapLinearFilter;
        material.map.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
        material.map.colorSpace = THREE.SRGBColorSpace;
      }
      material.roughness = 1;
    }
  });
  return root;
}

function placeModel(source, height, x, z, rotation = 0, y = 0) {
  const model = normalizedModel(voxelMaterials(source.clone()), height);
  model.position.set(x, y, z);
  model.rotation.y = rotation;
  staticArt.add(model);
  return model;
}

function flattenStaticModel(root) {
  root.updateMatrixWorld(true);
  const buckets = new Map();
  root.traverse(node => {
    if (!node.isMesh || node.isSkinnedMesh || Array.isArray(node.material)) return;
    const geometry = node.geometry.clone();
    geometry.applyMatrix4(node.matrixWorld);
    const key = node.material.uuid;
    if (!buckets.has(key)) buckets.set(key, { material: node.material, geometries: [] });
    buckets.get(key).geometries.push(geometry);
  });
  const flattened = new THREE.Group();
  for (const { material, geometries } of buckets.values()) {
    const merged = mergeGeometries(geometries, false);
    if (merged) flattened.add(new THREE.Mesh(merged, material));
    geometries.forEach(geometry => geometry.dispose());
  }
  return flattened;
}

async function loadVoxelFarm() {
  try {
    const [character, houseArt, fenceArt, treeLargeArt, treeSmallArt, planterArt] = await Promise.all([
      loader.loadAsync(voxel('character-a')),
      loader.loadAsync(voxel('building-type-n')),
      loader.loadAsync(voxel('fence-1x4')),
      loader.loadAsync(voxel('tree-large')),
      loader.loadAsync(voxel('tree-small')),
      loader.loadAsync(voxel('planter')),
    ]);

    farmerModel = normalizedModel(voxelMaterials(character.scene), 1.82);
    farmerRoot.add(farmerModel);
    farmerRoot.updateMatrixWorld(true);
    const farmerHead = farmerModel.getObjectByName('head');
    if (farmerHead) farmerHead.attach(strawHat);
    voxelLegLeft = farmerModel.getObjectByName('leg-left');
    voxelLegRight = farmerModel.getObjectByName('leg-right');
    voxelArmLeft = farmerModel.getObjectByName('arm-left');
    voxelArmRight = farmerModel.getObjectByName('arm-right');
    mixer = new THREE.AnimationMixer(farmerModel);
    const findClip = names => character.animations.find(clip => names.includes(clip.name.toLowerCase()));
    const idle = findClip(['idle', 'static']);
    const walk = findClip(['walk', 'sprint']);
    const interact = findClip(['interact-right', 'interact-left', 'pick-up']);
    if (idle) idleAction = mixer.clipAction(idle).play();
    if (walk) walkAction = mixer.clipAction(walk);
    if (interact) {
      interactAction = mixer.clipAction(interact);
      interactAction.setLoop(THREE.LoopOnce, 1);
      interactAction.clampWhenFinished = true;
    }
    const hoe = new THREE.Group();
    const hoeHandle = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.86, 0.09), mats.wood);
    const hoeHead = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.13, 0.14), new THREE.MeshLambertMaterial({ color: 0x495a78 }));
    hoeHead.position.y = 0.42;
    hoe.add(hoeHandle, hoeHead);
    hoe.position.set(0.45, 0.7, 0.02);
    hoe.rotation.z = -0.58;
    farmerRoot.add(hoe);
    assets.farmer = true;

    const house = normalizedModel(voxelMaterials(houseArt.scene), 4.25);
    house.position.set(-8.5, 0.02, -6.2);
    house.rotation.y = Math.PI * 0.12;
    staticArt.add(house);
    assets.farmhouse = true;

    const scenery = [
      [treeLargeArt.scene, 3.8, -12.8, -7.2, 0.2], [treeSmallArt.scene, 2.6, -11.8, -3.7, -0.3],
      [treeLargeArt.scene, 4.2, -12.1, 0.5, 0.5], [treeSmallArt.scene, 2.7, -12.8, 4.2, 0.1],
      [treeLargeArt.scene, 4.0, -12.2, 9.0, -0.4], [treeSmallArt.scene, 2.8, 12.4, -7.3, 0.25],
      [treeLargeArt.scene, 4.1, 12.5, -3.5, -0.2], [treeSmallArt.scene, 2.7, 12.1, 1.1, 0.45],
      [treeLargeArt.scene, 3.9, 12.6, 6.7, -0.35], [planterArt.scene, 0.65, -5.35, 0.9, 0],
      [treeLargeArt.scene, 3.7, -8.7, -8.9, 0.15], [treeSmallArt.scene, 2.6, -5.7, -9.5, -0.2],
      [treeLargeArt.scene, 3.9, -2.6, -9.8, 0.35], [treeSmallArt.scene, 2.7, 1.0, -10.2, -0.4],
      [treeLargeArt.scene, 4.0, 4.8, -9.7, 0.1], [treeSmallArt.scene, 2.8, 8.7, -9.1, -0.25],
      [treeLargeArt.scene, 4.4, -16.8, -11.8, 0.1], [treeSmallArt.scene, 3.0, -13.8, -13.2, -0.2],
      [treeLargeArt.scene, 4.2, -10.4, -13.6, 0.4], [treeSmallArt.scene, 2.9, -7.0, -13.9, -0.1],
      [treeLargeArt.scene, 4.5, -3.8, -14.2, 0.25], [treeSmallArt.scene, 3.0, -0.4, -14.4, -0.35],
      [treeLargeArt.scene, 4.3, 3.1, -14.0, 0.15], [treeSmallArt.scene, 2.9, 6.4, -13.6, -0.2],
      [treeLargeArt.scene, 4.5, 10.0, -13.0, 0.35], [treeSmallArt.scene, 3.0, 14.2, -11.8, -0.1],
      [treeLargeArt.scene, 4.2, -16.7, -6.6, 0.2], [treeSmallArt.scene, 2.8, -17.3, -1.6, -0.3],
      [treeLargeArt.scene, 4.4, -17.0, 4.0, 0.4], [treeSmallArt.scene, 3.0, -16.2, 9.0, -0.1],
      [treeLargeArt.scene, 4.3, 16.8, -6.0, 0.15], [treeSmallArt.scene, 2.9, 17.2, 2.8, -0.25],
    ];
    assets.treeCount = scenery.filter(([model]) => model === treeLargeArt.scene || model === treeSmallArt.scene).length;
    for (const [model, height, x, z, rotation] of scenery) placeModel(model, height, x, z, rotation, 0.02);
    for (const x of [-9.0, -7.6, -6.2]) placeModel(fenceArt.scene, 0.62, x, 2.0, 0);
    for (const z of [-1.5, 0.0]) placeModel(fenceArt.scene, 0.62, -9.7, z, Math.PI / 2);


    const flattenedScenery = flattenStaticModel(staticArt);
    world.remove(staticArt);
    world.add(flattenedScenery);
    assets.scenery = true;
    updateDebug();
  } catch (error) {
    window.__errors.push(`Voxel asset: ${error.message || error}`);
  }
}
loadVoxelFarm();

function updateWindmill() {
  tower.material = mats.cream;
  roof.visible = true;
  hub.visible = true;
  hub.children.forEach(part => { part.visible = true; });
  windmill.scale.setScalar(1);
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
  const rainy = weatherForDay(farm.day) === 'RAIN';
  ui.day.textContent = farm.day;
  ui.weather.textContent = weatherForDay(farm.day);
  ui.coins.textContent = farm.coins;
  ui.energy.textContent = farm.energy;
  ui['max-energy'].textContent = farm.maxEnergy;
  ui['turnip-count'].textContent = farm.seeds.turnip;
  ui['carrot-count'].textContent = farm.seeds.carrot;
  ui['pumpkin-count'].textContent = farm.seeds.pumpkin;
  ui['ready-count'].textContent = farm.tiles.filter(tile => tile.ready).length;
  rainVisuals.visible = rainy;
  scene.background.set(rainy ? 0x678fb5 : 0x8fdcff);
  skyLight.intensity = rainy ? 0.68 : 0.9;
  sun.intensity = rainy ? 0.72 : 1.18;
  const order = farm.order;
  ui['order-text'].textContent = `${order.count} ${CROPS[order.crop].name.toLowerCase()}s → ${order.reward} coins`;
  ui['buy-turnip'].textContent = 'TURNIP SEED · 8';
  ui['buy-carrot'].textContent = farm.day >= 2 ? 'BUY CARROT · 14' : 'CARROT · DAY 2';
  ui['buy-pumpkin'].textContent = farm.day >= 4 ? 'BUY PUMPKIN · 24' : 'PUMPKIN · DAY 4';
  ui['buy-energy'].textContent = farm.maxEnergy >= 20 ? 'MAX ENERGY · 20' : '+1 MAX ENERGY · 80';
  ui['buy-energy'].disabled = farm.maxEnergy >= 20;
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

function performAction(index, selectedAction = selectedTool) {
  const tool = ['turnip', 'carrot', 'pumpkin'].includes(selectedAction) ? 'seed' : selectedAction;
  const crop = tool === 'seed' ? selectedAction : null;
  const result = farm.act(index, tool, crop, { rainy: weatherForDay(farm.day) === 'RAIN' });
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
  if (state !== 'PLAYING' || transitioning || queuedIndex !== null) return;
  selectedIndex = clamp(index, 0, farm.tiles.length - 1);
  queuedIndex = selectedIndex;
  queuedTool = selectedTool;
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

const tutorialSteps = [
  ['HOE YOUR FIRST PLOT', 'Select HOE, then tap the glowing field plot.'],
  ['PLANT A SEED', 'Choose TURNIP and tap the freshly tilled soil.'],
  ['WATER THE CROP', 'Choose WATER and tap the planted crop before sleeping.'],
  ['REST FOR THE NIGHT', 'Use SLEEP / NEXT DAY to grow every watered crop.'],
  ['HARVEST AND SELL', 'Choose HARVEST, pick the mature crop, then sell your basket.'],
];
let tutorialIndex = 0;
let guideReturnState = 'MENU';

function showTutorial(index = 0) {
  tutorialIndex = clamp(index, 0, tutorialSteps.length - 1);
  ui['tutorial-progress'].textContent = `FIRST HARVEST · ${tutorialIndex + 1}/${tutorialSteps.length}`;
  ui['tutorial-title'].textContent = tutorialSteps[tutorialIndex][0];
  ui['tutorial-copy'].textContent = tutorialSteps[tutorialIndex][1];
  ui.tutorial.classList.remove('hidden');
}

function hideTutorial() {
  ui.tutorial.classList.add('hidden');
}

function resetInteractionState() {
  queuedIndex = null;
  queuedTool = null;
  selectedIndex = 0;
  selectedTool = 'hoe';
  farmerRoot.position.set(-1.5, 0.1, -3.8);
  farmerRoot.rotation.set(0, Math.PI, 0);
  messageTimer = 0;
  ui.message.classList.remove('show');
  setAnimation('idle');
}

function endDay() {
  if (state !== 'PLAYING' || transitioning) return { ok: false };
  transitioning = true;
  queuedIndex = null;
  queuedTool = null;
  setAnimation('idle');
  const before = farm.day;
  const result = farm.endDay();
  applyRain();
  save();
  updateHud();
  sound('coin');
  const weatherCopy = `DAY ${farm.day} IS ${weatherForDay(farm.day)}.`;
  const rotCopy = result.rotted
    ? `${result.rotted} CROP${result.rotted === 1 ? '' : 'S'} ROTTED${result.dryRotted ? ` · ${result.dryRotted} LEFT DRY FOR 2 DAYS` : ' · HARVEST WINDOW EXPIRED'}`
    : weatherCopy;
  ui['night-transition-copy'].textContent = rotCopy;
  ui['night-transition'].classList.add('show');
  setTimeout(() => {
    ui['night-transition'].classList.remove('show');
    transitioning = false;
    toast(result.rotted ? `ROT: ${result.rotted} crop${result.rotted === 1 ? '' : 's'} returned to tilled soil.` : `Day ${before} complete. ${weatherCopy}`, result.rotted === 0);
    updateDebug();
  }, 900);
  return { ok: true, ...result };
}

for (const button of document.querySelectorAll('.tool')) button.addEventListener('click', () => {
  if (transitioning) return;
  unlockAudio();
  selectTool(button.dataset.tool);
});
ui.start.addEventListener('click', startGame);
ui['new-game'].addEventListener('click', () => {
  unlockAudio();
  resetInteractionState();
  farm = new FarmModel();
  save();
  startGame();
  showTutorial(0);
});
ui['tutorial-next'].addEventListener('click', () => {
  if (tutorialIndex >= tutorialSteps.length - 1) hideTutorial();
  else showTutorial(tutorialIndex + 1);
});
ui['tutorial-skip'].addEventListener('click', hideTutorial);
ui['guide-open'].addEventListener('click', () => {
  guideReturnState = state;
  hideTutorial();
  changeState('GUIDE');
  ui['field-guide'].classList.remove('hidden');
});
ui['guide-close'].addEventListener('click', () => {
  ui['field-guide'].classList.add('hidden');
  changeState(guideReturnState);
});
ui['pause-toggle'].addEventListener('click', () => changeState('PAUSED'));
ui.resume.addEventListener('click', () => changeState('PLAYING'));
for (const button of document.querySelectorAll('.menu-return')) button.addEventListener('click', () => changeState('MENU'));
ui['end-day'].addEventListener('click', () => { if (state === 'PLAYING') endDay(); });
ui['sell-all'].addEventListener('click', () => {
  if (state !== 'PLAYING' || transitioning) return;
  unlockAudio();
  const result = farm.sellAll();
  if (result.ok) { sound('coin'); toast(`Sold ${result.items} crops for ${result.coins} coins.`, true); save(); }
  else toast(result.reason);
  updateHud();
});
ui['deliver-order'].addEventListener('click', () => {
  if (state !== 'PLAYING' || transitioning) return;
  unlockAudio();
  const result = farm.deliverOrder();
  if (result.ok) { sound('coin'); toast(`Order delivered! +${result.reward} coins.`, true); save(); }
  else toast(result.reason);
  updateHud();
});
ui['buy-energy'].addEventListener('click', () => {
  if (state !== 'PLAYING' || transitioning) return;
  unlockAudio();
  const result = farm.buyEnergyUpgrade();
  if (result.ok) { sound('coin'); toast(`Maximum energy increased to ${result.maxEnergy}!`, true); save(); }
  else toast(result.reason);
  updateHud();
});
for (const crop of Object.keys(CROPS)) {
  ui[`buy-${crop}`].addEventListener('click', () => {
    if (state !== 'PLAYING' || transitioning) return;
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
  if (transitioning) return;
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
  renderer.setSize(Math.max(1, Math.round(width * RENDER_SCALE)), Math.max(1, Math.round(height * RENDER_SCALE)), false);
  const aspect = width / Math.max(height, 1);
  const viewHeight = width < 700 ? 22 : 20;
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
    get transitioning() { return transitioning; },
    assets,
    windmillBlades: hub.children.length - 1,
    aesthetic: VOXEL_WORLD ? 'voxel-farm' : 'default',
    renderScale: RENDER_SCALE,
    layout,
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
    if (rainVisuals.visible) {
      for (let index = 0; index < rainState.length; index++) {
        const drop = rainState[index];
        drop.y -= dt * 10.5;
        if (drop.y < 0.35) drop.y += 11.5;
        voxelMatrix.makeRotationZ(-0.16);
        voxelMatrix.setPosition(drop.x, drop.y, drop.z);
        rainVisuals.setMatrixAt(index, voxelMatrix);
      }
      rainVisuals.instanceMatrix.needsUpdate = true;
    }
    if (mixer) mixer.update(dt);
    if (queuedIndex !== null) {
      const destination = tileGroups[queuedIndex].position;
      const dx = destination.x - farmerRoot.position.x;
      const dz = destination.z - farmerRoot.position.z;
      const distance = Math.hypot(dx, dz);
      if (distance < 0.18) {
        farmerRoot.position.set(destination.x, 0.1, destination.z - 0.46);
        const actionIndex = queuedIndex;
        const actionTool = queuedTool;
        queuedIndex = null;
        queuedTool = null;
        setAnimation('idle');
        performAction(actionIndex, actionTool);
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
    if (voxelLegLeft && voxelLegRight && voxelArmLeft && voxelArmRight) {
      const walking = queuedIndex !== null;
      voxelWalkPhase += dt * (walking ? 11 : 2);
      const stride = Math.sin(voxelWalkPhase) * (walking ? 0.72 : 0.035);
      voxelLegLeft.rotation.x = stride;
      voxelLegRight.rotation.x = -stride;
      voxelArmLeft.rotation.x = -stride * 0.75;
      voxelArmRight.rotation.x = stride * 0.75;
      farmerModel.position.y = walking ? Math.abs(Math.sin(voxelWalkPhase * 2)) * 0.055 : 0;
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
