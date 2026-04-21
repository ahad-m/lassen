/**
 * صفحة مزاج اليوم — كيف تشعر اليوم
 * — خلفية متبدّلة: قبل المحادثة = خلفية الـ Home الدافئة، بعدها = حروف "شعور" المتطايرة
 * — يعرض بيتاً واحداً فقط في البداية مع زر "المزيد" لإضافة المزيد
 * — صندوق الترحيب + البيت الأول مدمجان
 * — زر تنقل للصفحة التالية: رحلة عبر الزمن
 */
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import PageLayout from "@/components/PageLayout";
import OrnamentalDivider from "@/components/OrnamentalDivider";
import ArabicLettersBg from "@/components/ArabicLettersBg";
import PageNavButton from "@/components/PageNavButton";
import { useHistory } from "@/contexts/HistoryContext";
import {
  getMoodPoems, MoodResponse, PoemEntry, MoodHistoryItem, APIError
} from "@/services/api";

// ── أنواع الرسائل ──────────────────────────────────────────────
interface UserMessage    { id: string; role: "user";      content: string }
interface BotMessage     { id: string; role: "assistant"; data: MoodResponse; visibleCount: number }
type Message = UserMessage | BotMessage;

// ── الاقتراحات ────────────────────────────────────────────────
const SUGGESTED_MOODS = [
  "أشعر بالشوق لشخص بعيد",
  "قلبي حزين اليوم",
  "أبي أبيات دينية تريح قلبي",
  "زعلان من شخص خذلني",
  "أبي كلمات تشجعني وتقويني",
];

// ── بطاقة بيت شعري ────────────────────────────────────────────
const PoemCard = ({ poem, index }: { poem: PoemEntry; index: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.12 }}
    className="p-4 rounded-xl border border-brown-300/30 bg-brown-50/40 space-y-2"
  >
    <blockquote className="font-amiri text-base text-brown-700 leading-loose text-center">
      {poem.verse}
    </blockquote>
    <div className="w-10 h-px bg-brown-400/40 mx-auto" />
    <p className="font-body text-xs text-brown-600/80 leading-relaxed text-center">
      {poem.explanation}
    </p>
    {poem.poet && poem.poet !== "مجهول" && (
      <p className="font-ui text-[10px] text-brown-500/60 text-center">— {poem.poet}</p>
    )}
  </motion.div>
);

// ── رد الأبيات (مدمج: ترحيب + أول بيت + زر المزيد) ────────────
const PoemsResponse = ({
  data,
  visibleCount,
  onMore,
}: {
  data: MoodResponse;
  visibleCount: number;
  onMore: () => void;
}) => {
  const totalPoems = data.poems?.length ?? 0;
  const shown = Math.min(visibleCount, totalPoems);
  const hasMore = shown < totalPoems;

  return (
    <div className="space-y-3 max-w-[88%]">
      {/* صندوق مدمج: الترحيب + أول بيت */}
      <div className="glass-card-warm px-5 py-5 rounded-2xl rounded-bl-sm space-y-4">
        <div>
          <p className="font-body text-sm text-brown-700 leading-relaxed">
            {data.opening_line}
          </p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {data.feeling_detected && (
              <span className="text-[10px] font-ui text-brown-600 bg-brown-100/60 border border-brown-300/40 rounded-full px-2 py-0.5">
                {data.feeling_detected}
              </span>
            )}
            {data.feeling_intensity && (
              <span className="text-[10px] text-brown-500/60">
                {data.feeling_intensity}
              </span>
            )}
          </div>
        </div>

        {data.poems?.[0] && (
          <>
            <div className="h-px bg-brown-300/30" />
            <PoemCard poem={data.poems[0]} index={0} />
          </>
        )}
      </div>

      {/* الأبيات الإضافية المعروضة (بعد الضغط على المزيد) */}
      {data.poems?.slice(1, shown).map((poem, i) => (
        <PoemCard key={i + 1} poem={poem} index={i + 1} />
      ))}

      {/* زر المزيد */}
      {hasMore && (
        <Button
          onClick={onMore}
          variant="outline"
          size="sm"
          className="w-full font-ui border-brown-400/40 text-brown-700 hover:bg-brown-100/50 gap-2 rounded-xl"
        >
          <Plus className="h-3 w-3" />
          المزيد من الأبيات
        </Button>
      )}

      {data.closing_line && shown >= totalPoems && (
        <div className="glass-card px-5 py-3 rounded-2xl rounded-bl-sm border-brown-300/30">
          <p className="font-body text-xs text-brown-600/70 leading-relaxed italic">
            {data.closing_line}
          </p>
        </div>
      )}
    </div>
  );
};

// ── رد السؤال / التوجيه / التأكيد ────────────────────────────
const MessageResponse = ({
  data,
  onQuickReply,
}: {
  data: MoodResponse;
  onQuickReply: (text: string) => void;
}) => (
  <div className="max-w-[85%] space-y-2">
    <div className="glass-card-warm px-5 py-4 rounded-2xl rounded-bl-sm">
      <p className="font-body text-sm text-brown-700 leading-relaxed">
        {data.message}
      </p>
    </div>

    {data.response_type === "confirm" && (
      <div className="flex gap-2 flex-wrap">
        <Button
          size="sm" variant="outline"
          className="text-xs border-brown-400/40 hover:bg-brown-100/50 font-ui"
          onClick={() => onQuickReply("نعم")}
        >
          نعم، هذا ما أقصده
        </Button>
        <Button
          size="sm" variant="outline"
          className="text-xs border-border/40 hover:bg-secondary/50 font-ui"
          onClick={() => onQuickReply("لا، أبي شيء ثاني")}
        >
          لا، شيء ثاني
        </Button>
      </div>
    )}

    {data.response_type === "clarify" && data.suggested_categories && data.suggested_categories.length > 0 && (
      <div className="flex gap-2 flex-wrap">
        {data.suggested_categories.map(cat => (
          <Button
            key={cat} size="sm" variant="outline"
            className="text-xs border-brown-400/40 hover:bg-brown-100/50 font-ui"
            onClick={() => onQuickReply(`أبي أبيات عن ${cat}`)}
          >
            {cat}
          </Button>
        ))}
      </div>
    )}
  </div>
);

