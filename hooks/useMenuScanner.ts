/**
 * 메뉴판 스캐너 훅 - 백엔드 직접 호출
 */
import { useState } from "react";
import * as ImagePicker from "expo-image-picker";
import { imageUriToBase64 } from "@/lib/receipt-ocr";

const DEFAULT_BACKEND =
  (process.env.EXPO_PUBLIC_API_URL as string) || "http://localhost:8000";

export type MenuItemResult = {
  name: string;
  price: number;
  currency: string;
  price_krw: number;
  average_price: number | null;
  percentage_diff: number;
  price_comparison: "저렴" | "평균" | "비쌈" | "정보없음";
  message: string;
  exchange_rate: number;
};

export type MenuAnalysisResult = {
  success: boolean;
  currency: string;
  items: MenuItemResult[];
  error?: string;
};

export function useMenuScanner() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MenuAnalysisResult | null>(null);

  const pickImage = async (): Promise<string | null> => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") return null;
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });
    return res.canceled ? null : res.assets[0].uri;
  };

  const takePhoto = async (): Promise<string | null> => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") return null;
    const res = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.8,
    });
    return res.canceled ? null : res.assets[0].uri;
  };

  const analyzeImage = async (
    imageUri: string,
    currency = "USD",
    backendUrl = DEFAULT_BACKEND
  ): Promise<MenuAnalysisResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const base64 = await imageUriToBase64(imageUri);
      const resp = await fetch(`${backendUrl}/api/menu/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: base64, currency }),
      });
      const data: MenuAnalysisResult = await resp.json();
      if (!resp.ok) throw new Error((data as any).detail || "메뉴 분석 실패");
      setResult(data);
      return data;
    } catch (err: any) {
      setError(String(err?.message ?? err));
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeText = async (
    text: string,
    currency = "USD",
    backendUrl = DEFAULT_BACKEND
  ): Promise<MenuAnalysisResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${backendUrl}/api/menu/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, currency }),
      });
      const data: MenuAnalysisResult = await resp.json();
      if (!resp.ok) throw new Error((data as any).detail || "메뉴 분석 실패");
      setResult(data);
      return data;
    } catch (err: any) {
      setError(String(err?.message ?? err));
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
