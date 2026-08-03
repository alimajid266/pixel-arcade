export const COLORS = ['RED', 'BLUE', 'GREEN', 'YELLOW'];

export const SPEAKERS = {
  COMPUTER: { color: '#79ff9b', speed: 19, tone: 740 },
  SUPERVISOR: { color: '#efbd72', speed: 34, tone: 520 },
  UNKNOWN: { color: '#63e6ff', speed: 78, tone: 260 },
  EMERGENCY: { color: '#ff4b3e', speed: 12, tone: 900 },
  YOU: { color: '#e7ebe8', speed: 48, tone: 400 },
};

export const PROTOCOLS = [
  { name: 'CALIBRATION', rounds: 'ROUNDS 1–2', rule: 'Safe training: single press and no-input orders. Mistakes cost no integrity.' },
  { name: 'COMPOUND', rounds: 'ROUNDS 3–5', rule: 'Double-press and hold orders join the basic controls.' },
  { name: 'BREACH', rounds: 'ROUNDS 6–9', rule: 'Sequences, delayed inputs, and visible forged orders begin.' },
  { name: 'BLACKOUT', rounds: 'ROUNDS 10–14', rule: 'Authorization starts unclear. Trust the source pattern or spend Verify.' },
  { name: 'COLLAPSE', rounds: 'ROUND 15+', rule: 'Shortest deadlines, three-input sequences, highest-complexity orders, and maximum interference.' },
];

export const PHASE_THRESHOLDS = [0, 3, 6, 10, 15];
export const PHASE_TIME = [5.2, 4.9, 4.7, 4.5, 4.3];
export const MESSAGES = [
  'YOU ARE IMPROVING.',
  'PERFORMANCE DEGRADATION DETECTED.',
  'I DID NOT ASK YOU TO DO THAT.',
  'SOMEONE ELSE IS LISTENING.',
  'I REMEMBER YOUR LAST SHIFT.',
];
