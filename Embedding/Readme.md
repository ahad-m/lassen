📦 بيت-القصيد/
│
├── 📁 Backend/                              ← خادم بايثون (FastAPI)
│   ├── main.py                              ← نقطة دخول الخادم + تعريف API endpoints
│   ├── schemas.py                           ← نماذج البيانات (Pydantic models)
│   ├── download_dataset.py                  ← سكربت تحميل قاعدة بيانات الشعر
│   ├── explore_dataset.py                   ← استكشاف وتحليل البيانات
│   ├── poems_db.json                        ← قاعدة بيانات الشعر (170,000+ بيت)
│   ├── test.txt                             ← ملف اختبار
│   ├── test_siwar.py                        ← اختبار خدمة معجم سِوار
│   ├── MoodOfTheDay_promts.py               ← أنظمة المطالبة لميزة مزاج اليوم
│   ├── TreasuresOfWords_promts.py           ← أنظمة المطالبة لميزة كنوز الكلمات
│   │
│   └── 📁 services/                         ← خدمات الأعمال (Business Logic)
│       ├── ai_service.py                    ← خدمة GPT-4 (OpenAI API)
│       ├── poetry_retriever.py              ← البحث في قاعدة بيانات الشعر
│       ├── siwar_service.py                 ← خدمة معجم سِوار للمعاني واللفظ
│       └── verse_searcher.py                ← البحث عن الأبيات الشعرية
│
├── 📁 public/                               ← ملفات ثابتة (Static Assets)
│   ├── bg-texture.png                       ← خلفية نسيجية زخرفية
│   ├── favicon.ico                          ← أيقونة الموقع في التبويب
│   ├── placeholder.svg                      ← صورة افتراضية
│   └── robots.txt                           ← تعليمات محركات البحث
│
├── 📁 src/                                  ← كود الواجهة الأمامية (React + TypeScript)
│   │
│   ├── 📁 assets/                           ← موارد المشروع
│   │   └── bg-texture.png                   ← نسخة من الخلفية للاستيراد في الكود
│   │
│   ├── 📁 components/                       ← مكونات React المخصصة
│   │   ├── 📁 ui/                           ← مكتبة shadcn/ui (50+ مكون جاهز)
│   │   │   ├── button.tsx                   ← زر تفاعلي
│   │   │   ├── card.tsx                     ← بطاقة
│   │   │   ├── dialog.tsx                   ← حوار منبثق
│   │   │   ├── sidebar.tsx                  ← شريط جانبي
│   │   │   ├── tabs.tsx                     ← تبويبات
│   │   │   ├── toast.tsx                    ← إشعار منبثق
│   │   │   ├── input.tsx                    ← حقل إدخال
│   │   │   ├── textarea.tsx                 ← مساحة نصية
│   │   │   ├── select.tsx                   ← قائمة منسدلة
│   │   │   ├── badge.tsx                    ← شارة/وسم
│   │   │   ├── tooltip.tsx                  ← تلميح
│   │   │   ├── sheet.tsx                    ← لوحة جانبية منزلقة
│   │   │   ├── scroll-area.tsx              ← منطقة تمرير
│   │   │   └── ... (37 مكون إضافي)
│   │   │
│   │   ├── AppSidebar.tsx                   ← الشريط الجانبي (تنقل + سجل التاريخ)
│   │   ├── ArabicLettersBg.tsx              ← حروف عربية متحركة كخلفية زخرفية
│   │   ├── NavLink.tsx                      ← مكوّن رابط التنقل النشط
│   │   ├── OrnamentalDivider.tsx            ← فاصل زخرفي عربي
│   │   └── PageLayout.tsx                   ← تخطيط مشترك للصفحات (sidebar + header)
│   │
│   ├── 📁 contexts/                         ← سياقات React (State Management)
│   │   └── HistoryContext.tsx               ← إدارة سجل تفاعلات المستخدم
│   │
│   ├── 📁 hooks/                            ← Hooks مخصصة
│   │   ├── use-mobile.tsx                   ← كشف حجم الشاشة (موبايل/ديسكتوب)
│   │   └── use-toast.ts                     ← إدارة إشعارات Toast
│   │
│   ├── 📁 lib/                              ← مكتبات مساعدة
│   │   └── utils.ts                         ← دائل utilities (cn لدمج كلاسات Tailwind)
│   │
│   ├── 📁 pages/                            ← صفحات التطبيق (Routes)
│   │   ├── Index.tsx                        ← الصفحة الرئيسية (Hero + بطاقات الميزات)
│   │   ├── MoodOfTheDay.tsx                 ← مزاج اليوم (واجهة محادثة للشعر)
│   │   ├── HelpMeWrite.tsx                  ← ساعدني أكتب (توليد + إكمال أبيات)
│   │   ├── JourneyThroughTime.tsx           ← رحلة عبر الزمن (تايم لاين تفاعلي)
│   │   ├── TreasuresOfWords.tsx             ← كنوز الكلمات (تصميم كتاب مفتوح)
│   │   ├── PoetryInterpretation.tsx         ← تفسير الأبيات (خريطة ذهنية)
│   │   └── NotFound.tsx                     ← صفحة 404
│   │
│   ├── 📁 services/                         ← خدمات API
│   │   └── api.ts                           ← عميل HTTP (axios/fetch)
│   │
│   ├── 📁 test/                             ← اختبارات Vitest
│   │   ├── example.test.ts                  ← اختبار تجريبي
│   │   └── setup.ts                         ← إعداد بيئة الاختبار
│   │
│   ├── App.tsx                              ← الموجّه الرئيسي + React Router
│   ├── App.css                              ← أنماط CSS إضافية
│   ├── index.css                            ← نظام التصميم (CSS variables + خطوط عربية)
│   ├── main.tsx                             ← نقطة دخول React (ReactDOM.render)
│   └── vite-env.d.ts                        ← تعريفات TypeScript لـ Vite
│
├── index.html                               ← ملف HTML الرئيسي (نقطة دخول التطبيق)
├── vite.config.ts                           ← إعدادات Vite (aliases + dev server)
├── tailwind.config.ts                       ← إعدادات Tailwind (ألوان + خطوط عربية + RTL)
├── tsconfig.json                            ← إعدادات TypeScript الرئيسية
├── tsconfig.app.json                        ← إعدادات TS للتطبيق
├── tsconfig.node.json                       ← إعدادات TS لـ Node/Vite
├── vitest.config.ts                         ← إعدادات الاختبارات
├── eslint.config.js                         ← إعدادات ESLint
├── postcss.config.js                        ← إعدادات PostCSS
├── components.json                          ← إعدادات shadcn/ui
├── package.json                             ← التبعيات (dependencies + scripts)
├── bun.lock                                 ← قفل إصدارات Bun
├── bun.lockb                                ← قفل إصدارات Bun (binary)
├── package-lock.json                        ← قفل إصدارات npm
├── README.md                                ← وصف المشروع
└── .gitignore                               ← ملفات ي
