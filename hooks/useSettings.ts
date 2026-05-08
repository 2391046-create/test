import { useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppSettings, Currency, COUNTRY_CONFIGS, Language } from "@/types";

const DEFAULT_SETTINGS: AppSettings = {
  language: "ko",
  selectedCurrency: "USD",
  selectedCountry: "미국",
  backendUrl: "http://localhost:8000",
  autoSaveToXRPL: false,
};

const SETTINGS_STORAGE_KEY = "appSettings";
const settingsListeners = new Set<(settings: AppSettings) => void>();

function notifySettingsListeners(settings: AppSettings) {
  settingsListeners.forEach((listener) => listener(settings));
}

export function useSettings() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  // 설정 로드
  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    const listener = (nextSettings: AppSettings) => {
      setSettings(nextSettings);
    };
    settingsListeners.add(listener);
    return () => {
      settingsListeners.delete(listener);
    };
  }, []);

  const loadSettings = async () => {
    try {
      const stored = await AsyncStorage.getItem(SETTINGS_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<AppSettings>;
        const merged: AppSettings = { ...DEFAULT_SETTINGS, ...parsed };
        setSettings(merged);
        notifySettingsListeners(merged);
      }
      setIsLoading(false);
    } catch (error) {
      console.error("설정 로드 실패:", error);
      setIsLoading(false);
    }
  };

  const updateSettings = async (newSettings: Partial<AppSettings>) => {
    try {
      const updated = { ...settings, ...newSettings };
      setSettings(updated);
      notifySettingsListeners(updated);
      await AsyncStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error("설정 저장 실패:", error);
    }
  };

  const setCurrency = async (currency: Currency) => {
    const config = COUNTRY_CONFIGS[currency];
    const countryNameMap: Record<Language, string> = {
      ko: config.name,
      en: config.code,
    };
    await updateSettings({
      selectedCurrency: currency,
      selectedCountry: countryNameMap[settings.language],
    });
  };

  const setLanguage = async (language: Language) => {
    const currentCurrencyConfig = COUNTRY_CONFIGS[settings.selectedCurrency];
    await updateSettings({
      language,
      selectedCountry: language === "ko" ? currentCurrencyConfig.name : currentCurrencyConfig.code,
    });
  };

  const getExchangeRate = () => {
    const config = COUNTRY_CONFIGS[settings.selectedCurrency];
    return config?.exchangeRate || 1300;
  };

  const convertToKRW = (amount: number) => {
    return amount * getExchangeRate();
  };

  const convertFromKRW = (amount: number) => {
    return amount / getExchangeRate();
  };

  return {
    settings,
    isLoading,
    updateSettings,
    setCurrency,
    setLanguage,
    getExchangeRate,
    convertToKRW,
    convertFromKRW,
  };
}
