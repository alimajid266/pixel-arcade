import { COLORS, PHASE_TIME } from './config.js';
import { validateInstruction } from './rules.mjs';

export class InstructionManager {
  constructor(random = Math.random) {
    this.random = random;
    this.lastKind = null;
    this.lastSpeaker = null;
  }

  pick(values) {
    return values[Math.floor(this.random() * values.length)];
  }

  finish(instruction) {
    validateInstruction(instruction);
    this.lastKind = instruction.kind;
    return instruction;
  }

  training(round) {
    if (round === 1) {
      return this.finish({
        id: round,
        phase: 1,
        training: true,
        speaker: 'COMPUTER',
        color: 'RED',
        duration: 6.5,
        kind: 'press',
        text: 'PRESS RED',
        expected: ['RED'],
        authorized: true,
        authVisible: true,
        responseHint: 'YOUR INPUT: PRESS THE RED BUTTON ONCE',
      });
    }
    if (round === 2) {
      return this.finish({
        id: round,
        phase: 1,
        training: true,
        speaker: 'COMPUTER',
        color: null,
        duration: 5.5,
        kind: 'wait',
        text: 'WAIT. DO NOT PRESS ANY BUTTON.',
        expected: [],
        authorized: true,
        authVisible: true,
        responseHint: 'YOUR INPUT: NOTHING — LET THE TIMER EMPTY',
      });
    }
    return null;
  }

  create(phase, round) {
    const training = this.training(round);
    if (training) return training;

    const color = this.pick(COLORS);
    const speaker = this.speaker(phase);
    const authorized = this.authorization(phase, speaker);
    const base = {
      speaker,
      color,
      duration: PHASE_TIME[phase - 1],
      id: round,
      phase,
      authorized,
      authVisible: phase <= 3,
      training: false,
    };

    let kinds = ['press', 'avoid', 'wait'];
    if (phase >= 2) kinds = [...kinds, 'double', 'hold'];
    if (phase >= 3) kinds = [...kinds, 'sequence', 'delayed'];
    // Forged passive orders would require the same response as valid passive
    // orders, creating no trust decision. Remove them before no-repeat filtering
    // so the fallback cannot accidentally repeat the previous active kind.
    if (!authorized) kinds = kinds.filter(kind => kind !== 'avoid' && kind !== 'wait');
    const alternatives = kinds.filter(kind => kind !== this.lastKind);
    const kind = this.pick(alternatives.length ? alternatives : kinds);

    if (kind === 'press') return this.finish({ ...base, kind, text: `PRESS ${color}`, expected: [color], responseHint: `YOUR INPUT: PRESS ${color} ONCE` });
    if (kind === 'avoid') return this.finish({ ...base, kind, text: `DO NOT TOUCH ${color}`, expected: [], responseHint: 'YOUR INPUT: NOTHING — LET THE TIMER EMPTY' });
    if (kind === 'wait') return this.finish({ ...base, kind, text: this.pick(['WAIT.', 'DO NOTHING.', 'HOLD POSITION.']), expected: [], responseHint: 'YOUR INPUT: NOTHING — LET THE TIMER EMPTY' });
    if (kind === 'double') return this.finish({ ...base, kind, text: `PRESS ${color} TWICE`, expected: [color, color], responseHint: `YOUR INPUT: PRESS ${color} TWO TIMES` });
    if (kind === 'hold') return this.finish({ ...base, kind, text: `HOLD ${color}`, expected: [color], responseHint: `YOUR INPUT: HOLD ${color} FOR 0.65 SECONDS` });
    if (kind === 'delayed') return this.finish({ ...base, kind, text: `PRESS ${color} AFTER 3`, expected: [color], unlockAt: 3, responseHint: `YOUR INPUT: WAIT 3 SECONDS, THEN PRESS ${color}` });

    const second = this.pick(COLORS.filter(candidate => candidate !== color));
    const expected = [color, second];
    if (phase >= 5) expected.push(this.pick(COLORS.filter(candidate => !expected.includes(candidate))));
    return this.finish({
      ...base,
      kind,
      text: `SEQUENCE: ${expected.join(' / ')}`,
      expected,
      responseHint: `YOUR INPUT: PRESS ${expected.join(', THEN ')}`,
    });
  }

  authorization(phase, speaker) {
    if (phase < 3) return true;
    if (speaker === 'COMPUTER' || speaker === 'SUPERVISOR' || speaker === 'EMERGENCY') return true;
    return false;
  }

  speaker(phase) {
    if (phase === 1) {
      this.lastSpeaker = 'COMPUTER';
      return 'COMPUTER';
    }
    const pools = [
      ['COMPUTER', 'SUPERVISOR'],
      ['COMPUTER', 'SUPERVISOR', 'EMERGENCY', 'UNKNOWN'],
      ['COMPUTER', 'SUPERVISOR', 'EMERGENCY', 'UNKNOWN', 'YOU'],
      ['COMPUTER', 'SUPERVISOR', 'EMERGENCY', 'UNKNOWN', 'YOU'],
    ];
    const pool = pools[Math.min(3, phase - 2)];
    const alternatives = pool.filter(source => source !== this.lastSpeaker);
    const source = this.pick(alternatives.length ? alternatives : pool);
    this.lastSpeaker = source;
    return source;
  }
}
