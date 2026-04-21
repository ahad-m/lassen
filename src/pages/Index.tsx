/**
 * الصفحة الرئيسية — لَسِنْ
 */
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Heart, PenLine, Clock, BookOpen, MessageSquareText, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import OrnamentalDivider from "@/components/OrnamentalDivider";

const FIRST_PAGE = "/mood";

const features = [
  { title: "مزاج اليوم",     description: "اكتب مشاعرك واحصل على أبيات شعرية تعبّر عنك", icon: Heart,             url: "/mood" },
  { title: "رحلة عبر الزمن", description: "شاهد كيف تطور التعبير عن المشاعر عبر العصور", icon: Clock,             url: "/journey" },
  { title: "تفسير الأبيات",  description: "أدخل بيتاً شعرياً واحصل على شرح مبسّط",        icon: MessageSquareText, url: "/interpret" },
  { title: "كتابة الأبيات",  description: "ولّد أبيات شعرية أو أكمل بيتاً ناقصاً",        icon: PenLine,           url: "/write" },
  { title: "كنوز الكلمات",   description: "اكتشف معاني الكلمات واستخداماتها الشعرية",     icon: BookOpen,          url: "/treasures" },
];

const POETRY_LETTERS = ["ش", "ع", "ر"];

const HeroFloatingLetters = () => {
  const items = Array.from({ length: 22 }).map((_, i) => {
    const letter = POETRY_LETTERS[i % POETRY_LETTERS.length];
    const cols = 5; const rows = 5;
    const col = i % cols; const row = Math.floor(i / cols) % rows;
    return {
      letter, size: 38 + Math.random() * 30,
      left: (col / (cols - 1)) * 100 + (Math.random() - 0.5) * 10,
      top:  (row / (rows - 1)) * 100 + (Math.random() - 0.5) * 10,
      duration: 12 + Math.random() * 10, delay: Math.random() * 5,
    };
  });
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {items.map((it, i) => (
        <motion.span key={i} className="absolute font-display text-gradient-gold select-none"
          style={{ fontSize: `${it.size}px`, left: `${it.left}%`, top: `${it.top}%`, opacity: 0.16 }}
          animate={{ y: [0,-18,0], x: [0,6,-4,0], rotate: [0,3,-3,0], opacity: [0.12,0.22,0.12] }}
          transition={{ duration: it.duration, repeat: Infinity, delay: it.delay, ease: "easeInOut" }}
        >{it.letter}</motion.span>
      ))}
    </div>
  );
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.6, ease: "easeOut" as const } }),
};

const FeatureTabs = ({ onSelect, className = "" }: { onSelect: (url: string) => void; className?: string }) => (
  <div className={`mx-auto w-full max-w-[640px] flex flex-wrap justify-center gap-x-6 gap-y-2.5 ${className}`}>
    {features.map((feature, i) => (
      <motion.button key={`tab-${feature.url}`}
        initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
        transition={{ delay: 0.04 * i, duration: 0.35 }}
        onClick={() => onSelect(feature.url)}
        className="inline-flex items-center gap-1.5 font-kufi text-sm text-brown-700/90 transition-colors hover:text-brown-900"
      >
        <feature.icon className="h-3.5 w-3.5" />
        <span>{feature.title}</span>
      </motion.button>
    ))}
  </div>
);

