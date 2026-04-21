/**
 * ArabicLettersBg — خلفية حروف عربية متحركة (نسخة عامة)
 * يدعم تخصيص الحروف، الكثافة، والشفافية لإعادة الاستخدام في صفحات المحادثة.
 */
import { motion } from "framer-motion";
import { useMemo } from "react";

interface Props {
  letters?: string[];
  count?: number;
  opacity?: number;
  blur?: boolean;
  className?: string;
}

const DEFAULT_LETTERS = ["ب", "ت", "ش", "ع", "ق", "ن", "م", "و", "ي", "ل", "ك", "ه", "د", "ر", "ص"];

const ArabicLettersBg = ({
  letters = DEFAULT_LETTERS,
  count,
  opacity = 0.09,
  blur = false,
  className = "",
}: Props) => {
  // نضمن ثبات المواقع بين عمليات الـ re-render داخل نفس الجلسة
  const items = useMemo(() => {
    const total = count ?? letters.length * 2;
    return Array.from({ length: total }).map((_, i) => ({
      letter: letters[i % letters.length],
      size: 50 + Math.random() * 80,
      left: Math.random() * 100,
      top: Math.random() * 100,
      duration: 8 + Math.random() * 8,
      delay: Math.random() * 5,
    }));
  }, [letters, count]);

  return (
    <div
      className={`fixed inset-0 overflow-hidden pointer-events-none z-0 ${className}`}
      style={{ opacity }}
    >
      {items.map((it, i) => (
        <motion.span
          key={i}
          className={`absolute font-display text-brown-600 select-none ${blur ? "blur-[1px]" : ""}`}
          style={{
            fontSize: `${it.size}px`,
            left: `${it.left}%`,
            top: `${it.top}%`,
          }}
          animate={{ y: [0, -18, 0], opacity: [0.4, 0.85, 0.4] }}
          transition={{
            duration: it.duration,
            repeat: Infinity,
            delay: it.delay,
            ease: "easeInOut",
          }}
        >
          {it.letter}
        </motion.span>
      ))}
    </div>
  );
};

export default ArabicLettersBg;
