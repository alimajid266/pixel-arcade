import { PROTOCOLS } from './config.js';
import { penaltyFor } from './rules.mjs';

export class UI {
  constructor() {
    for (const id of [
      'instruction', 'subtext', 'response-hint', 'speaker-indicator', 'signal',
      'system-status', 'phase-label', 'time', 'mistakes', 'integrity',
      'integrity-bar', 'channel', 'trust', 'timer-bar', 'timer-wrap',
      'footer-message', 'status-light', 'panic-status', 'pressure-label'
    ]) {
      this[this.camel(id)] = document.getElementById(id);
    }
    this.flashElement = document.getElementById('flash');
    this.panicButton = document.getElementById('panic-button');
    this.pressureSegments = [...document.querySelectorAll('#pressure-segments span')];
  }

  camel(value) {
    return value.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
  }

  setSpeaker(name, color) {
    this.speakerIndicator.textContent = name;
    this.speakerIndicator.style.color = color;
    this.channel.textContent = name;
    this.channel.style.color = color;
  }

  setSubtext(text) {
    this.subtext.textContent = text;
  }

  presentAuthorization(instruction, revealed) {
    if (!instruction) return;
    const authorized = instruction.authorized !== false;
    this.signal.className = '';
    this.responseHint.className = 'response-hint';

    if (!revealed) {
      this.signal.textContent = 'AUTH: UNCLEAR';
      this.signal.classList.add('auth-unclear');
      this.trust.textContent = 'ORDER STATUS: VERIFY REQUIRED';
      this.responseHint.textContent = 'YOUR INPUT: USE VERIFY OR LEARN THE SOURCE PATTERN';
      this.responseHint.classList.add('caution');
      return;
    }

    if (authorized) {
      this.signal.textContent = 'AUTH: VALID';
      this.signal.classList.add('auth-valid');
      this.trust.textContent = 'ORDER STATUS: BINDING';
      if (instruction.expected?.length === 0) {
        this.responseHint.textContent = instruction.responseHint || 'YOUR INPUT: NOTHING — LET THE TIMER EMPTY';
      } else {
        const direction = instruction.phase >= 4 ? 'YOUR INPUT: EXECUTE THE CRT ORDER' : (instruction.responseHint || 'YOUR INPUT: FOLLOW THE CRT ORDER');
        this.responseHint.textContent = `${direction} · SKIP COST: -${penaltyFor(instruction)}`;
      }
      return;
    }

    this.signal.textContent = 'AUTH: INVALID';
    this.signal.classList.add('auth-invalid');
    this.trust.textContent = 'ORDER STATUS: FORGED — IGNORE';
    this.responseHint.textContent = 'YOUR INPUT: NO INPUT — IGNORE THE FORGED ORDER';
    this.responseHint.classList.add('danger');
  }

  setVerifierState(used) {
    this.panicStatus.textContent = used ? 'USED' : 'READY';
    this.panicButton.classList.toggle('used', used);
  }

  update(state, remaining = 1) {
    this.time.textContent = this.format(state.elapsed);
    this.mistakes.textContent = String(state.displayMistakes).padStart(2, '0');
    this.integrity.textContent = `${Math.round(state.integrity)}%`;
    this.integrityBar.style.width = `${state.integrity}%`;
    this.integrityBar.style.background = state.integrity < 35 ? '#ff493c' : '#83db72';
    const protocol = PROTOCOLS[state.phase - 1];
    this.phaseLabel.textContent = `PROTOCOL 0${state.phase} — ${protocol?.name || 'UNKNOWN'}`;
    this.systemStatus.textContent = state.running ? 'ACTIVE' : 'STANDBY';
    this.timerBar.style.transform = `scaleX(${Math.max(0, remaining)})`;
    this.updatePressure(state, remaining);
  }

  updatePressure(state, remaining) {
    const urgency = state.locked ? 0 : Math.max(0, 1 - remaining);
    const active = Math.max(1, Math.min(8, Math.ceil(state.phase + urgency * 3)));
    this.pressureSegments.forEach((segment, index) => {
      segment.className = '';
      if (index >= active) return;
      segment.classList.add(active >= 7 ? 'hot' : active >= 5 ? 'warn' : 'on');
    });
    this.pressureLabel.textContent = active >= 7 ? 'CRITICAL' : active >= 5 ? 'ELEVATED' : 'NOMINAL';
  }

  format(seconds) {
    return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
  }

  result(text, good) {
    this.subtext.textContent = text;
    this.subtext.className = `subtext ${good ? 'good' : 'bad'}`;
  }

  flash(text) {
    this.flashElement.textContent = text;
    this.flashElement.classList.add('show');
    setTimeout(() => this.flashElement.classList.remove('show'), 1300);
  }

  fakeCrash() {
    this.flashElement.replaceChildren();
    const title = document.createElement('b');
    title.textContent = 'FATAL SIGNAL LOSS';
    const detail = document.createElement('small');
    detail.textContent = 'THIS INCIDENT HAS BEEN REPORTED';
    this.flashElement.append(title, detail);
    this.flashElement.classList.add('show', 'crash');
    setTimeout(() => this.flashElement.classList.remove('show', 'crash'), 1700);
  }
}
