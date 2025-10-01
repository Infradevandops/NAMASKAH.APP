import React, { useEffect, useRef } from 'react';

const AnimatedIcon = () => {
  const iconRef = useRef(null);

  useEffect(() => {
    const icon = iconRef.current;
    let animationFrame;

    const animate = () => {
      if (icon) {
        const time = Date.now() / 1000;
        const rotate = 10 * Math.sin(time * 2);
        icon.style.transform = `rotate(${rotate}deg)`;
      }
      animationFrame = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <div
      ref={iconRef}
      style={{
        fontSize: '6rem',
        display: 'inline-block',
        transition: 'transform 0.1s ease-in-out',
      }}
      aria-label="Animated phone icon"
      role="img"
    >
      📱
    </div>
  );
};

export default AnimatedIcon;
