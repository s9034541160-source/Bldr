import React from 'react';
import { Select, Space } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';
import { useLocalization } from '../contexts/LocalizationContext';

const { Option } = Select;

interface LanguageSwitcherProps {
  size?: 'small' | 'middle' | 'large';
  style?: React.CSSProperties;
  className?: string;
}

const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({ 
  size = 'middle', 
  style,
  className 
}) => {
  const { language, setLanguage, t } = useLocalization();

  const handleLanguageChange = (value: string) => {
    setLanguage(value as 'ru' | 'en');
  };

  return (
    <Space>
      <GlobalOutlined />
      <Select
        value={language}
        onChange={handleLanguageChange}
        size={size}
        style={style}
        className={className}
        dropdownStyle={{
          background: 'var(--ant-color-bg-container)',
          border: '1px solid var(--ant-color-border)',
        }}
      >
        <Option value="ru">
          <Space>
            <span>🇷🇺</span>
            <span>{t('settings.languageOptions.ru')}</span>
          </Space>
        </Option>
        <Option value="en">
          <Space>
            <span>🇺🇸</span>
            <span>{t('settings.languageOptions.en')}</span>
          </Space>
        </Option>
      </Select>
    </Space>
  );
};

export default LanguageSwitcher;
