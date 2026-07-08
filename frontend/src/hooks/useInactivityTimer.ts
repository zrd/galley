import { useEffect } from 'react';

const TIMEOUT_MS = import.meta.env.VITE_INACTIVITY_TIMEOUT_MS
  ? Number(import.meta.env.VITE_INACTIVITY_TIMEOUT_MS)
  : 30 * 60 * 1000;
const EVENTS = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'] as const;

export function useInactivityTimer() {
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    const reset = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (!localStorage.getItem('access_token')) return;
        localStorage.removeItem('access_token');
        const returnTo = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login?expired=1&returnTo=${returnTo}`;
      }, TIMEOUT_MS);
    };

    EVENTS.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    reset();

    return () => {
      clearTimeout(timer);
      EVENTS.forEach((e) => window.removeEventListener(e, reset));
    };
  }, []);
}
