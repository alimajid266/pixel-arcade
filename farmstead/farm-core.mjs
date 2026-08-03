export const CROPS = Object.freeze({
  turnip: Object.freeze({ name: 'Turnip', growDays: 1, seedPrice: 8, sellPrice: 18, color: 0xf4f1e5 }),
  carrot: Object.freeze({ name: 'Carrot', growDays: 2, seedPrice: 14, sellPrice: 36, color: 0xf28c28 }),
  pumpkin: Object.freeze({ name: 'Pumpkin', growDays: 3, seedPrice: 24, sellPrice: 70, color: 0xf26a21 })
});

export const ORDERS = Object.freeze([
  Object.freeze({ crop: 'turnip', count: 3, reward: 35 }),
  Object.freeze({ crop: 'carrot', count: 2, reward: 80 }),
  Object.freeze({ crop: 'pumpkin', count: 2, reward: 150 })
]);

export const STARTING_PLOTS = 20;
export const MAX_PLOTS = 30;
export const PLOT_PRICE = 60;
export const MAX_ENERGY = 25;
export const PLOT_UNLOCK_ORDER = Object.freeze([
  1, 2, 3, 4, 7, 8, 9, 10, 13, 14, 15, 16, 19, 20, 21, 22, 25, 26, 27, 28,
  0, 5, 6, 11, 12, 17, 18, 23, 24, 29
]);

const freshTile = () => ({ state: 'grass', crop: null, growth: 0, watered: false, ready: false, readyDays: 0, dryDays: 0 });
const boundedInt = (value, fallback, min, max) => Number.isFinite(value)
  ? Math.max(min, Math.min(max, Math.floor(value)))
  : fallback;

export class FarmModel {
  constructor() {
    this.day = 1;
    this.coins = 60;
    this.maxEnergy = 14;
    this.energy = 14;
    this.seeds = { turnip: 6, carrot: 0, pumpkin: 0 };
    this.produce = { turnip: 0, carrot: 0, pumpkin: 0 };
    this.earnings = 0;
    this.orderIndex = 0;
    this.unlockedPlots = STARTING_PLOTS;
    this.tiles = Array.from({ length: 30 }, freshTile);
  }

  act(index, tool, crop = null, context = {}) {
    const tile = this.tiles[index];
    if (!tile) return { ok: false, reason: 'Outside the field' };
    if (!this.isPlotUnlocked(index)) return { ok: false, reason: 'Buy this plot first' };
    if (this.energy <= 0) return { ok: false, reason: 'Too tired' };

    if (tool === 'hoe') {
      if (tile.state !== 'grass') return { ok: false, reason: 'Already tilled' };
      tile.state = 'tilled';
    } else if (tool === 'seed') {
      if (tile.state === 'planted') return { ok: false, reason: 'Plot is occupied' };
      if (tile.state !== 'tilled') return { ok: false, reason: 'Plow the soil first' };
      if (!CROPS[crop]) return { ok: false, reason: 'Choose a seed' };
      if ((this.seeds[crop] || 0) <= 0) return { ok: false, reason: 'No seeds left' };
      tile.state = 'planted';
      tile.crop = crop;
      tile.growth = 0;
      tile.ready = false;
      tile.readyDays = 0;
      tile.dryDays = 0;
      tile.watered = context.rainy === true;
      this.seeds[crop] -= 1;
    } else if (tool === 'water') {
      if (tile.state !== 'planted') return { ok: false, reason: 'Nothing planted here' };
      if (tile.watered) return { ok: false, reason: 'Already watered' };
      tile.watered = true;
    } else if (tool === 'harvest') {
      if (tile.state !== 'planted' || !tile.ready) return { ok: false, reason: 'Not ready to harvest' };
      this.produce[tile.crop] += 1;
      Object.assign(tile, { state: 'tilled', crop: null, growth: 0, watered: false, ready: false, readyDays: 0, dryDays: 0 });
    } else {
      return { ok: false, reason: 'Choose a tool' };
    }

    this.energy -= 1;
    return { ok: true };
  }

  endDay() {
    let rotted = 0;
    let dryRotted = 0;
    for (const tile of this.tiles) {
      if (tile.state === 'planted' && tile.ready) {
        tile.readyDays += 1;
        if (tile.readyDays >= 2) {
          Object.assign(tile, { state: 'tilled', crop: null, growth: 0, watered: false, ready: false, readyDays: 0, dryDays: 0 });
          rotted += 1;
          continue;
        }
      } else if (tile.state === 'planted' && tile.watered) {
        tile.growth += 1;
        tile.dryDays = 0;
        tile.ready = tile.growth >= CROPS[tile.crop].growDays;
        if (tile.ready) tile.readyDays = 0;
      } else if (tile.state === 'planted') {
        tile.dryDays += 1;
        if (tile.dryDays >= 2) {
          Object.assign(tile, { state: 'tilled', crop: null, growth: 0, watered: false, ready: false, readyDays: 0, dryDays: 0 });
          rotted += 1;
          dryRotted += 1;
          continue;
        }
      }
      tile.watered = false;
    }
    this.day += 1;
    this.energy = this.maxEnergy;
    return { day: this.day, rotted, dryRotted };
  }

