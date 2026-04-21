/**
 * صفحة رحلة عبر الزمن - Journey Through Time
 * رحلة تفاعلية: بداية -> الجاهلي -> العباسي -> الحديث -> خلاصة نهائية
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Clock, Loader2, RefreshCcw, RotateCcw, Sparkles, Volume2, VolumeX } from "lucide-react";
import { Button } from "@/components/ui/button";
import PageLayout from "@/components/PageLayout";
import ArabicLettersBg from "@/components/ArabicLettersBg";
import OrnamentalDivider from "@/components/OrnamentalDivider";
import PageNavButton from "@/components/PageNavButton";
import { useHistory } from "@/contexts/HistoryContext";
import { APIError, getJourneyTTS, getTimeJourney, type JourneyEraPoem, type JourneyResponse } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const themes = ["غزل", "عتاب", "حزينه", "هجاء", "شوق", "فراق", "مدح", "رومنسيه"] as const;

const eraColors = ["bg-amber-500/20", "bg-emerald-500/20", "bg-rose-500/20"];
const eraGlowClasses = [
  "from-amber-500/20 via-amber-400/5 to-transparent",
  "from-emerald-500/20 via-emerald-400/5 to-transparent",
  "from-rose-500/20 via-rose-400/5 to-transparent",
];

const MAX_NARRATION_CHARS = 1700;
const THEMES_WITH_DIACRITICS: Record<string, string> = {
  "غزل": "الغَزَلِ",
  "عتاب": "العِتابِ",
  "حزينه": "الحَزِينَةِ",
  "هجاء": "الهِجاءِ",
  "شوق": "الشَّوْقِ",
  "فراق": "الفِراقِ",
  "مدح": "المَدْحِ",
  "رومنسيه": "الرُّومانسِيَّةِ",
};

const clampNarration = (text: string) => {
  const normalized = text.replace(/\s+/g, " ").trim();
  return normalized.length > MAX_NARRATION_CHARS
    ? `${normalized.slice(0, MAX_NARRATION_CHARS - 1)}…`
    : normalized;
};

const getNarratedTheme = (theme: string) => THEMES_WITH_DIACRITICS[theme] ?? theme;

const buildIntroNarration = (theme: string) =>
  clampNarration(
    `تَأهَّب... الآنَ نَفتَحُ بَوّابَةَ الزَّمَنِ، ونُرافِقُ الشُّعَراءَ عَبْرَ العُصورِ، لِنَرَى كَيْفَ تَجَلَّى مَوضوعُ ${getNarratedTheme(theme)} في لُغَتِهِم وصُوَرِهِم.`
  );

const buildEraNarration = (era: JourneyEraPoem) => {
  const verses = era.verses.slice(0, 4).join(" ... ");
  return clampNarration(verses);
};

const getSceneNarration = (journeyData: JourneyResponse | null, currentStep: number, selectedTheme: string) => {
  if (!journeyData || !selectedTheme) return "";
  if (currentStep === 0) return buildIntroNarration(selectedTheme);
  if (currentStep >= 1 && currentStep <= journeyData.eras.length) {
    return buildEraNarration(journeyData.eras[currentStep - 1]);
  }
  return "";
};

const base64ToBlob = (b64Data: string, mimeType: string) => {
  const byteCharacters = atob(b64Data);
  const arrayBuffer = new ArrayBuffer(byteCharacters.length);
  const bytes = new Uint8Array(arrayBuffer);
  for (let i = 0; i < byteCharacters.length; i += 1) {
    bytes[i] = byteCharacters.charCodeAt(i);
  }
  return new Blob([arrayBuffer], { type: mimeType || "audio/mpeg" });
};

const JourneyThroughTime = () => {
  const [selectedTheme, setSelectedTheme] = useState("");
  const [journeyData, setJourneyData] = useState<JourneyResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isNarrationLoading, setIsNarrationLoading] = useState(false);
  const [isNarrationPlaying, setIsNarrationPlaying] = useState(false);
  const { addHistoryItem } = useHistory();
  const { toast } = useToast();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCacheRef = useRef<Map<string, string>>(new Map());
  const narrationRequestIdRef = useRef(0);

  const stopNarration = useCallback(() => {
    narrationRequestIdRef.current += 1;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsNarrationLoading(false);
    setIsNarrationPlaying(false);
  }, []);

  const playNarration = useCallback(async (text: string) => {
    if (!text || isMuted) return;
    stopNarration();
    const requestId = narrationRequestIdRef.current;
    setIsNarrationLoading(true);

    try {
      let audioUrl = audioCacheRef.current.get(text);
      if (!audioUrl) {
        const tts = await getJourneyTTS(text);
        if (requestId !== narrationRequestIdRef.current) return;
        const audioBlob = base64ToBlob(tts.audio_base64, tts.mime_type);
        audioUrl = URL.createObjectURL(audioBlob);
        audioCacheRef.current.set(text, audioUrl);
      }

      if (requestId !== narrationRequestIdRef.current) return;
      const player = new Audio(audioUrl);
      audioRef.current = player;
      player.onended = () => {
        if (requestId === narrationRequestIdRef.current) {
          setIsNarrationPlaying(false);
          setIsNarrationLoading(false);
        }
      };
      player.onpause = () => {
        if (requestId === narrationRequestIdRef.current) {
          setIsNarrationPlaying(false);
        }
      };
      player.onplaying = () => {
        if (requestId === narrationRequestIdRef.current) {
          setIsNarrationPlaying(true);
          setIsNarrationLoading(false);
        }
      };
      await player.play();
    } catch (error) {
      setIsNarrationLoading(false);
      setIsNarrationPlaying(false);
      if (error instanceof APIError) {
        toast({
          title: "تعذر تشغيل التعليق الصوتي",
          description: error.message,
          variant: "destructive",
        });
        return;
      }
      toast({
        title: "تعذر تشغيل التعليق الصوتي",
        description: "قد تحتاج الضغط على إعادة التشغيل للسماح بالصوت.",
        variant: "destructive",
      });
    }
  }, [isMuted, stopNarration, toast]);

  useEffect(() => {
    return () => {
      stopNarration();
      audioCacheRef.current.forEach((url) => URL.revokeObjectURL(url));
      audioCacheRef.current.clear();
    };
  }, [stopNarration]);

  const maxStep = useMemo(() => {
    if (!journeyData) return 0;
    return journeyData.eras.length + 1; // 0 بداية، 1..n عصور، n+1 خلاصة
  }, [journeyData]);

  const handleExplore = async (theme: string) => {
    stopNarration();
    setSelectedTheme(theme);
    setIsLoading(true);
    setJourneyData(null);
    setCurrentStep(0);
    addHistoryItem("journey", "رحلة عبر الزمن", theme);
    try {
      const data = await getTimeJourney(theme);
      setJourneyData(data);
      setCurrentStep(0);
    } catch (error) {
      const message =
        error instanceof APIError
          ? error.message
          : "تعذر بدء الرحلة الآن. حاول مرة أخرى.";
      toast({
        title: "تعذر تحميل الرحلة",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, maxStep));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 0));

  const isIntroStep = currentStep === 0;
  const isSummaryStep = journeyData ? currentStep === journeyData.eras.length + 1 : false;
  const currentEra = journeyData && !isIntroStep && !isSummaryStep
    ? journeyData.eras[currentStep - 1]
    : null;

  const sceneTitle = useMemo(() => {
    if (!journeyData) return "مشهد تمهيدي";
    if (isIntroStep) return "مشهد البداية";
    if (isSummaryStep) return "المشهد الختامي";
    return currentEra?.era_label || "مشهد زمني";
  }, [journeyData, isIntroStep, isSummaryStep, currentEra]);

  const stepLabels = useMemo(() => {
    if (!journeyData) return [];
    return [
      "البداية",
      ...journeyData.eras.map((era) => era.era_label),
      "الخلاصة",
    ];
  }, [journeyData]);

  const currentEraColorClass = currentEra
    ? eraColors[(currentStep - 1) % eraColors.length]
    : "bg-gold/10";
  const currentEraGlowClass = currentEra
    ? eraGlowClasses[(currentStep - 1) % eraGlowClasses.length]
    : "from-gold/20 via-gold/5 to-transparent";

  const sceneNarrationText = useMemo(
    () => getSceneNarration(journeyData, currentStep, selectedTheme),
    [journeyData, currentStep, selectedTheme]
  );

  useEffect(() => {
    if (!journeyData || isLoading) return;
    if (isMuted || !sceneNarrationText) {
      stopNarration();
      return;
    }
    void playNarration(sceneNarrationText);
  }, [journeyData, isLoading, sceneNarrationText, isMuted, playNarration, stopNarration]);

  return (
    <PageLayout title="رحلة عبر الزمن">
      <div className="relative min-h-[calc(100vh-3.5rem)] p-6">
        <ArabicLettersBg />
        <motion.div
          aria-hidden
          className={`pointer-events-none absolute inset-0 bg-gradient-radial ${currentEraGlowClass}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: journeyData ? 1 : 0 }}
          transition={{ duration: 0.7 }}
        />
        <div className="max-w-5xl mx-auto relative z-10">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
            <Clock className="h-10 w-10 text-gold mx-auto mb-4" />
            <h2 className="font-display text-3xl text-foreground mb-2">رحلة عبر الزمن</h2>
            <p className="font-body text-muted-foreground">اختر موضوعاً وشاهد كيف عبّر عنه الشعراء عبر العصور</p>
          </motion.div>

          {/* اختيار الموضوع */}
          <div className="flex flex-wrap gap-3 justify-center mb-12">
            {themes.map((theme) => (
              <Button
                key={theme}
                variant={selectedTheme === theme ? "default" : "outline"}
                className={`font-ui ${
                  selectedTheme === theme
                    ? "bg-primary text-primary-foreground shadow-[0_0_18px_rgba(212,165,116,0.35)]"
                    : "border-gold/30 text-foreground/70 hover:bg-gold/10 hover:scale-[1.03]"
                }`}
                onClick={() => handleExplore(theme)}
              >
                {theme}
              </Button>
            ))}
          </div>

          {/* حالة التحميل */}
          {isLoading && (
            <div className="flex flex-col items-center py-20 glass-card bg-card/65">
              <Loader2 className="h-8 w-8 text-gold animate-spin mb-4" />
              <p className="font-body text-muted-foreground">نسافر عبر الزمن... يتم اختيار مشهد جديد لكل عصر</p>
            </div>
          )}

          {/* الرحلة التفاعلية */}
          <AnimatePresence mode="wait">
            {journeyData && !isLoading && (
              <motion.div
                key={`${selectedTheme}-${currentStep}`}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.35 }}
              >
                <OrnamentalDivider />

                {/* شريط المشهد + تقدم الرحلة */}
                <div className="mb-6">
                  <div className="flex flex-wrap items-center justify-center gap-2 mb-3">
                    <p className="font-ui text-xs text-muted-foreground">
                      المشهد الحالي: <span className="text-foreground">{sceneTitle}</span>
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-gold/30 hover:bg-gold/10"
                      onClick={() => {
                        if (isMuted) {
                          setIsMuted(false);
                        } else {
                          setIsMuted(true);
                          stopNarration();
                        }
                      }}
                    >
                      {isMuted ? <VolumeX className="h-4 w-4 ml-1" /> : <Volume2 className="h-4 w-4 ml-1" />}
                      {isMuted ? "تشغيل الصوت" : "كتم الصوت"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-gold/30 hover:bg-gold/10"
                      onClick={() => void playNarration(sceneNarrationText)}
                      disabled={!sceneNarrationText || isMuted || isNarrationLoading}
                    >
                      <RotateCcw className="h-4 w-4 ml-1" />
                      إعادة السرد
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-gold/30 hover:bg-gold/10"
                      onClick={stopNarration}
                      disabled={!isNarrationPlaying && !isNarrationLoading}
                    >
                      إيقاف الصوت
                    </Button>
                  </div>
                  {(isNarrationLoading || isNarrationPlaying) && (
                    <p className="font-ui text-[11px] text-muted-foreground text-center mt-2">
                      {isNarrationLoading ? "جاري تجهيز التعليق الصوتي..." : "يتم الآن إلقاء المشهد..."}
                    </p>
                  )}
                </div>

                {/* Timeline تفاعلي */}
                <div className="flex flex-wrap justify-center gap-2 mb-7">
                  {stepLabels.map((label, idx) => {
                    const active = idx === currentStep;
                    const passed = idx < currentStep;
                    return (
                      <button
                        key={`${label}-${idx}`}
                        onClick={() => setCurrentStep(idx)}
                        className={`px-3 py-1.5 rounded-full border text-xs font-ui transition-all ${
                          active
                            ? "bg-gold text-brown-900 border-gold shadow-[0_0_14px_rgba(212,165,116,0.35)]"
                            : passed
                              ? "bg-gold/20 text-foreground border-gold/30"
                              : "bg-transparent text-muted-foreground border-gold/20 hover:bg-gold/10"
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>

                {/* شاشة البداية */}
                {isIntroStep && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="glass-card p-8 text-center bg-card/85 border border-gold/20"
                  >
                    <p className="font-display text-2xl text-foreground mb-3"> بداية الرحلة</p>
                    <p className="font-body text-muted-foreground leading-loose text-lg">
                      {journeyData.intro_line}
                    </p>
                    <p className="font-ui text-xs text-muted-foreground/80 mt-3">
                      اضغط السهم للانتقال إلى أول عصر.
                    </p>
                  </motion.div>
                )}

                {/* شاشة العصر الحالي */}
                {currentEra && (
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`glass-card p-6 border border-gold/20 ${currentEraColorClass}`}
                  >
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <span className="font-display text-2xl text-foreground">{currentEra.era_label}</span>
                    </div>

                    <p className="font-ui text-xs text-muted-foreground mb-4">
                      {currentEra.poet_name || "غير معروف"}
                    </p>

                    <motion.div
                      className="space-y-2"
                      initial="hidden"
                      animate="show"
                      variants={{
                        hidden: {},
                        show: {
                          transition: { staggerChildren: 0.11 },
                        },
                      }}
                    >
                      {currentEra.verses.map((verse, idx) => (
                        <motion.blockquote
                          key={`${currentEra.era_key}-${idx}`}
                          initial={{ opacity: 0, x: 16 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.28 }}
                          className="font-display text-lg text-foreground/90 border-r-2 border-gold/40 pr-3 leading-loose"
                        >
                          {verse}
                        </motion.blockquote>
                      ))}
                    </motion.div>

                    {currentEra.fallback_used && (
                      <p className="font-ui text-xs text-muted-foreground mt-4">
                        ملاحظة: لم تتوفر قصيدة مصنفة مباشرة بنفس الموضوع في هذا العصر، فتم اختيار قصيدة من نفس العصر.
                      </p>
                    )}
                  </motion.div>
                )}

                {/* شاشة النهاية */}
                {isSummaryStep && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.99 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="glass-card p-8 bg-card/90 border border-gold/25"
                  >
                    <p className="font-display text-2xl text-foreground mb-4 text-center">
                      نهاية الرحلة عبر الزمن
                    </p>
                    <div className="mb-5">
                      <p className="font-ui text-sm text-muted-foreground mb-2">أوجه التشابه:</p>
                      <ul className="list-disc list-inside space-y-1 font-body text-foreground/90">
                        {journeyData.summary.similarities.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="mb-5">
                      <p className="font-ui text-sm text-muted-foreground mb-2">الاختلاف الجوهري:</p>
                      <p className="font-body text-foreground/90 leading-loose">
                        {journeyData.summary.core_difference}
                      </p>
                    </div>
                    <p className="font-display text-lg text-gold-dark text-center">
                      {journeyData.summary.final_line}
                    </p>

                    {journeyData.warnings.length > 0 && (
                      <div className="mt-6 p-3 rounded-lg bg-gold/10 border border-gold/25">
                        <p className="font-ui text-xs text-muted-foreground mb-1">ملاحظات البيانات:</p>
                        <ul className="list-disc list-inside space-y-1 font-ui text-xs text-muted-foreground">
                          {journeyData.warnings.map((w, idx) => (
                            <li key={idx}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </motion.div>
                )}

                {/* أزرار التنقل */}
                <div className="flex flex-wrap items-center justify-center gap-3 mt-8">
                  <Button
                    variant="outline"
                    className="border-gold/30 hover:bg-gold/10"
                    onClick={prevStep}
                    disabled={currentStep === 0}
                  >
                    <ArrowRight className="h-4 w-4 ml-1" />
                    السابق
                  </Button>
                  <Button
                    className="bg-primary text-primary-foreground hover:bg-primary/90"
                    onClick={nextStep}
                    disabled={currentStep >= maxStep}
                  >
                    التالي
                    <ArrowLeft className="h-4 w-4 mr-1" />
                  </Button>
                  {isSummaryStep && (
                    <Button
                      variant="outline"
                      className="border-gold/30 hover:bg-gold/10"
                      onClick={() => handleExplore(selectedTheme)}
                      disabled={!selectedTheme || isLoading}
                    >
                      <RefreshCcw className="h-4 w-4 ml-1" />
                      تجديد الرحلة
                    </Button>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* الحالة الفارغة */}
          {!selectedTheme && !isLoading && !journeyData && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
              <motion.div
                animate={{ y: [0, -6, 0] }}
                transition={{ duration: 2.2, repeat: Infinity }}
              >
                <Sparkles className="h-16 w-16 text-gold/30 mx-auto mb-4" />
              </motion.div>
              <p className="font-body text-muted-foreground/50">اختر موضوعاً لتبدأ الرحلة</p>
            </motion.div>
          )}

          {/* زر التنقل للصفحة التالية */}
          <div className="mt-12 flex justify-center">
            <PageNavButton to="/interpret" label="التالي: تفسير الأبيات" />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default JourneyThroughTime;