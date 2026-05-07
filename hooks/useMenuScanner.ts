import { useState } from "react";
import * as ImagePicker from "expo-image-picker";
import { MenuAnalysisResult, Currency } from "@/types";

export function useMenuScanner() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MenuAnalysisResult | null>(null);

  const pickImage = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== "granted") {
        setError("카메라 라이브러리 접근 권한이 필요합니다");
        return null;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 1,
      });

      if (!result.canceled) {
        return result.assets[0].uri;
      }
    } catch (err) {
      setError("이미지 선택 실패: " + String(err));
    }
    return null;
  };

  const takePhoto = async () => {
    try {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== "granted") {
        setError("카메라 접근 권한이 필요합니다");
        return null;
      }

      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 1,
      });

      if (!result.canceled) {
        return result.assets[0].uri;
      }
    } catch (err) {
      setError("카메라 실행 실패: " + String(err));
    }
    return null;
  };

  const analyzeMenu = async (
    imageUri: string,
    currency: Currency,
    backendUrl: string
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(imageUri);
      const blob = await response.blob();
      const reader = new FileReader();

      return new Promise<MenuAnalysisResult>((resolve, reject) => {
        reader.onload = async () => {
          try {
            const base64 = (reader.result as string).split(",")[1];

            const apiResponse = await fetch(`${backendUrl}/analyze-price`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                image_base64: base64,
                target_country: currency,
              }),
            });

            if (!apiResponse.ok) {
              throw new Error("메뉴판 분석 실패");
            }

            const data = await apiResponse.json();
            const analysisResult = data.data as MenuAnalysisResult;

            setResult(analysisResult);
            setIsLoading(false);
            resolve(analysisResult);
          } catch (err) {
            const errorMsg = "분석 오류: " + String(err);
            setError(errorMsg);
            setIsLoading(false);
            reject(err);
          }
        };

        reader.onerror = () => {
          setError("이미지 읽기 실패");
          setIsLoading(false);
          reject(new Error("이미지 읽기 실패"));
        };

        reader.readAsDataURL(blob);
      });
    } catch (err) {
      const errorMsg = "분석 실패: " + String(err);
      setError(errorMsg);
      setIsLoading(false);
      throw err;
    }
  };

  const analyzeMenuText = async (
    text: string,
    currency: Currency,
    backendUrl: string
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const apiResponse = await fetch(`${backendUrl}/analyze-price`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
          target_country: currency,
        }),
      });

      if (!apiResponse.ok) {
        throw new Error("메뉴판 분석 실패");
      }

      const data = await apiResponse.json();
      const analysisResult = data.data as MenuAnalysisResult;

      setResult(analysisResult);
      setIsLoading(false);
      return analysisResult;
    } catch (err) {
      const errorMsg = "분석 실패: " + String(err);
      setError(errorMsg);
      setIsLoading(false);
      throw err;
    }
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return {
    isLoading,
    error,
    result,
    pickImage,
    takePhoto,
    analyzeMenu,
    analyzeMenuText,
    clearResult,
  };
}
