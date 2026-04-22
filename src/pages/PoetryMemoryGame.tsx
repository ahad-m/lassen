/**
 * لعبة: تحدي حفظ الأبيات
 * - 5 جولات
 * - كل جولة تعرض بيتين + اسم الشاعر لمدة 5 ثوانٍ
 * - تختفي الأبيات ويكتب المستخدم ما حفظه
 * - تقييم تفصيلي: كل بيت + كل كلمة
 * - احتفال بمفرقعات عند النتيجة الكاملة 5/5
 * 
 * PoetryMemoryGame.tsx
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, RefreshCw, Timer, Trophy, CheckCircle2, XCircle, Sparkles } from "lucide-react";
import confetti from "canvas-confetti";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import PageLayout from "@/components/PageLayout";
import ArabicLettersBg from "@/components/ArabicLettersBg";
import OrnamentalDivider from "@/components/OrnamentalDivider";
import { APIError, getPoetryGameRound, type PoetryGameRoundResponse } from "@/services/api";

const TOTAL_ROUNDS = 5;
const MEMORIZE_SECONDS = 5;
const PASS_THRESHOLD = 0.8; // عتبة النجاح (80%)

function normalizeForCompare(text: string): string {
  return (text || "")
    .replace(/[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]/g, "")
    .replace(/ـ/g, "") // إزالة التطويل
    .replace(/[إأآٱ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/[^\u0600-\u06FF\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * تقارن كلمة المستخدم بكلمات البيت الأصلي
 * وترجع true لو الكلمة موجودة في البيت الأصلي
 */
function isWordCorrect(userWord: string, expectedWords: Set<string>): boolean {
  const normalized = normalizeForCompare(userWord);
  return expectedWords.has(normalized);
}

interface VerseComparison {
  verseIndex: number;
  expected: string;
  userAnswer: string;
  similarity: number;
  ok: boolean;
  userWords: Array<{ word: string; correct: boolean }>;
  missingWords: string[]; // كلمات البيت الأصلي اللي ما كتبها المستخدم
}

/**
 * تقارن بيت واحد مع إجابة المستخدم له
 */
function compareVerse(expected: string, userInput: string): VerseComparison {
  const expectedNorm = normalizeForCompare(expected);

  const expectedTokens = expectedNorm.split(" ").filter(Boolean);
  const expectedSet = new Set(expectedTokens);
  const userTokensRaw = (userInput || "").trim().split(/\s+/).filter(Boolean);

  // تحديد صحة كل كلمة كتبها المستخدم
  const userWords = userTokensRaw.map((word) => ({
    word,
    correct: isWordCorrect(word, expectedSet),
  }));

  // الكلمات الناقصة (موجودة في الأصل لكن مش في إجابة المستخدم)
  const userTokensNorm = new Set(userTokensRaw.map((w) => normalizeForCompare(w)));
  const missingWords = expectedTokens.filter((w) => !userTokensNorm.has(w));

  // حساب النسبة
  const matched = expectedTokens.filter((t) => userTokensNorm.has(t)).length;
  const similarity = expectedTokens.length ? matched / expectedTokens.length : 0;

  return {
    verseIndex: 0, // يُحدد خارجياً
    expected,
    userAnswer: userInput,
    similarity,
    ok: similarity >= PASS_THRESHOLD,
    userWords,
    missingWords,
  };
}

/**
 * تقسم إجابة المستخدم إلى بيتين (بناءً على السطر الفاصل)
 * لو المستخدم ما حط سطر جديد، نحاول نقسم بعدد الكلمات
 */
function splitUserAnswer(answer: string, expectedVerses: string[]): string[] {
  const trimmed = answer.trim();
  if (!trimmed) return ["", ""];

  // لو فيه سطور منفصلة
  const lines = trimmed.split(/\n+/).map((l) => l.trim()).filter(Boolean);
  if (lines.length >= 2) {
    return [lines[0], lines.slice(1).join(" ")];
  }

  // لو سطر واحد، نقسمه بناءً على عدد كلمات البيت الأول المتوقع
  const firstExpectedWords = normalizeForCompare(expectedVerses[0] || "").split(" ").filter(Boolean).length;
  const allWords = trimmed.split(/\s+/);
  
  if (allWords.length <= firstExpectedWords) {
    // كل الإجابة للبيت الأول
    return [trimmed, ""];
  }

  const firstHalf = allWords.slice(0, firstExpectedWords).join(" ");
  const secondHalf = allWords.slice(firstExpectedWords).join(" ");
  return [firstHalf, secondHalf];
}

