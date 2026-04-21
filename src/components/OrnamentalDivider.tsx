/**
 * OrnamentalDivider — فاصل زخرفي عربي بألوان بنية دافئة
 */
const OrnamentalDivider = ({ className = "" }: { className?: string }) => (
  <div className={`flex items-center justify-center gap-3 my-8 ${className}`}>
    <div className="h-px flex-1 bg-gradient-to-l from-brown-400/60 to-transparent" />
    <span className="text-brown-500 text-2xl font-display leading-none select-none">✦</span>
    <div className="h-px flex-1 bg-gradient-to-r from-brown-400/60 to-transparent" />
  </div>
);

export default OrnamentalDivider;
