/**
 * Умная система категоризации инструментов
 * Группирует 55 инструментов по функциональности и использованию
 */

export interface ToolCategory {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  priority: number; // для сортировки
}

export interface CategorizedTools {
  category: ToolCategory;
  tools: any[];
  count: number;
}

// Основные категории инструментов
export const TOOL_CATEGORIES: ToolCategory[] = [
  {
    id: 'analysis',
    title: 'Анализ и Отчеты',
    description: 'Инструменты для анализа данных и генерации отчетов',
    icon: '📊',
    color: '#1890ff',
    priority: 1
  },
  {
    id: 'construction',
    title: 'Строительство',
    description: 'Специализированные инструменты для строительной отрасли',
    icon: '🏗️',
    color: '#52c41a',
    priority: 2
  },
  {
    id: 'ai',
    title: 'ИИ и ML',
    description: 'Искусственный интеллект и машинное обучение',
    icon: '🤖',
    color: '#722ed1',
    priority: 3
  },
  {
    id: 'data',
    title: 'Работа с Данными',
    description: 'Обработка, очистка и анализ данных',
    icon: '💾',
    color: '#fa8c16',
    priority: 4
  },
  {
    id: 'automation',
    title: 'Автоматизация',
    description: 'Инструменты для автоматизации процессов',
    icon: '⚡',
    color: '#eb2f96',
    priority: 5
  },
  {
    id: 'communication',
    title: 'Коммуникации',
    description: 'Инструменты для общения и презентаций',
    icon: '💬',
    color: '#13c2c2',
    priority: 6
  },
  {
    id: 'utilities',
    title: 'Утилиты',
    description: 'Вспомогательные инструменты и утилиты',
    icon: '🔧',
    color: '#8c8c8c',
    priority: 7
  }
];

// Правила категоризации на основе названий и описаний
export const CATEGORIZATION_RULES = {
  analysis: [
    'analyze', 'analysis', 'report', 'summary', 'statistics', 'metrics',
    'tender', 'financial', 'budget', 'estimate', 'calculation'
  ],
  construction: [
    'construction', 'building', 'sp', 'снип', 'гост', 'смета', 'estimate',
    'project', 'design', 'planning', 'structural', 'engineering'
  ],
  ai: [
    'ai', 'ml', 'neural', 'model', 'prediction', 'classification',
    'nlp', 'text', 'image', 'recognition', 'intelligent'
  ],
  data: [
    'data', 'extract', 'parse', 'process', 'transform', 'clean',
    'import', 'export', 'convert', 'format', 'database'
  ],
  automation: [
    'auto', 'automation', 'batch', 'schedule', 'workflow', 'pipeline',
    'trigger', 'event', 'monitor', 'alert'
  ],
  communication: [
    'email', 'message', 'notification', 'alert', 'chat', 'voice',
    'speech', 'presentation', 'meeting', 'collaboration'
  ]
};

// Функция для определения категории инструмента
export function categorizeTool(tool: any): string {
  const name = tool.name?.toLowerCase() || '';
  const description = tool.description?.toLowerCase() || '';
  const category = tool.category?.toLowerCase() || '';
  
  const text = `${name} ${description} ${category}`;
  
  // Проверяем правила категоризации
  for (const [categoryId, keywords] of Object.entries(CATEGORIZATION_RULES)) {
    if (keywords.some(keyword => text.includes(keyword))) {
      return categoryId;
    }
  }
  
  // Если не найдено, возвращаем утилиты
  return 'utilities';
}

// Функция для группировки инструментов по категориям
export function groupToolsByCategory(tools: any[]): CategorizedTools[] {
  const grouped: { [key: string]: any[] } = {};
  
  // Группируем инструменты
  tools.forEach(tool => {
    const categoryId = categorizeTool(tool);
    if (!grouped[categoryId]) {
      grouped[categoryId] = [];
    }
    grouped[categoryId].push(tool);
  });
  
  // Создаем результат с категориями
  return TOOL_CATEGORIES
    .map(category => ({
      category,
      tools: grouped[category.id] || [],
      count: grouped[category.id]?.length || 0
    }))
    .filter(group => group.count > 0)
    .sort((a, b) => a.category.priority - b.category.priority);
}

// Функция для получения популярных инструментов
export function getPopularTools(tools: any[]): any[] {
  // Сортируем по частоте использования (если есть данные)
  return tools
    .filter(tool => tool.available)
    .sort((a, b) => {
      // Приоритет: избранные, затем по алфавиту
      const aFav = a.isFavorite ? 1 : 0;
      const bFav = b.isFavorite ? 1 : 0;
      if (aFav !== bFav) return bFav - aFav;
      return a.name.localeCompare(b.name);
    })
    .slice(0, 8); // Топ-8 популярных
}

// Функция для получения недавно использованных инструментов
export function getRecentTools(tools: any[]): any[] {
  return tools
    .filter(tool => tool.lastUsed)
    .sort((a, b) => new Date(b.lastUsed).getTime() - new Date(a.lastUsed).getTime())
    .slice(0, 6); // Последние 6
}
