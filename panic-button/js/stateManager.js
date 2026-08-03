export class StateManager {
  constructor() {
    this.reset();
  }

  reset() {
    this.running = false;
    this.phase = 1;
    this.round = 0;
    this.actualMistakes = 0;
    this.displayMistakes = 0;
    this.integrity = 100;
    this.elapsed = 0;
    this.instruction = null;
    this.input = [];
    this.locked = false;
    this.truth = true;
    this.lastResult = '';
  }

  setPhase(phase) {
    this.phase = Math.max(1, Math.min(5, phase));
  }

  damage(amount = 8) {
    const before = this.integrity;
    this.actualMistakes += 1;
    this.displayMistakes = this.actualMistakes;
    this.integrity = Math.max(0, this.integrity - amount);
    return before - this.integrity;
  }

  heal(amount = 1) {
    this.integrity = Math.min(100, this.integrity + amount);
  }
}
