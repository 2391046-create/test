import { useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppSettings, Currency, COUNTRY_CONFIGS } from "@/types";

const DEFAULT_SETTINGS: AppSettings = {
  selectedCurrency: "USD",
  selectedCountry: "미국",
  backendUrl: "http://localhost:8000",
  autoSaveToXRPL: false,
};

export function useSettings() {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  // 설정 로드
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const stored = await AsyncStorage.getItem("appSettings");
      if (stored) {
        setSettings(JSON.parse(stored));
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
      await AsyncStorage.setItem("appSettings", JSON.stringify(updated));
    } catch (error) {
      console.error("설정 저장 실패:", error);
    }
  };

  const setCurrency = async (currency: Currency) => {
    const config = COUNTRY_CONFIGS[currency];
    await updateSettings({
      selectedCurrency: currency,
      selectedCountry: config.name,
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
    getExchangeRate,
    convertToKRW,
    convertFromKRW,
  };
}
