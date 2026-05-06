import { CategorizationRule, createTransaction, Transaction } from './finance';

/**
 * Excel 파일 파싱 및 거래 정보 추출
 * 월별 거래내역 엑셀 파일 일괄 분석
 */

export type ExcelRow = {
  date?: string;
  merchant?: string;
  amount?: number;
  currency?: string;
  description?: string;
  [key: string]: any;
};

/**
 * Excel 파일에서 거래 데이터 추출
 * 실제 구현을 위해서는 xlsx 라이브러리 필요
 */
export async function parseExcelFile(fileUri: string): Promise<ExcelRow[]> {
  try {
    // 실제 구현: xlsx 라이브러리 사용
    // import XLSX from 'xlsx';
    // const workbook = XLSX.read(fileData, { type: 'binary' });
    // const sheetName = workbook.SheetNames[0];
    // const worksheet = workbook.Sheets[sheetName];
    // const data = XLSX.utils.sheet_to_json(worksheet);

    console.log('Excel parsing for:', fileUri);
    return [];
  } catch (error) {
    console.error('Failed to parse Excel file:', error);
    throw error;
  }
}

/**
 * Excel 행을 거래 객체로 변환
 */
function rowToTransaction(row: ExcelRow, customRules?: CategorizationRule[]): Transaction | null {
  const date = row.date || new Date().toISOString().slice(0, 10);
  const merchant = row.merchant || row.description || 'Unknown';
  const amount = row.amount || 0;
  const currency = row.currency || 'USD';

  if (!merchant || amount <= 0) {
    return null;
  }

  const rawText = `${merchant} ${amount} ${currency}`;
  return createTransaction(rawText, 'manual', date, customRules);
}

/**
 * Excel 파일 전체 파싱 및 거래 변환
 */
export async function processExcelFile(fileUri: string, customRules?: CategorizationRule[]): Promise<Transaction[]> {
  try {
    const rows = await parseExcelFile(fileUri);
    const transactions = rows
      .map((row) => rowToTransaction(row, customRules))
      .filter((tx): tx is Transaction => tx !== null);

    console.log(`Processed ${transactions.length} transactions from Excel file`);
    return transactions;
  } catch (error) {
    console.error('Failed to process Excel file:', error);
    throw error;
  }
}

/**
 * 일반적인 은행 거래내역 Excel 형식 감지 및 자동 매핑
 */
export function detectExcelFormat(rows: ExcelRow[]): { dateCol?: string; merchantCol?: string; amountCol?: string; currencyCol?: string } {
  if (rows.length === 0) {
    return {};
  }

  const firstRow = rows[0];
  const keys = Object.keys(firstRow);

  // 일반적인 컬럼명 패턴 매칭
  const dateCol = keys.find((k) => /date|거래일|거래날짜|일자/i.test(k));
  const merchantCol = keys.find((k) => /merchant|상인|가맹점|거래처|설명|description/i.test(k));
  const amountCol = keys.find((k) => /amount|금액|가격|price/i.test(k));
  const currencyCol = keys.find((k) => /currency|통화|화폐/i.test(k));

  return { dateCol, merchantCol, amountCol, currencyCol };
}
