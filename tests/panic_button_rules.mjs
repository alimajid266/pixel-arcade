import assert from 'node:assert/strict';
import { assessAction, timeoutOutcome, phaseForRound, disableCandidates, validateInstruction, penaltyFor } from '../panic-button/js/rules.mjs';
import { InstructionManager } from '../panic-button/js/instructions.js';
import { StateManager } from '../panic-button/js/stateManager.js';
import { PHASE_TIME, PROTOCOLS } from '../panic-button/js/config.js';

const base = { kind: 'press', expected: ['RED'], duration: 7 };
assert.deepEqual(assessAction(base, [], { type: 'down', color: 'RED' }, 100), { status: 'ignore', inputs: [] });
assert.deepEqual(assessAction(base, [], { type: 'press', color: 'RED' }, 100), { status: 'pass', inputs: ['RED'] });
assert.equal(assessAction(base, [], { type: 'press', color: 'BLUE' }, 100).status, 'fail');
assert.equal(assessAction(base, [], { type: 'hold', color: 'RED', duration: 800 }, 100).status, 'fail');

const double = { kind: 'double', expected: ['YELLOW', 'YELLOW'], duration: 6 };
assert.deepEqual(assessAction(double, [], { type: 'press', color: 'YELLOW' }, 200), { status: 'pending', inputs: ['YELLOW'] });
assert.equal(assessAction(double, ['YELLOW'], { type: 'press', color: 'YELLOW' }, 350).status, 'pass');
assert.equal(assessAction(double, ['YELLOW'], { type: 'press', color: 'RED' }, 350).status, 'fail');

const sequence = { kind: 'sequence', expected: ['GREEN', 'BLUE'], duration: 6 };
assert.equal(assessAction(sequence, [], { type: 'press', color: 'GREEN' }, 100).status, 'pending');
assert.equal(assessAction(sequence, ['GREEN'], { type: 'press', color: 'BLUE' }, 200).status, 'pass');

const hold = { kind: 'hold', expected: ['GREEN'], duration: 6 };
assert.equal(assessAction(hold, [], { type: 'hold', color: 'GREEN', duration: 649 }, 700).status, 'fail');
assert.equal(assessAction(hold, [], { type: 'hold', color: 'GREEN', duration: 650 }, 700).status, 'pass');
assert.equal(assessAction(hold, [], { type: 'press', color: 'GREEN', duration: 100 }, 700).status, 'fail');

const delayed = { kind: 'delayed', expected: ['BLUE'], duration: 7, unlockAt: 3 };
assert.equal(assessAction(delayed, [], { type: 'press', color: 'BLUE' }, 2999).status, 'fail');
assert.equal(assessAction(delayed, [], { type: 'press', color: 'BLUE' }, 3000).status, 'pass');

for (const kind of ['avoid', 'wait']) {
  const passive = { kind, expected: [], duration: 5 };
  assert.equal(assessAction(passive, [], { type: 'press', color: 'RED' }, 100).status, 'fail');
  assert.equal(timeoutOutcome(passive), true);
}
assert.equal(timeoutOutcome(base), false);

const forged = { ...base, authorized: false };
assert.equal(assessAction(forged, [], { type: 'press', color: 'RED' }, 100).status, 'fail');
assert.equal(timeoutOutcome(forged), true);

assert.deepEqual([0,2,3,5,6,9,10,14,15,999].map(phaseForRound), [1,1,2,2,3,3,4,4,5,5]);
assert.deepEqual(disableCandidates({ expected: ['RED', 'BLUE'] }).sort(), ['GREEN', 'YELLOW']);
assert.deepEqual(disableCandidates({ expected: [] }).sort(), ['BLUE', 'GREEN', 'RED', 'YELLOW']);
assert.equal(validateInstruction({ kind: 'sequence', expected: ['RED','GREEN'], duration: 5 }), true);
assert.throws(() => validateInstruction({ kind: 'sequence', expected: ['RED','PURPLE'], duration: 5 }), /color/i);
assert.throws(() => validateInstruction({ kind: 'press', expected: [], duration: 5 }), /expected/i);
assert.throws(() => validateInstruction({ kind: 'wait', expected: ['RED'], duration: 5 }), /passive/i);
assert.throws(() => validateInstruction({ kind: 'hold', expected: ['RED'], duration: 0 }), /duration/i);
assert.throws(() => validateInstruction({ kind: 'press', expected: ['RED', 'BLUE'], duration: 5 }), /one expected/i);
assert.throws(() => validateInstruction({ kind: 'double', expected: ['RED'], duration: 5 }), /two expected/i);
assert.throws(() => validateInstruction({ kind: 'double', expected: ['RED', 'BLUE'], duration: 5 }), /same color/i);
assert.throws(() => validateInstruction({ kind: 'sequence', expected: ['RED'], duration: 5 }), /two or three expected/i);