  buySeeds(crop, amount = 1) {
    const config = CROPS[crop];
    const unlockDay = { turnip: 1, carrot: 2, pumpkin: 4 }[crop];
    if (!config || this.day < unlockDay) return { ok: false, reason: 'Seed is locked' };
    if (!Number.isInteger(amount) || amount < 1) return { ok: false, reason: 'Invalid amount' };
    const spent = config.seedPrice * amount;
    if (this.coins < spent) return { ok: false, reason: 'Not enough coins' };
    this.coins -= spent;
    this.seeds[crop] += amount;
    return { ok: true, spent };
  }

  buyEnergyUpgrade() {
    if (this.maxEnergy >= MAX_ENERGY) return { ok: false, reason: 'Energy is maxed' };
    if (this.coins < 80) return { ok: false, reason: 'Not enough coins' };
    this.coins -= 80;
    this.maxEnergy += 1;
    this.energy = Math.min(this.maxEnergy, this.energy + 1);
    return { ok: true, spent: 80, maxEnergy: this.maxEnergy };
  }

  buyPlot() {
    if (this.unlockedPlots >= MAX_PLOTS) return { ok: false, reason: 'All plots unlocked' };
    if (this.coins < PLOT_PRICE) return { ok: false, reason: 'Not enough coins' };
    const plotIndex = PLOT_UNLOCK_ORDER[this.unlockedPlots];
    this.coins -= PLOT_PRICE;
    this.unlockedPlots += 1;
    return { ok: true, spent: PLOT_PRICE, unlockedPlots: this.unlockedPlots, plotIndex };
  }

  isPlotUnlocked(index) {
    const orderIndex = PLOT_UNLOCK_ORDER.indexOf(index);
    return orderIndex >= 0 && orderIndex < this.unlockedPlots;
  }

  sellAll() {
    let items = 0;
    let coins = 0;
    for (const [crop, count] of Object.entries(this.produce)) {
      items += count;
      coins += count * CROPS[crop].sellPrice;
      this.produce[crop] = 0;
    }
    if (!items) return { ok: false, reason: 'Basket is empty' };
    this.coins += coins;
    this.earnings += coins;
    return { ok: true, items, coins };
  }

  get order() {
    return { ...ORDERS[this.orderIndex % ORDERS.length] };
  }

  deliverOrder() {
    const order = this.order;
    if (this.produce[order.crop] < order.count) {
      return { ok: false, reason: `Need ${order.count} ${CROPS[order.crop].name.toLowerCase()}s` };
    }
    this.produce[order.crop] -= order.count;
    this.coins += order.reward;
    this.earnings += order.reward;
    this.orderIndex += 1;
    return { ok: true, reward: order.reward, crop: order.crop, count: order.count };
  }

  snapshot() {
    return {
      version: 2,
      day: this.day,
      coins: this.coins,
      maxEnergy: this.maxEnergy,
      energy: this.energy,
      seeds: { ...this.seeds },
      produce: { ...this.produce },
      earnings: this.earnings,
      orderIndex: this.orderIndex,
      unlockedPlots: this.unlockedPlots,
      tiles: this.tiles.map(tile => ({ ...tile }))
    };
  }

  static fromSnapshot(raw) {
    const farm = new FarmModel();
    if (!raw || typeof raw !== 'object' || ![1, 2].includes(raw.version)) return farm;
    farm.day = boundedInt(raw.day, farm.day, 1, 9999);
    farm.coins = boundedInt(raw.coins, farm.coins, 0, 999999);
    farm.maxEnergy = boundedInt(raw.maxEnergy, farm.maxEnergy, 14, MAX_ENERGY);
    farm.energy = boundedInt(raw.energy, farm.energy, 0, farm.maxEnergy);
    farm.earnings = boundedInt(raw.earnings, farm.earnings, 0, 9999999);
    farm.orderIndex = boundedInt(raw.orderIndex, farm.orderIndex, 0, 9999);
    farm.unlockedPlots = raw.version === 1
      ? MAX_PLOTS
      : boundedInt(raw.unlockedPlots, farm.unlockedPlots, STARTING_PLOTS, MAX_PLOTS);
    for (const crop of Object.keys(CROPS)) {
      farm.seeds[crop] = boundedInt(raw.seeds?.[crop], farm.seeds[crop], 0, 999);
      farm.produce[crop] = boundedInt(raw.produce?.[crop], farm.produce[crop], 0, 999);
    }
    if (Array.isArray(raw.tiles) && raw.tiles.length === farm.tiles.length) {
      farm.tiles = raw.tiles.map(source => {
        const tile = freshTile();
        if (!source || typeof source !== 'object') return tile;
        const crop = Object.hasOwn(CROPS, source.crop) ? source.crop : null;
        if (source.state === 'tilled') tile.state = 'tilled';
        if (source.state === 'planted' && crop) {
          tile.state = 'planted';
          tile.crop = crop;
          tile.growth = boundedInt(source.growth, 0, 0, CROPS[crop].growDays);
          tile.watered = source.watered === true;
          tile.ready = tile.growth >= CROPS[crop].growDays;
          tile.readyDays = tile.ready ? boundedInt(source.readyDays, 0, 0, 1) : 0;
          tile.dryDays = tile.ready ? 0 : boundedInt(source.dryDays, 0, 0, 1);
        }
        return tile;
      });
    }
    return farm;
  }
}
