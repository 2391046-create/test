/**
 * 메뉴판 스캐너 훅 - 백엔드 API 연동
 */
import { useState } from "react";
import * as ImagePicker from "expo-image-picker";
import { analyzeMenu } from "@/lib/api";
import { imageUriToBase64 } from "@/lib/receipt-ocr";

export type MenuAnalysisResult = {
  success: boolean;
  currency: string;
  items: Array<{
    name: string;
    price: number;
    currency: string;
    price_krw: number;
    average_price: number | null;
    percentage_diff: number;
    price_comparison: "저렴" | "평균" | "비쌈" | "정보없음";
    message: string;
    exchange_rate: number;
  }>;
};

export function useMenuScanner() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MenuAnalysisResult | null>(null);

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") return null;
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });
    return res.canceled ? null : res.assets[0].uri;
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") return null;
    const res = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.8,
    });
    return res.canceled ? null : res.assets[0].uri;
  };

  const analyzeImage = async (imageUri: string, currency = "USD") => {
    setIsLoading(true);
    setError(null);
    try {
      const base64 = await imageUriToBase64(imageUri);
      const data = await analyzeMenu(base64, null, currency) as MenuAnalysisResult;
      setResult(data);
      return data;
    } catch (err) {
      setError(String(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeText = async (text: string, currency = "USD") => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analyzeMenu(null, text, currency) as MenuAnalysisResult;
      setResult(data);
      return data;
    } catch (err) {
      setError(String(err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clear = () => {
    setResult(null);
    setError(null);
  };

  return { isLoading, error, result, pickImage, takePhoto, analyzeImage, analyzeText, clear };
}
