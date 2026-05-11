/**
 * 영수증 스캐너 훅 - 백엔드 API 연동
 */
import { useState } from "react";
import * as ImagePicker from "expo-image-picker";
import { analyzeReceiptImage, ReceiptData, imageUriToBase64 } from "@/lib/receipt-ocr";
import { analyzeReceipt } from "@/lib/api";

export function useReceiptScanner(userId: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReceiptData | null>(null);

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      setError("갤러리 접근 권한이 필요합니다");
      return null;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });
    return res.canceled ? null : res.assets[0].uri;
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      setError("카메라 접근 권한이 필요합니다");
      return null;
    }
    const res = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.8,
    });
    return res.canceled ? null : res.assets[0].uri;
  };

  const analyze = async (imageUri: string, currency = "USD") => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await analyzeReceiptImage(imageUri, userId, currency);
      setResult(data);
      return data;
    } catch (err) {
      const msg = String(err);
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clear = () => {
    setResult(null);
    setError(null);
  };

  return { isLoading, error, result, pickImage, takePhoto, analyze, clear };
}
