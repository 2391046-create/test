import { useCallback, useMemo, useState } from 'react';
import { FlatList, Pressable, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { categories, CategorizationRule, createRule, CategoryId } from '@/lib/finance';
import { useRules } from '@/lib/rules-context';

type ModalMode = 'add' | 'edit' | null;

export default function RulesScreen() {
  const { rules, addRule, updateRule, deleteRule, toggleRule, resetToDefaults } = useRules();
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [editingRule, setEditingRule] = useState<CategorizationRule | null>(null);
  const [formData, setFormData] = useState({ name: '', pattern: '', category: 'food' as CategoryId, priority: '5' });

  const sortedRules = useMemo(() => [...rules].sort((a, b) => b.priority - a.priority), [rules]);

  const handleOpenAdd = useCallback(() => {
    setFormData({ name: '', pattern: '', category: 'food', priority: '5' });
    setEditingRule(null);
    setModalMode('add');
  }, []);

  const handleOpenEdit = useCallback((rule: CategorizationRule) => {
    setFormData({
      name: rule.name,
      pattern: rule.pattern,
      category: rule.category,
      priority: rule.priority.toString(),
    });
    setEditingRule(rule);
    setModalMode('edit');
  }, []);

  const handleSave = useCallback(async () => {
    const priority = Math.max(1, Math.min(10, parseInt(formData.priority) || 5));
    if (!formData.name.trim() || !formData.pattern.trim()) {
      alert('규칙 이름과 패턴을 입력해주세요.');
      return;
    }

    if (modalMode === 'add') {
      const newRule = createRule(formData.name, formData.category, formData.pattern, 'keyword', priority);
      await addRule(newRule);
    } else if (modalMode === 'edit' && editingRule) {
      await updateRule(editingRule.id, {
        name: formData.name,
        pattern: formData.pattern,
        category: formData.category,
        priority,
      });
    }

    setModalMode(null);
  }, [formData, modalMode, editingRule, addRule, updateRule]);

  const handleCancel = useCallback(() => {
    setModalMode(null);
  }, []);

  return (
    <ScreenContainer className="px-5 pt-2">
      <View className="flex-1 gap-4">
        {/* 헤더 */}
        <View className="gap-2">
          <Text className="text-3xl font-bold text-foreground leading-10">분류 규칙</Text>
          <Text className="text-sm text-muted leading-5">결제 알림에서 자동으로 카테고리를 인식하는 규칙을 직접 관리하세요.</Text>
        </View>

        {/* 규칙 리스트 */}
        <FlatList
          data={sortedRules}
          keyExtractor={(item) => item.id}
          scrollEnabled={false}
          renderItem={({ item }) => {
            const category = categories.find((c) => c.id === item.category);
            return (
              <Pressable
                onPress={() => handleOpenEdit(item)}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="mb-3 rounded-2xl bg-surface border border-border p-4"
              >
                <View className="flex-row items-start justify-between gap-3">
                  <View className="flex-1 gap-2">
                    <View className="flex-row items-center gap-2">
                      <Text className="text-sm font-semibold text-foreground">{item.name}</Text>
                      <View className="rounded-full px-2 py-1" style={{ backgroundColor: category?.tone }}>
                        <Text className="text-xs font-medium text-white">{category?.label}</Text>
                      </View>
                    </View>
                    <Text className="text-xs text-muted font-mono">패턴: {item.pattern}</Text>
                    <View className="flex-row items-center gap-2 mt-1">
                      <Text className="text-xs text-muted">우선순위: {item.priority}/10</Text>
                      <View className="flex-row gap-1">
                        {Array.from({ length: 10 }).map((_, i) => (
                          <View key={i} className={`w-1 h-1 rounded-full ${i < item.priority ? 'bg-primary' : 'bg-border'}`} />
                        ))}
                      </View>
                    </View>
                  </View>
                  <Pressable
                    onPress={() => toggleRule(item.id, !item.enabled)}
                    style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1 }]}
                    className={`rounded-lg px-3 py-2 ${item.enabled ? 'bg-green-100' : 'bg-gray-100'}`}
                  >
                    <Text className={`text-xs font-semibold ${item.enabled ? 'text-green-700' : 'text-gray-700'}`}>
                      {item.enabled ? '활성' : '비활성'}
                    </Text>
                  </Pressable>
                </View>
                <Pressable
                  onPress={() => deleteRule(item.id)}
                  style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1 }]}
                  className="mt-3 pt-3 border-t border-border"
                >
                  <Text className="text-xs text-red-600 font-medium">삭제</Text>
                </Pressable>
              </Pressable>
            );
          }}
          ListEmptyComponent={
            <View className="items-center justify-center py-8">
              <Text className="text-sm text-muted">아직 규칙이 없습니다.</Text>
            </View>
          }
        />

        {/* 버튼 영역 */}
        <View className="gap-2 mt-auto pb-4">
          <TouchableOpacity onPress={handleOpenAdd} className="rounded-2xl bg-primary py-4 items-center active:opacity-80">
            <Text className="text-white font-bold">+ 새 규칙 추가</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={resetToDefaults} className="rounded-2xl bg-surface border border-border py-3 items-center active:opacity-80">
            <Text className="text-foreground font-semibold">기본값으로 초기화</Text>
          </TouchableOpacity>
        </View>

        {/* 모달 */}
        {modalMode && (
          <View className="absolute inset-0 bg-black/50 flex-1 justify-end rounded-t-3xl">
            <View className="bg-background rounded-t-3xl p-6 gap-4">
              <View className="flex-row items-center justify-between mb-2">
                <Text className="text-xl font-bold text-foreground">{modalMode === 'add' ? '새 규칙 추가' : '규칙 수정'}</Text>
                <Pressable onPress={handleCancel} style={({ pressed }) => [{ opacity: pressed ? 0.6 : 1 }]}>
                  <Text className="text-lg text-muted">✕</Text>
                </Pressable>
              </View>

              <View className="gap-3">
                <View>
                  <Text className="text-xs font-semibold text-muted mb-1">규칙 이름</Text>
                  <TextInput
                    value={formData.name}
                    onChangeText={(text) => setFormData({ ...formData, name: text })}
                    placeholder="예: Starbucks 체인"
                    className="border border-border rounded-lg px-3 py-2 text-foreground"
                    placeholderTextColor="#999"
                  />
                </View>

                <View>
                  <Text className="text-xs font-semibold text-muted mb-1">패턴 (키워드 또는 정규식)</Text>
                  <TextInput
                    value={formData.pattern}
                    onChangeText={(text) => setFormData({ ...formData, pattern: text })}
                    placeholder="예: starbucks|스타벅스"
                    className="border border-border rounded-lg px-3 py-2 text-foreground"
                    placeholderTextColor="#999"
                  />
                </View>

                <View>
                  <Text className="text-xs font-semibold text-muted mb-2">카테고리</Text>
                  <View className="flex-row flex-wrap gap-2">
                    {categories.map((cat) => (
                      <Pressable
                        key={cat.id}
                        onPress={() => setFormData({ ...formData, category: cat.id })}
                        style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                        className={`rounded-lg px-3 py-2 border-2 ${formData.category === cat.id ? 'border-primary bg-primary/10' : 'border-border'}`}
                      >
                        <Text className={`text-xs font-semibold ${formData.category === cat.id ? 'text-primary' : 'text-foreground'}`}>
                          {cat.label}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                <View>
                  <Text className="text-xs font-semibold text-muted mb-1">우선순위 (1-10)</Text>
                  <TextInput
                    value={formData.priority}
                    onChangeText={(text) => setFormData({ ...formData, priority: text })}
                    placeholder="5"
                    keyboardType="number-pad"
                    className="border border-border rounded-lg px-3 py-2 text-foreground"
                    placeholderTextColor="#999"
                  />
                </View>
              </View>

              <View className="flex-row gap-2 mt-4">
                <Pressable onPress={handleCancel} className="flex-1 rounded-lg border border-border py-3 items-center active:opacity-80">
                  <Text className="text-foreground font-semibold">취소</Text>
                </Pressable>
                <Pressable onPress={handleSave} className="flex-1 rounded-lg bg-primary py-3 items-center active:opacity-80">
                  <Text className="text-white font-semibold">저장</Text>
                </Pressable>
              </View>
            </View>
          </View>
        )}
      </View>
    </ScreenContainer>
  );
}
