/**
 * 영수증 스캐너 훅
 * receipt-scanner 탭과 records 탭 모두에서 사용
 */
import { useState } from "react";
import * as ImagePicker from "expo-image-picker";
import { ReceiptAnalysisResult } from "@/types";

const DEFAULT_BACKEND = "http://localhost:8000";

async function imageUriToBase64(imageUri: string): Promise<string> {
  const response = await fetch(imageUri);
  const blob = await response.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const r = reader.result as string;
      resolve(r.includes(",") ? r.split(",")[1] : r);
    };
    reader.onerror = () => reject(new Error("이미지 변환 실패"));
    reader.readAsDataURL(blob);
  });
}

export function useReceiptScanner() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReceiptAnalysisResult | null>(null);

  const pickImage = async (): Promise<string | null> => {
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

  const takePhoto = async (): Promise<string | null> => {
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

  /**
   * 영수증 이미지 분석 → ReceiptAnalysisResult 형태로 반환
   * records 탭 호환: processReceiptImage 역할도 겸함
   */
  const analyzeReceipt = async (
    imageUri: string,
    currency = "USD",
    backendUrl = DEFAULT_BACKEND
  ): Promise<ReceiptAnalysisResult> => {
    setIsLoading(true);
    setError(null);
    try {
      const base64 = await imageUriToBase64(imageUri);

      const resp = await fetch(`${backendUrl}/api/transactions/analyze-receipt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: base64,
          currency,
          user_id: "default",
        }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: "분석 실패" }));
        throw new Error(err.detail || "영수증 분석 실패");
      }

      const data = await resp.json();
      const tx = data.transaction;

      // ReceiptAnalysisResult 형태로 변환
      const analysisResult: ReceiptAnalysisResult = {
        merchant_name: tx.merchant_name ?? "Unknown",
        items: tx.items ?? [],
        subtotal_local: tx.amount_local ?? 0,
        tax_local: 0,
        total_local: tx.amount_local ?? 0,
        currency: tx.currency ?? currency,
        total_krw: tx.amount_krw ?? 0,
        exchange_rate: tx.exchange_rate ?? 0,
        dutch_pay: {
          num_people: 1,
          per_person_krw: tx.amount_krw ?? 0,
          per_person_local: tx.amount_local ?? 0,
        },
        date: tx.transaction_date?.split("T")[0],
      };

      setResult(analysisResult);
      return analysisResult;
    } catch (err: any) {
      const msg = err?.message ?? String(err);
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return { isLoading, error, result, pickImage, takePhoto, analyzeReceipt, clearResult };
}
