/**
 * صفحة كنوز الكلمات — تصميم محدّث
 * اليمين: الكلمة + المعنى المختصر + أبرز المعاني + الاستخدام الشعري + الرمزية
 * اليسار: الأمثلة الشعرية
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Search, Volume2, Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import PageLayout from "@/components/PageLayout";
import ArabicLettersBg from "@/components/ArabicLettersBg";
import PageNavButton from "@/components/PageNavButton";
import { useHistory } from "@/contexts/HistoryContext";
import {
  explainWord, TreasuresResponse, MeaningEntry, APIError
} from "@/services/api";

// ── مؤشر الثقة ────────────────────────────────────────────────
const ConfidenceBadge = ({ level }: { level: string }) => {
  const map: Record<string, { label: string; color: string }> = {
    high:   { label: "تأكيد عالٍ",   color: "text-emerald-500 border-emerald-500/30" },
    medium: { label: "تأكيد معقول", color: "text-amber-500  border-amber-500/30"   },
    low:    { label: "كلمة نادرة",   color: "text-rose-400   border-rose-400/30"    },
  };
  const { label, color } = map[level] ?? map.medium;
  return (
    <span className={`text-[10px] font-ui border rounded-full px-2 py-0.5 ${color}`}>
      {label}
    </span>
  );
};

// ── بطاقة بيت شعري ────────────────────────────────────────────
const ExampleVerseCard = ({
  verse,
  index,
}: {
  verse: { verse: string; poet: string; source: "database" | "gpt" };
  index: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.08 }}
    className="p-4 rounded-xl bg-brown-50/40 border border-brown-200/40 space-y-2"
  >
    <blockquote className="font-amiri text-sm text-brown-700 leading-loose text-center">
      {verse.verse}
    </blockquote>
    <div className="flex items-center justify-between gap-2">
      {verse.poet && verse.poet !== "مجهول" && (
        <p className="font-ui text-[10px] text-brown-500/70">— {verse.poet}</p>
      )}
      {verse.source === "database" && (
        <span className="text-[9px] text-emerald-500/80 border border-emerald-400/20 rounded-full px-1.5 py-0.5 font-ui mr-auto">
          من قاعدة البيانات
        </span>
      )}
    </div>
  </motion.div>
);

// ── بطاقة معنى واحد ───────────────────────────────────────────
const MeaningCard = ({ meaning, index }: { meaning: MeaningEntry; index: number }) => (
  <div className="space-y-0.5">
    <div className="flex items-center gap-2 flex-wrap">
      <p className="font-ui text-xs text-brown-700 font-medium">{index + 1}. {meaning.title}</p>
      {meaning.source === "siwar" && (
        <span className="text-[9px] text-blue-500/70 border border-blue-400/20 rounded-full px-1.5 py-0.5 font-ui">
          معجم سوار
        </span>
      )}
    </div>
    <p className="font-body text-xs text-brown-600/80 leading-relaxed pr-3">
      {meaning.explanation}
    </p>
  </div>
);

// ── أيقونة القلم ──────────────────────────────────────────────
const PenIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
  </svg>
);

// =============================================================
interface WordEntry { id: string; data: TreasuresResponse }

const TreasuresOfWords = () => {
  const [input,       setInput]       = useState("");
  const [entries,     setEntries]     = useState<WordEntry[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isLoading,   setIsLoading]   = useState(false);
  const [error,       setError]       = useState<string | null>(null);
  const { addHistoryItem } = useHistory();

  const handleSearch = async (followup = false) => {
    const word = followup ? entries[activeIndex]?.data.word! : input.trim();
    if (!word) return;
    setIsLoading(true);
    setError(null);
    if (!followup) addHistoryItem("treasures", "كنوز الكلمات", word);

    try {
      const result = await explainWord(word, undefined, followup);
      if (result.status === "error") {
        setError(result.message || "تعذّر شرح هذه الكلمة");
        return;
      }
      const entry: WordEntry = { id: `${word}-${Date.now()}`, data: result };
      if (followup) {
        setEntries(prev => prev.map((e, i) => i === activeIndex ? entry : e));
      } else {
        setEntries(prev => [entry, ...prev]);
        setActiveIndex(0);
        setInput("");
      }
    } catch (e) {
      setError(e instanceof APIError ? e.message : "تعذّر الاتصال بالسيرفر");
    } finally {
      setIsLoading(false);
    }
  };

  const active = entries[activeIndex];

  return (
    <PageLayout title="كنوز الكلمات">
      <div className="relative min-h-[calc(100vh-3.5rem)] p-6">
        <ArabicLettersBg />
        <div className="max-w-6xl mx-auto relative z-10">

          {/* ── Header ── */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <BookOpen className="h-10 w-10 text-brown-600 mx-auto mb-4" />
            <h2 className="font-display text-3xl text-gradient-brown mb-2">كنوز الكلمات</h2>
            <p className="font-kufi text-brown-600">اكتب كلمة لاكتشاف كنوزها ومعانيها</p>
          </motion.div>

          {/* ── حقل الإدخال ── */}
          <div className="max-w-lg mx-auto mb-4">
            <div className="relative glass-card p-2 flex items-center gap-2 glow-gold">
              <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gold/40 pointer-events-none">
                <PenIcon />
              </div>
              <Input
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="مثال: عنقاء، النوى، سَلَوتُ..."
                className="font-display text-lg border-0 bg-transparent pr-10 focus-visible:ring-0"
                onKeyDown={e => e.key === "Enter" && handleSearch()}
                disabled={isLoading}
              />
              <Button
                onClick={() => handleSearch()}
                disabled={!input.trim() || isLoading}
                className="bg-primary hover:bg-primary/90 text-primary-foreground gap-2 shrink-0 font-ui"
              >
                {isLoading
                  ? <Loader2 className="h-4 w-4 animate-spin" />
                  : <Search className="h-4 w-4" />}
                اكتشف
              </Button>
            </div>
          </div>

          {/* ── رسالة الخطأ ── */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="max-w-lg mx-auto mb-6 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm text-center"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── الكتاب المفتوح: تصميم جديد ── */}
          <AnimatePresence mode="wait">
            {active ? (
              <motion.div
                key={active.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-0 max-w-5xl mx-auto"
              >

                {/* ══════════════════════════════════════════════
                    الصفحة اليمنى:
                    الكلمة + المعنى المختصر + أبرز المعاني
                    + الاستخدام الشعري + الرمزية
                ══════════════════════════════════════════════ */}
                <div className="glass-card-warm rounded-l-none md:rounded-r-2xl md:rounded-l-none p-7 flex flex-col gap-5 bg-gradient-to-br from-card to-brown-50/20">

                  {/* ── الكلمة + صوت + جمع + ثقة ── */}
                  <div className="flex flex-col items-center text-center gap-2 pb-4 border-b border-brown-200/40">
                    <Button
                      variant="ghost" size="icon"
                      className="text-brown-500 hover:bg-brown-100/50 mb-1"
                      onClick={() => {
                        const u = new SpeechSynthesisUtterance(active.data.word || "");
                        u.lang = "ar-SA";
                        speechSynthesis.speak(u);
                      }}
                    >
                      <Volume2 className="h-5 w-5" />
                    </Button>

                    <h3 className="font-display text-5xl md:text-6xl text-brown-800">
                      {active.data.word}
                    </h3>

                    {active.data.plural && (
                      <span className="text-xs font-ui text-brown-500/60 border border-brown-300/30 rounded-full px-3 py-0.5">
                        الجمع: <span className="text-brown-700 font-display">{active.data.plural}</span>
                      </span>
                    )}

                    <div className="flex gap-2 flex-wrap justify-center">
                      {active.data.confidence && <ConfidenceBadge level={active.data.confidence} />}
                    </div>
                  </div>

                  {/* ── المعنى المختصر (simple_tip) ── */}
                  {active.data.simple_tip && (
                    <div className="p-3 rounded-lg bg-brown-100/40 border border-brown-200/40">
                      <p className="font-body text-sm text-brown-700 leading-relaxed text-center">
                         {active.data.simple_tip}
                      </p>
                    </div>
                  )}

                  {/* ── أبرز المعاني ── */}
                  {active.data.meanings && active.data.meanings.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-ui text-xs text-brown-600 tracking-wider border-b border-brown-200/40 pb-1">
                        أبرز المعاني
                      </h4>
                      {active.data.meanings.map((m: MeaningEntry, i: number) => (
                        <MeaningCard key={i} meaning={m} index={i} />
                      ))}
                    </div>
                  )}

                  {/* ── الاستخدام الشعري ── */}
                  {active.data.poetic_usage && (
                    <div className="space-y-1">
                      <h4 className="font-ui text-xs text-brown-600 tracking-wider">الاستخدام الشعري</h4>
                      <p className="font-body text-xs text-brown-600/80 leading-relaxed">
                        {active.data.poetic_usage}
                      </p>
                    </div>
                  )}

                  {/* ── الرمزية ── */}
                  {active.data.symbolism && (
                    <div className="space-y-1">
                      <h4 className="font-ui text-xs text-brown-600 tracking-wider">الرمزية والدلالة</h4>
                      <p className="font-body text-xs text-brown-600/80 leading-relaxed">
                        {active.data.symbolism}
                      </p>
                    </div>
                  )}

                  {/* ── وضّح أكثر ── */}
                  <Button
                    variant="ghost" size="sm"
                    className="mt-auto text-xs text-brown-500/50 hover:text-brown-700 gap-1 self-center"
                    onClick={() => handleSearch(true)} disabled={isLoading}
                  >
                    <RefreshCw className="h-3 w-3" /> وضّح أكثر
                  </Button>
                </div>

                {/* ══════════════════════════════════════════════
                    الصفحة اليسرى: الأمثلة الشعرية فقط
                ══════════════════════════════════════════════ */}
                <div className="glass-card rounded-r-none md:rounded-l-2xl md:rounded-r-none p-7 flex flex-col gap-4 bg-gradient-to-bl from-card to-brown-50/10">

                  <h4 className="font-ui text-xs text-brown-600 tracking-wider border-b border-brown-200/40 pb-1">
                    أمثلة من الشعر العربي
                  </h4>

                  {active.data.example_verses && active.data.example_verses.length > 0 ? (
                    <div className="space-y-3">
                      {active.data.example_verses.map((v, i) => (
                        <ExampleVerseCard key={i} verse={v} index={i} />
                      ))}
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-center">
                      <p className="font-body text-xs text-brown-500/40 text-center">
                        لم تُوجد أمثلة شعرية
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            ) : (
              /* ── Empty State ── */
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="text-center py-20"
              >
                <BookOpen className="h-20 w-20 text-brown-300 mx-auto mb-4" />
                <p className="font-body text-brown-600/70 mb-2">
                  اكتب كلمة لاكتشاف كنوزها ومعانيها
                </p>
                <p className="font-body text-xs text-muted-foreground/30">
                  مثال: عنقاء • النوى • سَلَوتُ • مَثولَةَ
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── الكلمات السابقة ── */}
          {entries.length > 1 && (
            <div className="mt-8 flex flex-wrap gap-2 justify-center">
              {entries.map((e, i) => (
                <Button
                  key={e.id}
                  variant={i === activeIndex ? "default" : "outline"}
                  size="sm"
                  className={`font-display ${
                    i === activeIndex
                      ? "bg-primary text-primary-foreground"
                      : "border-brown-300/40 text-brown-700/60 hover:bg-brown-100/50"
                  }`}
                  onClick={() => setActiveIndex(i)}
                >
                  {e.data.word}
                </Button>
              ))}
            </div>
          )}

          <div className="mt-12 flex justify-center">
            <PageNavButton to="/" label="العودة إلى الصفحة الرئيسية" variant="home" />
          </div>

        </div>
      </div>
    </PageLayout>
  );
};

export default TreasuresOfWords;
