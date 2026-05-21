import { useEffect, useRef } from "react";
import { createNoise2D } from "simplex-noise";

interface FlowerFieldProps {
  theme: "light" | "dark";
}

const ORBS = [
  { r: 52,  g: 211, b: 153, ox: 0,   oy: 100, speed: 0.00022, size: 0.44 },
  { r: 20,  g: 184, b: 166, ox: 200, oy: 350, speed: 0.00018, size: 0.38 },
  { r: 6,   g: 182, b: 212, ox: 450, oy: 550, speed: 0.00028, size: 0.34 },
  { r: 99,  g: 102, b: 241, ox: 650, oy: 750, speed: 0.00015, size: 0.30 },
  { r: 34,  g: 197, b: 94,  ox: 850, oy: 950, speed: 0.00032, size: 0.26 },
];

export default function FlowerField({ theme }: FlowerFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const noise2D = createNoise2D();
    const isDark = theme === "dark";
    const alpha = isDark ? 0.55 : 0.32;
    let t = 0;
    let rafId = 0;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();

    const draw = () => {
      t++;
      const { width: w, height: h } = canvas;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = isDark ? "screen" : "source-over";

      for (const orb of ORBS) {
        const nx = noise2D(orb.ox + t * orb.speed, orb.oy) * 0.5 + 0.5;
        const ny = noise2D(orb.oy + t * orb.speed, orb.ox) * 0.5 + 0.5;
        const x = nx * w;
        const y = ny * h;
        const r = Math.min(w, h) * orb.size;

        const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
        grad.addColorStop(0, `rgba(${orb.r},${orb.g},${orb.b},${alpha})`);
        grad.addColorStop(1, `rgba(${orb.r},${orb.g},${orb.b},0)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
      }

      rafId = requestAnimationFrame(draw);
    };

    rafId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
    };
  }, [theme]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 h-full w-full"
      style={{ filter: "blur(55px)" }}
    />
  );
}
