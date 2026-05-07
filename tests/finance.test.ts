import { describe, expect, it } from 'vitest';

import { analyzeExchangeTiming, createTransaction, exchangeSeries, parsePaymentNotification } from '../lib/finance';

describe('finance helpers', () => {
  it('parses merchant, amount and food category from Starbucks payment text', () => {
    const parsed = parsePaymentNotification('STARBUCKS LONDON 카드 승인 GBP 5.40');
    expect(parsed.merchant).toContain('STARBUCKS');
    expect(parsed.amount).toBe(5.4);
    expect(parsed.currency).toBe('GBP');
    expect(parsed.category).toBe('food');
  });

  it('creates deterministic proof-like hash for a transaction', () => {
    const transaction = createTransaction('UBER TRIP 결제 USD 18.20', 'notification', '2026-05-06');
    expect(transaction.category).toBe('transport');
    expect(transaction.hash.startsWith('XRPL-')).toBe(true);
  });

  it('returns a clear exchange action recommendation', () => {
    const recommendation = analyzeExchangeTiming(exchangeSeries, 1000);
    expect(['send_now', 'wait']).toContain(recommendation.action);
    expect(recommendation.title.length).toBeGreaterThan(0);
  });
});
