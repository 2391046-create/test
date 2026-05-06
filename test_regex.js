const text = '[신한카드]\n2026.05.06 14:30\n스타벅스 강남점\n₩5,500\n승인';
const cleanText = text.replace(/\s+/g, ' ').trim();
console.log('Original:', cleanText);

const textWithoutDates = cleanText.replace(/\d{4}\.\d{2}\.\d{2}|\d{1,2}\.\d{2}(?!\.\d)/g, '');
console.log('After date removal:', textWithoutDates);

const match1 = textWithoutDates.match(/(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|₩|\$|€|£)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)\s*(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|원|달러|유로|파운드)?/i);
console.log('Match 1 (with comma):', match1);

if (!match1) {
  const match2 = textWithoutDates.match(/(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|₩|\$|€|£)\s*([0-9]{4,})\s*(?:KRW|USD|EUR|GBP|JPY|CAD|AUD|원|달러|유로|파운드)?/i);
  console.log('Match 2 (4+ digits):', match2);
}
