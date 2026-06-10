import React, { useRef, useEffect } from 'react';

const StarField = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Particle representation
    class Star {
      constructor() {
        this.reset(true);
      }

      reset(init = false) {
        this.x = Math.random() * width;
        this.y = init ? Math.random() * height : -10;
        this.size = Math.random() * 1.5 + 0.4; // size in px
        this.speed = Math.random() * 0.15 + 0.05; // speed downward
        this.opacity = Math.random() * 0.7 + 0.15; // opacity
        this.drift = (Math.random() - 0.5) * 0.04; // drift direction
        this.pulsate = Math.random() > 0.5;
        this.pulseSpeed = Math.random() * 0.02 + 0.005;
      }

      update() {
        this.y += this.speed;
        this.x += this.drift;

        if (this.pulsate) {
          this.opacity += this.pulseSpeed;
          if (this.opacity > 0.85 || this.opacity < 0.15) {
            this.pulseSpeed = -this.pulseSpeed;
          }
        }

        // Reset if off boundaries
        if (this.y > height + 10 || this.x < -10 || this.x > width + 10) {
          this.reset(false);
        }
      }

      draw() {
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, Math.min(this.opacity, 1))})`;
        ctx.beginPath();
        // Draw standard star circle
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();

        // Occasional faint electric blue/violet tint for star colors
        if (this.size > 1.5) {
          ctx.fillStyle = this.pulsate ? 'rgba(79, 195, 247, 0.15)' : 'rgba(179, 136, 255, 0.15)';
          ctx.beginPath();
          ctx.arc(this.x, this.y, this.size * 2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    const stars = Array.from({ length: 200 }, () => new Star());

    const animate = () => {
      // Clear with radial gradient overlay to feel like deep space
      ctx.fillStyle = '#050710';
      ctx.fillRect(0, 0, width, height);

      // Deep space violet nebula background glow
      const nebulaGlow = ctx.createRadialGradient(
        width / 2,
        height,
        20,
        width / 2,
        height / 2,
        Math.max(width, height)
      );
      nebulaGlow.addColorStop(0, 'rgba(21, 23, 48, 0.65)');
      nebulaGlow.addColorStop(0.5, 'rgba(5, 7, 16, 0.95)');
      nebulaGlow.addColorStop(1, '#050710');
      ctx.fillStyle = nebulaGlow;
      ctx.fillRect(0, 0, width, height);

      stars.forEach((star) => {
        star.update();
        star.draw();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none -z-50"
    />
  );
};

export default StarField;
