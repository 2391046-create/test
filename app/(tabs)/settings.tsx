import { ScrollView, Text, View, TouchableOpacity, TextInput, Alert } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useSettings } from '@/hooks/useSettings';
import { COUNTRY_CONFIGS, Currency } from '@/types';
import { useState } from 'react';

export default function SettingsScreen() {
  const { settings, updateSettings, setCurrency } = useSettings();
  const [xrplSeed, setXrplSeed] = useState(settings.xrplWalletSeed || '');
  const [xrplAddress, setXrplAddress] = useState(settings.xrplAccountAddress || '');
  const [backendUrl, setBackendUrl] = useState(settings.backendUrl);

  const handleCurrencyChange = async (currency: Currency) => {
    await setCurrency(currency);
  };

  const handleSaveXRPL = async () => {
    if (!xrplSeed || !xrplAddress) {
      Alert.alert('오류', '지갑 정보를 모두 입력해주세요');
      return;
    }

    await updateSettings({
      xrplWalletSeed: xrplSeed,
      xrplAccountAddress: xrplAddress,
    });

    Alert.alert('성공', 'XRPL 지갑 정보가 저장되었습니다');
  };

  const handleSaveBackendUrl = async () => {
    if (!backendUrl) {
      Alert.alert('오류', '백엔드 URL을 입력해주세요');
      return;
    }

    await updateSettings({
      backendUrl: backendUrl,
    });

    Alert.alert('성공', '백엔드 URL이 저장되었습니다');
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} className="gap-6">
        {/* 헤더 */}
        <View className="gap-2">
          <Text className="text-3xl font-bold text-foreground">설정</Text>
          <Text className="text-sm text-muted">앱 설정 및 환경 구성</Text>
        </View>

        {/* 국가/통화 선택 */}
        <View className="gap-3">
          <Text className="text-lg font-semibold text-foreground">국가 및 통화</Text>
          <Text className="text-sm text-muted">
            현재 선택: {settings.selectedCountry} ({settings.selectedCurrency})
          </Text>

          <View className="gap-2">
            {Object.entries(COUNTRY_CONFIGS).map(([currency, config]) => (
              <TouchableOpacity
                key={currency}
                onPress={() => handleCurrencyChange(currency as Currency)}
                className={`p-4 rounded-lg border-2 ${
                  settings.selectedCurrency === currency
                    ? 'bg-primary border-primary'
                    : 'bg-surface border-border'
                }`}
              >
                <View className="flex-row items-center justify-between">
                  <View className="flex-row items-center gap-3">
                    <Text className="text-2xl">{config.flag}</Text>
                    <View>
                      <Text
                        className={`font-semibold ${
                          settings.selectedCurrency === currency
                            ? 'text-background'
                            : 'text-foreground'
                        }`}
                      >
                        {config.name}
                      </Text>
                      <Text
                        className={`text-xs ${
                          settings.selectedCurrency === currency
                            ? 'text-background'
                            : 'text-muted'
                        }`}
                      >
                        {currency} (1 {currency} = ₩{config.exchangeRate.toLocaleString()})
                      </Text>
                    </View>
                  </View>
                  {settings.selectedCurrency === currency && (
                    <Text className="text-lg text-background">✓</Text>
                  )}
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* XRPL 지갑 설정 */}
        <View className="gap-3 p-4 bg-surface rounded-lg border border-border">
          <Text className="text-lg font-semibold text-foreground">XRPL 지갑 설정</Text>

          <View className="gap-2">
            <Text className="text-sm font-medium text-muted">지갑 Seed</Text>
            <TextInput
              value={xrplSeed}
              onChangeText={setXrplSeed}
              placeholder="XRPL 지갑 시드 입력"
              secureTextEntry
              className="p-3 bg-background border border-border rounded-lg text-foreground"
              placeholderTextColor="#9BA1A6"
            />
          </View>

          <View className="gap-2">
            <Text className="text-sm font-medium text-muted">계정 주소</Text>
            <TextInput
              value={xrplAddress}
              onChangeText={setXrplAddress}
              placeholder="XRPL 계정 주소 입력"
              className="p-3 bg-background border border-border rounded-lg text-foreground"
              placeholderTextColor="#9BA1A6"
            />
          </View>

          <TouchableOpacity
            onPress={handleSaveXRPL}
            className="p-3 bg-primary rounded-lg mt-2"
          >
            <Text className="text-center font-semibold text-background">
              XRPL 지갑 저장
            </Text>
          </TouchableOpacity>

          {settings.xrplWalletSeed && (
            <Text className="text-xs text-success">✓ XRPL 지갑이 설정되었습니다</Text>
          )}
        </View>

        {/* 백엔드 URL 설정 */}
        <View className="gap-3 p-4 bg-surface rounded-lg border border-border">
          <Text className="text-lg font-semibold text-foreground">백엔드 설정</Text>

          <View className="gap-2">
            <Text className="text-sm font-medium text-muted">API URL</Text>
            <TextInput
              value={backendUrl}
              onChangeText={setBackendUrl}
              placeholder="http://localhost:8000"
              className="p-3 bg-background border border-border rounded-lg text-foreground"
              placeholderTextColor="#9BA1A6"
            />
          </View>

          <TouchableOpacity
            onPress={handleSaveBackendUrl}
            className="p-3 bg-primary rounded-lg mt-2"
          >
            <Text className="text-center font-semibold text-background">
              백엔드 URL 저장
            </Text>
          </TouchableOpacity>
        </View>

        {/* 정보 */}
        <View className="gap-2 p-4 bg-surface rounded-lg border border-border">
          <Text className="text-sm font-semibold text-foreground">앱 정보</Text>
          <Text className="text-xs text-muted">Finance Compass v1.0.0</Text>
          <Text className="text-xs text-muted">유학생 재정 관리 및 XRPL 블록체인 연동</Text>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
