import { ScrollView, Text, View, TouchableOpacity, ActivityIndicator, Alert } from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { useReceiptScanner } from "@/hooks/useReceiptScanner";
import { useSettings } from "@/hooks/useSettings";
import { useState } from "react";
import { ReceiptAnalysisResult } from "@/types";

export default function ReceiptScannerScreen() {
  const { isLoading, error, result, pickImage, takePhoto, analyzeReceipt, clearResult } = useReceiptScanner();
  const { settings } = useSettings();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const handlePickImage = async () => {
    const imageUri = await pickImage();
    if (imageUri) {
      setSelectedImage(imageUri);
      try {
        await analyzeReceipt(imageUri, settings.selectedCurrency, settings.backendUrl);
      } catch (err) {
        Alert.alert("오류", "영수증 분석 실패");
      }
    }
  };

  const handleTakePhoto = async () => {
    const imageUri = await takePhoto();
    if (imageUri) {
      setSelectedImage(imageUri);
      try {
        await analyzeReceipt(imageUri, settings.selectedCurrency, settings.backendUrl);
      } catch (err) {
        Alert.alert("오류", "영수증 분석 실패");
      }
    }
  };

  const handleClear = () => {
    clearResult();
    setSelectedImage(null);
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} className="gap-6">
        {/* 헤더 */}
        <View className="gap-2">
          <Text className="text-3xl font-bold text-foreground">영수증 스캔</Text>
          <Text className="text-sm text-muted">다국 영수증을 촬영하여 자동 분석</Text>
        </View>

        {/* 현재 통화 설정 */}
        <View className="p-4 bg-surface rounded-lg border border-border">
          <Text className="text-sm text-muted">현재 통화 설정</Text>
          <Text className="text-2xl font-bold text-foreground mt-1">
            {settings.selectedCountry} ({settings.selectedCurrency})
          </Text>
          <Text className="text-xs text-muted mt-1">
            환율: 1 {settings.selectedCurrency} = ₩{Math.round(1300 / (settings.selectedCurrency === "USD" ? 1 : 1)).toLocaleString()}
          </Text>
        </View>

        {/* 스캔 버튼 */}
        {!result && (
          <View className="gap-3">
            <TouchableOpacity
              onPress={handleTakePhoto}
              disabled={isLoading}
              className="p-4 bg-primary rounded-lg"
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-center font-semibold text-background">📷 카메라로 촬영</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handlePickImage}
              disabled={isLoading}
              className="p-4 bg-surface border border-border rounded-lg"
            >
              <Text className="text-center font-semibold text-foreground">🖼️ 갤러리에서 선택</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* 에러 메시지 */}
        {error && (
          <View className="p-4 bg-error rounded-lg">
            <Text className="text-sm text-background">{error}</Text>
          </View>
        )}

        {/* 분석 결과 */}
        {result && (
          <View className="gap-4">
            {/* 상호명 */}
            <View className="p-4 bg-surface rounded-lg border border-border">
              <Text className="text-sm text-muted">상호명</Text>
              <Text className="text-xl font-bold text-foreground mt-1">{result.merchant_name}</Text>
            </View>

            {/* 금액 정보 */}
            <View className="gap-3">
              <Text className="text-lg font-semibold text-foreground">결제 금액</Text>

              <View className="flex-row gap-3">
                <View className="flex-1 p-4 bg-surface rounded-lg border border-border">
                  <Text className="text-xs text-muted">현지 통화</Text>
                  <Text className="text-2xl font-bold text-foreground mt-1">
                    {result.total_local.toFixed(2)} {result.currency}
                  </Text>
                </View>

                <View className="flex-1 p-4 bg-primary rounded-lg">
                  <Text className="text-xs text-background">원화</Text>
                  <Text className="text-2xl font-bold text-background mt-1">
                    ₩{result.total_krw.toLocaleString()}
                  </Text>
                </View>
              </View>

              <View className="p-3 bg-surface rounded-lg">
                <Text className="text-xs text-muted">환율</Text>
                <Text className="text-sm text-foreground mt-1">
                  1 {result.currency} = ₩{result.exchange_rate.toLocaleString()}
                </Text>
              </View>
            </View>

            {/* 품목 목록 */}
            {result.items && result.items.length > 0 && (
              <View className="gap-2">
                <Text className="text-lg font-semibold text-foreground">구매 항목</Text>
                {result.items.map((item, index) => (
                  <View key={index} className="p-3 bg-surface rounded-lg border border-border">
                    <View className="flex-row justify-between items-center">
                      <Text className="font-medium text-foreground">{item.name}</Text>
                      <Text className="text-sm text-muted">
                        {item.quantity}개 × {item.price.toFixed(2)}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* 더치페이 정산 */}
            <View className="p-4 bg-success rounded-lg">
              <Text className="text-sm text-background font-semibold">더치페이 정산</Text>
              <View className="mt-3 gap-2">
                <View className="flex-row justify-between">
                  <Text className="text-background">인원수</Text>
                  <Text className="font-bold text-background">{result.dutch_pay.num_people}명</Text>
                </View>
                <View className="flex-row justify-between">
                  <Text className="text-background">1인당 (원화)</Text>
                  <Text className="font-bold text-background">
                    ₩{result.dutch_pay.per_person_krw.toLocaleString()}
                  </Text>
                </View>
                <View className="flex-row justify-between">
                  <Text className="text-background">1인당 ({result.currency})</Text>
                  <Text className="font-bold text-background">
                    {result.dutch_pay.per_person_local.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>

            {/* 액션 버튼 */}
            <View className="gap-2">
              <TouchableOpacity className="p-4 bg-primary rounded-lg">
                <Text className="text-center font-semibold text-background">💾 저장하기</Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={handleClear}
                className="p-4 bg-surface border border-border rounded-lg"
              >
                <Text className="text-center font-semibold text-foreground">다시 스캔</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}
