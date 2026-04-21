/**
 * PageNavButton — زر تنقّل موحّد بين صفحات الميزات
 * يعرض اسم الصفحة التالية بنمط بنّي زخرفي ثابت في كل الصفحات.
 */
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Home } from "lucide-react";

interface Props {
  to: string;
  label: string;
  variant?: "next" | "home";
  position?: "inline" | "fixed-bottom-left";
}

const PageNavButton = ({
  to,
  label,
  variant = "next",
  position = "inline",
}: Props) => {
  const navigate = useNavigate();
  const Icon = variant === "home" ? Home : ArrowLeft;

  const baseClasses =
    "group inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-ui text-sm " +
    "bg-brown-gradient text-primary-foreground shadow-[var(--shadow-soft)] " +
    "hover:shadow-[var(--shadow-warm)] transition-all duration-300 hover:gap-3 " +
    "border border-brown-600/30";

  const positionClass =
    position === "fixed-bottom-left"
      ? "fixed bottom-6 left-6 z-30"
      : "";

  return (
    <motion.button
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => navigate(to)}
      className={`${baseClasses} ${positionClass}`}
    >
      <span>{label}</span>
      <Icon className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
    </motion.button>
  );
};

export default PageNavButton;
