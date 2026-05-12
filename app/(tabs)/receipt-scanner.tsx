import { ScrollView, Text, View, TouchableOpacity, ActivityIndicator, Alert } from "react-native";
import { ScreenContainer } from "@/components/screen-container";
import { useReceiptScanner } from "@/hooks/useReceiptScanner";
import { useSettings } from "@/hooks/useSettings";
import { useTransactionStorage } from "@/hooks/useTransactionStorage";
import { useXRPL } from "@/hooks/useXRPL";
import { useState } from "react";
import { useFinance } from "@/lib/finance-context";

export default function ReceiptScannerScreen() {
  // ✅ 인자 없이 호출 (userId 불필요 - 훅 내부에서 "default" 사용)
  const { isLoading, error, result, pickImage, takePhoto, analyzeReceipt, clearResult } = useReceiptScanner();
  const { settings } = useSettings();
  const isEn = settings.language === "en";
  const { saveTransaction, updateTransactionXRPL } = useTransactionStorage();
  // ✅ 인자 없이 호출
  const { recordTransaction, isLoading: isXRPLLoading } = useXRPL();
  const { addNotification } = useFinance();
  const [isSaving, setIsSaving] = useState(false);
  const [savedTxId, setSavedTxId] = useState<string | null>(null);

  const handlePickImage = async () => {
    const imageUri = await pickImage();
    if (imageUri) {
      try {
        await analyzeReceipt(imageUri, settings.selectedCurrency, settings.backendUrl);
      } catch {
        Alert.alert(isEn ? "Error" : "오류", isEn ? "Failed to analyze receipt" : "영수증 분석 실패");
      }
    }
  };

  const handleTakePhoto = async () => {
    const imageUri = await takePhoto();
    if (imageUri) {
      try {
        await analyzeReceipt(imageUri, settings.selectedCurrency, settings.backendUrl);
      } catch {
        Alert.alert(isEn ? "Error" : "오류", isEn ? "Failed to analyze receipt" : "영수증 분석 실패");
      }
    }
  };

  const handleSave = async () => {
    if (!result) return;
    setIsSaving(true);
    try {
      await addNotification(`${result.merchant_name} ${result.total_local} ${result.currency}`);
      const tx = await saveTransaction("receipt", result);
      setSavedTxId(tx.id);
      Alert.alert(
        isEn ? "Success" : "성공",
        isEn ? "Receipt saved to records" : "영수증이 거래 기록에 저장되었습니다"
      );
    } catch {
      Alert.alert(isEn ? "Error" : "오류", isEn ? "Save failed" : "저장 실패");
    } finally {
      setIsSaving(false);
    }
  };

  const handleRecordXRPL = async () => {
    if (!savedTxId || !settings.xrplWalletSeed || !result) return;
    try {
      // ✅ recordTransaction(expenseObj, seed, backendUrl) 시그니처
      const xrplResult = await recordTransaction(
        {
          merchant: result.merchant_name,
          amount: result.total_krw,
          currency: result.currency,
          category: "receipt",
          description: result.items?.map((i) => i.name).join(", "),
          timestamp: new Date().toISOString(),
        },
        settings.xrplWalletSeed,
        settings.backendUrl
      );

      if (xrplResult.success && xrplResult.tx_hash) {
        await updateTransactionXRPL(savedTxId, xrplResult.tx_hash);
        Alert.alert(
          isEn ? "Success" : "성공",
          isEn
            ? `Recorded to XRPL\nTx: ${xrplResult.tx_hash.substring(0, 20)}...`
            : `XRPL에 기록됨\nTx: ${xrplResult.tx_hash.substring(0, 20)}...`
        );
      } else {
        Alert.alert(isEn ? "Error" : "오류", xrplResult.error ?? (isEn ? "XRPL failed" : "XRPL 기록 실패"));
      }
    } catch {
      Alert.alert(isEn ? "Error" : "오류", isEn ? "XRPL recording failed" : "XRPL 기록 실패");
    }
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} className="gap-6">
        <View className="gap-2">
          <Text className="text-3xl font-bold text-foreground">
            {isEn ? "Receipt Scanner" : "영수증 스캔"}
          </Text>
          <Text className="text-sm text-muted">
            {isEn ? "Capture multilingual receipts for auto analysis" : "다국 영수증을 촬영하여 자동 분석"}
          </Text>
        </View>

        {!result && (
          <View className="p-4 bg-surface rounded-lg border border-border">
            <Text className="text-sm text-muted">{isEn ? "Target currency" : "기준 통화"}</Text>
            <Text className="text-2xl font-bold text-foreground mt-1">
              {settings.selectedCurrency || "KRW"}
            </Text>
          </View>
        )}

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
                <Text className="text-center font-semibold text-background">
                  {isEn ? "📷 Take photo" : "📷 카메라로 촬영"}
                </Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handlePickImage}
              disabled={isLoading}
              className="p-4 bg-surface border border-border rounded-lg"
            >
              <Text className="text-center font-semibold text-foreground">
                {isEn ? "🖼️ Choose from gallery" : "🖼️ 갤러리에서 선택"}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {error && (
          <View className="p-4 bg-red-100 rounded-lg">
            <Text className="text-sm text-red-700">{error}</Text>
          </View>
        )}

        {result && (
          <View className="gap-4">
            <View className="p-4 bg-surface rounded-lg border border-border">
              <Text className="text-sm text-muted">{isEn ? "Merchant" : "상호명"}</Text>
              <Text className="text-xl font-bold text-foreground mt-1">{result.merchant_name}</Text>
            </View>

            <View className="gap-3">
              <Text className="text-lg font-semibold text-foreground">
                {isEn ? "Payment amount" : "결제 금액"}
              </Text>
              <View className="flex-row gap-3">
                <View className="flex-1 p-4 bg-surface rounded-lg border border-border">
                  <Text className="text-xs text-muted">{isEn ? "Local" : "현지 통화"}</Text>
                  <Text className="text-2xl font-bold text-foreground mt-1">
                    {(result.total_local ?? 0).toFixed(2)} {result.currency}
                  </Text>
                </View>
                <View className="flex-1 p-4 bg-primary rounded-lg">
                  <Text className="text-xs text-background">KRW</Text>
                  <Text className="text-2xl font-bold text-background mt-1">
                    ₩{(result.total_krw ?? 0).toLocaleString()}
                  </Text>
                </View>
              </View>
              <View className="p-3 bg-surface rounded-lg">
                <Text className="text-xs text-muted">{isEn ? "Exchange rate" : "환율"}</Text>
                <Text className="text-sm text-foreground mt-1">
                  1 {result.currency} = ₩{(result.exchange_rate ?? 0).toLocaleString()}
                </Text>
              </View>
            </View>

            <View className="gap-2">
              <TouchableOpacity
                onPress={handleSave}
                disabled={isSaving}
                className="p-4 bg-primary rounded-lg"
              >
                {isSaving ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text className="text-center font-semibold text-background">
                    {isEn ? "💾 Save to Records" : "💾 거래 기록에 저장"}
                  </Text>
                )}
              </TouchableOpacity>

              {savedTxId && settings.xrplWalletSeed && (
                <TouchableOpacity
                  onPress={handleRecordXRPL}
                  disabled={isXRPLLoading}
                  className="p-4 bg-green-600 rounded-lg"
                >
                  {isXRPLLoading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text className="text-center font-semibold text-white">
                      {isEn ? "⛓️ Record to XRPL" : "⛓️ XRPL에 기록"}
                    </Text>
                  )}
                </TouchableOpacity>
              )}

              <TouchableOpacity
                onPress={() => { clearResult(); setSavedTxId(null); }}
                className="p-4 bg-surface border border-border rounded-lg"
              >
                <Text className="text-center font-semibold text-foreground">
                  {isEn ? "Scan again" : "다시 스캔"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}
