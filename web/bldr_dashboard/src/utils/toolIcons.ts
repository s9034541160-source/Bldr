/**
 * Система иконок для инструментов
 * Определяет подходящие иконки для каждого инструмента
 */

import { 
  BarChartOutlined,
  CalculatorOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  SearchOutlined,
  ToolOutlined,
  SettingOutlined,
  EyeOutlined,
  AudioOutlined,
  MessageOutlined,
  BuildOutlined,
  ExperimentOutlined,
  RocketOutlined,
  StarOutlined,
  HeartOutlined,
  CrownOutlined,
  FireOutlined,
  BulbOutlined,
  GiftOutlined,
  TrophyOutlined,
  SunOutlined,
  CloudOutlined,
  StarOutlined
} from '@ant-design/icons';

// Правила определения иконок для инструментов
export const TOOL_ICON_RULES = {
  // Анализ и отчеты
  'analyze': BarChartOutlined,
  'analysis': BarChartOutlined,
  'report': FileTextOutlined,
  'summary': FileTextOutlined,
  'statistics': BarChartOutlined,
  'metrics': BarChartOutlined,
  'tender': FileTextOutlined,
  'financial': CalculatorOutlined,
  'budget': CalculatorOutlined,
  'estimate': CalculatorOutlined,
  'calculation': CalculatorOutlined,
  
  // Строительство
  'construction': BuildOutlined,
  'building': BuildOutlined,
  'sp': BuildOutlined,
  'снип': BuildOutlined,
  'гост': BuildOutlined,
  'смета': CalculatorOutlined,
  'project': BuildOutlined,
  'design': EyeOutlined,
  'planning': SettingOutlined,
  'structural': BuildOutlined,
  'engineering': BuildOutlined,
  
  // ИИ и ML
  'ai': RobotOutlined,
  'ml': RobotOutlined,
  'neural': RobotOutlined,
  'model': RobotOutlined,
  'prediction': StarOutlined,
  'classification': RobotOutlined,
  'nlp': MessageOutlined,
  'text': FileTextOutlined,
  'image': EyeOutlined,
  'recognition': EyeOutlined,
  'intelligent': BulbOutlined,
  
  // Работа с данными
  'data': DatabaseOutlined,
  'extract': ThunderboltOutlined,
  'parse': FileTextOutlined,
  'process': SettingOutlined,
  'transform': ThunderboltOutlined,
  'clean': StarOutlined,
  'import': ThunderboltOutlined,
  'export': ThunderboltOutlined,
  'convert': ThunderboltOutlined,
  'format': FileTextOutlined,
  'database': DatabaseOutlined,
  
  // Автоматизация
  'auto': ThunderboltOutlined,
  'automation': ThunderboltOutlined,
  'batch': SettingOutlined,
  'schedule': SettingOutlined,
  'workflow': ThunderboltOutlined,
  'pipeline': ThunderboltOutlined,
  'trigger': ThunderboltOutlined,
  'event': ThunderboltOutlined,
  'monitor': EyeOutlined,
  'alert': ThunderboltOutlined,
  
  // Коммуникации
  'email': MessageOutlined,
  'message': MessageOutlined,
  'notification': ThunderboltOutlined,
  'chat': MessageOutlined,
  'voice': AudioOutlined,
  'speech': AudioOutlined,
  'presentation': EyeOutlined,
  'meeting': MessageOutlined,
  'collaboration': MessageOutlined,
  
  // Поиск
  'search': SearchOutlined,
  'find': SearchOutlined,
  'lookup': SearchOutlined,
  'query': SearchOutlined,
  
  // Эксперименты
  'experiment': ExperimentOutlined,
  'test': ExperimentOutlined,
  'trial': ExperimentOutlined,
  'research': BulbOutlined,
  
  // Утилиты
  'utility': ToolOutlined,
  'helper': ToolOutlined,
  'assistant': RobotOutlined,
  'support': HeartOutlined
};

// Функция для определения иконки инструмента
export function getToolIcon(tool: any): React.ComponentType<any> {
  const name = tool.name?.toLowerCase() || '';
  const description = tool.description?.toLowerCase() || '';
  const category = tool.category?.toLowerCase() || '';
  
  const text = `${name} ${description} ${category}`;
  
  // Проверяем правила определения иконок
  for (const [keyword, icon] of Object.entries(TOOL_ICON_RULES)) {
    if (text.includes(keyword)) {
      return icon;
    }
  }
  
  // Если не найдено, возвращаем иконку по умолчанию
  return ToolOutlined;
}

// Функция для получения цвета иконки
export function getToolIconColor(tool: any): string {
  const category = tool.category?.toLowerCase() || '';
  
  const categoryColors: { [key: string]: string } = {
    'analysis': '#1890ff',
    'construction': '#52c41a',
    'ai': '#722ed1',
    'data': '#fa8c16',
    'automation': '#eb2f96',
    'communication': '#13c2c2',
    'search': '#faad14',
    'experiment': '#f759ab',
    'utility': '#8c8c8c'
  };
  
  return categoryColors[category] || '#8c8c8c';
}