/**
 * 🎉 إطلاق مفرقعات احتفالية من اليمين واليسار
 * تستمر ~4 ثوانٍ بتأثير متتابع
 */
function fireCelebrationConfetti(): void {
  const duration = 4000;
  const animationEnd = Date.now() + duration;
  const defaults = {
    startVelocity: 45,
    spread: 360,
    ticks: 80,
    zIndex: 9999,
    colors: ["#d97706", "#f59e0b", "#fbbf24", "#fde68a", "#92400e", "#78350f"],
  };

  function randomInRange(min: number, max: number): number {
    return Math.random() * (max - min) + min;
  }

  // ── دفعة أولى كبيرة في المنتصف ─────────────────────────────
  confetti({
    ...defaults,
    particleCount: 150,
    origin: { x: 0.5, y: 0.6 },
    spread: 100,
  });

  // ── مفرقعات متتابعة من اليمين واليسار ─────────────────────
  const interval = window.setInterval(() => {
    const timeLeft = animationEnd - Date.now();

    if (timeLeft <= 0) {
      clearInterval(interval);
      return;
    }

    const particleCount = 50 * (timeLeft / duration);

    // من اليسار
    confetti({
      ...defaults,
      particleCount,
      origin: { x: randomInRange(0.05, 0.25), y: Math.random() - 0.2 },
    });

    // من اليمين
    confetti({
      ...defaults,
      particleCount,
      origin: { x: randomInRange(0.75, 0.95), y: Math.random() - 0.2 },
    });
  }, 250);
}

type Phase = "idle" | "memorize" | "answer" | "roundResult" | "finished";

interface RoundResult {
  round: number;
  poem_id: string;
  poet: string;
  expected: string[];
  answer: string;
  verseComparisons: VerseComparison[];
  overallOk: boolean;
  overallSimilarity: number;
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

  // عشان نتأكد إن المفرقعات ما تشتغل إلا مرة وحدة لكل انتهاء لعبة
  const celebratedRef = useRef(false);

  const score = useMemo(() => results.filter((r) => r.overallOk).length, [results]);
  const isPerfectScore = score === TOTAL_ROUNDS;

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
    celebratedRef.current = false; // إعادة تصفير لاحتفال جديد
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

    // قسم إجابة المستخدم إلى بيتين
    const userVerses = splitUserAnswer(answer, verseStrings);

    // قارن كل بيت على حدة
    const verseComparisons: VerseComparison[] = verseStrings.map((expected, idx) => {
      const comp = compareVerse(expected, userVerses[idx] || "");
      return { ...comp, verseIndex: idx + 1 };
    });

    // التقييم الكلي: كلا البيتين يجب أن يكونا صحيحين
    const overallOk = verseComparisons.every((c) => c.ok);
    const overallSimilarity =
      verseComparisons.reduce((sum, c) => sum + c.similarity, 0) / verseComparisons.length;