const manager = new InstructionManager(() => 0);
assert.deepEqual(
  [manager.create(1, 1).text, manager.create(1, 2).text],
  ['PRESS RED', 'WAIT. DO NOT PRESS ANY BUTTON.']
);
const forgedManager = new InstructionManager(() => 0.99);
assert.equal(forgedManager.create(3, 6).authorized, false);
assert.equal(forgedManager.create(3, 7).authVisible, true);
assert.equal(forgedManager.create(4, 10).authVisible, false);

const repeatRandom = [0, 0.99, 0];
const noRepeatManager = new InstructionManager(() => repeatRandom.shift() ?? 0);
noRepeatManager.lastKind = 'press';
assert.notEqual(noRepeatManager.create(3, 8).kind, 'press');

// Emergency is always authenticated; every late protocol retains all source types.
const emergencyManager = new InstructionManager(() => 0);
assert.equal(emergencyManager.authorization(5, 'EMERGENCY'), true);
const phaseFiveSources = [0, 0.21, 0.41, 0.61, 0.81].map(value => new InstructionManager(() => value).speaker(5));
assert.deepEqual(new Set(phaseFiveSources), new Set(['COMPUTER', 'SUPERVISOR', 'EMERGENCY', 'UNKNOWN', 'YOU']));
const sourceVarietyManager = new InstructionManager(() => 0);
assert.notEqual(sourceVarietyManager.speaker(5), sourceVarietyManager.speaker(5));

// Protocols are named game rules, not unexplained phase numbers.
assert.deepEqual(PROTOCOLS.map(protocol => protocol.name), ['CALIBRATION', 'COMPOUND', 'BREACH', 'BLACKOUT', 'COLLAPSE']);
assert.deepEqual(PHASE_TIME, [5.2, 4.9, 4.7, 4.5, 4.3]);

// Skipping binding active orders gets progressively more expensive.
assert.equal(penaltyFor({ ...base, kind: 'press' }), 8);
assert.equal(penaltyFor({ ...base, kind: 'double', expected: ['RED', 'RED'] }), 10);
assert.equal(penaltyFor({ ...base, kind: 'sequence', expected: ['RED', 'BLUE', 'GREEN'] }), 12);
assert.equal(penaltyFor({ ...base, authorized: false }), 12);

const triple = { ...base, kind: 'sequence', expected: ['RED', 'BLUE', 'GREEN'] };
assert.equal(assessAction(triple, [], { type: 'press', color: 'RED' }, 100).status, 'pending');
assert.equal(assessAction(triple, ['RED'], { type: 'press', color: 'BLUE' }, 200).status, 'pending');
assert.equal(assessAction(triple, ['RED', 'BLUE'], { type: 'press', color: 'GREEN' }, 300).status, 'pass');
const state = new StateManager();
state.integrity = 80;
state.heal();
assert.equal(state.integrity, 81);
state.integrity = 5;
assert.equal(state.damage(12), 5);
assert.equal(state.integrity, 0);

const sequenceForPhase = phase => {
  const values = [0, 0, 0.75, 0, 0];
  return new InstructionManager(() => values.shift() ?? 0).create(phase, phase === 4 ? 10 : 15);
};
assert.equal(sequenceForPhase(4).expected.length, 2);
assert.equal(sequenceForPhase(5).expected.length, 3);

console.log('PANIC BUTTON RULES PASS: authorization, authored training, press, double, sequence, hold, delayed, passive, phase, validation, and fair-disable rules');
