/**
 * صفحة كتابة الأبيات الشعرية — Help Me Write
 * — توليد الأبيات + إكمال البيت
 * — auto-scroll للنتائج + سجل لكل ميزة (يمين: العنوان، يسار: السجلّ)
 * — زر تنقل: التالي = كنوز الكلمات
 */
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PenLine, Wand2, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PageLayout from "@/components/PageLayout";
import ArabicLettersBg from "@/components/ArabicLettersBg";
import OrnamentalDivider from "@/components/OrnamentalDivider";
import PageNavButton from "@/components/PageNavButton";
import { useHistory } from "@/contexts/HistoryContext";
import { APIError, completeVerse, generateVerse, type CompleteVerseResponse } from "@/services/api";

// === نقاط ربط النماذج (لا تغيّر بنية التواقيع) ================
async function generatePoetry(idea: string): Promise<string> {
  const response = await generateVerse({
    idea,
    meter_num: 1, // حاليًا نبدأ بالبحر الافتراضي (الطويل)
    num_verses: 4,
  });

  if (!response.success) {
    throw new Error(response.message || "تعذّر توليد الأبيات.");
  }

  const verses = (response.verses || []).filter((v) => v.trim().length > 0);
  if (verses.length === 0) {
    throw new Error("لم يتم توليد أبيات صالحة، حاول بفكرة أخرى.");
  }

  const meterLine = response.meter ? `البحر: ${response.meter}\n\n` : "";
  return `${meterLine}${verses.join("\n")}`;
}
interface CompletePoemResult {
  text: string;
  alternatives: NonNullable<CompleteVerseResponse["alternatives"]>;
  currentIndex: number;
  totalCandidates: number;
}
type CompleteAlternative = NonNullable<CompleteVerseResponse["alternatives"]>[number];

function buildCompleteResultText(
  alt: NonNullable<CompleteVerseResponse["alternatives"]>[number],
  totalCandidates: number,
  rank: number
): string {
  const meta = alt.meta;
  const poetLine = `الشاعر: ${meta?.poet || "مجهول"}\n`;
  const sourceLine = alt.source === "web"
    ? `المصدر: ${alt.source_label || "الديوان"}\n`
    : "المصدر: قاعدة البيانات\n";
  const header = `${sourceLine}${poetLine}`;
  const hint = totalCandidates > 1 ? `\nالنتيجة ${rank} من ${totalCandidates}\n` : "\n";
  const poemLines = (alt.poem_verses || []).map((v) => v.verse || "").filter(Boolean).join("\n");
  return `${header}${hint}${poemLines}`.trim();
}

function ordinalLabel(rank: number): string {
  if (rank === 1) return "الأولى";
  if (rank === 2) return "الثانية";
  if (rank === 3) return "الثالثة";
  return `${rank}`;
}

async function completePoem(partial: string): Promise<CompletePoemResult> {
  const response = await completeVerse(partial);
  if (!response.success) {
    throw new Error(response.message || "تعذّر إكمال البيت.");
  }

  if (response.found === false) {
    throw new Error(response.message || "هذا البيت غير موجود في قاعدة البيانات.");
  }

  const alternatives: CompleteAlternative[] = Array.isArray(response.alternatives)
    ? response.alternatives.map((alt) => {
        const source: CompleteAlternative["source"] = alt.source === "web" ? "web" : "database";
        return {
          ...alt,
          source,
          source_label: alt.source_label || (source === "web" ? "الديوان" : "قاعدة البيانات"),
        };
      })
    : [];
  const fallbackAlt: CompleteAlternative = {
    rank: 1,
    poem_verses: response.poem_verses || [],
    meta: response.meta,
    matched_verse: undefined,
    source: "database",
    source_label: "قاعدة البيانات",
  };
  const finalAlternatives: CompleteAlternative[] = alternatives.length > 0 ? alternatives : [fallbackAlt];
  if ((finalAlternatives[0]?.poem_verses || []).length === 0) {
    throw new Error(response.message || "تم العثور على البيت لكن لم نتمكن من عرض القصيدة.");
  }
  const totalCandidates = response.total_candidates || finalAlternatives.length;
  const currentIndex = Math.max(0, Math.min(response.current_index || 0, finalAlternatives.length - 1));
  const selectedAlternative = finalAlternatives[currentIndex] || fallbackAlt;
  const text = buildCompleteResultText(
    selectedAlternative,
    totalCandidates,
    (selectedAlternative.rank || currentIndex + 1)
  );
  return {
    text,
    alternatives: finalAlternatives,
    currentIndex,
    totalCandidates,
  };
}

