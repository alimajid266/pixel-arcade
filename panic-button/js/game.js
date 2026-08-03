import { StateManager } from './stateManager.js';
import { AudioSystem } from './audio.js';
import { Narrator } from './narrator.js';
import { ButtonBank } from './buttons.js';
import { InstructionManager } from './instructions.js';
import { EventManager } from './events.js';
import { Effects } from './effects.js';
import { UI } from './ui.js';
import { MESSAGES, PROTOCOLS } from './config.js';
import { assessAction, penaltyFor, phaseForRound, timeoutOutcome } from './rules.mjs';

class Game {
  constructor() {
    this.state = new StateManager();
    this.ui = new UI();
    this.audio = new AudioSystem();
    this.machine = document.getElementById('machine');
    this.effects = new Effects(this.machine);
    this.narrator = new Narrator(this.ui, this.audio);
    this.instructions = new InstructionManager();
    this.buttons = new ButtonBank(document.getElementById('button-bank'), this.audio, action => this.action(action));
    this.events = new EventManager(this.machine, this.buttons, this.audio, this.ui);
    this.deadline = 0;
    this.instructionStartedAt = 0;
    this.nextTimer = 0;
    this.nextDueAt = 0;
    this.pausedNextDelay = null;
    this.guidePausedDirective = false;
    this.directiveToken = 0;
    this.activeGestures = new Map();
    this.verifierUsed = false;
    this.authorizationRevealed = true;
    this.guidePausedAt = null;
    this.last = performance.now();
    this.errors = [];

    window.addEventListener('error', event => this.errors.push(String(event.error || event.message)));
    window.addEventListener('unhandledrejection', event => this.errors.push(String(event.reason)));
    document.getElementById('start').onclick = () => this.start();
    const guideDialog = document.getElementById('guide-dialog');
    const openGuide = () => {
      if (this.state.running && this.guidePausedAt === null) {
        const now = performance.now();
        this.guidePausedAt = now;
        this.guidePausedDirective = Boolean(this.state.instruction && !this.state.locked);
        if (this.nextTimer) {
          this.pausedNextDelay = Math.max(0, this.nextDueAt - now);
          clearTimeout(this.nextTimer);
          this.nextTimer = 0;
          this.nextDueAt = 0;
        }
      }
      if (!guideDialog.open) guideDialog.showModal();
    };
    guideDialog.addEventListener('close', () => {
      if (this.guidePausedAt === null) return;
      const pausedFor = performance.now() - this.guidePausedAt;
      const resumeDelay = this.pausedNextDelay;
      if (this.guidePausedDirective && this.state.instruction && !this.state.locked) {
        this.deadline += pausedFor;
        this.instructionStartedAt += pausedFor;
      }
      this.guidePausedAt = null;
      this.guidePausedDirective = false;
      this.pausedNextDelay = null;
      if (resumeDelay !== null && this.state.running) this.nextInstruction(resumeDelay);
    });
    document.getElementById('boot-guide').onclick = openGuide;
    document.getElementById('guide-button').onclick = openGuide;
    document.getElementById('audio-toggle').onclick = event => {
      const muted = this.audio.toggle();
      event.currentTarget.textContent = muted ? 'SOUND: MUTED' : 'SOUND: ARMED';
    };
    document.getElementById('panic-button').onclick = () => this.verifyOrder();

    this.effects.start();
    requestAnimationFrame(time => this.loop(time));
  }

  start() {
    clearTimeout(this.nextTimer);
    this.nextTimer = 0;
    this.nextDueAt = 0;
    this.pausedNextDelay = null;
    this.guidePausedDirective = false;
    this.guidePausedAt = null;
    this.events.reset();
    this.narrator.cancel();
    document.getElementById('overlay').classList.add('gone');
    this.audio.start();
    this.state.reset();
    this.directiveToken += 1;
    this.activeGestures.clear();
    this.verifierUsed = false;
    this.authorizationRevealed = true;
    this.ui.setVerifierState(false);
    this.state.running = true;
    this.ui.footerMessage.textContent = 'NO EXTERNAL SIGNAL';
    this.machine.classList.add('powered');
    this.effects.setPhase(1);
    this.nextInstruction(700);
  }

  nextInstruction(delay = 1100) {
    clearTimeout(this.nextTimer);
    this.state.locked = true;
    this.nextDueAt = performance.now() + delay;
    this.nextTimer = setTimeout(() => {
      this.nextTimer = 0;
      this.nextDueAt = 0;
      if (!this.state.running) return;
      this.state.round += 1;
      const phase = phaseForRound(this.state.round);
      if (phase !== this.state.phase) {
        this.state.setPhase(phase);
        this.effects.setPhase(phase);
        this.ui.flash(`PROTOCOL 0${phase} — ${PROTOCOLS[phase - 1].name}`);
      }
      const instruction = this.instructions.create(phase, this.state.round);
      this.directiveToken += 1;
      this.activeGestures.clear();
      this.buttons.enableAll();
      this.state.instruction = instruction;
      this.state.input = [];
      this.state.locked = false;
      this.verifierUsed = false;
      this.authorizationRevealed = instruction.authVisible !== false;
      this.ui.setVerifierState(false);
      this.ui.presentAuthorization(instruction, this.authorizationRevealed);
      this.state.truth = true;
      this.instructionStartedAt = performance.now();
      this.deadline = this.instructionStartedAt + instruction.duration * 1000;
      this.narrator.say(
        instruction.speaker,
        instruction.text,
        instruction.kind === 'delayed' ? 'COUNTDOWN LINK ACTIVE' : 'DIRECTIVE RECEIVED'
      );
      if (phase >= 3) this.buttons.flash(instruction.color);
      this.events.maybe(phase, instruction);
    }, delay);
  }