    setResults((prev) => [
      ...prev,
      {
        round: currentRound,
        poem_id: roundData.poem_id || "",
        poet: roundData.poet_name || "مجهول",
        expected: verseStrings,
        answer,
        verseComparisons,
        overallOk,
        overallSimilarity,
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

  // 🎉 شغّل المفرقعات لما نوصل لمرحلة "finished" بنتيجة كاملة
  useEffect(() => {
    if (phase === "finished" && isPerfectScore && !celebratedRef.current) {
      celebratedRef.current = true;
      fireCelebrationConfetti();
    }
  }, [phase, isPerfectScore]);

  const lastResult = results[results.length - 1];

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
                  <p className="font-body text-brown-700 text-center">
                    اكتب البيتين الآن من الذاكرة (كل بيت في سطر):
                  </p>
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

              {phase === "roundResult" && lastResult && (
                <motion.div
                  key="roundResult"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="space-y-4"
                >
                  {/* النتيجة الكلية */}
                  <div className="text-center">
                    {lastResult.overallOk ? (
                      <p className="font-kufi text-green-700 flex items-center justify-center gap-2 text-lg">
                        <CheckCircle2 className="h-5 w-5" />
                        ممتاز! حفظت البيتين بشكل صحيح
                      </p>
                    ) : (
                      <div className="space-y-1">
                        <p className="font-kufi text-amber-700 flex items-center justify-center gap-2 text-lg">
                          <XCircle className="h-5 w-5" />
                          راجع إجابتك أدناه
                        </p>
                        <p className="font-ui text-xs text-brown-500">
                        </p>
                      </div>
                    )}
                  </div>

                  {/* مقارنة تفصيلية لكل بيت */}
                  <div className="space-y-3">
                    {lastResult.verseComparisons.map((comp, idx) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-xl border-2 ${
                          comp.ok
                            ? "border-green-300/50 bg-green-50/40"
                            : "border-red-300/50 bg-red-50/40"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-ui text-xs text-brown-600">
                            البيت {comp.verseIndex}
                          </span>
                          <span
                            className={`font-ui text-xs flex items-center gap-1 ${
                              comp.ok ? "text-green-700" : "text-red-700"
                            }`}
                          >
                            {comp.ok ? (
                              <>
                                <CheckCircle2 className="h-4 w-4" /> صحيح
                              </>
                            ) : (
                              <>
                              </>
                            )}
                          </span>
                        </div>

                        {/* البيت الأصلي */}
                        <div className="mb-2">
                          <p className="font-ui text-xs text-brown-500 mb-1">البيت الأصلي:</p>
                          <p className="font-amiri text-base text-brown-800 leading-loose">
                            {comp.expected}
                          </p>
                        </div>

                        {/* إجابة المستخدم مع تلوين الكلمات */}
                        {comp.userWords.length > 0 && (
                          <div className="mb-2">
                            <p className="font-ui text-xs text-brown-500 mb-1">إجابتك:</p>
                            <p className="font-amiri text-base leading-loose">
                              {comp.userWords.map((w, i) => (
                                <span
                                  key={i}
                                  className={
                                    w.correct
                                      ? "text-green-700 font-semibold"
                                      : "text-red-700 line-through decoration-red-500 font-semibold"
                                  }
                                >
                                  {w.word}
                                  {i < comp.userWords.length - 1 ? " " : ""}
                                </span>
                              ))}
                            </p>
                          </div>
                        )}

                        {/* الكلمات الناقصة */}
                        {comp.missingWords.length > 0 && (
                          <div>
                            <p className="font-ui text-xs text-brown-500 mb-1">
                              كلمات فاتتك:
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {comp.missingWords.map((w, i) => (
                                <span
                                  key={i}
                                  className="font-amiri text-sm px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 border border-amber-300/60"
                                >
                                  {w}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* اسم الشاعر */}
                  <p className="font-ui text-xs text-brown-500 text-center">
                    — {lastResult.poet}
                  </p>

                  <div className="flex justify-center">
                    <Button
                      className="font-ui bg-brown-gradient text-primary-foreground rounded-full px-8"
                      onClick={nextRound}
                    >
                      {currentRound >= TOTAL_ROUNDS ? "عرض النتيجة النهائية" : "الجولة التالية"}
                    </Button>
                  </div>
                </motion.div>
              )}

              {phase === "finished" && (
                <motion.div
                  key="finished"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-center space-y-4"
                >
                  {/* عرض خاص للفائز الكامل 5/5 */}
                  {isPerfectScore ? (
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ type: "spring", stiffness: 200, damping: 15 }}
                      className="space-y-3"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <Sparkles className="h-8 w-8 text-amber-500 animate-pulse" />
                        <p className="font-display text-4xl text-gradient-brown">
                          أداء استثنائي!
                        </p>
                        <Sparkles className="h-8 w-8 text-amber-500 animate-pulse" />
                      </div>
                      <motion.p
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="font-kufi text-xl text-brown-700"
                      >
                        حفظت جميع الأبيات بإتقان ✦
                      </motion.p>
                      <motion.p
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="font-display text-3xl text-amber-600"
                      >
                      </motion.p>
                    </motion.div>
                  ) : (
                    <>
                      <p className="font-display text-2xl text-gradient-brown">انتهت اللعبة ✦</p>
                      <p className="font-kufi text-brown-700">
                        نتيجتك: {score} / {TOTAL_ROUNDS}
                      </p>
                    </>
                  )}

                  <div className="flex items-center justify-center gap-3 pt-2">
                    <Button
                      className="font-ui bg-brown-gradient text-primary-foreground rounded-full px-8"
                      onClick={startGame}
                    >
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
                        celebratedRef.current = false;
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