// ── خريطة الميزات — دائرة مركزية مع 5 بطاقات في نفس الصف ──────────────────────
const RoadmapFeatures = ({ onSelect }: { onSelect: (url: string) => void }) => {

  const FeatureCard = ({ feature, delay }: { feature: typeof features[0]; delay: number }) => (
    <motion.button
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.4 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      onClick={() => onSelect(feature.url)}
      className="group flex flex-col items-center gap-2.5 p-4 rounded-2xl bg-brown-soft border border-brown-300/50 shadow-[var(--shadow-soft)] hover:border-brown-500/50 hover:shadow-[var(--shadow-warm)] transition-all text-center"
      style={{ width: "140px", minHeight: "140px" }}
    >
      <div className="w-9 h-9 rounded-full bg-brown-200/60 border border-brown-300/40 flex items-center justify-center group-hover:bg-brown-300/50 transition-colors flex-shrink-0">
        <feature.icon className="h-4 w-4 text-brown-700" />
      </div>
      <span className="font-kufi text-[13px] text-brown-800 font-medium leading-tight">{feature.title}</span>
      <p className="font-body text-[10px] text-brown-500/80 leading-relaxed">{feature.description}</p>
    </motion.button>
  );

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col items-center gap-0">

      {/* الدائرة المركزية */}
      <motion.div
        initial={{ opacity: 0, scale: 0.7 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
      >
        <div className="w-24 h-24 rounded-full bg-brown-gradient flex flex-col items-center justify-center shadow-[var(--shadow-warm)] border-2 border-brown-600/40">
          <span className="font-display text-2xl text-primary-foreground">لَسِنْ</span>
          <span className="font-kufi text-[9px] text-primary-foreground/70 mt-0.5">رحلة الشعر</span>
        </div>
      </motion.div>

      {/* خط عمودي من الدائرة للأسفل */}
      <motion.div
        initial={{ scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true }}
        transition={{ duration: 0.3, delay: 0.4 }}
        className="w-px h-10 bg-brown-300/60 origin-top"
      />

      {/* الخط الأفقي الذي يربط كل البطاقات */}
      <motion.div
        initial={{ scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="w-full max-w-3xl h-px bg-brown-300/50 origin-center"
      />

      {/* خطوط عمودية صغيرة فوق كل بطاقة */}
      <div className="w-full max-w-3xl flex justify-between px-[70px]">
        {features.map((_, i) => (
          <motion.div key={i}
            initial={{ scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true }}
            transition={{ duration: 0.25, delay: 0.6 + i * 0.07 }}
            className="w-px h-8 bg-brown-300/50 origin-top"
          />
        ))}
      </div>

      {/* البطاقات الخمس في نفس الصف */}
      <div className="w-full flex flex-wrap justify-center gap-4">
        {features.map((feature, i) => (
          <FeatureCard key={feature.url} feature={feature} delay={0.55 + i * 0.08} />
        ))}
      </div>

    </div>
  );
};


const Index = () => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen relative bg-warm-page">
      <section className="relative z-20 px-6 pt-6">
        <div className="max-w-6xl mx-auto space-y-1">
          <FeatureTabs onSelect={(url) => navigate(url)} className="mb-0" />
          <div className="mx-auto w-full max-w-[640px] flex items-center justify-center gap-2">
            <div className="h-px flex-1 bg-brown-400/50" />
            <span className="text-brown-500 text-lg">✦</span>
            <div className="h-px flex-1 bg-brown-400/50" />
          </div>
        </div>
      </section>

      <section className="relative min-h-screen flex items-center justify-center px-6 overflow-hidden">
        <HeroFloatingLetters />
        <div className="relative z-10 text-center max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9 }} className="space-y-6">
            <h1 className="font-display text-7xl sm:text-8xl md:text-9xl leading-none tracking-wide" style={{ color: "hsl(25, 50%, 28%)" }}>لَسِنْ</h1>
            <div className="flex items-center justify-center gap-3">
              <div className="h-px w-16 bg-brown-400/50" />
              <span className="text-brown-500 text-lg">✦</span>
              <div className="h-px w-16 bg-brown-400/50" />
            </div>
            <motion.blockquote initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 1 }}
              className="font-amiri italic text-lg sm:text-xl md:text-2xl text-brown-700/90 leading-loose px-4">
              دُنياكَ لَو حاوَرَتْكَ ناطِقَةً
              <span className="mx-3 text-brown-400">…</span>
              خاطَبْتَ مِنْها بَليغَةً لَسِنَه
            </motion.blockquote>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="space-y-2 pt-4">
              <p className="font-kufi text-base sm:text-lg text-brown-600 max-w-xl mx-auto">رحلة تفاعلية تعيد اكتشاف الشعر العربي بأسلوب عصري وسلس</p>
              <p className="font-body text-sm text-brown-500/80 max-w-lg mx-auto">من المعلّقات إلى الشعر الحديث — اشعر، اكتب، واستكشف جمال اللغة</p>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 }} className="flex flex-wrap gap-3 justify-center pt-6">
              <Button size="lg" className="font-ui text-base bg-brown-gradient text-primary-foreground gap-2 px-8 rounded-full glow-warm hover:shadow-[var(--shadow-warm)] border border-brown-600/30" onClick={() => navigate(FIRST_PAGE)}>
                ابدأ الرحلة <ArrowLeft className="h-4 w-4" />
              </Button>
              <Button size="lg" variant="outline" className="font-ui text-base border-brown-400/50 text-brown-700 hover:bg-brown-100/50 gap-2 px-8 rounded-full"
                onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}>
                استكشف المزايا
              </Button>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <section id="features" className="py-20 px-6 relative">
        <div className="max-w-6xl mx-auto">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} className="text-center mb-8">
            <motion.h2 variants={fadeUp} custom={0} className="font-display text-3xl md:text-4xl text-gradient-brown mb-3">خمس تجارب فريدة</motion.h2>
            <motion.p variants={fadeUp} custom={1} className="font-kufi text-brown-600 max-w-lg mx-auto">كل تجربة صُمّمت لتقرّبك من الشعر العربي بطريقة مختلفة</motion.p>
          </motion.div>
          <OrnamentalDivider />
          <div className="flex justify-center mt-12">
            <RoadmapFeatures onSelect={(url) => navigate(url)} />
          </div>
        </div>
      </section>

      <section className="py-20 px-6 relative">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <motion.h2 variants={fadeUp} custom={0} className="font-display text-3xl md:text-4xl text-gradient-brown mb-6">لماذا لَسِنْ؟</motion.h2>
            <motion.p variants={fadeUp} custom={1} className="font-body text-brown-700/80 max-w-2xl mx-auto leading-loose mb-12">
              نؤمن أن الشعر ليس حكراً على المتخصصين. هو مرآة مشاعرنا وتاريخنا ولغتنا.
              صمّمنا لَسِنْ ليكون بوابتك إلى عالم الشعر بلا تعقيد، بلا حواجز، وبكل متعة.
            </motion.p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { title: "بسيط وسهل",   desc: "واجهة سلسة تجعل اكتشاف الشعر ممتعاً للجميع" },
                { title: "تفاعلي وذكي", desc: "تقنيات حديثة تفهم مشاعرك وتقدّم لك ما يناسبك" },
                { title: "ثقافي وأصيل", desc: "محتوى غني يربطك بجذور اللغة العربية وتراثها" },
              ].map((item, i) => (
                <motion.div key={i} variants={fadeUp} custom={i + 2} className="p-6 rounded-2xl bg-card/50 border border-brown-200/40 backdrop-blur-sm">
                  <h3 className="font-display text-xl text-brown-700 mb-2">{item.title}</h3>
                  <p className="font-body text-sm text-brown-600/80">{item.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <section className="py-20 px-6 relative">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="max-w-3xl mx-auto rounded-3xl p-12 text-center bg-brown-gradient glow-warm border border-brown-600/30">
          <h2 className="font-display text-3xl text-primary-foreground mb-4">ابدأ تجربتك الأولى في اكتشاف الشعر ومعانيه</h2>
          <p className="font-kufi text-primary-foreground/80 mb-8">اختر نقطة انطلاقتك ولنخطُ معاً في عالم الكلمة</p>
          <Button size="lg" className="font-ui bg-card text-brown-700 hover:bg-card/90 gap-2 px-10 rounded-full" onClick={() => navigate(FIRST_PAGE)}>
            ابدأ الآن <ArrowLeft className="h-4 w-4" />
          </Button>
        </motion.div>
      </section>

      <footer className="py-8 px-6 text-center border-t border-brown-200/40">
        <p className="font-display text-base text-brown-600/70">لَسِنْ ... حيث يلتقي الشعر بالتقنية ✦</p>
      </footer>
    </div>
  );
};

export default Index;