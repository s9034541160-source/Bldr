import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ru } from '../locales/ru';
import { en } from '../locales/en';

export type Language = 'ru' | 'en';

export interface LocalizationContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string) => string;
  isRTL: boolean;
}

const LocalizationContext = createContext<LocalizationContextType | undefined>(undefined);

// Функция для получения значения по ключу с поддержкой вложенных объектов
const getNestedValue = (obj: any, key: string): string => {
  const keys = key.split('.');
  let value = obj;
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return key; // Возвращаем ключ, если значение не найдено
    }
  }
  
  return typeof value === 'string' ? value : key;
};

export const LocalizationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    // Получаем язык из localStorage или используем русский по умолчанию
    const savedLanguage = localStorage.getItem('bldr-language') as Language;
    return savedLanguage || 'ru';
  });

  const setLanguage = (newLanguage: Language) => {
    setLanguageState(newLanguage);
    localStorage.setItem('bldr-language', newLanguage);
  };

  const t = (key: string): string => {
    const translations = language === 'ru' ? ru : en;
    return getNestedValue(translations, key);
  };

  const isRTL = false; // Русский и английский - LTR языки

  const value: LocalizationContextType = {
    language,
    setLanguage,
    t,
    isRTL
  };

  return (
    <LocalizationContext.Provider value={value}>
      {children}
    </LocalizationContext.Provider>
  );
};

export const useLocalization = (): LocalizationContextType => {
  const context = useContext(LocalizationContext);
  if (context === undefined) {
    throw new Error('useLocalization must be used within a LocalizationProvider');
  }
  return context;
};

// Хук для получения перевода
export const useTranslation = () => {
  const { t } = useLocalization();
  return t;
};
