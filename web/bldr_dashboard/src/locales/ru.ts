// Русская локализация для Bldr Dashboard
export const ru = {
  // Общие элементы
  common: {
    loading: 'Загрузка...',
    error: 'Ошибка',
    success: 'Успешно',
    cancel: 'Отмена',
    save: 'Сохранить',
    delete: 'Удалить',
    edit: 'Редактировать',
    close: 'Закрыть',
    back: 'Назад',
    next: 'Далее',
    search: 'Поиск',
    filter: 'Фильтр',
    clear: 'Очистить',
    refresh: 'Обновить',
    settings: 'Настройки',
    help: 'Помощь',
    about: 'О программе',
    logout: 'Выйти',
    login: 'Войти',
    register: 'Регистрация',
    profile: 'Профиль',
    dashboard: 'Панель управления',
    tools: 'Инструменты',
    history: 'История',
    tabs: 'Вкладки'
  },

  // Навигация и меню
  navigation: {
    home: 'Главная',
    dashboard: 'Панель управления',
    tools: 'Инструменты',
    quickTools: 'Быстрые инструменты',
    unifiedTools: 'Унифицированные инструменты',
    toolTabs: 'Вкладки инструментов',
    history: 'История выполнения',
    settings: 'Настройки',
    profile: 'Профиль',
    help: 'Помощь'
  },

  // Инструменты
  tools: {
    title: 'Инструменты',
    searchPlaceholder: 'Поиск инструментов...',
    category: 'Категория',
    allCategories: 'Все категории',
    popular: 'Популярные',
    recent: 'Недавние',
    favorites: 'Избранные',
    execute: 'Выполнить',
    executeInTab: 'Выполнить во вкладке',
    openInNewTab: 'Открыть в новой вкладке',
    addToFavorites: 'Добавить в избранное',
    removeFromFavorites: 'Удалить из избранного',
    toolInfo: 'Информация об инструменте',
    parameters: 'Параметры',
    results: 'Результаты',
    executionTime: 'Время выполнения',
    status: 'Статус',
    success: 'Успешно',
    error: 'Ошибка',
    warning: 'Предупреждение',
    loading: 'Выполняется...',
    noResults: 'Нет результатов',
    noTools: 'Инструменты не найдены',
    toolNotFound: 'Инструмент не найден',
    executionFailed: 'Выполнение не удалось',
    executionSuccess: 'Выполнение завершено успешно'
  },

  // Категории инструментов
  toolCategories: {
    all: 'Все',
    quick: 'Быстрые',
    analysis: 'Анализ',
    construction: 'Строительство',
    finance: 'Финансы',
    documents: 'Документы',
    search: 'Поиск',
    conversion: 'Конвертация',
    visualization: 'Визуализация',
    automation: 'Автоматизация',
    integration: 'Интеграция',
    utilities: 'Утилиты'
  },

  // Быстрые инструменты
  quickTools: {
    title: 'Быстрые инструменты',
    description: 'Часто используемые инструменты',
    mostUsed: 'Наиболее используемые',
    searchRAG: 'Поиск в базе знаний',
    generateLetter: 'Генерация письма',
    analyzeTender: 'Анализ тендера',
    calculateEstimate: 'Расчет сметы',
    autoBudget: 'Автобюджет',
    textToSpeech: 'Текст в речь',
    imageAnalysis: 'Анализ изображений',
    financialMetrics: 'Финансовые метрики',
    constructionSchedule: 'Строительный график',
    ganttChart: 'Диаграмма Ганта',
    monteCarloSim: 'Симуляция Монте-Карло'
  },

  // RAG поиск
  ragSearch: {
    title: 'Поиск в базе знаний',
    placeholder: 'Введите запрос для поиска...',
    searchButton: 'Поиск',
    results: 'Результаты поиска',
    totalFound: 'Найдено результатов',
    processingTime: 'Время обработки',
    searchMethod: 'Метод поиска',
    noResults: 'Результаты не найдены',
    searchError: 'Ошибка поиска',
    query: 'Запрос',
    score: 'Оценка',
    source: 'Источник',
    documentType: 'Тип документа',
    spNumber: 'Номер СП',
    metadata: 'Метаданные',
    content: 'Содержимое',
    rank: 'Ранг'
  },

  // Вкладки инструментов
  toolTabs: {
    title: 'Вкладки инструментов',
    newTab: 'Новая вкладка',
    closeTab: 'Закрыть вкладку',
    closeAllTabs: 'Закрыть все вкладки',
    executeTool: 'Выполнить инструмент',
    openInNewTab: 'Открыть в новой вкладке',
    toolParameters: 'Параметры инструмента',
    executionResults: 'Результаты выполнения',
    executionHistory: 'История выполнения',
    noTabs: 'Нет открытых вкладок',
    tabCollapsed: 'Вкладки свернуты',
    tabExpanded: 'Вкладки развернуты',
    collapse: 'Свернуть',
    expand: 'Развернуть'
  },

  // Настройки
  settings: {
    title: 'Настройки',
    language: 'Язык',
    theme: 'Тема',
    appearance: 'Внешний вид',
    notifications: 'Уведомления',
    security: 'Безопасность',
    advanced: 'Дополнительно',
    save: 'Сохранить настройки',
    reset: 'Сбросить настройки',
    languageOptions: {
      ru: 'Русский',
      en: 'English'
    },
    themeOptions: {
      light: 'Светлая',
      dark: 'Темная',
      auto: 'Автоматически'
    }
  },

  // Уведомления
  notifications: {
    toolExecuted: 'Инструмент выполнен',
    toolFailed: 'Инструмент не выполнен',
    toolAddedToFavorites: 'Инструмент добавлен в избранное',
    toolRemovedFromFavorites: 'Инструмент удален из избранного',
    settingsSaved: 'Настройки сохранены',
    settingsReset: 'Настройки сброшены',
    languageChanged: 'Язык изменен',
    themeChanged: 'Тема изменена',
    sessionExpired: 'Сессия истекла',
    networkError: 'Ошибка сети',
    serverError: 'Ошибка сервера',
    unauthorized: 'Не авторизован',
    forbidden: 'Доступ запрещен',
    notFound: 'Не найдено',
    internalError: 'Внутренняя ошибка'
  },

  // Формы и валидация
  forms: {
    required: 'Обязательное поле',
    invalidEmail: 'Неверный email',
    invalidUrl: 'Неверный URL',
    invalidNumber: 'Неверное число',
    minLength: 'Минимальная длина',
    maxLength: 'Максимальная длина',
    pattern: 'Неверный формат',
    fileRequired: 'Файл обязателен',
    fileSize: 'Размер файла',
    fileType: 'Тип файла',
    upload: 'Загрузить',
    download: 'Скачать',
    preview: 'Предварительный просмотр',
    remove: 'Удалить',
    selectFile: 'Выбрать файл',
    selectFiles: 'Выбрать файлы',
    selectFolder: 'Выбрать папку',
    dragAndDrop: 'Перетащите файлы сюда',
    or: 'или',
    clickToSelect: 'нажмите для выбора'
  },

  // Ошибки
  errors: {
    general: 'Произошла ошибка',
    network: 'Ошибка сети',
    server: 'Ошибка сервера',
    authentication: 'Ошибка аутентификации',
    authorization: 'Ошибка авторизации',
    validation: 'Ошибка валидации',
    notFound: 'Не найдено',
    forbidden: 'Доступ запрещен',
    timeout: 'Время ожидания истекло',
    unknown: 'Неизвестная ошибка',
    tryAgain: 'Попробуйте снова',
    contactSupport: 'Обратитесь в поддержку'
  }
};
