import React, { createContext, useContext, useState, ReactNode } from 'react';
import { apiService } from '../services/api';

interface ToolInfo {
  name: string;
  category: string;
  description: string;
  ui_placement: 'dashboard' | 'tools' | 'service';
  available: boolean;
  source: string;
}

interface ToolTab {
  tool: ToolInfo;
  toolInfo: ToolInfo;
  params: Record<string, any>;
  id?: number;
}

interface ToolTabsContextType {
  toolTabs: ToolTab[];
  setToolTabs: React.Dispatch<React.SetStateAction<ToolTab[]>>;
  tabsDrawerVisible: boolean;
  setTabsDrawerVisible: React.Dispatch<React.SetStateAction<boolean>>;
  openToolInNewTab: (tool: ToolInfo) => Promise<void>;
}

const ToolTabsContext = createContext<ToolTabsContextType | undefined>(undefined);

export const ToolTabsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toolTabs, setToolTabs] = useState<ToolTab[]>([]);
  const [tabsDrawerVisible, setTabsDrawerVisible] = useState(false);

  const openToolInNewTab = async (tool: ToolInfo) => {
    // Загружаем полную информацию об инструменте
    let fullToolInfo = tool;
    try {
      console.log('Loading full tool info for:', tool.name);
      const info = await apiService.getToolInfo(tool.name);
      if (info.status === 'success' && info.data) {
        const toolData = info.data.data || info.data;
        fullToolInfo = {
          ...tool,
          parameters: Object.entries(toolData.parameters || {}).map(([key, param]: [string, any]) => ({
            name: key,
            type: param.type,
            required: param.required,
            default: param.default,
            description: param.description,
            ui: param.ui,
            enum: param.enum
          }))
        };
        console.log('Loaded full tool info:', fullToolInfo);
      }
    } catch (error) {
      console.error('Failed to load tool info:', error);
    }
    
    const newTab = {
      tool: tool,
      toolInfo: fullToolInfo, // Используем полную информацию об инструменте
      params: {}
    };
    
    setToolTabs(prev => [...prev, newTab]);
    setTabsDrawerVisible(true);
  };

  return (
    <ToolTabsContext.Provider value={{
      toolTabs,
      setToolTabs,
      tabsDrawerVisible,
      setTabsDrawerVisible,
      openToolInNewTab
    }}>
      {children}
    </ToolTabsContext.Provider>
  );
};

export const useToolTabs = () => {
  const context = useContext(ToolTabsContext);
  if (context === undefined) {
    throw new Error('useToolTabs must be used within a ToolTabsProvider');
  }
  return context;
};
