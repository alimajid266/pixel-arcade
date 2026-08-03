import { COLORS } from './config.js';

const HOLD_THRESHOLD_MS = 650;
const ACTIVATION_KEYS = new Set([' ', 'Enter']);

export class ButtonBank {
  constructor(root, audio, onAction) {
    this.root = root;
    this.audio = audio;
    this.onAction = onAction;
    this.buttons = new Map();
    this.order = [...COLORS];
    this.gestureSerial = 0;
    this.render();
  }

  render() {
    this.root.innerHTML = '';
    this.buttons.clear();

    this.order.forEach((color, index) => {
      const wrap = document.createElement('div');
      wrap.className = 'button-module';
      wrap.dataset.color = color;
      wrap.innerHTML = `<div class="bolts"><i></i><i></i></div><button class="mechanical ${color.toLowerCase()}" aria-label="${color} control"><span class="button-cap"></span></button><label>${color}</label><small>CH-${index + 1}</small>`;

      const button = wrap.querySelector('button');
      let pointerGesture = null;
      let keyboardGesture = null;

      const syncPressed = () => {
        button.classList.toggle('pressed', pointerGesture !== null || keyboardGesture !== null);
      };

      const beginAction = (source) => {
        const gesture = {
          id: `${source}-${++this.gestureSerial}`,
          startedAt: performance.now(),
        };
        this.audio.click((index - 1.5) / 2);
        this.onAction({ type: 'down', color, gestureId: gesture.id, time: gesture.startedAt });
        return gesture;
      };

      const completeAction = (gesture) => {
        const time = performance.now();
        const duration = time - gesture.startedAt;
        this.onAction({
          type: duration >= HOLD_THRESHOLD_MS ? 'hold' : 'press',
          color,
          gestureId: gesture.id,
          duration,
          time,
        });
      };

      button.addEventListener('pointerdown', (event) => {
        pointerGesture = beginAction('pointer');
        syncPressed();
        button.setPointerCapture(event.pointerId);
      });

      button.addEventListener('pointerup', () => {
        if (pointerGesture === null) return;
        const gesture = pointerGesture;
        pointerGesture = null;
        syncPressed();
        completeAction(gesture);
      });

      button.addEventListener('pointercancel', () => {
        if (pointerGesture !== null) this.onAction({ type: 'cancel', color, gestureId: pointerGesture.id, time: performance.now() });
        pointerGesture = null;
        syncPressed();
      });

      button.addEventListener('keydown', (event) => {
        if (!ACTIVATION_KEYS.has(event.key) || event.repeat || keyboardGesture !== null) return;
        event.preventDefault();
        keyboardGesture = beginAction('keyboard');
        syncPressed();
      });

      button.addEventListener('keyup', (event) => {
        if (!ACTIVATION_KEYS.has(event.key) || keyboardGesture === null) return;
        event.preventDefault();
        const gesture = keyboardGesture;
        keyboardGesture = null;
        syncPressed();
        completeAction(gesture);
      });

      // Prevent the synthetic keyboard click from duplicating keyup handling.
      button.addEventListener('click', (event) => {
        if (event.detail === 0) event.preventDefault();
      });

      this.root.appendChild(wrap);
      this.buttons.set(color, wrap);
    });
  }

  shuffle() {
    for (let index = this.order.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [this.order[index], this.order[swapIndex]] = [this.order[swapIndex], this.order[index]];
    }
    this.render();
  }

  swapLabels() {
    const labels = [...this.root.querySelectorAll('label')];
    const values = labels.map((label) => label.textContent);
    labels.forEach((label, index) => {
      label.textContent = values[(index + 1) % values.length];
    });
  }

  restoreLabels() {
    for (const wrap of this.buttons.values()) {
      wrap.querySelector('label').textContent = wrap.dataset.color;
    }
  }

  flash(color) {
    const element = this.buttons.get(color);
    if (!element) return;
    element.classList.add('signal');
    setTimeout(() => element.classList.remove('signal'), 600);
  }

  enableAll() {
    for (const wrap of this.buttons.values()) {
      wrap.querySelector('button').disabled = false;
    }
  }

  disable(color, milliseconds = 1600) {
    const button = this.buttons.get(color)?.querySelector('button');
    if (!button) return;
    button.disabled = true;
    setTimeout(() => {
      button.disabled = false;
    }, milliseconds);
  }

  reset() {
    this.order = [...COLORS];
    this.render();
  }
}
