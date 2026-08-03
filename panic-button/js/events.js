import { disableCandidates } from './rules.mjs';

export class EventManager {
  constructor(machine, buttons, audio, ui) {
    this.machine = machine;
    this.buttons = buttons;
    this.audio = audio;
    this.ui = ui;
    this.timers = new Set();
  }

  schedule(callback, delay) {
    const timer = setTimeout(() => {
      this.timers.delete(timer);
      callback();
    }, delay);
    this.timers.add(timer);
  }

  maybe(phase, instruction) {
    if (phase < 2 || Math.random() > 0.43) return;
    const pool = ['flicker', 'alarm', 'timer', 'corrupt'];
    if (phase >= 4) pool.push('shuffle', 'labels', 'disabled', 'shake');
    if (phase >= 5) pool.push('crash', 'silence');
    this.trigger(pool[Math.floor(Math.random() * pool.length)], instruction);
  }

  trigger(type, instruction = { expected: [] }) {
    if (type === 'flicker') {
      this.machine.classList.add('flicker');
      this.schedule(() => this.machine.classList.remove('flicker'), 500);
    }
    if (type === 'alarm') {
      this.ui.flash('SYSTEM ALARM — PANEL LIGHTS UNRELIABLE');
      this.audio.fail();
    }
    if (type === 'timer') {
      this.ui.timerWrap.classList.add('hidden-timer');
      this.schedule(() => this.ui.timerWrap.classList.remove('hidden-timer'), 1800);
    }
    if (type === 'corrupt') {
      this.machine.classList.add('glitching');
      this.audio.glitch();
      this.schedule(() => this.machine.classList.remove('glitching'), 600);
    }
    if (type === 'shuffle') this.buttons.shuffle();
    if (type === 'labels') {
      this.buttons.swapLabels();
      this.schedule(() => this.buttons.restoreLabels(), 2400);
    }
    if (type === 'disabled') {
      const candidates = disableCandidates(instruction);
      if (candidates.length) this.buttons.disable(candidates[Math.floor(Math.random() * candidates.length)]);
    }
    if (type === 'shake') {
      this.machine.classList.add('shake');
      this.schedule(() => this.machine.classList.remove('shake'), 500);
    }
    if (type === 'crash') this.ui.fakeCrash();
    if (type === 'silence' && this.audio.master) {
      this.audio.master.gain.value = 0;
      this.schedule(() => {
        if (this.audio.master) this.audio.master.gain.value = this.audio.muted ? 0 : 0.2;
      }, 2200);
    }
  }

  reset() {
    for (const timer of this.timers) clearTimeout(timer);
    this.timers.clear();
    this.machine.classList.remove('flicker', 'glitching', 'shake');
    this.ui.timerWrap.classList.remove('hidden-timer');
    this.ui.flashElement.classList.remove('show', 'crash');
    this.buttons.reset();
    if (this.audio.master) this.audio.master.gain.value = this.audio.muted ? 0 : 0.2;
  }
}
