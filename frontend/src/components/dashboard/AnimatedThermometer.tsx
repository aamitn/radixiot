import { useState, useEffect } from "react";
import { motion, useAnimation } from "motion/react";

const AnimatedThermometer = ({ value = 25 }) => {
  const [temp, setTemp] = useState(value);
  const controls = useAnimation();

  // Fluctuating temperature
  useEffect(() => {
    const interval = setInterval(() => {
      setTemp((prev) => Math.min(100, Math.max(0, prev + (Math.random() * 6 - 3))));
    }, 500); // faster updates
    return () => clearInterval(interval);
  }, []);

  // Jiggle animation on hover
  const handleHover = () => {
    controls.start({
      rotate: [-5, 5, -5, 5, 0],
      transition: { duration: 0.5, ease: "easeInOut" },
    });
  };

  return (
    <motion.div
      animate={controls}
      onHoverStart={handleHover}
      className="relative w-14 h-52 bg-gray-200 rounded-xl overflow-hidden cursor-pointer"
    >
      {/* Glow overlay */}
      <motion.div
        animate={{ opacity: [0.6, 0.9, 0.6] }}
        transition={{ repeat: Infinity, duration: 1.2 }}
        className="absolute inset-0 bg-gradient-to-t from-red-400 via-yellow-400 to-yellow-200 rounded-xl filter blur-xl"
      />
      {/* Temperature bar */}
      <motion.div
        animate={{ height: `${temp}%` }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
        className="absolute bottom-0 w-full bg-gradient-to-t from-red-500 to-yellow-400 rounded-xl"
      />
      {/* Temperature text */}
      <div className="absolute bottom-0 w-full text-center text-sm font-bold text-white">
        {Math.round(temp)}°C
      </div>
    </motion.div>
  );
};

export default AnimatedThermometer;