interface HistoryEntry {
  id: string;
  title: string;
  prompt: string;
  result: string;
  alternatives?: NonNullable<CompleteVerseResponse["alternatives"]>;
  currentIndex?: number;
  totalCandidates?: number;
}

const summarize = (text: string, max = 30) => {
  const t = text.trim().replace(/\s+/g, " ");
  return t.length > max ? t.slice(0, max) + "…" : t;
};

const ResultCard = ({
  entry,
  onSelectAlternative,
}: {
  entry: HistoryEntry;
  onSelectAlternative?: (index: number) => void;
}) => (
  <div className="glass-card-warm p-5 rounded-xl">
    <p className="font-ui text-xs text-brown-500 mb-2">— {entry.title}</p>
    <p className="font-amiri text-base text-brown-700 whitespace-pre-wrap leading-loose text-center">
      {entry.result}
    </p>
    {!!entry.alternatives && entry.totalCandidates && entry.totalCandidates > 1 && (
      <div className="mt-4 space-y-2">
        <p className="font-ui text-xs text-brown-600 text-center">اختر من أقرب القصائد:</p>
        <div className="flex items-center justify-center gap-2">
          {entry.alternatives.map((alt, idx) => {
            const isActive = (entry.currentIndex || 0) === idx;
            const label = ordinalLabel(alt.rank || idx + 1);
            return (
              <Button
                key={`${entry.id}-alt-${idx}`}
                variant={isActive ? "default" : "outline"}
                size="sm"
                className={
                  isActive
                    ? "bg-brown-gradient text-primary-foreground"
                    : "border-brown-300/60 text-brown-700 hover:bg-brown-100/50"
                }
                onClick={() => onSelectAlternative?.(idx)}
              >
                {`القصيدة ${label}`}
              </Button>
            );
          })}
        </div>
      </div>
    )}
  </div>
);

interface FeatureSectionProps {
  label: string;
  placeholder: string;
  buttonIdle: string;
  buttonLoading: string;
  buttonIcon: React.ReactNode;
  historyTitle: string;
  history: HistoryEntry[];
  activeId: string | null;
  setActiveId: (id: string | null) => void;
  input: string;
  setInput: (v: string) => void;
  isLoading: boolean;
  onSubmit: () => void;
  onSelectAlternative?: (entryId: string, index: number) => void;
}

