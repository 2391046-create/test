import { ScrollView, Text, View, TouchableOpacity, TextInput, Alert, ActivityIndicator, Platform } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useSettings } from '@/hooks/useSettings';
import { COUNTRY_CONFIGS, Currency, Language } from '@/types';
import { useState } from 'react';
import { livingFundApi } from '@/lib/livingFundApi';
import { router } from 'expo-router';

export default function SettingsScreen() {
  const { settings, updateSettings, setCurrency, setLanguage } = useSettings();
  const [backendUrl, setBackendUrl] = useState(settings.backendUrl);
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [userPhone, setUserPhone] = useState('');
  const [creatingWallet, setCreatingWallet] = useState(false);
  const isEn = settings.language === 'en';

  const api = livingFundApi(settings.backendUrl);

  const handleCurrencyChange = async (currency: Currency) => {
    await setCurrency(currency);
  };

  const handleLanguageChange = async (language: Language) => {
    await setLanguage(language);
  };

  const handleCreateWallet = async () => {
    if (!userName || !userEmail) {
      Alert.alert(isEn ? 'Error' : '오류', isEn ? 'Please enter name and email.' : '이름과 이메일을 입력해주세요');
      return;
    }
    setCreatingWallet(true);
    try {
      const user = await api.createUser(userName, userEmail, userPhone || undefined);
      const wallet = await api.createWallet(user.id);
      await updateSettings({
        xrplUserId: user.id,
        xrplWalletId: wallet.id,
        xrplAddress: wallet.xrpl_address,
      });
      Alert.alert(isEn ? 'Success' : '성공', isEn ? `Wallet created.\nAddress: ${wallet.xrpl_address}` : `지갑이 생성되었습니다!\n주소: ${wallet.xrpl_address}`);
    } catch (e: any) {
      Alert.alert(isEn ? 'Error' : '오류', e.message ?? (isEn ? 'Failed to create wallet' : '지갑 생성 실패'));
    } finally {
      setCreatingWallet(false);
    }
  };

  const handleResetWallet = async () => {
    if (Platform.OS === 'web') {
      if (!window.confirm(isEn ? 'Disconnect this wallet?' : '지갑 연결을 해제하시겠습니까?')) return;
      await updateSettings({ xrplUserId: undefined, xrplWalletId: undefined, xrplAddress: undefined });
    } else {
      Alert.alert(isEn ? 'Reset Wallet' : '지갑 초기화', isEn ? 'Disconnect this wallet?' : '지갑 연결을 해제하시겠습니까?', [
        { text: isEn ? 'Cancel' : '취소', style: 'cancel' },
        {
          text: isEn ? 'Reset' : '초기화', style: 'destructive', onPress: async () => {
            await updateSettings({ xrplUserId: undefined, xrplWalletId: undefined, xrplAddress: undefined });
          }
        },
      ]);
    }
  };

  const handleOpenRules = () => {
    router.push('/(tabs)/rules');
  };
  

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} className="gap-6">
        {/* 헤더 */}
        <View className="gap-2">
          <Text className="text-3xl font-bold text-foreground">{isEn ? 'Settings' : '설정'}</Text>
          <Text className="text-sm text-muted">{isEn ? 'Configure app preferences' : '앱 설정 및 환경 구성'}</Text>
        </View>

        {/* 국가/통화 선택 */}
        <View className="gap-3">
          <Text className="text-lg font-semibold text-foreground">{isEn ? 'Country & Currency' : '국가 및 통화'}</Text>
          <Text className="text-sm text-muted">
            {isEn ? 'Current' : '현재 선택'}: {settings.selectedCountry} ({settings.selectedCurrency})
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
                        {isEn ? config.code : config.name}
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
          <Text className="text-lg font-semibold text-foreground">{isEn ? 'XRPL Wallet' : 'XRPL 지갑 설정'}</Text>

          {settings.xrplAddress ? (
            <View className="gap-3">
              <View className="p-3 bg-background rounded-lg border border-border">
                <Text className="text-xs text-muted mb-1">{isEn ? 'Connected wallet address' : '연결된 지갑 주소'}</Text>
                <Text className="text-sm text-foreground font-mono" numberOfLines={1} ellipsizeMode="middle">
                  {settings.xrplAddress}
                </Text>
              </View>
              <Text className="text-xs text-success">✓ {isEn ? 'XRPL wallet connected' : 'XRPL 지갑이 연결되어 있습니다'}</Text>
              <TouchableOpacity
                onPress={handleResetWallet}
                className="p-3 bg-surface border border-border rounded-lg"
              >
                <Text className="text-center font-semibold text-foreground">{isEn ? 'Disconnect wallet' : '지갑 연결 해제'}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View className="gap-3">
              <View className="gap-2">
                <Text className="text-sm font-medium text-muted">{isEn ? 'Name' : '이름'}</Text>
                <TextInput
                  value={userName}
                  onChangeText={setUserName}
                  placeholder={isEn ? 'John Doe' : '홍길동'}
                  className="p-3 bg-background border border-border rounded-lg text-foreground"
                  placeholderTextColor="#9BA1A6"
                />
              </View>
              <View className="gap-2">
                <Text className="text-sm font-medium text-muted">{isEn ? 'Email' : '이메일'}</Text>
                <TextInput
                  value={userEmail}
                  onChangeText={setUserEmail}
                  placeholder="example@email.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  className="p-3 bg-background border border-border rounded-lg text-foreground"
                  placeholderTextColor="#9BA1A6"
                />
              </View>
              <View className="gap-2">
                <Text className="text-sm font-medium text-muted">{isEn ? 'Phone (optional)' : '전화번호 (선택)'}</Text>
                <TextInput
                  value={userPhone}
                  onChangeText={setUserPhone}
                  placeholder="010-0000-0000"
                  keyboardType="phone-pad"
                  className="p-3 bg-background border border-border rounded-lg text-foreground"
                  placeholderTextColor="#9BA1A6"
                />
              </View>
              <TouchableOpacity
                onPress={handleCreateWallet}
                disabled={creatingWallet}
                className={`p-3 rounded-lg mt-1 flex-row items-center justify-center gap-2 ${creatingWallet ? 'bg-muted' : 'bg-primary'}`}
              >
                {creatingWallet && <ActivityIndicator size="small" color="#fff" />}
                <Text className="text-center font-semibold text-background">
                  {isEn ? (creatingWallet ? 'Creating wallet... (15~30s)' : 'Create XRPL Wallet') : (creatingWallet ? '지갑 생성 중... (15~30초)' : 'XRPL 지갑 생성')}
                </Text>
              </TouchableOpacity>
              <Text className="text-xs text-muted">
                {isEn
                  ? 'Registers your account on backend and creates an XRPL Testnet wallet automatically.'
                  : '백엔드 서버에 계정을 등록하고 XRPL Testnet 지갑을 자동으로 생성합니다.'}
              </Text>
            </View>
          )}
        </View>

        {/* 백엔드 URL 설정 */}
        <View className="gap-3 p-4 bg-surface rounded-lg border border-border">
          <Text className="text-lg font-semibold text-foreground">{isEn ? 'Backend' : '백엔드 설정'}</Text>
          <Text className="text-xs text-muted">
            {isEn
              ? 'On mobile, use your PC IP instead of localhost (e.g. http://192.168.x.x:8000)'
              : '폰에서 사용할 때는 localhost 대신 PC의 IP 주소로 변경하세요 (예: http://192.168.x.x:8000)'}
          </Text>
          <View className="gap-2">
            <Text className="text-sm font-medium text-muted">{isEn ? 'FastAPI URL' : 'FastAPI URL'}</Text>
            <TextInput
              value={backendUrl}
              onChangeText={setBackendUrl}
              placeholder="http://localhost:8000"
              autoCapitalize="none"
              className="p-3 bg-background border border-border rounded-lg text-foreground"
              placeholderTextColor="#9BA1A6"
            />
          </View>
          <TouchableOpacity
            onPress={async () => {
              await updateSettings({ backendUrl });
              Alert.alert(isEn ? 'Success' : '성공', isEn ? 'Saved.' : '저장되었습니다');
            }}
            className="p-3 bg-primary rounded-lg"
          >
            <Text className="text-center font-semibold text-background">{isEn ? 'Save' : '저장'}</Text>
          </TouchableOpacity>
        </View>


       {/* 분류 규칙 */}
       <TouchableOpacity
          onPress={handleOpenRules}
          className="gap-2 p-4 bg-surface rounded-lg border border-border active:opacity-80"
        >
          <Text className="text-sm font-semibold text-foreground">{isEn ? 'Classification Rules' : '분류 규칙'}</Text>
          <Text className="text-xs text-muted">{isEn ? 'Manage auto-categorization rules for payment notifications' : '결제 알림 자동 분류 규칙을 관리합니다'}</Text>
          <Text className="text-xs text-primary font-semibold mt-1">{isEn ? 'Open rules manager →' : '규칙 관리 열기 →'}</Text>
        </TouchableOpacity>


        {/* Language */}
        <View className="gap-3 p-4 bg-surface rounded-lg border border-border">
          <Text className="text-lg font-semibold text-foreground">{isEn ? 'Language' : '언어 설정'}</Text>
          <Text className="text-xs text-muted">{isEn ? 'Choose app display language' : '앱 화면 언어를 선택하세요'}</Text>
          <View className="flex-row gap-2">
            {([
              { key: 'ko', label: 'KR' },
              { key: 'en', label: 'EN' },
            ] as const).map((item) => (
              <TouchableOpacity
                key={item.key}
                onPress={() => handleLanguageChange(item.key)}
                className={`flex-1 p-3 rounded-lg border-2 ${
                  settings.language === item.key ? 'bg-primary border-primary' : 'bg-background border-border'
                }`}
              >
                <Text className={`text-center font-semibold ${settings.language === item.key ? 'text-background' : 'text-foreground'}`}>
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* 정보 */}
        <View className="gap-2 p-4 bg-surface rounded-lg border border-border">
          <Text className="text-sm font-semibold text-foreground">{isEn ? 'App Info' : '앱 정보'}</Text>
          <Text className="text-xs text-muted">https://github.com/tamszero/XRPL_Project</Text>
          <Text className="text-xs text-muted">
            {isEn
              ? 'Student finance manager with XRPL-based remittance/exchange features.'
              : '유학생 재정 관리 및 XRPL 블록체인 기반 생활비 송금/환전 앱'}
          </Text>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
