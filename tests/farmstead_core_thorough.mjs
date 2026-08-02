import assert from 'node:assert/strict';
import { CROPS, ORDERS, FarmModel } from '../farmstead/farm-core.mjs';

let passed = 0;
function test(name, fn) {
  try {
    fn();
    passed += 1;
  } catch (error) {
    error.message = `${name}: ${error.message}`;
    throw error;
  }
}

const unchangedAfter = (farm, action) => {
  const before = farm.snapshot();
  const result = action();
  assert.equal(result.ok, false);
  assert.deepEqual(farm.snapshot(), before);
};

test('fresh farm has complete bounded starting state', () => {
  const farm = new FarmModel();
  assert.deepEqual([farm.day, farm.coins, farm.energy, farm.earnings, farm.orderIndex], [1, 60, 14, 0, 0]);
  assert.deepEqual(farm.seeds, { turnip: 6, carrot: 0, pumpkin: 0 });
  assert.deepEqual(farm.produce, { turnip: 0, carrot: 0, pumpkin: 0 });
  assert.equal(farm.tiles.length, 30);
  assert.ok(farm.tiles.every(tile => tile.state === 'grass' && tile.crop === null && !tile.ready && !tile.watered));
});

test('failed field actions are atomic and spend no energy', () => {
  const farm = new FarmModel();
  unchangedAfter(farm, () => farm.act(-1, 'hoe'));
  unchangedAfter(farm, () => farm.act(30, 'hoe'));
  unchangedAfter(farm, () => farm.act(0, 'water'));
  unchangedAfter(farm, () => farm.act(0, 'harvest'));
  unchangedAfter(farm, () => farm.act(0, 'seed', 'turnip'));
  unchangedAfter(farm, () => farm.act(0, 'shovel'));
});

test('energy reaches zero exactly and blocks further valid work', () => {
  const farm = new FarmModel();
  for (let index = 0; index < 14; index++) assert.equal(farm.act(index, 'hoe').ok, true);
  assert.equal(farm.energy, 0);
  const before = farm.snapshot();
  assert.deepEqual(farm.act(14, 'hoe'), { ok: false, reason: 'Too tired' });
  assert.deepEqual(farm.snapshot(), before);
  farm.endDay();
  assert.equal(farm.energy, 14);
});

test('unwatered crops do not grow and watering resets nightly', () => {
  const farm = new FarmModel();
  farm.act(0, 'hoe');
  farm.act(0, 'seed', 'turnip');
  farm.endDay();
  assert.deepEqual([farm.tiles[0].growth, farm.tiles[0].ready], [0, false]);
  farm.act(0, 'water');
  farm.endDay();
  assert.deepEqual([farm.tiles[0].growth, farm.tiles[0].ready, farm.tiles[0].watered], [1, true, false]);
});

test('every crop requires exactly its configured watered days', () => {
  for (const [crop, config] of Object.entries(CROPS)) {
    const farm = new FarmModel();
    farm.seeds[crop] = 1;
    farm.act(0, 'hoe');
    farm.act(0, 'seed', crop);
    for (let day = 1; day <= config.growDays; day++) {
      assert.equal(farm.act(0, 'water').ok, true);
      farm.endDay();
      assert.equal(farm.tiles[0].growth, day);
      assert.equal(farm.tiles[0].ready, day === config.growDays);
    }
    assert.equal(farm.act(0, 'harvest').ok, true);
    assert.equal(farm.produce[crop], 1);
    assert.equal(farm.tiles[0].state, 'tilled');
  }
});

test('ready crops stop growing but remain harvestable', () => {
  const farm = new FarmModel();
  farm.act(0, 'hoe');
  farm.act(0, 'seed', 'turnip');
  farm.act(0, 'water');
  farm.endDay();
  for (let day = 0; day < 5; day++) farm.endDay();
  assert.deepEqual([farm.tiles[0].growth, farm.tiles[0].ready], [1, true]);
  assert.equal(farm.act(0, 'harvest').ok, true);
});

test('seed purchases enforce unlocks amounts funds and atomicity', () => {
  const farm = new FarmModel();
  unchangedAfter(farm, () => farm.buySeeds('carrot'));
  unchangedAfter(farm, () => farm.buySeeds('pumpkin'));
  unchangedAfter(farm, () => farm.buySeeds('turnip', 0));
  unchangedAfter(farm, () => farm.buySeeds('turnip', 1.5));
  unchangedAfter(farm, () => farm.buySeeds('radish'));
  unchangedAfter(farm, () => farm.buySeeds('turnip', 100));
  farm.day = 4;
  assert.deepEqual(farm.buySeeds('pumpkin', 2), { ok: true, spent: 48 });
  assert.deepEqual([farm.coins, farm.seeds.pumpkin], [12, 2]);
});

test('basket sales total mixed produce exactly once', () => {
  const farm = new FarmModel();
  farm.produce = { turnip: 2, carrot: 3, pumpkin: 1 };
  assert.deepEqual(farm.sellAll(), { ok: true, items: 6, coins: 214 });
  assert.deepEqual([farm.coins, farm.earnings], [274, 214]);
  assert.deepEqual(farm.produce, { turnip: 0, carrot: 0, pumpkin: 0 });
  unchangedAfter(farm, () => farm.sellAll());
});

