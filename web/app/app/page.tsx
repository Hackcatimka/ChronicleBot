"use client";

import { CSSProperties, FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { authenticatedHeaders } from "@/lib/supabase-client";
import "./workspace.css";

type Moment = {
  id: number;
  title: string;
  content: string;
  category: string;
  mood: string;
  isFavorite: boolean;
  createdAt: string;
  goalIds: number[];
};
type Goal = {
  id: number;
  title: string;
  description: string;
  targetSteps: number;
  completedSteps: number;
  category: string;
  deadline: string | null;
  status: "active" | "completed" | "abandoned";
  completedAt: string | null;
  createdAt: string;
};
type Settings = {
  displayName: string;
  language: "en" | "ru";
  tone: "gentle" | "thoughtful" | "direct";
  timezone: string;
  remindersEnabled: boolean;
  reminderTime: string;
  reminderFrequency: "daily" | "weekdays" | "weekly";
  onboardingComplete: boolean;
  selectedAreas: string[];
};
type ChronicleData = { moments: Moment[]; goals: Goal[]; settings: Settings };
type View = "today" | "moments" | "goals" | "stats" | "time" | "settings";
type StatsPeriod = "week" | "month" | "all";
type OnboardingDraft = {
  name: string;
  language: "en" | "ru";
  areas: string[];
  goalTitle: string;
  goalCategory: string;
  goalSteps: number;
  momentTitle: string;
  momentContent: string;
  momentCategory: string;
  momentMood: string;
};
type ConfirmDialog = {
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
};

const defaultSettings: Settings = {
  displayName: "Alex",
  language: "en",
  tone: "thoughtful",
  timezone: "Europe/Moscow",
  remindersEnabled: false,
  reminderTime: "20:00",
  reminderFrequency: "daily",
  onboardingComplete: true,
  selectedAreas: [
    "Growth",
    "Work",
    "Relationships",
    "Health",
    "Creativity",
    "Rest",
  ],
};
const categories = [
  "All",
  "Growth",
  "Work",
  "Relationships",
  "Health",
  "Creativity",
  "Rest",
];
const moods = ["Proud", "Grateful", "Calm", "Excited", "Brave", "Thoughtful"];

const copy = {
  en: {
    today: "Today",
    moments: "Moments",
    goals: "Goals",
    stats: "Insights",
    time: "Time Machine",
    timeShort: "Archive",
    settings: "Settings",
    newMoment: "+ New moment",
    newGoal: "+ New goal",
    goodMorning: "Good morning",
    goodAfternoon: "Good afternoon",
    goodEvening: "Good evening",
    todayStory: "TODAY'S STORY",
    timeline: "YOUR TIMELINE",
    remember: "What will you remember?",
    shaped: "Moments that shaped you",
    search: "Search your moments",
    edit: "Edit",
    delete: "Delete",
    capture: "Capture a moment",
    demo: "Load demo data",
    emptyTitle: "Your Chronicle is ready",
    emptyText:
      "Capture your first moment, or load a small demo to explore the experience.",
    noMatch: "No moments match this view",
    noMatchText: "Try another category or search phrase.",
    goalsTitle: "Goals grounded in your life",
    goalsIntro:
      "Connect everyday moments to a direction, set a deadline and see meaningful progress.",
    active: "Active",
    completed: "Completed",
    abandoned: "Archived",
    completeGoal: "Complete",
    reopen: "Reopen",
    archive: "Archive",
    noGoals: "No goals yet",
    createGoal: "Create a goal",
    linkedMomentOne: "linked moment",
    linkedMomentMany: "linked moments",
    due: "Due",
    overdue: "Overdue",
    statsTitle: "See how you are moving",
    statsIntro:
      "Look beyond totals and notice the rhythm, themes and consistency in your journal.",
    week: "7 days",
    month: "30 days",
    all: "All time",
    captured: "Moments captured",
    activeDays: "Active days",
    favorites: "Favorites",
    streak: "Current streak",
    days: "days",
    categoryBalance: "Life areas",
    comparison: "Compared with previous period",
    timeTitle: "Return to a moment",
    timeIntro:
      "The Time Machine brings back something you once wanted to remember.",
    surprise: "Show another moment",
    noPast: "Add moments on different days and return here to revisit them.",
    settingsTitle: "Make Chronicle yours",
    profile: "Profile & language",
    reminders: "Gentle reminders",
    data: "Your data",
    displayName: "Display name",
    language: "Language",
    tone: "Reflection tone",
    timezone: "Timezone",
    reminderTime: "Reminder time",
    frequency: "Frequency",
    save: "Save settings",
    exportJson: "Export JSON",
    exportMd: "Export journal",
    exportPdf: "Beautiful PDF",
    deleteAll: "Delete all data",
    privacy:
      "Your journal stays in the Chronicle database. Export it whenever you want and erase everything in one action.",
    reminderNote:
      "Reminder preferences are saved. Browser notifications will be connected when Chronicle is published.",
    momentTitle: "What would you like to remember?",
    title: "Title",
    details: "Details",
    area: "Area of life",
    mood: "Mood",
    relatedGoals: "Related goals",
    saveChanges: "Save changes",
    captureMoment: "Capture moment",
    goalQuestion: "Where do you want to move next?",
    description: "Why it matters",
    steps: "Number of steps",
    deadline: "Deadline",
    category: "Category",
    updateGoal: "Update goal",
    personalJournal: "PERSONAL JOURNAL",
    dayStreak: "day streak",
    allMoments: "all moments",
    activeGoals: "active goals",
    currentPattern: "CURRENT PATTERN",
    currentReflection: "CURRENT REFLECTION",
    activeGoal: "ACTIVE GOAL",
    travelBack: "Travel back",
    todayChapter: "TODAY'S CHAPTER",
    storyTimeline: "THE TIMELINE",
    rememberedToday: "What you chose to remember",
    oneMomentAtTime: "Your story, one moment at a time",
    favoritesLabel: "favorites",
    lifeConstellation: "YOUR LIFE CONSTELLATION",
    seeMoving: "See where your life is moving.",
    constellationIntro:
      "Chronicle turns your moments and completed goal steps into a living picture of attention and progress.",
    lifeBalance: "LIFE BALANCE",
    shapePeriod: "Your shape this period",
    goalSteps: "goal steps",
    overall: "OVERALL",
    exploreMoments: "Explore moments",
    quietDirection: "Explore the quietest direction",
    gentleNext: "GENTLE NEXT STEP",
    addMoment: "Add a moment",
    noLifeData: "Your constellation is waiting",
    noLifeDataText:
      "Capture moments or create a goal to reveal the first shape of your life.",
    scoreHelp: "How the percentages work",
    scoreSummary: "60% journal attention + 40% related goal progress",
    scoreFormula:
      "Up to 60% comes from moments in this direction and up to 40% from progress on related goals. Eight moments fill the attention part; goal progress fills the rest.",
    monthlyHistory: "Six-month history",
    monthlyHistoryText:
      "The monthly bars show attention based on recorded moments. Goal progress affects the current wheel but is not applied retroactively.",
    noMonthlyData: "No moments in this direction during these months.",
    attentionIndex: "attention",
    todayGreeting: "Keep one thing from today.",
    todaySupport:
      "Small moments become a life when you give them a place to stay.",
    livingArchive: "YOUR LIVING ARCHIVE",
    momentsMadeYou: "Moments that made you.",
    archiveIntro:
      "Search the details, feelings and choices that are shaping your story.",
    momentsPreserved: "moments preserved",
    returnMemory: "Return to something you once wanted to remember.",
    patternFallback: "Your story begins with one honest moment.",
    patternIntro:
      "Every entry makes your personal patterns a little easier to see.",
    directionMomentum: "is carrying your momentum.",
    directionQuiet:
      "has received less attention lately. One small, intentional moment can begin to rebalance the picture.",
    balancedAttention:
      "Your attention is becoming more balanced across the areas that matter to you.",
    captureMeaningful:
      "Capture one meaningful moment in this direction this week.",
    balanceQuote: "Balance is not stillness. It is conscious movement.",
    enableReminders: "Enable reminders",
    daily: "Daily",
    weekdays: "Weekdays",
    weekly: "Weekly",
    gentle: "Gentle",
    thoughtful: "Thoughtful",
    direct: "Direct",
    yourSpace: "YOUR SPACE",
    intentionalProgress: "INTENTIONAL PROGRESS",
    editMomentLabel: "EDIT MOMENT",
    newMomentLabel: "NEW MOMENT",
    editGoalLabel: "EDIT GOAL",
    newGoalLabel: "NEW GOAL",
    momentOne: "moment",
    momentFew: "moments",
    momentMany: "moments",
    settingsSaved: "Settings saved.",
    momentUpdated: "Moment updated.",
    momentCaptured: "Moment captured.",
    goalUpdated: "Goal updated.",
    goalCreated: "Goal created.",
    progressUpdated: "Progress updated.",
    goalCompleted: "Goal completed.",
    goalReopened: "Goal reopened.",
    momentDeleted: "Moment deleted.",
    demoAdded: "Demo moments added.",
    allDeleted: "All journal entries and goals were deleted.",
    deleteMomentConfirm: "Delete this moment?",
    deleteGoalConfirm: "Delete this goal?",
    archiveGoalConfirm: "Archive this goal?",
    deleteAllConfirm: "Delete every moment and goal?",
    deleteMomentExplain: "This journal entry will be permanently removed.",
    deleteGoalExplain:
      "This goal will be permanently removed. Linked moments will remain.",
    archiveGoalExplain: "It will move to Archived and can be restored later.",
    deleteAllExplain:
      "All moments and goals will be permanently removed. Your profile and preferences will remain.",
    requiredFields: "Fill in the title and details.",
    requiredTitle: "Enter a title.",
    close: "Close",
    confirm: "Confirm",
    loadError: "Unable to load Chronicle.",
    saveError: "Unable to save changes.",
    loadingLabel: "Opening your Chronicle…",
    savingLabel: "Saving changes…",
    retry: "Try again",
    privacyPolicy: "Privacy policy",
    dangerZone: "Danger zone",
    deleteAccount: "Delete account",
    deleteAccountText:
      "Permanently erase your profile, moments, goals and preferences.",
    deleteAccountConfirm: "Type DELETE to confirm",
    cancel: "Cancel",
    accountDeleted: "Your Chronicle account was deleted.",
  },
  ru: {
    today: "Сегодня",
    moments: "Моменты",
    goals: "Цели",
    stats: "Статистика",
    time: "Машина времени",
    timeShort: "Архив",
    settings: "Настройки",
    newMoment: "+ Новый момент",
    newGoal: "+ Новая цель",
    goodMorning: "Доброе утро",
    goodAfternoon: "Добрый день",
    goodEvening: "Добрый вечер",
    todayStory: "ИСТОРИЯ СЕГОДНЯ",
    timeline: "ВАША ХРОНИКА",
    remember: "Что вы хотите запомнить?",
    shaped: "Моменты, которые вас изменили",
    search: "Поиск по моментам",
    edit: "Изменить",
    delete: "Удалить",
    capture: "Добавить момент",
    demo: "Загрузить пример",
    emptyTitle: "Chronicle готов",
    emptyText: "Добавьте первый момент или загрузите небольшой пример.",
    noMatch: "Ничего не найдено",
    noMatchText: "Попробуйте другую категорию или поисковую фразу.",
    goalsTitle: "Цели, связанные с жизнью",
    goalsIntro:
      "Связывайте моменты с направлением, задавайте срок и наблюдайте прогресс.",
    active: "Активные",
    completed: "Завершённые",
    abandoned: "Архив",
    completeGoal: "Завершить",
    reopen: "Вернуть",
    archive: "В архив",
    noGoals: "Целей пока нет",
    createGoal: "Создать цель",
    linkedMomentOne: "связанный момент",
    linkedMomentMany: "связанных моментов",
    due: "До",
    overdue: "Просрочено",
    statsTitle: "Посмотрите, как вы движетесь",
    statsIntro:
      "Замечайте не только количество, но и ритм, темы и регулярность записей.",
    week: "7 дней",
    month: "30 дней",
    all: "Всё время",
    captured: "Записано моментов",
    activeDays: "Активных дней",
    favorites: "Избранное",
    streak: "Текущая серия",
    days: "дн.",
    categoryBalance: "Сферы жизни",
    comparison: "По сравнению с прошлым периодом",
    timeTitle: "Вернитесь к моменту",
    timeIntro:
      "Машина времени показывает то, что когда-то было важно сохранить.",
    surprise: "Показать другой момент",
    noPast: "Добавляйте записи в разные дни, чтобы возвращаться к ним здесь.",
    settingsTitle: "Настройте Chronicle под себя",
    profile: "Профиль и язык",
    reminders: "Мягкие напоминания",
    data: "Ваши данные",
    displayName: "Имя",
    language: "Язык",
    tone: "Тон размышлений",
    timezone: "Часовой пояс",
    reminderTime: "Время напоминания",
    frequency: "Частота",
    save: "Сохранить настройки",
    exportJson: "Экспорт JSON",
    exportMd: "Экспорт дневника",
    exportPdf: "Красивый PDF",
    deleteAll: "Удалить все данные",
    privacy:
      "Ваш дневник хранится в базе Chronicle. Его можно экспортировать или полностью удалить в любой момент.",
    reminderNote:
      "Настройки напоминаний сохранены. Уведомления браузера подключим после публикации Chronicle.",
    momentTitle: "Что вы хотите запомнить?",
    title: "Название",
    details: "Описание",
    area: "Сфера жизни",
    mood: "Настроение",
    relatedGoals: "Связанные цели",
    saveChanges: "Сохранить",
    captureMoment: "Добавить момент",
    goalQuestion: "Куда вы хотите двигаться дальше?",
    description: "Почему это важно",
    steps: "Количество шагов",
    deadline: "Срок",
    category: "Категория",
    updateGoal: "Обновить цель",
    personalJournal: "ЛИЧНЫЙ ДНЕВНИК",
    dayStreak: "дней подряд",
    allMoments: "всего моментов",
    activeGoals: "активных целей",
    currentPattern: "ТЕКУЩАЯ ТЕМА",
    currentReflection: "ТЕКУЩЕЕ НАБЛЮДЕНИЕ",
    activeGoal: "АКТИВНАЯ ЦЕЛЬ",
    travelBack: "Вернуться назад",
    todayChapter: "ГЛАВА СЕГОДНЯ",
    storyTimeline: "ХРОНОЛОГИЯ",
    rememberedToday: "Что вы решили сохранить",
    oneMomentAtTime: "Ваша история — момент за моментом",
    favoritesLabel: "избранных",
    lifeConstellation: "СОЗВЕЗДИЕ ВАШЕЙ ЖИЗНИ",
    seeMoving: "Посмотрите, куда движется ваша жизнь.",
    constellationIntro:
      "Chronicle превращает моменты и выполненные шаги целей в живую картину внимания и прогресса.",
    lifeBalance: "БАЛАНС ЖИЗНИ",
    shapePeriod: "Ваша форма за период",
    goalSteps: "шагов по целям",
    overall: "В ЦЕЛОМ",
    exploreMoments: "Открыть моменты",
    quietDirection: "Посмотреть самое тихое направление",
    gentleNext: "МЯГКИЙ СЛЕДУЮЩИЙ ШАГ",
    addMoment: "Добавить момент",
    noLifeData: "Ваше созвездие ждёт",
    noLifeDataText:
      "Добавьте моменты или создайте цель, чтобы появилась первая форма вашей жизни.",
    scoreHelp: "Как рассчитываются проценты",
    scoreSummary: "60% — внимание в дневнике, 40% — прогресс связанных целей",
    scoreFormula:
      "До 60% дают моменты в выбранной сфере, ещё до 40% — прогресс связанных целей. Восемь моментов заполняют часть внимания, а выполнение целей — оставшуюся часть.",
    monthlyHistory: "История за шесть месяцев",
    monthlyHistoryText:
      "Столбцы показывают внимание по сохранённым моментам. Прогресс целей влияет на текущий круг, но не применяется к прошлым месяцам.",
    noMonthlyData: "За эти месяцы в направлении пока нет моментов.",
    attentionIndex: "внимание",
    todayGreeting: "Сохраните один момент сегодняшнего дня.",
    todaySupport:
      "Из маленьких моментов складывается жизнь, когда у них есть место, где остаться.",
    livingArchive: "ЖИВОЙ АРХИВ",
    momentsMadeYou: "Моменты, которые создали вас.",
    archiveIntro:
      "Находите детали, чувства и решения, из которых складывается ваша история.",
    momentsPreserved: "сохранённых моментов",
    returnMemory: "Вернитесь к тому, что когда-то захотели запомнить.",
    patternFallback: "Ваша история начинается с одного честного момента.",
    patternIntro:
      "Каждая запись делает ваши личные закономерности немного понятнее.",
    directionMomentum: "сейчас поддерживает ваше движение.",
    directionQuiet:
      "— этой сфере в последнее время уделялось меньше внимания. Один небольшой осознанный момент поможет восстановить баланс.",
    balancedAttention:
      "Ваше внимание становится более равномерным между важными сферами жизни.",
    captureMeaningful:
      "Добавьте на этой неделе один значимый момент в этом направлении.",
    balanceQuote: "Баланс — не неподвижность, а осознанное движение.",
    enableReminders: "Включить напоминания",
    daily: "Ежедневно",
    weekdays: "По будням",
    weekly: "Раз в неделю",
    gentle: "Мягкий",
    thoughtful: "Вдумчивый",
    direct: "Прямой",
    yourSpace: "ВАШЕ ПРОСТРАНСТВО",
    intentionalProgress: "ОСОЗНАННЫЙ ПРОГРЕСС",
    editMomentLabel: "ИЗМЕНИТЬ МОМЕНТ",
    newMomentLabel: "НОВЫЙ МОМЕНТ",
    editGoalLabel: "ИЗМЕНИТЬ ЦЕЛЬ",
    newGoalLabel: "НОВАЯ ЦЕЛЬ",
    momentOne: "момент",
    momentFew: "момента",
    momentMany: "моментов",
    settingsSaved: "Настройки сохранены.",
    momentUpdated: "Момент обновлён.",
    momentCaptured: "Момент сохранён.",
    goalUpdated: "Цель обновлена.",
    goalCreated: "Цель создана.",
    progressUpdated: "Прогресс обновлён.",
    goalCompleted: "Цель завершена.",
    goalReopened: "Цель снова активна.",
    momentDeleted: "Момент удалён.",
    demoAdded: "Пример добавлен.",
    allDeleted: "Все записи и цели удалены.",
    deleteMomentConfirm: "Удалить этот момент?",
    deleteGoalConfirm: "Удалить эту цель?",
    archiveGoalConfirm: "Перенести цель в архив?",
    deleteAllConfirm: "Удалить все моменты и цели?",
    deleteMomentExplain: "Эта запись будет удалена навсегда.",
    deleteGoalExplain:
      "Цель будет удалена навсегда. Связанные моменты останутся.",
    archiveGoalExplain:
      "Цель переместится в архив, откуда её можно будет вернуть.",
    deleteAllExplain:
      "Все моменты и цели будут удалены навсегда. Профиль и настройки сохранятся.",
    requiredFields: "Заполните название и описание.",
    requiredTitle: "Введите название.",
    close: "Закрыть",
    confirm: "Подтвердить",
    loadError: "Не удалось загрузить Chronicle.",
    saveError: "Не удалось сохранить изменения.",
    loadingLabel: "Открываем ваш Chronicle…",
    savingLabel: "Сохраняем изменения…",
    retry: "Попробовать снова",
    privacyPolicy: "Политика конфиденциальности",
    dangerZone: "Опасная зона",
    deleteAccount: "Удалить аккаунт",
    deleteAccountText: "Навсегда удалить профиль, моменты, цели и настройки.",
    deleteAccountConfirm: "Введите УДАЛИТЬ для подтверждения",
    cancel: "Отмена",
    accountDeleted: "Ваш аккаунт Chronicle удалён.",
  },
} as const;

const onboardingCopy = {
  en: {
    step: "STEP",
    welcome: "Welcome to Chronicle",
    welcomeText: "A private place to notice your life as it happens.",
    name: "What should we call you?",
    namePlaceholder: "Your name",
    language: "Interface language",
    continue: "Continue",
    back: "Back",
    areas: "Choose the parts of life that matter now",
    areasText:
      "Pick at least three. Your constellation will be built around them.",
    areaError: "Choose at least three life areas.",
    goal: "Set your first direction",
    goalText: "Start with one goal that feels meaningful, not perfect.",
    goalTitle: "Goal title",
    goalPlaceholder: "Launch my own project",
    goalArea: "Direction",
    goalSteps: "Steps",
    required: "Please complete this step.",
    moment: "Save your first moment",
    momentText: "Write down something from today worth keeping.",
    momentTitle: "Moment title",
    momentPlaceholder: "I finally started",
    details: "What happened?",
    detailsPlaceholder: "A few honest lines are enough…",
    mood: "Mood",
    finish: "Start my Chronicle",
    ready: "Your Chronicle is ready.",
    error: "We couldn't finish setup. Check your connection and try again.",
  },
  ru: {
    step: "ШАГ",
    welcome: "Добро пожаловать в Chronicle",
    welcomeText:
      "Личное пространство, где можно замечать свою жизнь, пока она происходит.",
    name: "Как к вам обращаться?",
    namePlaceholder: "Ваше имя",
    language: "Язык интерфейса",
    continue: "Продолжить",
    back: "Назад",
    areas: "Выберите важные сейчас сферы жизни",
    areasText: "Отметьте минимум три. На них будет построено ваше созвездие.",
    areaError: "Выберите хотя бы три сферы жизни.",
    goal: "Задайте первое направление",
    goalText:
      "Начните с одной значимой цели — ей не обязательно быть идеальной.",
    goalTitle: "Название цели",
    goalPlaceholder: "Запустить собственный проект",
    goalArea: "Направление",
    goalSteps: "Количество шагов",
    required: "Заполните поля этого шага.",
    moment: "Сохраните первый момент",
    momentText:
      "Запишите то, что произошло сегодня и достойно остаться с вами.",
    momentTitle: "Название момента",
    momentPlaceholder: "Я наконец начал",
    details: "Что произошло?",
    detailsPlaceholder: "Достаточно нескольких честных строк…",
    mood: "Настроение",
    finish: "Начать мой Chronicle",
    ready: "Ваш Chronicle готов.",
    error:
      "Не удалось завершить настройку. Проверьте соединение и попробуйте снова.",
  },
} as const;

const categoryCopy: Record<Settings["language"], Record<string, string>> = {
  en: {
    All: "All",
    Growth: "Growth",
    Work: "Work",
    Relationships: "Relationships",
    Health: "Health",
    Creativity: "Creativity",
    Rest: "Rest",
  },
  ru: {
    All: "Все",
    Growth: "Развитие",
    Work: "Работа",
    Relationships: "Отношения",
    Health: "Здоровье",
    Creativity: "Творчество",
    Rest: "Отдых",
  },
};

const moodCopy: Record<Settings["language"], Record<string, string>> = {
  en: {
    Proud: "Proud",
    Grateful: "Grateful",
    Calm: "Calm",
    Excited: "Excited",
    Brave: "Brave",
    Thoughtful: "Thoughtful",
  },
  ru: {
    Proud: "Гордость",
    Grateful: "Благодарность",
    Calm: "Спокойствие",
    Excited: "Воодушевление",
    Brave: "Смелость",
    Thoughtful: "Задумчивость",
  },
};

function startOfPeriod(period: StatsPeriod, previous = false) {
  if (period === "all") return new Date(0);
  const days = period === "week" ? 7 : 30;
  return new Date(Date.now() - days * (previous ? 2 : 1) * 86_400_000);
}

function calculateStreak(moments: Moment[]) {
  const dates = new Set(
    moments.map((moment) => new Date(moment.createdAt).toDateString()),
  );
  const cursor = new Date();
  if (!dates.has(cursor.toDateString())) cursor.setDate(cursor.getDate() - 1);
  let streak = 0;
  while (dates.has(cursor.toDateString())) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function downloadFile(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function ChronicleWorkspace() {
  const [data, setData] = useState<ChronicleData>({
    moments: [],
    goals: [],
    settings: defaultSettings,
  });
  const [view, setView] = useState<View>("stats");
  const [activeCategory, setActiveCategory] = useState("All");
  const [goalFilter, setGoalFilter] = useState<Goal["status"]>("active");
  const [statsPeriod, setStatsPeriod] = useState<StatsPeriod>("week");
  const [selectedDirection, setSelectedDirection] = useState("Growth");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadFailed, setLoadFailed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [momentError, setMomentError] = useState("");
  const [goalError, setGoalError] = useState("");
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialog | null>(
    null,
  );
  const [momentOpen, setMomentOpen] = useState(false);
  const [goalOpen, setGoalOpen] = useState(false);
  const [editingMoment, setEditingMoment] = useState<Moment | null>(null);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [timeMomentId, setTimeMomentId] = useState<number | null>(null);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const [onboardingError, setOnboardingError] = useState("");
  const [onboardingDraft, setOnboardingDraft] = useState<OnboardingDraft>({
    name: "",
    language: "en",
    areas: ["Growth", "Work", "Relationships"],
    goalTitle: "",
    goalCategory: "Growth",
    goalSteps: 10,
    momentTitle: "",
    momentContent: "",
    momentCategory: "Growth",
    momentMood: "Proud",
  });
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);
  const [deleteAccountPhrase, setDeleteAccountPhrase] = useState("");
  const lang = data.settings.language;
  const t = (key: keyof typeof copy.en) => copy[lang][key];
  const categoryLabel = (category: string) =>
    categoryCopy[lang][category] || category;
  const moodLabel = (mood: string) => moodCopy[lang][mood] || mood;
  const availableAreas = useMemo(
    () =>
      data.settings.selectedAreas?.length
        ? data.settings.selectedAreas
        : categories.slice(1),
    [data.settings.selectedAreas],
  );
  const momentCountLabel = (count: number) => {
    if (lang === "en") return count === 1 ? t("momentOne") : t("momentMany");
    const lastTwo = count % 100;
    const last = count % 10;
    if (lastTwo >= 11 && lastTwo <= 14) return t("momentMany");
    if (last === 1) return t("momentOne");
    return last >= 2 && last <= 4 ? t("momentFew") : t("momentMany");
  };
  const linkedMomentCountLabel = (count: number) => {
    if (lang === "en")
      return count === 1 ? t("linkedMomentOne") : t("linkedMomentMany");
    const lastTwo = count % 100;
    const last = count % 10;
    if (lastTwo >= 11 && lastTwo <= 14) return t("linkedMomentMany");
    if (last === 1) return t("linkedMomentOne");
    return last >= 2 && last <= 4
      ? `связанных ${t("momentFew")}`
      : t("linkedMomentMany");
  };

  const load = async () => {
    setLoading(true);
    setLoadFailed(false);
    setNotice("");
    try {
      const response = await fetch("/api/chronicle", {
        cache: "no-store",
        headers: await authenticatedHeaders(),
      });
      if (response.status === 401) {
        window.location.assign(`/auth?returnTo=${encodeURIComponent("/app")}`);
        return;
      }
      const payload = (await response.json()) as ChronicleData & {
        error?: string;
      };
      if (!response.ok) throw new Error(copy[data.settings.language].loadError);
      setData(payload);
      if (!payload.settings.onboardingComplete) {
        const browserLanguage =
          typeof navigator !== "undefined" &&
          navigator.language.toLowerCase().startsWith("ru")
            ? "ru"
            : payload.settings.language;
        setOnboardingDraft((current) => ({
          ...current,
          language: browserLanguage,
          name:
            payload.settings.displayName === "Alex"
              ? ""
              : payload.settings.displayName,
          areas:
            payload.settings.selectedAreas?.length >= 3
              ? payload.settings.selectedAreas
              : current.areas,
        }));
      }
    } catch {
      setLoadFailed(true);
      setNotice(copy[data.settings.language].loadError);
    } finally {
      setLoading(false);
    }
  };

  // Initial loading is intentionally performed once when the workspace mounts.
  /* eslint-disable react-hooks/exhaustive-deps */
  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, []);
  /* eslint-enable react-hooks/exhaustive-deps */

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(""), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const mutate = async (
    payload: Record<string, unknown>,
    successMessage?: string,
  ) => {
    setSaving(true);
    setNotice("");
    try {
      const response = await fetch("/api/chronicle", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(await authenticatedHeaders()),
        },
        body: JSON.stringify(payload),
      });
      if (response.status === 401) {
        window.location.assign(`/auth?returnTo=${encodeURIComponent("/app")}`);
        return false;
      }
      const next = (await response.json()) as ChronicleData & {
        error?: string;
      };
      if (!response.ok) throw new Error(t("saveError"));
      setData(next);
      if (successMessage) setNotice(successMessage);
      return true;
    } catch {
      setNotice(t("saveError"));
      return false;
    } finally {
      setSaving(false);
    }
  };

  const visibleMoments = useMemo(() => {
    const query = search.trim().toLowerCase();
    return data.moments.filter(
      (moment) =>
        (activeCategory === "All" || moment.category === activeCategory) &&
        (!query ||
          `${moment.title} ${moment.content} ${moment.mood}`
            .toLowerCase()
            .includes(query)) &&
        (view !== "today" ||
          new Date(moment.createdAt).toDateString() ===
            new Date().toDateString()),
    );
  }, [activeCategory, data.moments, search, view]);

  const filteredGoals = data.goals.filter((goal) => goal.status === goalFilter);
  const activeGoals = data.goals.filter((goal) => goal.status === "active");
  const pastMoments = data.moments.filter(
    (moment) =>
      new Date(moment.createdAt).toDateString() !== new Date().toDateString(),
  );
  const timeMoment =
    pastMoments.find((moment) => moment.id === timeMomentId) || pastMoments[0];

  const stats = useMemo(() => {
    const start = startOfPeriod(statsPeriod);
    const current = data.moments.filter(
      (moment) => new Date(moment.createdAt) >= start,
    );
    const days = statsPeriod === "week" ? 7 : 30;
    const previous =
      statsPeriod === "all"
        ? []
        : data.moments.filter((moment) => {
            const date = new Date(moment.createdAt);
            return date >= startOfPeriod(statsPeriod, true) && date < start;
          });
    const counts = availableAreas.map((category) => ({
      category,
      count: current.filter((moment) => moment.category === category).length,
    }));
    return {
      current,
      previous,
      days,
      counts,
      activeDays: new Set(
        current.map((moment) => new Date(moment.createdAt).toDateString()),
      ).size,
    };
  }, [availableAreas, data.moments, statsPeriod]);

  const lifeScores = useMemo(
    () =>
      availableAreas.map((category) => {
        const moments = stats.current.filter(
          (moment) => moment.category === category,
        );
        const goals = data.goals.filter(
          (goal) => goal.category === category && goal.status !== "abandoned",
        );
        const attentionScore = Math.min(
          60,
          Math.round((moments.length / 8) * 60),
        );
        const goalScore = goals.length
          ? Math.round(
              (goals.reduce(
                (sum, goal) =>
                  sum + Math.min(1, goal.completedSteps / goal.targetSteps),
                0,
              ) /
                goals.length) *
                40,
            )
          : 0;
        return {
          category,
          score: Math.min(100, attentionScore + goalScore),
          moments: moments.length,
          goals,
        };
      }),
    [availableAreas, data.goals, stats],
  );

  const selectedLifeScore =
    lifeScores.find((item) => item.category === selectedDirection) ||
    lifeScores[0];
  const highestDirection = [...lifeScores].sort((a, b) => b.score - a.score)[0];
  const lowestDirection = [...lifeScores].sort((a, b) => a.score - b.score)[0];
  const wheelPoints = lifeScores
    .map((item, index) => {
      const angle = -Math.PI / 2 + index * ((Math.PI * 2) / lifeScores.length);
      const radius = 32 + item.score * 1.18;
      return `${210 + Math.cos(angle) * radius},${210 + Math.sin(angle) * radius}`;
    })
    .join(" ");

  const directionHistory = useMemo(
    () =>
      Array.from({ length: 6 }, (_, index) => {
        const cursor = new Date();
        cursor.setDate(1);
        cursor.setHours(0, 0, 0, 0);
        cursor.setMonth(cursor.getMonth() - (5 - index));
        const end = new Date(cursor);
        end.setMonth(end.getMonth() + 1);
        const count = data.moments.filter((moment) => {
          const date = new Date(moment.createdAt);
          return (
            moment.category === selectedDirection &&
            date >= cursor &&
            date < end
          );
        }).length;
        return {
          label: cursor.toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
            month: "short",
          }),
          count,
          score: Math.min(100, Math.round((count / 8) * 100)),
        };
      }),
    [data.moments, lang, selectedDirection],
  );

  const submitMoment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") || "").trim();
    const content = String(form.get("content") || "").trim();
    if (!title || !content) {
      setMomentError(t("requiredFields"));
      return;
    }
    setMomentError("");
    const goalIds = form.getAll("goalIds").map(Number);
    if (
      await mutate(
        {
          action: editingMoment ? "updateMoment" : "createMoment",
          id: editingMoment?.id,
          title,
          content,
          category: form.get("category"),
          mood: form.get("mood"),
          goalIds,
        },
        editingMoment ? t("momentUpdated") : t("momentCaptured"),
      )
    ) {
      setMomentOpen(false);
      setEditingMoment(null);
    }
  };

  const submitGoal = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get("title") || "").trim();
    if (!title) {
      setGoalError(t("requiredTitle"));
      return;
    }
    setGoalError("");
    if (
      await mutate(
        {
          action: editingGoal ? "updateGoal" : "createGoal",
          id: editingGoal?.id,
          title,
          description: form.get("description"),
          targetSteps: Number(form.get("targetSteps")),
          completedSteps: editingGoal?.completedSteps || 0,
          category: form.get("category"),
          deadline: form.get("deadline"),
          status: editingGoal?.status || "active",
        },
        editingGoal ? t("goalUpdated") : t("goalCreated"),
      )
    ) {
      setGoalOpen(false);
      setEditingGoal(null);
    }
  };

  const submitSettings = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const nextLanguage = form.get("language") === "ru" ? "ru" : "en";
    await mutate(
      {
        action: "updateSettings",
        displayName: form.get("displayName"),
        language: nextLanguage,
        tone: form.get("tone"),
        timezone: form.get("timezone"),
        remindersEnabled: form.get("remindersEnabled") === "on",
        reminderTime: form.get("reminderTime"),
        reminderFrequency: form.get("reminderFrequency"),
      },
      copy[nextLanguage].settingsSaved,
    );
  };

  const finishOnboarding = async () => {
    const onboardingLanguage = onboardingDraft.language;
    const o = onboardingCopy[onboardingLanguage];
    if (
      !onboardingDraft.momentTitle.trim() ||
      !onboardingDraft.momentContent.trim()
    ) {
      setOnboardingError(o.required);
      return;
    }
    setOnboardingError("");
    const success = await mutate(
      {
        action: "completeOnboarding",
        displayName: onboardingDraft.name,
        language: onboardingLanguage,
        selectedAreas: onboardingDraft.areas,
        goalTitle: onboardingDraft.goalTitle,
        goalCategory: onboardingDraft.goalCategory,
        goalSteps: onboardingDraft.goalSteps,
        momentTitle: onboardingDraft.momentTitle,
        momentContent: onboardingDraft.momentContent,
        momentCategory: onboardingDraft.momentCategory,
        momentMood: onboardingDraft.momentMood,
      },
      o.ready,
    );
    if (!success) setOnboardingError(o.error);
  };

  const deleteAccount = async () => {
    const requiredPhrase = lang === "ru" ? "УДАЛИТЬ" : "DELETE";
    if (deleteAccountPhrase.trim().toUpperCase() !== requiredPhrase) return;
    if (await mutate({ action: "deleteAccount" })) {
      setDeleteAccountOpen(false);
      setDeleteAccountPhrase("");
      setOnboardingStep(0);
      setView("stats");
    }
  };

  const updateGoal = (goal: Goal, changes: Partial<Goal>, message?: string) =>
    mutate({ action: "updateGoal", ...goal, ...changes }, message);
  const openMoment = (moment?: Moment) => {
    setMomentError("");
    setEditingMoment(moment || null);
    setMomentOpen(true);
  };
  const openGoal = (goal?: Goal) => {
    setGoalError("");
    setEditingGoal(goal || null);
    setGoalOpen(true);
  };
  const askForConfirmation = (
    title: string,
    description: string,
    confirmLabel: string,
    onConfirm: () => void,
  ) => setConfirmDialog({ title, description, confirmLabel, onConfirm });
  const showAnotherMoment = () => {
    if (!pastMoments.length) return;
    const candidates = pastMoments.filter(
      (moment) => moment.id !== timeMoment?.id,
    );
    setTimeMomentId((candidates[0] || pastMoments[0]).id);
  };

  const exportJson = () =>
    downloadFile(
      `chronicle-${new Date().toISOString().slice(0, 10)}.json`,
      JSON.stringify(data, null, 2),
      "application/json",
    );
  const exportMarkdown = () => {
    const journal = data.moments
      .map(
        (moment) =>
          `## ${moment.title}\n\n${formatDate(moment.createdAt)} · ${categoryLabel(moment.category)} · ${moodLabel(moment.mood)}\n\n${moment.content}`,
      )
      .join("\n\n---\n\n");
    downloadFile(
      `chronicle-journal-${new Date().toISOString().slice(0, 10)}.md`,
      `# Chronicle — ${data.settings.displayName}\n\n${journal}`,
      "text/markdown",
    );
  };

  const formatDate = (value: string) =>
    new Date(value).toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  const greeting =
    new Date().getHours() < 12
      ? t("goodMorning")
      : new Date().getHours() < 18
        ? t("goodAfternoon")
        : t("goodEvening");
  const nav: { id: View; icon: string; label: keyof typeof copy.en }[] = [
    { id: "today", icon: "✦", label: "today" },
    { id: "moments", icon: "○", label: "moments" },
    { id: "goals", icon: "◇", label: "goals" },
    { id: "stats", icon: "◉", label: "stats" },
    { id: "time", icon: "↶", label: "time" },
  ];

  const renderOnboarding = () => {
    const onboardingLanguage = onboardingDraft.language;
    const o = onboardingCopy[onboardingLanguage];
    const areaLabel = (area: string) =>
      categoryCopy[onboardingLanguage][area] || area;
    const moodName = (mood: string) =>
      moodCopy[onboardingLanguage][mood] || mood;
    const next = () => {
      setOnboardingError("");
      if (onboardingStep === 0 && !onboardingDraft.name.trim()) {
        setOnboardingError(o.required);
        return;
      }
      if (onboardingStep === 1 && onboardingDraft.areas.length < 3) {
        setOnboardingError(o.areaError);
        return;
      }
      if (onboardingStep === 2 && !onboardingDraft.goalTitle.trim()) {
        setOnboardingError(o.required);
        return;
      }
      setOnboardingStep((step) => Math.min(3, step + 1));
    };
    return (
      <div
        className="onboarding-shell"
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-title"
      >
        <div className="onboarding-stars">
          <i />
          <i />
          <i />
          <i />
        </div>
        <section className="onboarding-card">
          <header>
            <Link className="workspace-brand" href="/">
              <span>C</span>
              <strong>chronicle</strong>
            </Link>
            <div className="onboarding-progress">
              <small>
                {o.step} {onboardingStep + 1} / 4
              </small>
              <div>
                {[0, 1, 2, 3].map((step) => (
                  <span
                    key={step}
                    className={step <= onboardingStep ? "active" : ""}
                  />
                ))}
              </div>
            </div>
          </header>
          {onboardingStep === 0 && (
            <div className="onboarding-step">
              <small>✦ CHRONICLE</small>
              <h1 id="onboarding-title">{o.welcome}</h1>
              <p>{o.welcomeText}</p>
              <label>
                {o.name}
                <input
                  value={onboardingDraft.name}
                  onChange={(event) =>
                    setOnboardingDraft({
                      ...onboardingDraft,
                      name: event.target.value,
                    })
                  }
                  placeholder={o.namePlaceholder}
                  autoFocus
                  maxLength={40}
                />
              </label>
              <label>
                {o.language}
                <select
                  value={onboardingDraft.language}
                  onChange={(event) =>
                    setOnboardingDraft({
                      ...onboardingDraft,
                      language: event.target.value === "ru" ? "ru" : "en",
                    })
                  }
                >
                  <option value="en">English</option>
                  <option value="ru">Русский</option>
                </select>
              </label>
            </div>
          )}
          {onboardingStep === 1 && (
            <div className="onboarding-step">
              <small>✦ {o.step} 2</small>
              <h1 id="onboarding-title">{o.areas}</h1>
              <p>{o.areasText}</p>
              <div className="onboarding-areas">
                {categories.slice(1).map((area) => {
                  const checked = onboardingDraft.areas.includes(area);
                  return (
                    <button
                      type="button"
                      key={area}
                      className={checked ? "active" : ""}
                      onClick={() => {
                        const areas = checked
                          ? onboardingDraft.areas.filter(
                              (item) => item !== area,
                            )
                          : [...onboardingDraft.areas, area];
                        const fallback = areas[0] || "Growth";
                        setOnboardingDraft({
                          ...onboardingDraft,
                          areas,
                          goalCategory: areas.includes(
                            onboardingDraft.goalCategory,
                          )
                            ? onboardingDraft.goalCategory
                            : fallback,
                          momentCategory: areas.includes(
                            onboardingDraft.momentCategory,
                          )
                            ? onboardingDraft.momentCategory
                            : fallback,
                        });
                      }}
                    >
                      <span>{checked ? "✓" : "○"}</span>
                      {areaLabel(area)}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          {onboardingStep === 2 && (
            <div className="onboarding-step">
              <small>◇ {o.step} 3</small>
              <h1 id="onboarding-title">{o.goal}</h1>
              <p>{o.goalText}</p>
              <label>
                {o.goalTitle}
                <input
                  value={onboardingDraft.goalTitle}
                  onChange={(event) =>
                    setOnboardingDraft({
                      ...onboardingDraft,
                      goalTitle: event.target.value,
                    })
                  }
                  placeholder={o.goalPlaceholder}
                  autoFocus
                  maxLength={100}
                />
              </label>
              <div className="onboarding-grid">
                <label>
                  {o.goalArea}
                  <select
                    value={onboardingDraft.goalCategory}
                    onChange={(event) =>
                      setOnboardingDraft({
                        ...onboardingDraft,
                        goalCategory: event.target.value,
                      })
                    }
                  >
                    {onboardingDraft.areas.map((area) => (
                      <option key={area} value={area}>
                        {areaLabel(area)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {o.goalSteps}
                  <input
                    type="number"
                    min="1"
                    max="999"
                    value={onboardingDraft.goalSteps}
                    onChange={(event) =>
                      setOnboardingDraft({
                        ...onboardingDraft,
                        goalSteps: Math.max(1, Number(event.target.value)),
                      })
                    }
                  />
                </label>
              </div>
            </div>
          )}
          {onboardingStep === 3 && (
            <div className="onboarding-step">
              <small>● {o.step} 4</small>
              <h1 id="onboarding-title">{o.moment}</h1>
              <p>{o.momentText}</p>
              <label>
                {o.momentTitle}
                <input
                  value={onboardingDraft.momentTitle}
                  onChange={(event) =>
                    setOnboardingDraft({
                      ...onboardingDraft,
                      momentTitle: event.target.value,
                    })
                  }
                  placeholder={o.momentPlaceholder}
                  autoFocus
                  maxLength={100}
                />
              </label>
              <label>
                {o.details}
                <textarea
                  value={onboardingDraft.momentContent}
                  onChange={(event) =>
                    setOnboardingDraft({
                      ...onboardingDraft,
                      momentContent: event.target.value,
                    })
                  }
                  placeholder={o.detailsPlaceholder}
                  rows={4}
                />
              </label>
              <div className="onboarding-grid">
                <label>
                  {o.goalArea}
                  <select
                    value={onboardingDraft.momentCategory}
                    onChange={(event) =>
                      setOnboardingDraft({
                        ...onboardingDraft,
                        momentCategory: event.target.value,
                      })
                    }
                  >
                    {onboardingDraft.areas.map((area) => (
                      <option key={area} value={area}>
                        {areaLabel(area)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {o.mood}
                  <select
                    value={onboardingDraft.momentMood}
                    onChange={(event) =>
                      setOnboardingDraft({
                        ...onboardingDraft,
                        momentMood: event.target.value,
                      })
                    }
                  >
                    {moods.map((mood) => (
                      <option key={mood} value={mood}>
                        {moodName(mood)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
          )}
          {onboardingError && (
            <p className="onboarding-error" role="alert">
              {onboardingError}
            </p>
          )}
          <footer>
            {onboardingStep > 0 && (
              <button
                className="workspace-secondary"
                type="button"
                onClick={() => {
                  setOnboardingError("");
                  setOnboardingStep((step) => Math.max(0, step - 1));
                }}
              >
                {o.back}
              </button>
            )}
            <button
              className="workspace-primary"
              type="button"
              disabled={saving}
              onClick={() =>
                onboardingStep === 3 ? void finishOnboarding() : next()
              }
            >
              {saving
                ? copy[onboardingLanguage].savingLabel
                : onboardingStep === 3
                  ? o.finish
                  : o.continue}
            </button>
          </footer>
        </section>
      </div>
    );
  };

  const renderMoments = () => (
    <>
      <div className="workspace-toolbar">
        <div className="category-pills">
          {["All", ...availableAreas].map((category) => (
            <button
              key={category}
              className={activeCategory === category ? "active" : ""}
              onClick={() => setActiveCategory(category)}
            >
              {categoryLabel(category)}
            </button>
          ))}
        </div>
        <label className="workspace-search">
          <span>⌕</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("search")}
          />
        </label>
      </div>
      {!visibleMoments.length ? (
        <div className="workspace-empty">
          <span>✦</span>
          <h3>{data.moments.length ? t("noMatch") : t("emptyTitle")}</h3>
          <p>{data.moments.length ? t("noMatchText") : t("emptyText")}</p>
          <div>
            <button className="workspace-primary" onClick={() => openMoment()}>
              {t("capture")}
            </button>
            {!data.moments.length && (
              <button
                className="workspace-secondary"
                disabled={saving}
                onClick={() =>
                  void mutate({ action: "seedDemo" }, t("demoAdded"))
                }
              >
                {t("demo")}
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="workspace-moment-list">
          {visibleMoments.map((moment) => (
            <article className="workspace-moment" key={moment.id}>
              <div
                className={`workspace-moment-marker marker-${moment.category.toLowerCase()}`}
              />
              <div className="workspace-moment-card">
                <div className="workspace-moment-meta">
                  <span>{formatDate(moment.createdAt)}</span>
                  <span>{categoryLabel(moment.category)}</span>
                  <span>{moodLabel(moment.mood)}</span>
                </div>
                <h3>{moment.title}</h3>
                <p>{moment.content}</p>
                {moment.goalIds.length > 0 && (
                  <div className="workspace-linked-goals">
                    {moment.goalIds.map((id) => (
                      <span key={id}>
                        ◇ {data.goals.find((goal) => goal.id === id)?.title}
                      </span>
                    ))}
                  </div>
                )}
                <div className="workspace-card-actions">
                  <button
                    onClick={() =>
                      void mutate({
                        action: "toggleFavorite",
                        id: moment.id,
                        favorite: !moment.isFavorite,
                      })
                    }
                    aria-label={t("favorites")}
                  >
                    {moment.isFavorite ? "♥" : "♡"}
                  </button>
                  <button onClick={() => openMoment(moment)}>
                    {t("edit")}
                  </button>
                  <button
                    className="danger"
                    onClick={() =>
                      askForConfirmation(
                        t("deleteMomentConfirm"),
                        t("deleteMomentExplain"),
                        t("delete"),
                        () =>
                          void mutate(
                            { action: "deleteMoment", id: moment.id },
                            t("momentDeleted"),
                          ),
                      )
                    }
                  >
                    {t("delete")}
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );

  const renderInsights = () => {
    const selectedGoalSteps = selectedLifeScore.goals.reduce(
      (sum, goal) => sum + goal.completedSteps,
      0,
    );
    const periodLabel = t(statsPeriod);
    const hasLifeData = data.moments.length > 0 || data.goals.length > 0;
    if (!hasLifeData)
      return (
        <div className="constellation-empty-insights">
          <div className="constellation-empty-orbit">
            <span>✦</span>
            <i />
            <i />
            <i />
          </div>
          <small>{t("lifeConstellation")}</small>
          <h2>{t("noLifeData")}</h2>
          <p>{t("noLifeDataText")}</p>
          <div>
            <button className="workspace-primary" onClick={() => openMoment()}>
              + {t("addMoment")}
            </button>
            <button className="workspace-secondary" onClick={() => openGoal()}>
              + {t("createGoal")}
            </button>
          </div>
          <details>
            <summary>{t("scoreHelp")}</summary>
            <p>{t("scoreFormula")}</p>
          </details>
        </div>
      );
    return (
      <div className="constellation-insights">
        <section className="constellation-intro">
          <small>
            {t("lifeConstellation")} · {periodLabel.toUpperCase()}
          </small>
          <h2>{t("seeMoving")}</h2>
          <p>{t("constellationIntro")}</p>
          <div className="workspace-status-tabs">
            {(["week", "month", "all"] as const).map((period) => (
              <button
                className={statsPeriod === period ? "active" : ""}
                onClick={() => setStatsPeriod(period)}
                key={period}
              >
                {t(period)}
              </button>
            ))}
          </div>
          <article className="constellation-selected">
            <div>
              <span />
              <small>
                {categoryLabel(selectedLifeScore.category).toUpperCase()}
              </small>
            </div>
            <strong>{selectedLifeScore.score}%</strong>
            <p>
              {selectedLifeScore.moments}{" "}
              {momentCountLabel(selectedLifeScore.moments)} ·{" "}
              {selectedGoalSteps} {t("goalSteps")}
            </p>
            <small className="constellation-score-summary">
              {t("scoreSummary")}
            </small>
            <button
              onClick={() => {
                setActiveCategory(selectedLifeScore.category);
                setView("moments");
              }}
            >
              {t("exploreMoments")}: {categoryLabel(selectedLifeScore.category)}{" "}
              →
            </button>
          </article>
        </section>
        <section className="constellation-wheel-panel">
          <header>
            <div>
              <small>{t("lifeBalance")}</small>
              <h2>{t("shapePeriod")}</h2>
            </div>
            <span>
              {stats.current.length} {momentCountLabel(stats.current.length)} ·{" "}
              {data.goals.reduce((sum, goal) => sum + goal.completedSteps, 0)}{" "}
              {t("goalSteps")}
            </span>
          </header>
          <div className="constellation-wheel-wrap">
            <svg
              viewBox="0 0 420 420"
              role="img"
              aria-label={lifeScores
                .map((item) => `${categoryLabel(item.category)} ${item.score}%`)
                .join(", ")}
            >
              <g className="constellation-wheel-grid">
                {[40, 75, 110, 145].map((radius) => (
                  <circle key={radius} cx="210" cy="210" r={radius} />
                ))}
                {lifeScores.map((item, index) => {
                  const angle =
                    -Math.PI / 2 + index * ((Math.PI * 2) / lifeScores.length);
                  return (
                    <line
                      key={item.category}
                      x1="210"
                      y1="210"
                      x2={210 + Math.cos(angle) * 145}
                      y2={210 + Math.sin(angle) * 145}
                    />
                  );
                })}
              </g>
              <polygon
                className="constellation-wheel-area"
                points={wheelPoints}
              />
              <g className="constellation-wheel-points">
                {lifeScores.map((item, index) => {
                  const angle =
                    -Math.PI / 2 + index * ((Math.PI * 2) / lifeScores.length);
                  const radius = 32 + item.score * 1.18;
                  return (
                    <circle
                      key={item.category}
                      cx={210 + Math.cos(angle) * radius}
                      cy={210 + Math.sin(angle) * radius}
                      r="6"
                    />
                  );
                })}
              </g>
              <g className="constellation-wheel-labels">
                {lifeScores.map((item, index) => {
                  const angle =
                    -Math.PI / 2 + index * ((Math.PI * 2) / lifeScores.length);
                  const x = 210 + Math.cos(angle) * 181;
                  const y = 210 + Math.sin(angle) * 181;
                  return (
                    <text
                      key={item.category}
                      x={x}
                      y={y}
                      textAnchor={
                        Math.cos(angle) > 0.3
                          ? "start"
                          : Math.cos(angle) < -0.3
                            ? "end"
                            : "middle"
                      }
                    >
                      {categoryLabel(item.category)} · {item.score}%
                    </text>
                  );
                })}
              </g>
            </svg>
            <div className="constellation-wheel-center">
              <span>✦</span>
              <strong>
                {Math.round(
                  lifeScores.reduce((sum, item) => sum + item.score, 0) /
                    lifeScores.length,
                )}
                %
              </strong>
              <small>{t("overall")}</small>
            </div>
          </div>
          <div className="constellation-direction-buttons">
            {lifeScores.map((item) => (
              <button
                key={item.category}
                className={selectedDirection === item.category ? "active" : ""}
                onClick={() => setSelectedDirection(item.category)}
              >
                <span />
                {categoryLabel(item.category)}
              </button>
            ))}
          </div>
        </section>
        <aside className="constellation-rail">
          <article className="constellation-reflection">
            <span>✦</span>
            <small>{t("currentReflection")}</small>
            <h2>
              {highestDirection.score
                ? `${categoryLabel(highestDirection.category)} ${t("directionMomentum")}`
                : t("patternFallback")}
            </h2>
            <p>
              {lowestDirection.score < 35
                ? `${categoryLabel(lowestDirection.category)} ${t("directionQuiet")}`
                : t("balancedAttention")}
            </p>
            <button
              onClick={() => setSelectedDirection(lowestDirection.category)}
            >
              {t("quietDirection")} →
            </button>
          </article>
          <article className="constellation-next-step">
            <small>{t("gentleNext")}</small>
            <h3>{t("captureMeaningful")}</h3>
            <button
              className="workspace-primary"
              onClick={() => {
                setActiveCategory(lowestDirection.category);
                openMoment();
              }}
            >
              + {t("addMoment")}
            </button>
          </article>
          <blockquote>“{t("balanceQuote")}”</blockquote>
        </aside>
        <section className="constellation-insights-details">
          <article className="constellation-history">
            <header>
              <div>
                <small>{t("monthlyHistory")}</small>
                <h2>{categoryLabel(selectedDirection)}</h2>
              </div>
              <p>{t("monthlyHistoryText")}</p>
            </header>
            {directionHistory.some((item) => item.count > 0) ? (
              <div className="constellation-history-chart">
                {directionHistory.map((item) => (
                  <div className="history-month" key={item.label}>
                    <div>
                      <span style={{ height: `${Math.max(8, item.score)}%` }}>
                        <b>{item.score}%</b>
                      </span>
                    </div>
                    <strong>{item.label}</strong>
                    <small>
                      {item.count} {momentCountLabel(item.count)}
                    </small>
                  </div>
                ))}
              </div>
            ) : (
              <div className="constellation-history-empty">
                <span>○</span>
                <p>{t("noMonthlyData")}</p>
              </div>
            )}
          </article>
          <details className="constellation-score-help">
            <summary>
              {t("scoreHelp")}
              <span>+</span>
            </summary>
            <p>{t("scoreFormula")}</p>
            <div>
              <span>
                <b>60%</b>
                {t("moments")}
              </span>
              <span>
                <b>40%</b>
                {t("goals")}
              </span>
            </div>
          </details>
        </section>
      </div>
    );
  };

  if (loading)
    return (
      <main className="workspace-system-state">
        <div
          className="workspace-brand workspace-system-brand-image"
          aria-label="Chronicle"
        >
          <span aria-hidden="true" />
        </div>
        <div className="workspace-loading" aria-label={t("loadingLabel")}>
          <span />
          <span />
          <span />
        </div>
        <p>{t("loadingLabel")}</p>
      </main>
    );
  if (loadFailed)
    return (
      <main className="workspace-system-state workspace-error-state">
        <span>!</span>
        <h1>{t("loadError")}</h1>
        <p>
          {lang === "ru"
            ? "Ваши данные не изменены. Проверьте соединение и повторите попытку."
            : "Your data is unchanged. Check your connection and try again."}
        </p>
        <button className="workspace-primary" onClick={() => void load()}>
          {t("retry")}
        </button>
      </main>
    );
  if (!data.settings.onboardingComplete) return renderOnboarding();

  return (
    <main className="workspace-page">
      <header className="constellation-app-header celestial-header">
        <Link
          className="workspace-brand constellation-brand constellation-brand-image"
          href="/"
          aria-label="Chronicle"
        >
          <span aria-hidden="true" />
        </Link>
        <div className="constellation-nav-shell">
          <i className="constellation-nav-track" />
          <nav aria-label="Chronicle">
            {nav.map((item) => (
              <button
                key={item.id}
                className={view === item.id ? "active" : ""}
                onClick={() => setView(item.id)}
              >
                <span
                  className={`constellation-nav-icon nav-icon-${item.id}`}
                  aria-hidden="true"
                >
                  <i />
                </span>
                <span
                  data-mobile-label={
                    item.id === "time" ? t("timeShort") : t(item.label)
                  }
                >
                  {t(item.label)}
                </span>
              </button>
            ))}
          </nav>
        </div>
        <button
          className={`constellation-profile celestial-profile ${view === "settings" ? "active" : ""}`}
          onClick={() => setView("settings")}
          aria-label={t("settings")}
        >
          <span
            className="celestial-streak-ring"
            style={
              {
                "--streak-progress": `${Math.min(100, calculateStreak(data.moments) * 10)}%`,
              } as CSSProperties
            }
          >
            <b>{calculateStreak(data.moments)}</b>
          </span>
          <div>
            <b>{data.settings.displayName}</b>
            <small>{t("dayStreak")}</small>
          </div>
        </button>
        <div className="constellation-header-glow" />
      </header>
      <section className="workspace-main">
        {!["stats", "today", "moments"].includes(view) && (
          <header className="workspace-header">
            <div>
              <span>
                {new Date()
                  .toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
                    weekday: "long",
                    month: "long",
                    day: "numeric",
                  })
                  .toUpperCase()}
              </span>
              <h1>{t(view)}</h1>
            </div>
            {!["time", "settings"].includes(view) && (
              <button
                className="workspace-primary"
                onClick={() => (view === "goals" ? openGoal() : openMoment())}
              >
                {view === "goals" ? t("newGoal") : t("newMoment")}
              </button>
            )}
            <button
              className="workspace-mobile-settings"
              onClick={() => setView("settings")}
              aria-label={t("settings")}
            >
              ⚙
            </button>
          </header>
        )}
        {notice && (
          <div className="workspace-notice" role="status">
            <span>✦</span>
            {notice}
            <button onClick={() => setNotice("")} aria-label={t("close")}>
              ×
            </button>
          </div>
        )}
        {view === "goals" ? (
          <div className="workspace-goals">
            <div className="workspace-section-title">
              <div>
                <span>
                  {lang === "ru"
                    ? "ОСОЗНАННЫЙ ПРОГРЕСС"
                    : "INTENTIONAL PROGRESS"}
                </span>
                <h2>{t("goalsTitle")}</h2>
              </div>
              <p>{t("goalsIntro")}</p>
            </div>
            <div className="workspace-status-tabs">
              {(["active", "completed", "abandoned"] as const).map((status) => (
                <button
                  className={goalFilter === status ? "active" : ""}
                  onClick={() => setGoalFilter(status)}
                  key={status}
                >
                  {t(status)}{" "}
                  <span>
                    {data.goals.filter((goal) => goal.status === status).length}
                  </span>
                </button>
              ))}
            </div>
            {!filteredGoals.length ? (
              <div className="workspace-empty">
                <span>◇</span>
                <h3>{t("noGoals")}</h3>
                <button
                  className="workspace-primary"
                  onClick={() => openGoal()}
                >
                  {t("createGoal")}
                </button>
              </div>
            ) : (
              filteredGoals.map((goal) => {
                const percent = Math.min(
                  100,
                  Math.round((goal.completedSteps / goal.targetSteps) * 100),
                );
                const linked = data.moments.filter((moment) =>
                  moment.goalIds.includes(goal.id),
                ).length;
                const overdue =
                  goal.deadline &&
                  new Date(goal.deadline) < new Date() &&
                  goal.status === "active";
                return (
                  <article
                    className={`workspace-goal status-${goal.status}`}
                    key={goal.id}
                  >
                    <div
                      className="workspace-goal-ring"
                      style={
                        { "--goal-progress": `${percent}%` } as CSSProperties
                      }
                    >
                      <span>{percent}%</span>
                    </div>
                    <div className="workspace-goal-copy">
                      <small>
                        {categoryLabel(goal.category).toUpperCase()} ·{" "}
                        {t(goal.status)}
                      </small>
                      <h3>{goal.title}</h3>
                      <p>
                        {goal.description ||
                          (lang === "ru"
                            ? "Значимое направление для следующей главы вашей жизни."
                            : "A meaningful direction for your next chapter.")}
                      </p>
                      <div className="workspace-goal-meta">
                        <span>
                          ◇ {linked} {linkedMomentCountLabel(linked)}
                        </span>
                        {goal.deadline && (
                          <span className={overdue ? "overdue" : ""}>
                            {overdue ? t("overdue") : t("due")}:{" "}
                            {formatDate(goal.deadline)}
                          </span>
                        )}
                      </div>
                      <div className="workspace-progress">
                        <i style={{ width: `${percent}%` }} />
                      </div>
                      <span>
                        {goal.completedSteps} / {goal.targetSteps}
                      </span>
                    </div>
                    <div className="workspace-goal-actions">
                      {goal.status === "active" ? (
                        <>
                          <button
                            disabled={goal.completedSteps <= 0}
                            onClick={() =>
                              void updateGoal(goal, {
                                completedSteps: goal.completedSteps - 1,
                              })
                            }
                          >
                            −
                          </button>
                          <button
                            disabled={goal.completedSteps >= goal.targetSteps}
                            onClick={() =>
                              void updateGoal(
                                goal,
                                { completedSteps: goal.completedSteps + 1 },
                                t("progressUpdated"),
                              )
                            }
                          >
                            +
                          </button>
                          <button onClick={() => openGoal(goal)}>
                            {t("edit")}
                          </button>
                          <button
                            className="complete"
                            onClick={() =>
                              void updateGoal(
                                goal,
                                {
                                  status: "completed",
                                  completedSteps: goal.targetSteps,
                                },
                                t("goalCompleted"),
                              )
                            }
                          >
                            {t("completeGoal")}
                          </button>
                          <button
                            onClick={() =>
                              askForConfirmation(
                                t("archiveGoalConfirm"),
                                t("archiveGoalExplain"),
                                t("archive"),
                                () =>
                                  void updateGoal(goal, {
                                    status: "abandoned",
                                  }),
                              )
                            }
                          >
                            {t("archive")}
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() =>
                            void updateGoal(
                              goal,
                              { status: "active" },
                              t("goalReopened"),
                            )
                          }
                        >
                          {t("reopen")}
                        </button>
                      )}
                      <button
                        className="danger"
                        onClick={() =>
                          askForConfirmation(
                            t("deleteGoalConfirm"),
                            t("deleteGoalExplain"),
                            t("delete"),
                            () =>
                              void mutate({
                                action: "deleteGoal",
                                id: goal.id,
                              }),
                          )
                        }
                      >
                        {t("delete")}
                      </button>
                    </div>
                  </article>
                );
              })
            )}
          </div>
        ) : view === "stats" ? (
          renderInsights()
        ) : view === "time" ? (
          <div className="workspace-time-machine">
            <div className="workspace-section-title">
              <div>
                <span>{t("time").toUpperCase()}</span>
                <h2>{t("timeTitle")}</h2>
              </div>
              <p>{t("timeIntro")}</p>
            </div>
            {timeMoment ? (
              <article className="workspace-memory">
                <div className="workspace-memory-date">
                  <strong>{new Date(timeMoment.createdAt).getDate()}</strong>
                  <span>
                    {new Date(timeMoment.createdAt).toLocaleDateString(
                      lang === "ru" ? "ru-RU" : "en-US",
                      { month: "long", year: "numeric" },
                    )}
                  </span>
                </div>
                <div className="workspace-memory-copy">
                  <small>
                    {categoryLabel(timeMoment.category)} ·{" "}
                    {moodLabel(timeMoment.mood)}
                  </small>
                  <h3>{timeMoment.title}</h3>
                  <p>{timeMoment.content}</p>
                  {timeMoment.goalIds.length > 0 && (
                    <div className="workspace-linked-goals">
                      {timeMoment.goalIds.map((id) => (
                        <span key={id}>
                          ◇ {data.goals.find((goal) => goal.id === id)?.title}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  className="workspace-primary"
                  onClick={showAnotherMoment}
                >
                  ↶ {t("surprise")}
                </button>
              </article>
            ) : (
              <div className="workspace-empty">
                <span>↶</span>
                <h3>{t("timeTitle")}</h3>
                <p>{t("noPast")}</p>
                <button
                  className="workspace-primary"
                  onClick={() => openMoment()}
                >
                  {t("capture")}
                </button>
              </div>
            )}
          </div>
        ) : view === "settings" ? (
          <div className="workspace-settings">
            <div className="workspace-section-title">
              <div>
                <span>{t("yourSpace")}</span>
                <h2>{t("settingsTitle")}</h2>
              </div>
              <p>{t("privacy")}</p>
            </div>
            <form onSubmit={submitSettings}>
              <section>
                <h3>{t("profile")}</h3>
                <div className="workspace-settings-grid">
                  <label>
                    {t("displayName")}
                    <input
                      name="displayName"
                      defaultValue={data.settings.displayName}
                      maxLength={40}
                    />
                  </label>
                  <label>
                    {t("language")}
                    <select name="language" defaultValue={lang}>
                      <option value="en">English</option>
                      <option value="ru">Русский</option>
                    </select>
                  </label>
                  <label>
                    {t("tone")}
                    <select name="tone" defaultValue={data.settings.tone}>
                      <option value="gentle">{t("gentle")}</option>
                      <option value="thoughtful">{t("thoughtful")}</option>
                      <option value="direct">{t("direct")}</option>
                    </select>
                  </label>
                  <label>
                    {t("timezone")}
                    <select
                      name="timezone"
                      defaultValue={data.settings.timezone}
                    >
                      <option>Europe/Moscow</option>
                      <option>Europe/London</option>
                      <option>Europe/Berlin</option>
                      <option>America/New_York</option>
                      <option>Asia/Tokyo</option>
                    </select>
                  </label>
                </div>
              </section>
              <section>
                <h3>{t("reminders")}</h3>
                <label className="workspace-toggle">
                  <input
                    type="checkbox"
                    name="remindersEnabled"
                    defaultChecked={data.settings.remindersEnabled}
                  />
                  <span />
                  {t("enableReminders")}
                </label>
                <div className="workspace-settings-grid">
                  <label>
                    {t("reminderTime")}
                    <input
                      type="time"
                      name="reminderTime"
                      defaultValue={data.settings.reminderTime}
                    />
                  </label>
                  <label>
                    {t("frequency")}
                    <select
                      name="reminderFrequency"
                      defaultValue={data.settings.reminderFrequency}
                    >
                      <option value="daily">{t("daily")}</option>
                      <option value="weekdays">{t("weekdays")}</option>
                      <option value="weekly">{t("weekly")}</option>
                    </select>
                  </label>
                </div>
                <p className="workspace-form-note">{t("reminderNote")}</p>
              </section>
              <button
                className="workspace-primary"
                type="submit"
                disabled={saving}
              >
                {saving ? t("savingLabel") : t("save")}
              </button>
            </form>
            <section className="workspace-data-card">
              <div>
                <h3>{t("data")}</h3>
                <p>{t("privacy")}</p>
                <a className="workspace-privacy-link" href="/privacy">
                  {t("privacyPolicy")} →
                </a>
              </div>
              <div>
                <a className="workspace-secondary" href="/journal">
                  {t("exportPdf")}
                </a>
                <button className="workspace-secondary" onClick={exportJson}>
                  {t("exportJson")}
                </button>
                <button
                  className="workspace-secondary"
                  onClick={exportMarkdown}
                >
                  {t("exportMd")}
                </button>
                <button
                  className="workspace-danger-button"
                  disabled={saving}
                  onClick={() =>
                    askForConfirmation(
                      t("deleteAllConfirm"),
                      t("deleteAllExplain"),
                      t("deleteAll"),
                      () =>
                        void mutate({ action: "deleteAll" }, t("allDeleted")),
                    )
                  }
                >
                  {t("deleteAll")}
                </button>
              </div>
            </section>
            <section className="workspace-danger-zone">
              <div>
                <small>{t("dangerZone")}</small>
                <h3>{t("deleteAccount")}</h3>
                <p>{t("deleteAccountText")}</p>
              </div>
              <button
                className="workspace-danger-button"
                onClick={() => setDeleteAccountOpen(true)}
              >
                {t("deleteAccount")}
              </button>
            </section>
          </div>
        ) : (
          <div
            className={`workspace-dashboard constellation-journal-page ${view === "today" ? "constellation-today-page" : "constellation-moments-page"}`}
          >
            {view === "today" ? (
              <section className="constellation-today-hero">
                <div className="constellation-today-copy">
                  <small>
                    {new Date()
                      .toLocaleDateString(lang === "ru" ? "ru-RU" : "en-US", {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                      })
                      .toUpperCase()}
                  </small>
                  <p>
                    {greeting}, {data.settings.displayName}
                  </p>
                  <h2>{t("todayGreeting")}</h2>
                  <span>{t("todaySupport")}</span>
                  <button
                    className="workspace-primary"
                    onClick={() => openMoment()}
                  >
                    + {t("capture")}
                  </button>
                </div>
                <div
                  className="constellation-today-orbit"
                  aria-label={t("todayStory")}
                >
                  <div className="today-orbit-center">
                    <strong>{visibleMoments.length}</strong>
                    <small>{t("today").toUpperCase()}</small>
                  </div>
                  <div className="today-orbit-stat stat-moments">
                    <strong>{data.moments.length}</strong>
                    <span>{t("allMoments")}</span>
                  </div>
                  <div className="today-orbit-stat stat-streak">
                    <strong>{calculateStreak(data.moments)}</strong>
                    <span>{t("dayStreak")}</span>
                  </div>
                  <div className="today-orbit-stat stat-goals">
                    <strong>{activeGoals.length}</strong>
                    <span>{t("activeGoals")}</span>
                  </div>
                </div>
              </section>
            ) : (
              <div className="constellation-moments-heading">
                <div>
                  <small>{t("livingArchive")}</small>
                  <h2>{t("momentsMadeYou")}</h2>
                  <p>{t("archiveIntro")}</p>
                </div>
                <div className="constellation-moments-actions">
                  <div className="constellation-archive-count">
                    <strong>{data.moments.length}</strong>
                    <span>{t("momentsPreserved")}</span>
                  </div>
                  <button
                    className="workspace-primary"
                    onClick={() => openMoment()}
                  >
                    + {t("addMoment")}
                  </button>
                </div>
              </div>
            )}
            <div className="constellation-journal-heading">
              <div>
                <small>
                  {view === "today" ? t("todayChapter") : t("storyTimeline")}
                </small>
                <h2>
                  {view === "today"
                    ? t("rememberedToday")
                    : t("oneMomentAtTime")}
                </h2>
              </div>
              <div className="workspace-mini-stats">
                <span>
                  <b>
                    {data.moments.filter((moment) => moment.isFavorite).length}
                  </b>{" "}
                  {t("favoritesLabel")}
                </span>
                <span>
                  <b>{activeGoals.length}</b> {t("goals")}
                </span>
              </div>
            </div>
            <div className="workspace-grid">
              <section>{renderMoments()}</section>
              <aside>
                <article className="workspace-reflection-card">
                  <small>✦ {t("currentPattern")}</small>
                  <h3>
                    {data.moments.length
                      ? `${categoryLabel(data.moments[0].category)} ${t("directionMomentum")}`
                      : t("patternFallback")}
                  </h3>
                  <p>{t("patternIntro")}</p>
                  <button onClick={() => setView("stats")}>
                    {t("stats")} →
                  </button>
                </article>
                {activeGoals[0] && (
                  <article className="workspace-goal-mini">
                    <small>{t("activeGoal")}</small>
                    <h3>{activeGoals[0].title}</h3>
                    <div className="workspace-progress">
                      <i
                        style={{
                          width: `${Math.round((activeGoals[0].completedSteps / activeGoals[0].targetSteps) * 100)}%`,
                        }}
                      />
                    </div>
                    <span>
                      {activeGoals[0].completedSteps} /{" "}
                      {activeGoals[0].targetSteps}
                    </span>
                    <button onClick={() => setView("goals")}>
                      {t("goals")} →
                    </button>
                  </article>
                )}
                <article className="constellation-time-teaser">
                  <small>{t("time").toUpperCase()}</small>
                  <h3>{t("returnMemory")}</h3>
                  <button onClick={() => setView("time")}>
                    {t("travelBack")} →
                  </button>
                </article>
              </aside>
            </div>
          </div>
        )}
      </section>

      {momentOpen && (
        <div
          className="workspace-modal-backdrop"
          onMouseDown={() => {
            setMomentOpen(false);
            setMomentError("");
          }}
        >
          <div
            className="workspace-modal"
            role="dialog"
            aria-modal="true"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              className="workspace-modal-close"
              onClick={() => {
                setMomentOpen(false);
                setMomentError("");
              }}
              aria-label={t("close")}
            >
              ×
            </button>
            <span>
              {editingMoment ? t("editMomentLabel") : t("newMomentLabel")}
            </span>
            <h2>{t("momentTitle")}</h2>
            <form
              onSubmit={submitMoment}
              noValidate
              onInput={() => momentError && setMomentError("")}
            >
              <label>
                {t("title")}
                <input
                  name="title"
                  defaultValue={editingMoment?.title}
                  autoFocus
                  aria-invalid={Boolean(momentError)}
                />
              </label>
              <label>
                {t("details")}
                <textarea
                  name="content"
                  defaultValue={editingMoment?.content}
                  rows={5}
                  aria-invalid={Boolean(momentError)}
                />
              </label>
              <div className="workspace-form-grid">
                <label>
                  {t("area")}
                  <select
                    name="category"
                    defaultValue={editingMoment?.category || availableAreas[0]}
                  >
                    {availableAreas.map((category) => (
                      <option key={category} value={category}>
                        {categoryLabel(category)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {t("mood")}
                  <select
                    name="mood"
                    defaultValue={editingMoment?.mood || "Proud"}
                  >
                    {moods.map((mood) => (
                      <option key={mood} value={mood}>
                        {moodLabel(mood)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {activeGoals.length > 0 && (
                <fieldset className="workspace-goal-picker">
                  <legend>{t("relatedGoals")}</legend>
                  {activeGoals.map((goal) => (
                    <label key={goal.id}>
                      <input
                        type="checkbox"
                        name="goalIds"
                        value={goal.id}
                        defaultChecked={editingMoment?.goalIds.includes(
                          goal.id,
                        )}
                      />
                      <span>{goal.title}</span>
                    </label>
                  ))}
                </fieldset>
              )}
              {momentError && (
                <p className="workspace-inline-error" role="alert">
                  {momentError}
                </p>
              )}
              <button
                className="workspace-primary"
                type="submit"
                disabled={saving}
              >
                {saving
                  ? t("savingLabel")
                  : editingMoment
                    ? t("saveChanges")
                    : t("captureMoment")}
              </button>
            </form>
          </div>
        </div>
      )}
      {goalOpen && (
        <div
          className="workspace-modal-backdrop"
          onMouseDown={() => {
            setGoalOpen(false);
            setGoalError("");
          }}
        >
          <div
            className="workspace-modal"
            role="dialog"
            aria-modal="true"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              className="workspace-modal-close"
              onClick={() => {
                setGoalOpen(false);
                setGoalError("");
              }}
              aria-label={t("close")}
            >
              ×
            </button>
            <span>{editingGoal ? t("editGoalLabel") : t("newGoalLabel")}</span>
            <h2>{t("goalQuestion")}</h2>
            <form
              onSubmit={submitGoal}
              noValidate
              onInput={() => goalError && setGoalError("")}
            >
              <label>
                {t("title")}
                <input
                  name="title"
                  defaultValue={editingGoal?.title}
                  autoFocus
                  aria-invalid={Boolean(goalError)}
                />
              </label>
              <label>
                {t("description")}
                <textarea
                  name="description"
                  defaultValue={editingGoal?.description}
                  rows={4}
                />
              </label>
              <div className="workspace-form-grid">
                <label>
                  {t("steps")}
                  <input
                    name="targetSteps"
                    type="number"
                    min="1"
                    max="999"
                    defaultValue={editingGoal?.targetSteps || 10}
                    required
                  />
                </label>
                <label>
                  {t("deadline")}
                  <input
                    name="deadline"
                    type="date"
                    defaultValue={editingGoal?.deadline || ""}
                  />
                </label>
                <label>
                  {t("category")}
                  <select
                    name="category"
                    defaultValue={editingGoal?.category || availableAreas[0]}
                  >
                    {availableAreas.map((category) => (
                      <option key={category} value={category}>
                        {categoryLabel(category)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {goalError && (
                <p className="workspace-inline-error" role="alert">
                  {goalError}
                </p>
              )}
              <button
                className="workspace-primary"
                type="submit"
                disabled={saving}
              >
                {saving
                  ? t("savingLabel")
                  : editingGoal
                    ? t("updateGoal")
                    : t("createGoal")}
              </button>
            </form>
          </div>
        </div>
      )}
      {deleteAccountOpen && (
        <div
          className="workspace-modal-backdrop"
          onMouseDown={() => setDeleteAccountOpen(false)}
        >
          <div
            className="workspace-modal workspace-delete-account"
            role="alertdialog"
            aria-modal="true"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              className="workspace-modal-close"
              onClick={() => setDeleteAccountOpen(false)}
              aria-label={t("close")}
            >
              ×
            </button>
            <span>{t("dangerZone")}</span>
            <h2>{t("deleteAccount")}</h2>
            <p>{t("deleteAccountText")}</p>
            <label>
              {t("deleteAccountConfirm")}
              <input
                value={deleteAccountPhrase}
                onChange={(event) => setDeleteAccountPhrase(event.target.value)}
                autoFocus
              />
            </label>
            <div>
              <button
                className="workspace-secondary"
                onClick={() => setDeleteAccountOpen(false)}
              >
                {t("cancel")}
              </button>
              <button
                className="workspace-danger-button"
                disabled={
                  saving ||
                  deleteAccountPhrase.trim().toUpperCase() !==
                    (lang === "ru" ? "УДАЛИТЬ" : "DELETE")
                }
                onClick={() => void deleteAccount()}
              >
                {saving ? t("savingLabel") : t("deleteAccount")}
              </button>
            </div>
          </div>
        </div>
      )}
      {confirmDialog && (
        <div
          className="workspace-modal-backdrop"
          onMouseDown={() => setConfirmDialog(null)}
        >
          <div
            className="workspace-modal workspace-confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-dialog-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              className="workspace-modal-close"
              onClick={() => setConfirmDialog(null)}
              aria-label={t("close")}
            >
              ×
            </button>
            <span>{t("confirm")}</span>
            <h2 id="confirm-dialog-title">{confirmDialog.title}</h2>
            <p>{confirmDialog.description}</p>
            <div>
              <button
                className="workspace-secondary"
                onClick={() => setConfirmDialog(null)}
              >
                {t("cancel")}
              </button>
              <button
                className="workspace-danger-button"
                onClick={() => {
                  const action = confirmDialog.onConfirm;
                  setConfirmDialog(null);
                  action();
                }}
              >
                {confirmDialog.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
      {saving && !momentOpen && !goalOpen && !deleteAccountOpen && (
        <div className="workspace-saving" role="status">
          <span />
          {t("savingLabel")}
        </div>
      )}
    </main>
  );
}
