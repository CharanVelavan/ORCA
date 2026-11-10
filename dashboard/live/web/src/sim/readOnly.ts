import { useLiveStore } from '../store';

export function isReadOnlyNow(): boolean {
  return new URLSearchParams(window.location.search).get('fake') === '1'
    || useLiveStore.getState().source === 'replay';
}
