<div align="center">

<!-- LOGO SVG -->
<svg width="110" height="110" viewBox="0 0 110 110" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="bgc" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#4A2510"/>
      <stop offset="100%" stop-color="#2C1810"/>
    </radialGradient>
  </defs>
  <circle cx="55" cy="55" r="52" fill="url(#bgc)" stroke="#B8860B" stroke-width="1.2"/>
  <circle cx="55" cy="55" r="44" fill="none" stroke="#B8860B" stroke-width="0.5" stroke-dasharray="3 2.5" opacity="0.5"/>
  <polygon points="55,7 58,10 55,13 52,10" fill="#D4A017" opacity="0.8"/>
  <polygon points="55,97 58,100 55,103 52,100" fill="#D4A017" opacity="0.8"/>
  <polygon points="7,55 10,52 13,55 10,58" fill="#D4A017" opacity="0.8"/>
  <polygon points="97,55 100,52 103,55 100,58" fill="#D4A017" opacity="0.8"/>
  <path d="M 52 26 C 51 30, 50 36, 50 44 C 50 52, 51 58, 53 62 C 55 66, 57 68, 60 69" fill="none" stroke="#D4A017" stroke-width="4" stroke-linecap="round"/>
  <path d="M 60 69 C 65 70, 70 68, 72 63 C 74 58, 72 52, 66 50" fill="none" stroke="#D4A017" stroke-width="4" stroke-linecap="round"/>
  <path d="M 38 62 C 36 59, 36 55, 40 54 C 44 53, 46 57, 44 60 C 42 63, 38 62, 38 62" fill="#D4A017"/>
  <circle cx="55" cy="78" r="3.2" fill="#D4A017" opacity="0.9"/>
  <circle cx="62" cy="83" r="1.8" fill="#D4A017" opacity="0.7"/>
  <circle cx="55" cy="85" r="1.8" fill="#D4A017" opacity="0.7"/>
  <circle cx="48" cy="83" r="1.8" fill="#D4A017" opacity="0.7"/>
  <path d="M 50 22 C 53 18, 58 18, 60 22" fill="none" stroke="#D4A017" stroke-width="1.5" stroke-linecap="round" opacity="0.8"/>
</svg>

# لَسِنْ — Lassen

### منصة الشعر العربي التفاعلية | Interactive Arabic Poetry Platform

*"دُنياكَ لَو حاوَرَتْكَ ناطِقَةً — خاطَبْتَ مِنْها بَليغَةً لَسِنَه"*

