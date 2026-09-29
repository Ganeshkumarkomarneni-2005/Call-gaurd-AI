'use client';

import React, { useEffect, useRef } from 'react';

interface CyberShield3DProps {
  size?: number;
  className?: string;
  shieldActive?: boolean;
}

export default function CyberShield3D({
  size = 400,
  className = '',
  shieldActive = true,
}: CyberShield3DProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let rotation = 0;
    let pulse = 0;

    // Generate 3D spherical node cloud
    const numPoints = 140;
    const points: Array<{ x: number; y: number; z: number; size: number; color: string; speed: number }> = [];

    for (let i = 0; i < numPoints; i++) {
      const theta = Math.acos(2 * Math.random() - 1);
      const phi = 2 * Math.PI * Math.random();
      const radius = 110 + (Math.random() * 20 - 10);

      points.push({
        x: radius * Math.sin(theta) * Math.cos(phi),
        y: radius * Math.sin(theta) * Math.sin(phi),
        z: radius * Math.cos(theta),
        size: Math.random() * 2.2 + 1,
        color: i % 3 === 0 ? '#06b6d4' : i % 3 === 1 ? '#8b5cf6' : '#3b82f6',
        speed: (Math.random() * 0.005 + 0.002) * (Math.random() > 0.5 ? 1 : -1),
      });
    }

    // Outer orbital rings
    const rings = [
      { radius: 155, tiltX: 0.6, tiltY: 0.3, speed: 0.015, color: 'rgba(6, 182, 212, 0.4)' },
      { radius: 175, tiltX: -0.4, tiltY: 0.8, speed: -0.01, color: 'rgba(139, 92, 246, 0.4)' },
      { radius: 195, tiltX: 0.2, tiltY: -0.5, speed: 0.008, color: 'rgba(59, 130, 246, 0.3)' },
    ];

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
      const y = (e.clientY - rect.top - rect.height / 2) / (rect.height / 2);
      mouseRef.current.targetX = x * 0.4;
      mouseRef.current.targetY = y * 0.4;
    };

    window.addEventListener('mousemove', handleMouseMove);

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Smooth mouse interpolation
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.06;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.06;

      rotation += 0.01;
      pulse += 0.03;

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const currentPulse = Math.sin(pulse) * 5;

      // 1. Core Energy Glow
      const coreGlow = ctx.createRadialGradient(
        centerX,
        centerY,
        10,
        centerX,
        centerY,
        140 + currentPulse
      );
      coreGlow.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
      coreGlow.addColorStop(0.35, 'rgba(139, 92, 246, 0.15)');
      coreGlow.addColorStop(0.8, 'rgba(3, 7, 18, 0)');
      ctx.fillStyle = coreGlow;
      ctx.beginPath();
      ctx.arc(centerX, centerY, 150 + currentPulse, 0, Math.PI * 2);
      ctx.fill();

      // 2. Draw 3D Rotating Rings
      rings.forEach((ring) => {
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(rotation * ring.speed * 40 + mouseRef.current.x);
        ctx.scale(1, Math.cos(ring.tiltX + mouseRef.current.y));

        ctx.strokeStyle = ring.color;
        ctx.lineWidth = 1.5;
        ctx.shadowColor = ring.color;
        ctx.shadowBlur = 12;

        ctx.beginPath();
        ctx.arc(0, 0, ring.radius, 0, Math.PI * 2);
        ctx.stroke();

        // Orbiting satellite node on ring
        const satAngle = rotation * ring.speed * 80;
        const satX = Math.cos(satAngle) * ring.radius;
        const satY = Math.sin(satAngle) * ring.radius;
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#06b6d4';
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.arc(satX, satY, 3, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      });

      // 3. Project & Draw 3D Spherical Nodes & Network Lines
      const rotY = rotation * 0.7 + mouseRef.current.x * 1.5;
      const rotX = mouseRef.current.y * 1.5;

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      const projectedPoints: Array<{ x: number; y: number; z: number; size: number; color: string }> = [];

      points.forEach((p) => {
        // Rotate around Y
        let x1 = p.x * cosY - p.z * sinY;
        let z1 = p.z * cosY + p.x * sinY;

        // Rotate around X
        let y1 = p.y * cosX - z1 * sinX;
        let z2 = z1 * cosX + p.y * sinX;

        // Perspective projection
        const fov = 340;
        const scale = fov / (fov + z2);
        const projX = centerX + x1 * scale;
        const projY = centerY + y1 * scale;

        projectedPoints.push({
          x: projX,
          y: projY,
          z: z2,
          size: Math.max(0.5, p.size * scale),
          color: p.color,
        });
      });

      // Sort by Z for realistic depth
      projectedPoints.sort((a, b) => b.z - a.z);

      // Connect nearby nodes with glowing cyber vectors
      ctx.lineWidth = 0.6;
      for (let i = 0; i < projectedPoints.length; i++) {
        for (let j = i + 1; j < projectedPoints.length; j++) {
          const dx = projectedPoints[i].x - projectedPoints[j].x;
          const dy = projectedPoints[i].y - projectedPoints[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 42 && projectedPoints[i].z > -100) {
            const alpha = (1 - dist / 42) * (projectedPoints[i].z > 0 ? 0.35 : 0.1);
            ctx.strokeStyle = `rgba(6, 182, 212, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(projectedPoints[i].x, projectedPoints[i].y);
            ctx.lineTo(projectedPoints[j].x, projectedPoints[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw nodes
      projectedPoints.forEach((p) => {
        const alpha = Math.min(1, Math.max(0.2, (p.z + 140) / 280));
        ctx.fillStyle = p.color;
        ctx.globalAlpha = alpha;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = p.z > 0 ? 8 : 2;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.globalAlpha = 1.0;
      ctx.shadowBlur = 0;

      // 4. Center Holographic Shield Emblem
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.shadowColor = '#06b6d4';
      ctx.shadowBlur = 20;

      // Shield path
      ctx.beginPath();
      ctx.moveTo(0, -32);
      ctx.lineTo(26, -18);
      ctx.lineTo(26, 12);
      ctx.quadraticCurveTo(0, 38, 0, 42);
      ctx.quadraticCurveTo(0, 38, -26, 12);
      ctx.lineTo(-26, -18);
      ctx.closePath();

      ctx.fillStyle = 'rgba(6, 182, 212, 0.12)';
      ctx.fill();
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 2.2;
      ctx.stroke();

      // Inner Core Icon
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(0, 2, 6, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [size]);

  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="w-full h-full max-w-[500px] aspect-square drop-shadow-[0_0_40px_rgba(6,182,212,0.25)]"
      />
    </div>
  );
}