const FeatureSection = ({
  label, placeholder, buttonIdle, buttonLoading, buttonIcon,
  historyTitle, history, activeId, setActiveId,
  input, setInput, isLoading, onSubmit,
  onSelectAlternative,
}: FeatureSectionProps) => {
  const active = history.find(h => h.id === activeId) ?? history[0] ?? null;
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (active) {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [active?.id]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* اليمين: الميزة + الناتج النشط */}
      <div className="lg:col-span-2 order-1">
        <div className="glass-card-warm p-8">
          <label className="font-ui text-sm text-brown-700 mb-3 block">{label}</label>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            className="font-body min-h-[100px] bg-background/60 border-brown-300/40 focus:border-brown-500/60"
          />
          <Button
            onClick={onSubmit}
            disabled={!input.trim() || isLoading}
            className="mt-4 font-ui bg-brown-gradient text-primary-foreground gap-2 rounded-full px-6"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : buttonIcon}
            {isLoading ? buttonLoading : buttonIdle}
          </Button>
        </div>

        <div ref={resultsRef} />
        {active && (
          <div className="mt-6">
            <OrnamentalDivider className="my-4" />
            <AnimatePresence mode="wait">
              <motion.div
                key={active.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
              >
                <ResultCard
                  entry={active}
                  onSelectAlternative={
                    onSelectAlternative ? (index) => onSelectAlternative(active.id, index) : undefined
                  }
                />
              </motion.div>
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* اليسار: السجل القابل للنقر */}
      <aside className="order-2 lg:sticky lg:top-20 lg:self-start">
        <div className="glass-card p-4">
          <h3 className="font-kufi text-sm text-brown-700 mb-3">{historyTitle}</h3>
          {history.length === 0 ? (
            <p className="font-body text-xs text-brown-500/60">لا يوجد سجل بعد</p>
          ) : (
            <ul className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin">
              {history.map(e => {
                const isActive = (active?.id ?? history[0]?.id) === e.id;
                return (
                  <li key={e.id}>
                    <button
                      onClick={() => setActiveId(e.id)}
                      className={`w-full text-right text-xs font-ui px-3 py-2 rounded-lg border transition-all ${
                        isActive
                          ? "bg-brown-gradient text-primary-foreground border-brown-600/40 shadow-[var(--shadow-soft)]"
                          : "bg-brown-100/40 text-brown-700 border-brown-200/40 hover:bg-brown-100/70"
                      }`}
                    >
                      {e.title}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>
    </div>
  );
};

const HelpMeWrite = () => {
  const [generateInput, setGenerateInput] = useState("");
  const [completeInput, setCompleteInput] = useState("");
  const [generateHistory, setGenerateHistory] = useState<HistoryEntry[]>([]);
  const [completeHistory, setCompleteHistory] = useState<HistoryEntry[]>([]);
  const [generateActiveId, setGenerateActiveId] = useState<string | null>(null);
  const [completeActiveId, setCompleteActiveId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [completeError, setCompleteError] = useState<string | null>(null);
  const { addHistoryItem } = useHistory();

  const selectCompleteAlternative = (entryId: string, selectedIndex: number) => {
    setCompleteHistory((prev) =>
      prev.map((entry) => {
        if (entry.id !== entryId || !entry.alternatives || entry.alternatives.length <= 1) {
          return entry;
        }
        if (selectedIndex < 0 || selectedIndex >= entry.alternatives.length) {
          return entry;
        }
        const nextAlt = entry.alternatives[selectedIndex];
        return {
          ...entry,
          currentIndex: selectedIndex,
          result: buildCompleteResultText(
            nextAlt,
            entry.totalCandidates || entry.alternatives.length,
            nextAlt.rank || selectedIndex + 1
          ),
        };
      })
    );
  };

  const handleGenerate = async () => {
    if (!generateInput.trim()) return;
    setIsGenerating(true);
    setGenerateError(null);
    addHistoryItem("write", "ساعدني أكتب", generateInput);
    try {
      const result = await generatePoetry(generateInput);
      const entry: HistoryEntry = {
        id: crypto.randomUUID(),
        title: summarize(generateInput),
        prompt: generateInput,
        result,
      };
      setGenerateHistory(prev => [entry, ...prev]);
      setGenerateActiveId(entry.id);
      setGenerateInput("");
    } catch (error) {
      const message =
        error instanceof APIError
          ? error.message
          : error instanceof Error
            ? error.message
            : "تعذّر توليد الأبيات حالياً. حاول مرة أخرى.";
      setGenerateError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleComplete = async () => {
    if (!completeInput.trim()) return;
    setIsCompleting(true);
    setCompleteError(null);
    addHistoryItem("write", "ساعدني أكتب", completeInput);
    try {
      const result = await completePoem(completeInput);
      const entry: HistoryEntry = {
        id: crypto.randomUUID(),
        title: summarize(completeInput),
        prompt: completeInput,
        result: result.text,
        alternatives: result.alternatives,
        currentIndex: result.currentIndex,
        totalCandidates: result.totalCandidates,
      };
      setCompleteHistory(prev => [entry, ...prev]);
      setCompleteActiveId(entry.id);
      setCompleteInput("");
    } catch (error) {
      const message =
        error instanceof APIError
          ? error.message
          : error instanceof Error
            ? error.message
            : "تعذّر إكمال البيت حالياً. حاول مرة أخرى.";
      setCompleteError(message);
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <PageLayout title="كتابة الأبيات الشعرية">
      <div className="relative min-h-[calc(100vh-3.5rem)] p-6">
        <ArabicLettersBg letters={["ك", "ت", "ا", "ب", "ة"]} count={18} opacity={0.06} />
        <div className="max-w-5xl mx-auto relative z-10">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
            <PenLine className="h-10 w-10 text-brown-600 mx-auto mb-4" />
            <h2 className="font-display text-3xl text-gradient-brown mb-2">كتابة الأبيات الشعرية</h2>
            <p className="font-kufi text-brown-600">ولّد أبياتاً شعرية أو أكمل بيتاً ناقصاً</p>
          </motion.div>

          <Tabs defaultValue="generate" className="w-full" dir="rtl">
            <TabsList className="w-full max-w-md mx-auto grid grid-cols-2 bg-card/70 border border-brown-200/50 mb-8 h-12 rounded-xl">
              <TabsTrigger value="generate" className="font-ui data-[state=active]:bg-brown-gradient data-[state=active]:text-primary-foreground rounded-lg">
                توليد أبيات
              </TabsTrigger>
              <TabsTrigger value="complete" className="font-ui data-[state=active]:bg-brown-gradient data-[state=active]:text-primary-foreground rounded-lg">
                إكمال بيت
              </TabsTrigger>
            </TabsList>

            <TabsContent value="generate">
              {generateError && (
                <div className="max-w-2xl mx-auto mb-4 rounded-lg border border-red-300/40 bg-red-100/30 p-3">
                  <p className="font-ui text-sm text-red-700">{generateError}</p>
                </div>
              )}
              <FeatureSection
                label="اكتب فكرة أو موضوعاً"
                placeholder="مثال: الشوق إلى الوطن، جمال الصحراء، الحب الأول..."
                buttonIdle="ولّد أبيات"
                buttonLoading="جارٍ التوليد..."
                buttonIcon={<Wand2 className="h-4 w-4" />}
                historyTitle="سجل التوليد"
                history={generateHistory}
                activeId={generateActiveId}
                setActiveId={setGenerateActiveId}
                input={generateInput}
                setInput={setGenerateInput}
                isLoading={isGenerating}
                onSubmit={handleGenerate}
              />
            </TabsContent>

            <TabsContent value="complete">
              {completeError && (
                <div className="max-w-2xl mx-auto mb-4 rounded-lg border border-red-300/40 bg-red-100/30 p-3">
                  <p className="font-ui text-sm text-red-700">{completeError}</p>
                </div>
              )}
              <FeatureSection
                label="اكتب بيتاً ناقصاً أو شطراً"
                placeholder="مثال: إذا المرءُ لا يرعاكَ إلا تكلُّفاً..."
                buttonIdle="أكمل البيت"
                buttonLoading="جارٍ البحث..."
                buttonIcon={<ArrowLeft className="h-4 w-4" />}
                historyTitle="سجل الإكمال"
                history={completeHistory}
                activeId={completeActiveId}
                setActiveId={setCompleteActiveId}
                input={completeInput}
                setInput={setCompleteInput}
                isLoading={isCompleting}
                onSubmit={handleComplete}
                onSelectAlternative={selectCompleteAlternative}
              />
            </TabsContent>
          </Tabs>

          <div className="mt-12 flex justify-center">
            <PageNavButton to="/treasures" label="التالي: كنوز الكلمات" />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default HelpMeWrite;
