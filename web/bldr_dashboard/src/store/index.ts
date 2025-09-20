import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiService, Project } from '../services/api';

export interface User {
  token: string;
  role: string;
  username: string;
}

export interface Settings {
  k: number;
  temp: number;
  chunkSize: number;
  threshold: number;
  model: string;
  retry: number;
  timeout: number;
  useGPU: boolean;
  host: string;
  port: number;
  lang: string;
}

interface ChatMessage {
  type: 'user' | 'ai' | 'system' | 'error';
  content: string;
  fileId?: string;
  timestamp: number;
}

interface StoreState {
  user: User | null;
  theme: 'light' | 'dark';
  settings: Settings;
  projects: Project[];
  chatHistory: ChatMessage[]; // Add chat history to store
  
  // Actions
  setUser: (user: User | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setSettings: (settings: Partial<Settings>) => void;
  setProjects: (projects: Project[]) => void;
  setChatHistory: (history: ChatMessage[]) => void; // Add action for chat history
  addChatMessage: (message: Omit<ChatMessage, 'timestamp'>) => void; // Update action to add messages
  clearChatHistory: () => void; // Add action to clear history
  fetchProjects: () => Promise<void>;
  clearUser: () => void;
}

const defaultSettings: Settings = {
  k: 5,
  temp: 0.7,
  chunkSize: 1000,
  threshold: 0.8,
  model: 'sbert_ru',
  retry: 3,
  timeout: 1800,
  useGPU: false,
  host: 'localhost:8000',
  port: 8000,
  lang: 'ru'
};

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      user: null,
      theme: 'light',
      settings: defaultSettings,
      projects: [],
      chatHistory: [], // Initialize chat history
      
      setUser: (user) => set({ user }),
      setTheme: (theme) => set({ theme }),
      setSettings: (newSettings) => set((state) => ({ 
        settings: { ...state.settings, ...newSettings } 
      })),
      setProjects: (projects) => set({ projects }),
      setChatHistory: (history) => set({ chatHistory: history }), // Set chat history
      addChatMessage: (message) => set((state) => ({ 
        chatHistory: [...state.chatHistory, { ...message, timestamp: Date.now() }] 
      })), // Add message to history with timestamp
      clearChatHistory: () => set({ chatHistory: [] }), // Clear chat history
      fetchProjects: async () => {
        try {
          const projects = await apiService.getProjects();
          set({ projects });
        } catch (error) {
          console.error('Failed to fetch projects:', error);
        }
      },
      clearUser: () => {
        // Clear user from state
        set({ user: null });
        // Also remove from localStorage directly to ensure it's cleared
        if (typeof window !== 'undefined') {
          localStorage.removeItem('bldr-empire-storage');
        }
      },
    }),
    {
      name: 'bldr-empire-storage',
      partialize: (state) => ({ 
        theme: state.theme, 
        settings: state.settings,
        user: state.user,
        chatHistory: state.chatHistory // Persist chat history
      }),
    }
  )
);