  verifyOrder() {
    const instruction = this.state.instruction;
    if (!this.state.running || this.state.locked || !instruction || this.guidePausedAt !== null) return;
    if (performance.now() >= this.deadline) {
      this.resolve(timeoutOutcome(instruction), 'timeout');
      return;
    }
    if (this.verifierUsed) {
      this.ui.flash('ORDER CHECK ALREADY USED');
      return;
    }
    this.verifierUsed = true;
    this.authorizationRevealed = true;
    this.deadline += 1200;
    this.audio.beep(instruction.authorized === false ? 145 : 540);
    this.ui.setVerifierState(true);
    this.ui.presentAuthorization(instruction, true);
    this.ui.panicButton.classList.add('revealed');
    setTimeout(() => this.ui.panicButton.classList.remove('revealed'), 900);
    this.ui.flash(instruction.authorized === false ? 'FORGED ORDER — PROVIDE NO INPUT' : 'ORDER VERIFIED — EXECUTE');
  }

  action(action) {
    if (!this.state.running || this.state.locked || this.guidePausedAt !== null) return;
    const instruction = this.state.instruction;
    if (!instruction) return;

    if (!action.gestureId) return;
    if (action.type === 'down') {
      this.activeGestures.set(action.gestureId, this.directiveToken);
      return;
    }
    if (action.type === 'cancel') {
      this.activeGestures.delete(action.gestureId);
      return;
    }

    const gestureToken = this.activeGestures.get(action.gestureId);
    this.activeGestures.delete(action.gestureId);
    if (gestureToken !== this.directiveToken) return;

    const actionTime = Number.isFinite(action.time) ? action.time : performance.now();
    if (action.type !== 'down' && actionTime >= this.deadline) {
      this.resolve(timeoutOutcome(instruction), 'timeout');
      return;
    }
    const outcome = assessAction(
      instruction,
      this.state.input,
      action,
      performance.now() - this.instructionStartedAt
    );
    this.state.input = outcome.inputs;
    if (outcome.status === 'pass') this.resolve(true);
    if (outcome.status === 'fail') this.resolve(false);
  }

  resolve(correct, reason = 'action') {
    if (this.state.locked) return;
    this.state.locked = true;

    if (this.state.instruction?.training && !correct) {
      this.audio.fail();
      this.ui.result('TRAINING INPUT MISSED — NO INTEGRITY LOST — TRY AGAIN', false);
      this.state.round = Math.max(0, this.state.round - 1);
      this.nextInstruction(900);
      return;
    }

    const instruction = this.state.instruction;
    const nominalPenalty = correct ? 0 : penaltyFor(instruction);
    const damage = correct ? 0 : this.state.damage(nominalPenalty);
    if (correct) this.state.heal();
    this.audio[correct ? 'success' : 'fail']();
    this.effects.pulse();

    let message;
    if (correct && instruction?.authorized === false) message = 'FORGED ORDER IGNORED — INTEGRITY STABLE';
    else if (correct && instruction?.expected?.length === 0) message = 'NO INPUT CONFIRMED — DIRECTIVE ACCEPTED';
    else if (correct) message = 'INPUT MATCHED — DIRECTIVE ACCEPTED';
    else if (instruction?.authorized === false) message = `INPUT ON FORGED ORDER — DIRECTIVE FAILED — INTEGRITY -${damage}`;
    else if (instruction?.expected?.length === 0) message = `INPUT DETECTED — REQUIRED NO INPUT — INTEGRITY -${damage}`;
    else if (reason === 'timeout') message = `ORDER SKIPPED — ACTIVE ORDER FAILED — INTEGRITY -${damage}`;
    else message = `INCORRECT INPUT — DIRECTIVE FAILED — INTEGRITY -${damage}`;
    this.ui.result(message, correct);

    if (this.state.phase >= 3 && Math.random() < 0.28) {
      this.ui.footerMessage.textContent = MESSAGES[Math.floor(Math.random() * MESSAGES.length)];
    }
    if (this.state.integrity <= 0) {
      this.end(message);
      return;
    }
    this.nextInstruction(900);
  }

  end(finalResult = '') {
    this.state.running = false;
    clearTimeout(this.nextTimer);
    this.narrator.say('YOU', 'THE SYSTEM IS STILL RUNNING. YOU ARE NOT.', 'SHIFT TERMINATED');
    if (finalResult) this.ui.result(finalResult, false);
    this.ui.fakeCrash();
    setTimeout(() => document.getElementById('overlay').classList.remove('gone'), 2200);
  }

  loop(time) {
    const dt = Math.min(0.05, (time - this.last) / 1000);
    this.last = time;
    if (this.state.running) {
      if (this.guidePausedAt === null) this.state.elapsed += dt;
      if (this.state.instruction && !this.state.locked) {
        const timerTime = this.guidePausedAt ?? time;
        const remaining = (this.deadline - timerTime) / (this.state.instruction.duration * 1000);
        if (this.guidePausedAt === null && remaining <= 0) this.resolve(timeoutOutcome(this.state.instruction), 'timeout');
        this.ui.update(this.state, remaining);
      } else {
        this.ui.update(this.state, 0);
      }
    }
    requestAnimationFrame(next => this.loop(next));
  }

  debug() {
    return {
      ...this.state,
      errors: [...this.errors],
      deadline: this.deadline,
      instructionStartedAt: this.instructionStartedAt
    };
  }
}

window.__game = new Game();
