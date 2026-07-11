import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  twinkle: number;
}

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);

    const PARTICLE_COUNT = Math.min(60, Math.floor((w * h) / 25000));
    const MAX_DIST = 180;
    const GOLD = [224, 176, 80];

    // Init particles
    if (particlesRef.current.length === 0) {
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particlesRef.current.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.25,
          vy: (Math.random() - 0.5) * 0.25,
          size: Math.random() * 1.8 + 0.5,
          alpha: Math.random() * 0.5 + 0.15,
          twinkle: Math.random() * Math.PI * 2,
        });
      }
    }

    let mouseX = w / 2;
    let mouseY = h / 2;

    const onResize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };

    const onMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', onMouseMove);

    const animate = () => {
      ctx.clearRect(0, 0, w, h);

      const particles = particlesRef.current;

      // Draw ambient starlight gradient blobs
      const blob = ctx.createRadialGradient(mouseX, mouseY, 0, mouseX, mouseY, 400);
      blob.addColorStop(0, `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, 0.025)`);
      blob.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = blob;
      ctx.fillRect(0, 0, w, h);

      // Update + draw particles
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.twinkle += 0.015;

        // Wrap around edges
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        const twinkleAlpha = p.alpha * (0.5 + Math.sin(p.twinkle) * 0.5);

        // Glow dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${twinkleAlpha})`;
        ctx.fill();

        // Soft halo
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${twinkleAlpha * 0.08})`;
        ctx.fill();
      }

      // Draw connecting lines (constellation)
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < MAX_DIST) {
            const lineAlpha = (1 - dist / MAX_DIST) * 0.12;
            ctx.strokeStyle = `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${lineAlpha})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // Lines from mouse to nearby particles (parallax effect)
      for (const p of particles) {
        const dx = p.x - mouseX;
        const dy = p.y - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 250) {
          const lineAlpha = (1 - dist / 250) * 0.06;
          ctx.strokeStyle = `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${lineAlpha})`;
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(mouseX, mouseY);
          ctx.lineTo(p.x, p.y);
          ctx.stroke();
        }
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMouseMove);
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} className="bg-canvas" />
      <div className="bg-grid-overlay" />
    </>
  );
}