[![HuggingFace Space](https://img.shields.io/badge/🤗%20HuggingFace%20Space-Live%20Demo-FFD21E?style=for-the-badge)](https://huggingface.co/spaces/Rahaf2001/Lassen)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)](https://rahaf2001-lassen.hf.space/docs)
[![React](https://img.shields.io/badge/React%2018-Frontend-61DAFB?style=for-the-badge&logo=react)](https://github.com/Alaaax/Lassen_Final_Project)
[![Models](https://img.shields.io/badge/🧠%20Fine--tuned-3%20Models-7F77DD?style=for-the-badge)](https://huggingface.co/Rahaf2001)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=for-the-badge&logo=typescript)](https://typescriptlang.org)

</div>

---

## ✦ ما هو لَسِنْ؟

**لَسِنْ** منصة ويب تفاعلية مدعومة بالذكاء الاصطناعي تجعل الشعر العربي الكلاسيكي والحديث في متناول الجميع. الاسم مأخوذ من الجذر العربي الذي يعني *الفصيح البليغ* — وهو اسم يليق بمنصة تجمع بين غنى التراث الأدبي العربي وتقنيات معالجة اللغة الطبيعية الحديثة.

---

## ✦ خمس تجارب فريدة | Five Features

| الميزة | Feature | الوصف |
|---|---|---|
| 🤍 **مزاج اليوم** | Mood of the Day | اكتب مشاعرك واحصل على أبيات شعرية — محادثة متعددة الأدوار مع GPT-4o |
| ⏳ **رحلة عبر الزمن** | Journey Through Time | قصيدة واحدة لكل عصر (جاهلي · عباسي · حديث) مع تحليل سينمائي |
| 📖 **فسّرها لي** | Verse Interpretation | ثلاثة موديلات + GPT-4o يكشفون البحر والعصر والموضوع والصور |
| ✍️ **ساعدني أكتب** | Help Me Write | توليد أبيات على 16 بحراً كلاسيكياً بناءً على فكرة المستخدم |
| 💎 **كنوز الكلمات** | Word Treasures | معجم سوار + قاعدة البيانات + GPT في شرح شعري غني |

---

## ✦ هيكل النظام | System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│       TypeScript · Vite · TailwindCSS · Framer Motion       │
│            shadcn/ui · React Query · React Router           │
└──────────────────────┬──────────────────────────────────────┘
                       │  HTTPS · JSON
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend  (Python 3.11)                  │
│          HuggingFace Space · Docker · Port 7860             │
│                                                              │
│  POST /api/treasures/explain    ← كنوز الكلمات              │
│  POST /api/mood/poems           ← مزاج اليوم                │
│  POST /api/write/generate       ← ساعدني أكتب               │
│  POST /api/journey/explore      ← رحلة عبر الزمن            │
│  POST /api/interpret/verses     ← فسّرها لي                 │
└──────┬──────────────┬───────────────────┬───────────────────┘
       │              │                   │
       ▼              ▼                   ▼
┌──────────┐   ┌────────────┐   ┌──────────────────────────┐
│  OpenAI  │   │ معجم سوار  │   │   Supabase (pgvector)    │
│  GPT-4o  │   │ KSAA API   │   │  3.7M verse · HNSW index │
└──────────┘   └────────────┘   └──────────────────────────┘
                                           ▲
                                  ┌────────┴─────────┐
                                  │  HF Fine-tuned   │
                                  │  Models ×3       │
                                  └──────────────────┘
                 ┌──────────────────┐
                 │  poems_db.json   │  ← local fallback
                 └──────────────────┘
```

---

## ✦ مسار فسّرها لي | Interpretation Pipeline

```
أبيات شعرية (Input)
        │
        ▼
  إزالة التشكيل · التحقق من العربية
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
 Meter Classifier    Era Classifier    Topic Classifier
 (14 بحراً)          (كلاسيكي/حديث)    (وطن·غزل·رثاء)
 Lassen-meter        Lassen-era        Lassen-topic
        │                  │                  │
        └──────────┬────────┘                 │
                   └────────────┬─────────────┘
                                ▼
                    GPT-4o — ناقد أدبي
                                │
                                ▼
              ┌─────────────────────────────┐
              │  • شرح بيت بيت              │
              │  • الصور الشعرية            │
              │  • تأثير البحر              │
              │  • المزاج العام             │
              │  • الكلمة المحورية          │
              └─────────────────────────────┘
```

> إذا انخفضت ذاكرة الخادم عن 3.5 GB، تُعطَّل الموديلات تلقائياً ويعمل GPT وحده.

---

## ✦ مسار مزاج اليوم | Mood Pipeline

```
رسالة المستخدم (نص عربي حر)
        │
        ▼
  مطابقة الكلمات → تصنيف عاطفي
        │
        ▼
  poems_db.json → 20 بيتاً مطابقاً
        │
        ▼
  GPT-4o يقرر نوع الرد:
  ┌──────────┬──────────┬───────────┬──────────┐
  │  poems   │ clarify  │  confirm  │ redirect │
  └──────────┴──────────┴───────────┴──────────┘
        │
        ▼
  feeling_detected · intensity · opening_line
  3 أبيات مع شروح · closing_line
```

---

## ✦ الأدوات والتقنيات | Tech Stack

### 🖥️ Frontend

| الأداة | الإصدار | الغرض |
|---|---|---|
| ![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black) | 18.3 | إطار العمل |
| ![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?logo=typescript) | 5.8 | اللغة |
| ![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite) | 5.4 | بيئة البناء |
| ![Tailwind](https://img.shields.io/badge/TailwindCSS-3.4-06B6D4?logo=tailwindcss) | 3.4 | التصميم |
| ![Framer](https://img.shields.io/badge/Framer%20Motion-11-FF4D4D) | 11 | الأنيميشن |
| ![shadcn](https://img.shields.io/badge/shadcn%2Fui-latest-0ea5e9) | latest | مكونات UI |
| ![React Query](https://img.shields.io/badge/TanStack%20Query-5-FF6384) | 5 | إدارة البيانات |
| ![React Router](https://img.shields.io/badge/React%20Router-6-CA4245?logo=reactrouter) | 6 | التنقل |

### ⚙️ Backend

| الأداة | الإصدار | الغرض |
|---|---|---|
| ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi) | 0.111 | إطار الـ API |
| ![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python) | 3.11 | اللغة |
| ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-10A37F) | GPT-4o | الذكاء الاصطناعي |
| ![HuggingFace](https://img.shields.io/badge/🤗%20Transformers-4.44-FFD21E) | 4.44 | الموديلات |
| ![PyTorch](https://img.shields.io/badge/PyTorch-2.2-EE4B28?logo=pytorch) | 2.2 | التعلم العميق |
| ![Supabase](https://img.shields.io/badge/Supabase-2.5-3FCF8E?logo=supabase) | 2.5 | قاعدة البيانات |
| ![Docker](https://img.shields.io/badge/Docker-latest-2496ED?logo=docker) | latest | النشر |
| ![uvicorn](https://img.shields.io/badge/uvicorn-0.30-E34F26) | 0.30 | ASGI Server |

### 🧠 AI & Data

| الأداة | الغرض |
|---|---|
| **AraBERT / CAMeLBERT** | أساس الموديلات المدرّبة |
| **Siwar API (KSAA)** | معجم اللغة العربية الرسمي |
| **pgvector + HNSW** | بحث التشابه المتجهي السريع |
| **Ashaar Dataset** | 3.7 مليون بيت شعري عربي |
| **Fine-tuned Models ×3** | بحر · عصر · موضوع |

---

## ✦ الموديلات المدرّبة | Fine-tuned Models

| الموديل | الريبو | المهمة | المخرجات |
|---|---|---|---|
| **Meter Classifier** | `Rahaf2001/Lassen-meter-classifier` | Sequence Classification | 14 بحراً كلاسيكياً |
| **Era Classifier** | `Rahaf2001/Lassen-era-classifier` | Sequence Classification | كلاسيكي / حديث |
| **Topic Classifier** | `Rahaf2001/Lassen-topic-classifier` | Sequence Classification | وطن · غزل · رثاء ... |

---

## ✦ هيكل المشروع | Project Structure

```
Lassen_Final_Project/
│
├── src/                              # React Frontend
│   ├── pages/
│   │   ├── Index.tsx                 # الصفحة الرئيسية
│   │   ├── MoodOfTheDay.tsx          # 🤍 مزاج اليوم
│   │   ├── JourneyThroughTime.tsx    # ⏳ رحلة عبر الزمن
│   │   ├── PoetryInterpretation.tsx  # 📖 فسّرها لي
│   │   ├── HelpMeWrite.tsx           # ✍️ ساعدني أكتب
│   │   └── TreasuresOfWords.tsx      # 💎 كنوز الكلمات
│   ├── components/                   # مكونات مشتركة
│   ├── services/api.ts               # كل API calls في مكان واحد
│   └── contexts/                     # Global state
│
├── Backend/
│   ├── main.py                       # FastAPI + كل الـ endpoints
│   ├── schemas.py                    # Pydantic models
│   ├── poems_db.json                 # قاعدة الأبيات المحلية
│   ├── *_prompts.py                  # برومبتات GPT لكل ميزة
│   └── services/
│       ├── ai_service.py             # OpenAI calls
│       ├── siwar_service.py          # معجم سوار
│       ├── fasserha_service.py       # فسّرها (3 classifiers)
│       ├── help_me_write_service.py  # توليد الأبيات
│       ├── journey_service.py        # رحلة الزمن (Supabase)
│       ├── poetry_retriever.py       # مزاج اليوم (local DB)
│       ├── verse_searcher.py         # بحث الكلمات
│       └── supabase_client.py        # Supabase client
│
├── Dockerfile                        # HuggingFace Space deployment
├── requirements.txt
└── README.md
```

---

## ✦ متغيرات البيئة | Environment Variables

```env
# ─── Core AI ──────────────────────────────────────
OPENAI_API_KEY=sk-...

# ─── Arabic Dictionary ────────────────────────────
SIWAR_API_KEY=your-siwar-key

# ─── Vector Database ──────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# ─── Fine-tuned Classifiers (فسّرها لي) ───────────
FASSERHA_METER_MODEL_PATH=Rahaf2001/Lassen-meter-classifier
FASSERHA_ERA_MODEL_PATH=Rahaf2001/Lassen-era-classifier
FASSERHA_TOPIC_MODEL_PATH=Rahaf2001/Lassen-topic-classifier

# ─── Optional ─────────────────────────────────────
FASSERHA_LLM_MODEL=gpt-4o
FASSERHA_MIN_MEMORY_MB=3500
FASSERHA_DISABLE_CLASSIFIERS=0
OPENAI_MODEL=gpt-4o
```

---

## ✦ تشغيل محلي | Local Development

**Backend**
```bash
cd Backend
pip install -r requirements.txt
cp .env.example .env       # أضف مفاتيحك
uvicorn main:app --reload --port 8000
# التوثيق: http://localhost:8000/docs
```

**Frontend**
```bash
npm install
npm run dev
# يعمل على: http://localhost:5173
```

لتوجيه الفرونت إلى الباكند المحلي، غيّر `BASE` في `src/services/api.ts`:
```typescript
const BASE = "http://localhost:8000";
```

---

## ✦ النشر | Deployment

الباكند منشور كـ Docker container على [HuggingFace Spaces](https://huggingface.co/spaces/Rahaf2001/Lassen). الـ `Dockerfile` يعرض المنفذ `7860` كما تطلبه المنصة. للفرونت: أي static host (Vercel, Netlify) — تأكد أن `BASE` في `api.ts` يشير إلى `https://rahaf2001-lassen.hf.space`.

---

## ✦ قاعدة البيانات | Database

**Supabase (PostgreSQL + pgvector)** يحفظ embeddings بأبعاد 512 مع HNSW index. جدول `poetry_verses` يحتوي: `verse, poem_id, poet_name, poet_era, poem_meter, poem_theme, embedding vector(512)`.

**poems_db.json** نسخة محلية مصنّفة حسب التصنيف العاطفي للاستخدام السريع في مزاج اليوم.

**Ashaar Dataset** [arbml/ashaar](https://huggingface.co/datasets/arbml/ashaar) — أكثر من 3.7 مليون بيت شعري عربي.

---

<div align="center">

لَسِنْ — حيث يلتقي الشعر بالتقنية ✦

*Made with ❤️ for Arabic poetry and NLP*

</div>
