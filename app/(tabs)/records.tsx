import { FlatList, Pressable, Text, TextInput, TouchableOpacity, View, Modal, ScrollView } from 'react-native';
import { useCallback, useMemo, useState } from 'react';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';

import { ScreenContainer } from '@/components/screen-container';
import { useFinance } from '@/lib/finance-context';
import { categories, CategoryId, getCategory } from '@/lib/finance';
import { processReceiptImage } from '@/lib/receipt-ocr';
import { processExcelFile } from '@/lib/excel-parser';

type FilterMode = 'all' | 'date' | 'category';

export default function RecordsScreen() {
  const { transactions, addNotification, updateCategory } = useFinance();
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [selectedCategory, setSelectedCategory] = useState<CategoryId | null>(null);
  const [searchText, setSearchText] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [inputText, setInputText] = useState('');
  const [activeTab, setActiveTab] = useState<'manual' | 'receipt' | 'excel'>('manual');

  const filteredTransactions = useMemo(() => {
    let result = transactions;

    if (selectedCategory) {
      result = result.filter((t) => t.category === selectedCategory);
    }

    if (searchText.trim()) {
      const query = searchText.toLowerCase();
      result = result.filter((t) => t.merchant.toLowerCase().includes(query) || t.rawText.toLowerCase().includes(query));
    }

    return result.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [transactions, selectedCategory, searchText]);

  const handleAddManual = useCallback(() => {
    if (inputText.trim()) {
      addNotification(inputText);
      setInputText('');
      setModalVisible(false);
    }
  }, [inputText, addNotification]);

  const handlePickReceipt = useCallback(async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.8,
      });

      if (!result.canceled && result.assets[0]) {
        const receiptData = await processReceiptImage(result.assets[0].uri);
        const rawText = `${receiptData.merchantName} ${receiptData.amount} ${receiptData.currency}`;
        addNotification(rawText);
        setModalVisible(false);
      }
    } catch (error) {
      alert('영수증 처리 중 오류가 발생했습니다.');
      console.error('Receipt processing error:', error);
    }
  }, [addNotification]);

  const handlePickExcel = useCallback(async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
      });

      if (!result.canceled && result.assets[0]) {
        const txs = await processExcelFile(result.assets[0].uri);
        txs.forEach((tx) => {
          addNotification(tx.rawText);
        });
        alert(`${txs.length}개의 거래가 추가되었습니다.`);
        setModalVisible(false);
      }
    } catch (error) {
      alert('Excel 파일 처리 중 오류가 발생했습니다.');
      console.error('Excel processing error:', error);
    }
  }, [addNotification]);

  return (
    <ScreenContainer className="px-5 pt-10">
      <View className="flex-1 gap-4">
        {/* 헤더 */}
        <View className="gap-2 mb-5">
          <Text className="text-3xl font-bold text-foreground leading-10">거래 기록</Text>
          <Text className="text-sm text-muted leading-5">모든 거래 내역을 확인하고 관리하세요</Text>
        </View>

        {/* 검색 및 필터 */}
        <View className="gap-4">
          <TextInput
            value={searchText}
            onChangeText={setSearchText}
            placeholder="상인명 또는 설명으로 검색..."
            className="rounded-2xl border border-border bg-surface px-4 py-3 text-foreground"
            placeholderTextColor="#999"
          />

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ columnGap: 10, paddingRight: 8 }}
          >
            <Pressable
              onPress={() => setSelectedCategory(null)}
              style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
              className={`rounded-full px-5 py-2.5 border ${selectedCategory === null ? 'bg-primary border-primary' : 'border-border bg-surface'}`}
            >
              <Text className={`text-sm font-semibold ${selectedCategory === null ? 'text-white' : 'text-foreground'}`}>전체</Text>
            </Pressable>
            {categories.map((cat) => (
              <Pressable
                key={cat.id}
                onPress={() => setSelectedCategory(cat.id as CategoryId)}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className={`rounded-full px-5 py-2.5 border ${selectedCategory === cat.id ? 'border-primary bg-primary/10' : 'border-border bg-surface'}`}
              >
                <Text className={`text-sm font-semibold ${selectedCategory === cat.id ? 'text-primary' : 'text-foreground'}`}>{cat.label}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>

        {/* 거래 리스트 */}
        <FlatList
          data={filteredTransactions}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => {
            const category = getCategory(item.category);
            return (
              <Pressable
                onPress={() => {
                  // 카테고리 수정 모달 표시 가능
                }}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="mb-4 rounded-2xl bg-surface border border-border p-5"
              >
                <View className="flex-row items-start justify-between gap-3">
                  <View className="flex-row items-center gap-3 flex-1">
                    <View className="w-12 h-12 rounded-2xl items-center justify-center" style={{ backgroundColor: category.tone + '20' }}>
                      <Text className="text-xl">{getCategoryEmoji(item.category)}</Text>
                    </View>
                    <View className="flex-1">
                      <Text className="text-sm font-bold text-foreground leading-5">{item.merchant}</Text>
                      <View className="flex-row items-center gap-2 mt-2">
                        <View className="rounded-full px-2 py-1" style={{ backgroundColor: category.tone }}>
                          <Text className="text-xs font-medium text-white">{category.label}</Text>
                        </View>
                        <Text className="text-xs text-muted">{item.date}</Text>
                      </View>
                    </View>
                  </View>
                  <View className="items-end">
                    <Text className="text-sm font-bold text-foreground leading-5">{item.amount}</Text>
                    <Text className="text-xs text-muted mt-1">{item.currency}</Text>
                  </View>
                </View>
                {item.confidence < 0.9 && (
                  <View className="mt-2 pt-2 border-t border-border">
                    <Text className="text-xs text-warning">⚠️ 분류 신뢰도: {Math.round(item.confidence * 100)}%</Text>
                  </View>
                )}
              </Pressable>
            );
          }}
          ListEmptyComponent={
            <View className="items-center justify-center py-16">
              <Text className="text-lg text-muted font-semibold mb-2">거래 기록이 없습니다</Text>
              <Text className="text-sm text-muted">아래 버튼으로 거래를 추가해보세요</Text>
            </View>
          }
          scrollEnabled={true}
          contentContainerStyle={{ paddingBottom: 100 }}
        />

        {/* 추가 버튼 */}
        <TouchableOpacity onPress={() => setModalVisible(true)} className="absolute bottom-6 right-6 rounded-full bg-primary w-16 h-16 items-center justify-center shadow-lg active:opacity-80">
          <Text className="text-3xl">+</Text>
        </TouchableOpacity>

        {/* 모달 */}
        <Modal visible={modalVisible} animationType="slide" transparent>
          <View className="flex-1 bg-black/50 justify-end">
            <View className="bg-background rounded-t-3xl p-6 gap-5">
              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-2xl font-bold text-foreground">거래 추가</Text>
                <Pressable onPress={() => setModalVisible(false)} style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1 }]}>
                  <Text className="text-2xl text-muted">✕</Text>
                </Pressable>
              </View>

              {/* 탭 */}
              <View className="flex-row gap-2 border-b border-border">
                {(['manual', 'receipt', 'excel'] as const).map((tab) => (
                  <Pressable
                    key={tab}
                    onPress={() => setActiveTab(tab)}
                    style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                    className={`flex-1 py-3 border-b-2 ${activeTab === tab ? 'border-primary' : 'border-transparent'}`}
                  >
                    <Text className={`text-sm font-bold text-center ${activeTab === tab ? 'text-primary' : 'text-muted'}`}>
                      {tab === 'manual' ? '텍스트' : tab === 'receipt' ? '영수증' : 'Excel'}
                    </Text>
                  </Pressable>
                ))}
              </View>

              {/* 콘텐츠 */}
              <ScrollView showsVerticalScrollIndicator={false}>
                {activeTab === 'manual' && (
                  <View className="gap-3 pb-6">
                    <Text className="text-sm text-muted">은행 앱 알림을 복사해서 붙여넣으세요</Text>
                    <TextInput
                      value={inputText}
                      onChangeText={setInputText}
                      placeholder="예: STARBUCKS LONDON 승인 GBP 5.40"
                      multiline
                      numberOfLines={4}
                      className="rounded-2xl border border-border bg-surface px-4 py-3 text-foreground"
                      placeholderTextColor="#999"
                    />
                    <TouchableOpacity onPress={handleAddManual} className="rounded-2xl bg-primary py-4 items-center active:opacity-80">
                      <Text className="text-white font-bold">추가</Text>
                    </TouchableOpacity>
                  </View>
                )}

                {activeTab === 'receipt' && (
                  <View className="gap-3 pb-6">
                    <Text className="text-sm text-muted">현금 결제 영수증 사진을 업로드하세요</Text>
                    <TouchableOpacity onPress={handlePickReceipt} className="rounded-2xl border-2 border-dashed border-primary py-8 items-center active:opacity-80">
                      <Text className="text-4xl mb-2">📸</Text>
                      <Text className="text-sm font-bold text-primary">사진 선택</Text>
                    </TouchableOpacity>
                  </View>
                )}

                {activeTab === 'excel' && (
                  <View className="gap-3 pb-6">
                    <Text className="text-sm text-muted">월별 거래내역 Excel 파일을 업로드하세요</Text>
                    <TouchableOpacity onPress={handlePickExcel} className="rounded-2xl border-2 border-dashed border-primary py-8 items-center active:opacity-80">
                      <Text className="text-4xl mb-2">📊</Text>
                      <Text className="text-sm font-bold text-primary">파일 선택</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </ScrollView>
            </View>
          </View>
        </Modal>
      </View>
    </ScreenContainer>
  );
}

function getCategoryEmoji(categoryId: string): string {
  const emojiMap: Record<string, string> = {
    food: '🍽️',
    transport: '🚗',
    housing: '🏠',
    study: '📚',
    shopping: '🛍️',
    health: '🏥',
    transfer: '💸',
    other: '📌',
  };
  return emojiMap[categoryId] || '📌';
}
