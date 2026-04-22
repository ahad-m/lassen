/**
 * لعبة: تحدي حفظ الأبيات
 * - 5 جولات
 * - كل جولة تعرض بيتين + اسم الشاعر لمدة 5 ثوانٍ
 * - تختفي الأبيات ويكتب المستخدم ما حفظه
 * - تقييم محلي داخل الجلسة فقط
 * 
 * PoetryMemoryGame.tsx
 */
import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, RefreshCw, Timer, Trophy, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import PageLayout from "@/components/PageLayout";
import ArabicLettersBg from "@/components/ArabicLettersBg";
import OrnamentalDivider from "@/components/OrnamentalDivider";
import { APIError, getPoetryGameRound, type PoetryGameRoundResponse } from "@/services/api";

const TOTAL_ROUNDS = 5;
const MEMORIZE_SECONDS = 5;

function normalizeForCompare(text: string): string {
  return (text || "")
    .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g, "")
    .replace(/[إأآٱ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/[^\u0600-\u06FF\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function compareVerses(expected: string[], userInput: string): { ok: boolean; similarity: number } {
  const expectedNorm = normalizeForCompare(expected.join("\n"));
  const actualNorm = normalizeForCompare(userInput);
  if (!expectedNorm || !actualNorm) {
    return { ok: false, similarity: 0 };
  }
  if (expectedNorm === actualNorm) {
    return { ok: true, similarity: 1 };
  }
  const expTokens = expectedNorm.split(" ").filter(Boolean);
  const actTokens = new Set(actualNorm.split(" ").filter(Boolean));
  if (!expTokens.length) {
    return { ok: false, similarity: 0 };
  }
  const matched = expTokens.filter((t) => actTokens.has(t)).length;
  const similarity = matched / expTokens.length;
  return { ok: similarity >= 0.9, similarity };
}

type Phase = "idle" | "memorize" | "answer" | "roundResult" | "finished";

interface RoundResult {
  round: number;
  poem_id: string;
  poet: string;
  expected: string[];
  answer: string;
  ok: boolean;
  similarity: number;
}

const PoetryMemoryGame = () => {
  const [phase, setPhase] = useState<Phase>("idle");
  const [currentRound, setCurrentRound] = useState(1);
  const [countdown, setCountdown] = useState(MEMORIZE_SECONDS);
  const [roundData, setRoundData] = useState<PoetryGameRoundResponse | null>(null);
  const [answer, setAnswer] = useState("");
  const [loadingRound, setLoadingRound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<RoundResult[]>([]);

  const score = useMemo(() => results.filter((r) => r.ok).length, [results]);

  const fetchRound = async () => {
    setLoadingRound(true);
    setError(null);
    try {
      const usedPoemIds = results.map((r) => r.poem_id).filter(Boolean);
      const data = await getPoetryGameRound({ exclude_poem_ids: usedPoemIds });
      setRoundData(data);
      setCountdown(MEMORIZE_SECONDS);
      setAnswer("");
      setPhase("memorize");
    } catch (e) {
      setError(e instanceof APIError ? e.message : "تعذر جلب الجولة، حاول مرة أخرى.");
    } finally {
      setLoadingRound(false);
    }
  };

  const startGame = async () => {
    setResults([]);
    setCurrentRound(1);
    setPhase("idle");
    await fetchRound();
  };

  const nextRound = async () => {
    if (currentRound >= TOTAL_ROUNDS) {
      setPhase("finished");
      return;
    }
    setCurrentRound((n) => n + 1);
    await fetchRound();
  };

  const submitAnswer = () => {
    if (!roundData) return;
    const verseStrings = roundData.verses.map((v) => v.verse);
    const { ok, similarity } = compareVerses(verseStrings, answer);
    setResults((prev) => [
      ...prev,
      {
        round: currentRound,
        poem_id: roundData.poem_id || "",
        poet: roundData.poet_name || "مجهول",
        expected: verseStrings,
        answer,
        ok,
        similarity,
      },
    ]);
    setPhase("roundResult");
  };

  useEffect(() => {
    if (phase !== "memorize") return;
    if (countdown <= 0) {
      setPhase("answer");
      return;
    }
    const t = setTimeout(() => setCountdown((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [phase, countdown]);

  return (
    <PageLayout title="لعبة حفظ الأبيات">
      <div className="relative min-h-[calc(100vh-3.5rem)] p-6">
        <ArabicLettersBg letters={["ح", "ف", "ظ", "ش", "ع", "ر"]} count={20} opacity={0.06} />
        <div className="max-w-4xl mx-auto relative z-10">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
            <Brain className="h-10 w-10 text-brown-600 mx-auto mb-3 animate-float" />
            <h2 className="font-display text-3xl text-gradient-brown mb-2">تحدّي حفظ الأبيات</h2>
            <p className="font-kufi text-brown-600">
              خمس جولات — في كل جولة احفظ بيتين خلال 5 ثوانٍ ثم اكتبهما
            </p>
          </motion.div>

          <div className="glass-card-warm p-6 rounded-2xl">
            <div className="flex items-center justify-between gap-4 mb-4">
              <span className="font-ui text-sm text-brown-700">
                الجولة {Math.min(currentRound, TOTAL_ROUNDS)} / {TOTAL_ROUNDS}
              </span>
              <span className="font-ui text-sm text-brown-700 flex items-center gap-1">
                <Trophy className="h-4 w-4" />
                النقاط: {score}
              </span>
            </div>

            <OrnamentalDivider className="my-4" />

            {error && (
              <div className="mb-4 rounded-lg border border-red-300/40 bg-red-100/30 p-3">
                <p className="font-ui text-sm text-red-700">{error}</p>
              </div>
            )}

            <AnimatePresence mode="wait">
              {phase === "idle" && (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="text-center space-y-4"
                >
                  <p className="font-body text-brown-700">جاهز للتحدّي؟</p>
                  <Button
                    className="font-ui bg-brown-gradient text-primary-foreground rounded-full px-8"
                    onClick={startGame}
                    disabled={loadingRound}
                  >
                    {loadingRound ? "جارٍ التحضير..." : "ابدأ اللعبة"}
                  </Button>
                </motion.div>
              )}

              {phase === "memorize" && roundData && (
                <motion.div
                  key="memorize"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="space-y-4"
                >
                  <div className="flex items-center justify-center gap-2 text-brown-700">
                    <Timer className="h-4 w-4" />
                    <span className="font-ui text-sm">الوقت المتبقي: {countdown} ث</span>
                  </div>
                  <div className="p-5 rounded-xl border border-brown-300/40 bg-brown-50/50 text-center space-y-3">
                    <p className="font-amiri text-lg text-brown-800 leading-loose">{roundData.verses[0]?.verse}</p>
                    <p className="font-amiri text-lg text-brown-800 leading-loose">{roundData.verses[1]?.verse}</p>
                    <p className="font-ui text-xs text-brown-500">— {roundData.poet_name || "مجهول"}</p>
                  </div>
                </motion.div>
              )}

              {phase === "answer" && (
                <motion.div
                  key="answer"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="space-y-3"
                >
                  <p className="font-body text-brown-700 text-center">اكتب البيتين الآن من الذاكرة:</p>
                  <Textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder={"اكتب البيت الأول\nاكتب البيت الثاني"}
                    className="font-amiri min-h-[130px] text-base bg-background/70 border-brown-300/40"
                  />
                  <div className="flex justify-center">
                    <Button
                      className="font-ui bg-brown-gradient text-primary-foreground rounded-full px-8"
                      disabled={!answer.trim()}
                      onClick={submitAnswer}
                    >
                      تأكيد الإجابة
                    </Button>
                  </div>
                </motion.div>
              )}

              {phase === "roundResult" && (
                <motion.div
                  key="roundResult"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="text-center space-y-4"
                >
                  {results[results.length - 1]?.ok ? (
                    <p className="font-kufi text-green-700 flex items-center justify-center gap-2">
                      <CheckCircle2 className="h-5 w-5" />
                      ممتاز! إجابتك صحيحة
                    </p>
                  ) : (
                    <p className="font-kufi text-red-700 flex items-center justify-center gap-2">
                      <XCircle className="h-5 w-5" />
                      لم تُحسب هذه الجولة
                    </p>
                  )}

                  <div className="p-4 rounded-xl border border-brown-300/40 bg-brown-50/50 text-center space-y-2">
                    <p className="font-ui text-xs text-brown-500">
                      الشاعر: {results[results.length - 1]?.poet || "مجهول"}
                    </p>
                    {(results[results.length - 1]?.expected || []).map((v, i) => (
                      <p key={i} className="font-amiri text-base text-brown-800 leading-loose">
                        {v}
                      </p>
                    ))}
                  </div>

                  <Button className="font-ui bg-brown-gradient text-primary-foreground rounded-full px-8" onClick={nextRound}>
                    {currentRound >= TOTAL_ROUNDS ? "عرض النتيجة النهائية" : "الجولة التالية"}
                  </Button>
                </motion.div>
              )}

              {phase === "finished" && (
                <motion.div
                  key="finished"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center space-y-4"
                >
                  <p className="font-display text-2xl text-gradient-brown">انتهت اللعبة ✦</p>
                  <p className="font-kufi text-brown-700">
                    نتيجتك: {score} / {TOTAL_ROUNDS}
                  </p>
                  <div className="flex items-center justify-center gap-3">
                    <Button className="font-ui bg-brown-gradient text-primary-foreground rounded-full px-8" onClick={startGame}>
                      إعادة اللعب
                    </Button>
                    <Button
                      variant="outline"
                      className="font-ui border-brown-400/40 text-brown-700 rounded-full px-8"
                      onClick={() => {
                        setPhase("idle");
                        setCurrentRound(1);
                        setResults([]);
                        setAnswer("");
                        setRoundData(null);
                      }}
                    >
                      إنهاء
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="mt-6 flex justify-center">
            <Button
              variant="outline"
              className="font-ui border-brown-400/40 text-brown-700 rounded-full px-5 gap-2"
              onClick={startGame}
              disabled={loadingRound}
            >
              <RefreshCw className="h-4 w-4" />
              جلب أبيات جديدة
            </Button>
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default PoetryMemoryGame;
