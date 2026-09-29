'use client';

import React, { useEffect, useRef } from 'react';

export default function CyberBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Starfield particles
    const particleCount = 75;
    const particles = Array.from({ length: particleCount }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      size: Math.random() * 1.8 + 0.4,
      speedX: (Math.random() - 0.5) * 0.3,
      speedY: (Math.random() - 0.5) * 0.3,
      opacity: Math.random() * 0.7 + 0.2,
      color: Math.random() > 0.6 ? '#06b6d4' : Math.random() > 0.3 ? '#8b5cf6' : '#38bdf8',
    }));

    let gridOffset = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Deep dark futuristic background gradient
      const bgGradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      bgGradient.addColorStop(0, '#030712'); // obsidian black
      bgGradient.addColorStop(0.5, '#050b1a'); // dark navy
      bgGradient.addColorStop(1, '#02050e');
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Ambient radial neon glowing orbs
      const glow1 = ctx.createRadialGradient(
        canvas.width * 0.2,
        canvas.height * 0.3,
        10,
        canvas.width * 0.2,
        canvas.height * 0.3,
        canvas.width * 0.45
      );
      glow1.addColorStop(0, 'rgba(6, 182, 212, 0.08)');
      glow1.addColorStop(0.7, 'rgba(14, 165, 233, 0.02)');
      glow1.addColorStop(1, 'transparent');
      ctx.fillStyle = glow1;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const glow2 = ctx.createRadialGradient(
        canvas.width * 0.8,
        canvas.height * 0.7,
        10,
        canvas.width * 0.8,
        canvas.height * 0.7,
        canvas.width * 0.4
      );
      glow2.addColorStop(0, 'rgba(139, 92, 246, 0.08)');
      glow2.addColorStop(0.7, 'rgba(124, 58, 237, 0.015)');
      glow2.addColorStop(1, 'transparent');
      ctx.fillStyle = glow2;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 3D Perspective Grid at the bottom
      gridOffset = (gridOffset + 0.4) % 40;
      const horizonY = canvas.height * 0.55;
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.04)';
      ctx.lineWidth = 1;

      // Vertical perspective lines
      const numLines = 24;
      for (let i = -numLines; i <= numLines; i++) {
        const startX = canvas.width / 2 + i * 30;
        const endX = canvas.width / 2 + i * 180;
        ctx.beginPath();
        ctx.moveTo(startX, horizonY);
        ctx.lineTo(endX, canvas.height);
        ctx.stroke();
      }

      // Horizontal moving depth lines
      for (let y = horizonY; y < canvas.height; y += 22) {
        const depthFactor = (y - horizonY) / (canvas.height - horizonY);
        ctx.strokeStyle = `rgba(6, 182, 212, ${depthFactor * 0.08})`;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw floating particles
      particles.forEach((p) => {
        p.x += p.speedX;
        p.y += p.speedY;

        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.opacity;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.globalAlpha = 1.0;
      ctx.shadowBlur = 0;

      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none -z-10 w-full h-full"
    />
  );
}
