import { useEffect, useRef } from 'react';

export function useAnimationFrame(callback: (deltaTime: number) => void, running: boolean = true) {
  const cbRef = useRef(callback);
  cbRef.current = callback;

  useEffect(() => {
    if (!running) return;

    let lastTime = performance.now();
    let id: number;

    const tick = (now: number) => {
      const dt = (now - lastTime) / 1000;
      lastTime = now;
      cbRef.current(dt);
      id = requestAnimationFrame(tick);
    };

    id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [running]);
}