// =============================================================
const MoodOfTheDay = () => {
  const [messages,  setMessages]  = useState<Message[]>([]);
  const [input,     setInput]     = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { addHistoryItem } = useHistory();

  const hasStartedChat = messages.length > 0;

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const buildHistory = (): MoodHistoryItem[] => {
    return messages.slice(-6).map(msg => ({
      role:    msg.role,
      content: msg.role === "user"
        ? msg.content
        : JSON.stringify((msg as BotMessage).data),
    }));
  };

  const handleShowMore = (msgId: string) => {
    setMessages(prev => prev.map(m => {
      if (m.id === msgId && m.role === "assistant") {
        return { ...m, visibleCount: m.visibleCount + 1 };
      }
      return m;
    }));
  };

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || isLoading) return;

    setInput("");
    setError(null);
    addHistoryItem("mood", "مزاج اليوم", msg);

    const userMsg: UserMessage = {
      id: crypto.randomUUID(), role: "user", content: msg
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await getMoodPoems(msg, buildHistory());
      const botMsg: BotMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        data: result,
        visibleCount: 1, // نبدأ بعرض بيت واحد فقط
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (e) {
      setError(e instanceof APIError ? e.message : "تعذّر الاتصال بالسيرفر");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageLayout title="كيف تشعر اليوم">
      <div className="relative flex flex-col h-[calc(100vh-3.5rem)]">
        {/* خلفية متبدّلة */}
        {hasStartedChat ? (
          <ArabicLettersBg
            letters={["ش", "ع", "و", "ر"]}
            count={20}
            opacity={0.07}
            blur
          />
        ) : (
          <div className="fixed inset-0 bg-warm-page pointer-events-none z-0" />
        )}

        <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin p-6 relative z-10">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                <Sparkles className="h-12 w-12 text-brown-500 mx-auto mb-6 animate-float" />
                <h2 className="font-display text-3xl text-gradient-brown mb-3">
                  كيف تشعر اليوم؟
                </h2>
                <p className="font-kufi text-brown-600 mb-8 max-w-md">
                  اكتب مشاعرك أو اختر من الاقتراحات، وسنجد لك أبياتاً شعرية تعبّر عنك
                </p>
                <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                  {SUGGESTED_MOODS.map(mood => (
                    <Button
                      key={mood} variant="outline" size="sm"
                      className="font-ui border-brown-400/40 text-brown-700 hover:bg-brown-100/50 rounded-full"
                      onClick={() => handleSend(mood)}
                      disabled={isLoading}
                    >
                      {mood}
                    </Button>
                  ))}
                </div>
              </motion.div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              <AnimatePresence>
                {messages.map(msg => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {msg.role === "user" ? (
                      <div className="max-w-[75%] rounded-2xl rounded-br-sm px-5 py-4 bg-brown-gradient text-primary-foreground font-body text-sm leading-relaxed shadow-[var(--shadow-soft)]">
                        {msg.content}
                      </div>
                    ) : (
                      (() => {
                        const bot = msg as BotMessage;
                        if (bot.data.response_type === "poems") {
                          return (
                            <PoemsResponse
                              data={bot.data}
                              visibleCount={bot.visibleCount}
                              onMore={() => handleShowMore(bot.id)}
                            />
                          );
                        }
                        return <MessageResponse data={bot.data} onQuickReply={handleSend} />;
                      })()
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                  <div className="glass-card-warm px-5 py-4 rounded-2xl rounded-bl-sm">
                    <div className="flex gap-1">
                      {[0, 1, 2].map(i => (
                        <span
                          key={i}
                          className="w-2 h-2 bg-brown-500 rounded-full animate-bounce"
                          style={{ animationDelay: `${i * 0.15}s` }}
                        />
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {error && (
                <p className="text-center text-xs text-destructive font-body">{error}</p>
              )}
            </div>
          )}
        </div>

        <OrnamentalDivider className="my-0 mx-6" />

        {/* حقل الإدخال + زر التنقل */}
        <div className="p-4 relative z-10">
          <div className="max-w-3xl mx-auto flex gap-3 items-end">
            <Textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="اكتب مشاعرك هنا..."
              className="font-body resize-none min-h-[50px] max-h-[120px] bg-card/70 border-brown-300/40 focus:border-brown-500/60 rounded-xl"
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isLoading}
            />
            <Button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              size="icon"
              className="bg-brown-gradient text-primary-foreground rounded-xl h-[50px] w-[50px] shrink-0 border border-brown-600/30"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>

          {/* زر الانتقال للصفحة التالية: رحلة عبر الزمن */}
          <div className="max-w-3xl mx-auto mt-3 flex justify-start">
            <PageNavButton to="/journey" label="التالي: رحلة عبر الزمن" />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

export default MoodOfTheDay;
