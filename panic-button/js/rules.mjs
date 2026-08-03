import { COLORS, PHASE_THRESHOLDS } from './config.js';

const ACTIVE_KINDS = new Set(['press', 'double', 'hold', 'sequence', 'delayed']);
const PASSIVE_KINDS = new Set(['avoid', 'wait']);

export function validateInstruction(instruction) {
  if (!instruction || typeof instruction !== 'object') throw new TypeError('Instruction is required');
  if (!ACTIVE_KINDS.has(instruction.kind) && !PASSIVE_KINDS.has(instruction.kind)) throw new TypeError(`Unknown instruction kind: ${instruction.kind}`);
  if (!Number.isFinite(instruction.duration) || instruction.duration <= 0) throw new RangeError('Instruction duration must be positive');
  if (!Array.isArray(instruction.expected)) throw new TypeError('Instruction expected actions must be an array');
  if (instruction.expected.some(color => !COLORS.includes(color))) throw new RangeError('Instruction contains an invalid color');
  if (ACTIVE_KINDS.has(instruction.kind) && instruction.expected.length === 0) throw new RangeError('Active instruction requires an expected action');
  if (PASSIVE_KINDS.has(instruction.kind) && instruction.expected.length !== 0) throw new RangeError('Passive instruction cannot contain expected actions');
  if (instruction.kind === 'hold' && instruction.expected.length !== 1) throw new RangeError('Hold instruction requires one expected action');
  if ((instruction.kind === 'press' || instruction.kind === 'delayed') && instruction.expected.length !== 1) throw new RangeError('Press instruction requires one expected action');
  if (instruction.kind === 'double' && instruction.expected.length !== 2) throw new RangeError('Double instruction requires two expected actions');
  if (instruction.kind === 'sequence' && (instruction.expected.length < 2 || instruction.expected.length > 3)) throw new RangeError('Sequence instruction requires two or three expected actions');
  if (instruction.kind === 'double' && instruction.expected[0] !== instruction.expected[1]) throw new RangeError('Double instruction requires the same color twice');
  if ('authorized' in instruction && typeof instruction.authorized !== 'boolean') throw new TypeError('Instruction authorization must be boolean');
  if (instruction.kind === 'delayed' && (!Number.isFinite(instruction.unlockAt) || instruction.unlockAt < 0 || instruction.unlockAt >= instruction.duration)) throw new RangeError('Delayed instruction unlock time must be inside its duration');
  return true;
}

export function assessAction(instruction, priorInputs, action, elapsedMs) {
  validateInstruction(instruction);
  const inputs = Array.isArray(priorInputs) ? [...priorInputs] : [];
  if (!action || action.type === 'down') return { status: 'ignore', inputs };
  if (!COLORS.includes(action.color)) return { status: 'fail', inputs };
  if (instruction.authorized === false) return { status: 'fail', inputs };

  if (instruction.kind === 'hold') {
    const validHold = action.type === 'hold' && Number(action.duration) >= 650;
    return { status: validHold && action.color === instruction.expected[0] ? 'pass' : 'fail', inputs: validHold ? [action.color] : inputs };
  }
  if (action.type === 'hold') return { status: 'fail', inputs };
  if (instruction.kind === 'delayed' && elapsedMs < instruction.unlockAt * 1000) return { status: 'fail', inputs };
  if (instruction.expected.length === 0) return { status: 'fail', inputs };

  const expectedColor = instruction.expected[inputs.length];
  inputs.push(action.color);
  if (action.color !== expectedColor) return { status: 'fail', inputs };
  return { status: inputs.length === instruction.expected.length ? 'pass' : 'pending', inputs };
}

export function penaltyFor(instruction) {
  if (!instruction || instruction.authorized === false) return 12;
  if (instruction.kind === 'sequence' || instruction.kind === 'delayed') return 12;
  if (instruction.kind === 'double' || instruction.kind === 'hold') return 10;
  if (PASSIVE_KINDS.has(instruction.kind)) return 10;
  return 8;
}

export function timeoutOutcome(instruction) {
  validateInstruction(instruction);
  return instruction.authorized === false || instruction.expected.length === 0;
}

export function phaseForRound(round) {
  const safeRound = Number.isFinite(round) ? Math.max(0, Math.floor(round)) : 0;
  let phase = 1;
  for (let index = 1; index < PHASE_THRESHOLDS.length; index += 1) {
    if (safeRound >= PHASE_THRESHOLDS[index]) phase = index + 1;
  }
  return phase;
}

export function disableCandidates(instruction) {
  const expected = new Set(instruction?.expected || []);
  return COLORS.filter(color => !expected.has(color));
}