test('orders reject shortages atomically and cycle after completion', () => {
  const farm = new FarmModel();
  for (let index = 0; index < ORDERS.length * 2; index++) {
    const order = farm.order;
    assert.deepEqual(order, ORDERS[index % ORDERS.length]);
    const before = farm.snapshot();
    assert.equal(farm.deliverOrder().ok, false);
    assert.deepEqual(farm.snapshot(), before);
    farm.produce[order.crop] = order.count;
    const result = farm.deliverOrder();
    assert.equal(result.ok, true);
    assert.equal(farm.produce[order.crop], 0);
  }
  assert.equal(farm.orderIndex, 6);
  assert.equal(farm.earnings, 530);
});

test('snapshot is a deep copy and round trips valid state', () => {
  const farm = new FarmModel();
  farm.act(0, 'hoe');
  farm.act(0, 'seed', 'turnip');
  farm.act(0, 'water');
  const snapshot = farm.snapshot();
  snapshot.tiles[0].state = 'grass';
  snapshot.seeds.turnip = 999;
  assert.equal(farm.tiles[0].state, 'planted');
  assert.equal(farm.seeds.turnip, 5);
  const restored = FarmModel.fromSnapshot(farm.snapshot());
  assert.deepEqual(restored.snapshot(), farm.snapshot());
});

test('snapshot numbers are finite integers and clamped', () => {
  const tiles = Array.from({ length: 30 }, () => ({ state: 'grass' }));
  const farm = FarmModel.fromSnapshot({
    version: 1, day: 2.9, coins: Infinity, energy: -8, earnings: 99999999,
    orderIndex: -2, seeds: { turnip: 4.8, carrot: -1, pumpkin: NaN },
    produce: { turnip: 10000, carrot: 2.9, pumpkin: -4 }, tiles,
  });
  assert.deepEqual([farm.day, farm.coins, farm.energy, farm.earnings, farm.orderIndex], [2, 60, 0, 9999999, 0]);
  assert.deepEqual(farm.seeds, { turnip: 4, carrot: 0, pumpkin: 0 });
  assert.deepEqual(farm.produce, { turnip: 999, carrot: 2, pumpkin: 0 });
});

test('snapshot sanitizes invalid crop and tile combinations', () => {
  const tiles = Array.from({ length: 30 }, () => ({ state: 'grass' }));
  tiles[0] = { state: 'planted', crop: 'radish', growth: 999, watered: true, ready: true };
  tiles[1] = { state: 'tilled', crop: 'pumpkin', growth: 3, watered: true, ready: true };
  tiles[2] = null;
  const farm = FarmModel.fromSnapshot({ version: 1, tiles });
  assert.deepEqual(farm.tiles[0], { state: 'grass', crop: null, growth: 0, watered: false, ready: false });
  assert.deepEqual(farm.tiles[1], { state: 'tilled', crop: null, growth: 0, watered: false, ready: false });
  assert.deepEqual(farm.tiles[2], { state: 'grass', crop: null, growth: 0, watered: false, ready: false });
});

test('unknown save versions and wrong tile counts fall back safely', () => {
  const future = FarmModel.fromSnapshot({ version: 2, day: 99, coins: 999, tiles: Array(30).fill({ state: 'tilled' }) });
  assert.deepEqual([future.day, future.coins, future.tiles[0].state], [1, 60, 'grass']);
  const short = FarmModel.fromSnapshot({ version: 1, day: 8, tiles: [] });
  assert.equal(short.day, 8);
  assert.ok(short.tiles.every(tile => tile.state === 'grass'));
});

test('malformed ready flag cannot bypass crop growth', () => {
  const tiles = Array.from({ length: 30 }, () => ({ state: 'grass' }));
  tiles[0] = { state: 'planted', crop: 'pumpkin', growth: 1, watered: false, ready: true };
  const farm = FarmModel.fromSnapshot({ version: 1, tiles });
  assert.equal(farm.tiles[0].ready, false);
  assert.equal(farm.act(0, 'harvest').ok, false);
});

test('repeatable turnip loop can fund restoration without bankruptcy', () => {
  const farm = new FarmModel();
  assert.equal(farm.act(0, 'hoe').ok, true);
  for (let cycle = 0; cycle < 20; cycle++) {
    if (farm.seeds.turnip === 0) assert.equal(farm.buySeeds('turnip').ok, true);
    assert.equal(farm.act(0, 'seed', 'turnip').ok, true);
    assert.equal(farm.act(0, 'water').ok, true);
    farm.endDay();
    assert.equal(farm.act(0, 'harvest').ok, true);
    assert.equal(farm.sellAll().ok, true);
  }
  assert.equal(farm.earnings, 360);
  assert.ok(farm.coins >= 0);
});

console.log(`FARMSTEAD THOROUGH CORE PASS: ${passed} scenarios`);
