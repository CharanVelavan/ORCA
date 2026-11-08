import { api } from '../api';
import { useUi } from '../stage/uiStore';
import type { ExerciseConfig } from '../stage/uiStore';

const plain = (error: unknown, fallback: string): Error => {
  const text = error instanceof Error ? error.message : '';
  return new Error(text ? `${fallback} (${text})` : fallback);
};

/** IST wall-clock time, HH:MM:SS. */
export function istNow(): string {
  return new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date());
}

export async function startExercise(config: ExerciseConfig): Promise<void> {
  try {
    await api.session({ scenario: config.scenario, llm: config.llm, rules: config.rules, kb: config.kb, autoplay: true, sync: true });
    await api.clock({ action: 'play', speed: config.speed });
  } catch (error) {
    throw plain(error, 'Could not start the exercise. Is the engine running?');
  }
  useUi.getState().start();
}

export async function fireInject(injector: string, target: string, durationMin = 15): Promise<void> {
  try {
    await api.inject({ kind: injector, target, duration_min: durationMin });
  } catch (error) {
    throw plain(error, 'Could not fire that event.');
  }
  useUi.getState().markFired({ injector, target, at: istNow() });
}

export async function endExercise(): Promise<void> {
  try {
    await api.clock({ action: 'pause' });
  } catch (error) {
    throw plain(error, 'Could not pause the clock.');
  } finally {
    useUi.getState().end();
  }
}
