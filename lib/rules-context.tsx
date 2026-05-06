import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CategorizationRule, defaultRules } from './finance';

type RulesContextType = {
  rules: CategorizationRule[];
  addRule: (rule: CategorizationRule) => Promise<void>;
  updateRule: (id: string, updates: Partial<CategorizationRule>) => Promise<void>;
  deleteRule: (id: string) => Promise<void>;
  toggleRule: (id: string, enabled: boolean) => Promise<void>;
  reorderRules: (rules: CategorizationRule[]) => Promise<void>;
  resetToDefaults: () => Promise<void>;
  loading: boolean;
};

const RulesContext = createContext<RulesContextType | undefined>(undefined);

export function RulesProvider({ children }: { children: ReactNode }) {
  const [rules, setRules] = useState<CategorizationRule[]>([]);
  const [loading, setLoading] = useState(true);

  // 초기 로드 및 저장소 동기화
  useEffect(() => {
    loadRules();
  }, []);

  async function loadRules() {
    try {
      const stored = await AsyncStorage.getItem('categorization_rules');
      if (stored) {
        setRules(JSON.parse(stored));
      } else {
        // 첫 실행: 기본 규칙 설정
        await AsyncStorage.setItem('categorization_rules', JSON.stringify(defaultRules));
        setRules(defaultRules);
      }
    } catch (error) {
      console.error('Failed to load rules:', error);
      setRules(defaultRules);
    } finally {
      setLoading(false);
    }
  }

  async function saveRules(newRules: CategorizationRule[]) {
    try {
      await AsyncStorage.setItem('categorization_rules', JSON.stringify(newRules));
      setRules(newRules);
    } catch (error) {
      console.error('Failed to save rules:', error);
    }
  }

  async function addRule(rule: CategorizationRule) {
    const updated = [...rules, rule];
    await saveRules(updated);
  }

  async function updateRule(id: string, updates: Partial<CategorizationRule>) {
    const updated = rules.map((rule) => (rule.id === id ? { ...rule, ...updates } : rule));
    await saveRules(updated);
  }

  async function deleteRule(id: string) {
    const updated = rules.filter((rule) => rule.id !== id);
    await saveRules(updated);
  }

  async function toggleRule(id: string, enabled: boolean) {
    await updateRule(id, { enabled });
  }

  async function reorderRules(newRules: CategorizationRule[]) {
    await saveRules(newRules);
  }

  async function resetToDefaults() {
    await saveRules(defaultRules);
  }

  return (
    <RulesContext.Provider value={{ rules, addRule, updateRule, deleteRule, toggleRule, reorderRules, resetToDefaults, loading }}>
      {children}
    </RulesContext.Provider>
  );
}

export function useRules() {
  const context = useContext(RulesContext);
  if (!context) {
    throw new Error('useRules must be used within RulesProvider');
  }
  return context;
}
