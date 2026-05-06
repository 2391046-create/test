import { Transaction, categories, CategoryId, summarizeByCategory } from './finance';

/**
 * PDF 증빙 리포트 생성
 * 기간별 필터링 및 장학금 신청용 서식
 */

export type ReportFormat = 'scholarship' | 'visa' | 'tax' | 'general';

export type ReportConfig = {
  format: ReportFormat;
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
  categories?: CategoryId[];
  includeDetails: boolean;
  studentName?: string;
  studentId?: string;
  purpose?: string;
};

export type ReportData = {
  title: string;
  generatedDate: string;
  period: string;
  studentInfo?: {
    name: string;
    id: string;
  };
  purpose?: string;
  summary: {
    totalAmount: number;
    totalTransactions: number;
    categoryBreakdown: Array<{
      category: string;
      amount: number;
      count: number;
      percentage: number;
    }>;
  };
  transactions: Array<{
    date: string;
    merchant: string;
    category: string;
    amount: number;
    currency: string;
  }>;
  notes: string[];
};

/**
 * 거래내역 필터링
 */
export function filterTransactions(
  transactions: Transaction[],
  config: ReportConfig
): Transaction[] {
  return transactions.filter((tx) => {
    const txDate = new Date(tx.date);
    const startDate = new Date(config.startDate);
    const endDate = new Date(config.endDate);

    const dateMatch = txDate >= startDate && txDate <= endDate;
    const categoryMatch = !config.categories || config.categories.includes(tx.category);

    return dateMatch && categoryMatch;
  });
}

/**
 * 리포트 데이터 생성
 */
export function generateReportData(
  transactions: Transaction[],
  config: ReportConfig
): ReportData {
  const filteredTxs = filterTransactions(transactions, config);
  const summary = summarizeByCategory(filteredTxs);

  const totalAmount = summary.reduce((sum, item) => sum + item.amount, 0);

  const categoryBreakdown = summary.map((item) => ({
    category: item.category.label,
    amount: item.amount,
    count: item.count,
    percentage: totalAmount > 0 ? (item.amount / totalAmount) * 100 : 0,
  }));

  const reportTxs = filteredTxs
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .map((tx) => {
      const category = categories.find((c) => c.id === tx.category);
      return {
        date: tx.date,
        merchant: tx.merchant,
        category: category?.label || 'Unknown',
        amount: tx.amount,
        currency: tx.currency,
      };
    });

  const notes = getReportNotes(config.format, filteredTxs.length, totalAmount);

  return {
    title: getReportTitle(config.format),
    generatedDate: new Date().toISOString().slice(0, 10),
    period: `${config.startDate} ~ ${config.endDate}`,
    studentInfo: config.studentName
      ? {
          name: config.studentName,
          id: config.studentId || '',
        }
      : undefined,
    purpose: config.purpose,
    summary: {
      totalAmount,
      totalTransactions: filteredTxs.length,
      categoryBreakdown,
    },
    transactions: reportTxs,
    notes,
  };
}

/**
 * 리포트 제목 생성
 */
function getReportTitle(format: ReportFormat): string {
  const titles: Record<ReportFormat, string> = {
    scholarship: '장학금 신청 거래내역 증명',
    visa: '비자 신청 거래내역 증명',
    tax: '세금 신고용 거래내역 증명',
    general: '거래내역 보고서',
  };
  return titles[format];
}

/**
 * 리포트 주석 생성
 */
function getReportNotes(format: ReportFormat, txCount: number, totalAmount: number): string[] {
  const notes: string[] = [
    `총 ${txCount}건의 거래 기록이 포함되어 있습니다.`,
    `총 지출액: ${totalAmount.toLocaleString('ko-KR')}원`,
  ];

  switch (format) {
    case 'scholarship':
      notes.push('이 문서는 장학금 신청 시 재정 능력 증명 자료로 사용될 수 있습니다.');
      notes.push('거래내역은 자동 분류되었으며, 정확성을 위해 검토하시기 바랍니다.');
      break;
    case 'visa':
      notes.push('이 문서는 비자 신청 시 재정 능력 증명 자료로 사용될 수 있습니다.');
      notes.push('거래내역은 은행 또는 카드사 기록을 기반으로 작성되었습니다.');
      break;
    case 'tax':
      notes.push('이 문서는 세금 신고 시 참고 자료로 사용될 수 있습니다.');
      notes.push('정확한 세금 신고를 위해 전문가 상담을 권장합니다.');
      break;
  }

  return notes;
}

/**
 * HTML 형식 리포트 생성 (PDF 변환 전)
 */
export function generateReportHTML(reportData: ReportData): string {
  const categoryRows = reportData.summary.categoryBreakdown
    .map(
      (cat) => `
    <tr>
      <td>${cat.category}</td>
      <td style="text-align: right;">${cat.count}</td>
      <td style="text-align: right;">${cat.amount.toLocaleString('ko-KR')}원</td>
      <td style="text-align: right;">${cat.percentage.toFixed(1)}%</td>
    </tr>
  `
    )
    .join('');

  const transactionRows = reportData.transactions
    .slice(0, 50) // 처음 50개만 표시 (PDF 크기 제한)
    .map(
      (tx) => `
    <tr>
      <td>${tx.date}</td>
      <td>${tx.merchant}</td>
      <td>${tx.category}</td>
      <td style="text-align: right;">${tx.amount} ${tx.currency}</td>
    </tr>
  `
    )
    .join('');

  const studentInfo = reportData.studentInfo
    ? `
    <div style="margin-bottom: 20px;">
      <p><strong>학생명:</strong> ${reportData.studentInfo.name}</p>
      <p><strong>학번:</strong> ${reportData.studentInfo.id}</p>
    </div>
  `
    : '';

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${reportData.title}</title>
  <style>
    body {
      font-family: 'Arial', sans-serif;
      margin: 20px;
      color: #333;
    }
    h1 {
      text-align: center;
      color: #0a7ea4;
      margin-bottom: 10px;
    }
    .header {
      text-align: center;
      margin-bottom: 30px;
      border-bottom: 2px solid #0a7ea4;
      padding-bottom: 15px;
    }
    .meta-info {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
      font-size: 12px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }
    th {
      background-color: #0a7ea4;
      color: white;
      padding: 10px;
      text-align: left;
      font-weight: bold;
    }
    td {
      padding: 8px;
      border-bottom: 1px solid #ddd;
    }
    tr:nth-child(even) {
      background-color: #f9f9f9;
    }
    .summary {
      background-color: #f0f7ff;
      padding: 15px;
      border-radius: 5px;
      margin-bottom: 20px;
    }
    .notes {
      background-color: #fff8e1;
      padding: 15px;
      border-left: 4px solid #ffc107;
      margin-top: 20px;
      font-size: 12px;
    }
    .footer {
      text-align: center;
      margin-top: 30px;
      font-size: 11px;
      color: #666;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>${reportData.title}</h1>
    <div class="meta-info">
      <span>기간: ${reportData.period}</span>
      <span>생성일: ${reportData.generatedDate}</span>
    </div>
  </div>

  ${studentInfo}

  ${reportData.purpose ? `<p><strong>신청 목적:</strong> ${reportData.purpose}</p>` : ''}

  <div class="summary">
    <h3>거래 요약</h3>
    <p><strong>총 거래건수:</strong> ${reportData.summary.totalTransactions}건</p>
    <p><strong>총 지출액:</strong> ${reportData.summary.totalAmount.toLocaleString('ko-KR')}원</p>
  </div>

  <h3>카테고리별 지출 현황</h3>
  <table>
    <thead>
      <tr>
        <th>카테고리</th>
        <th>건수</th>
        <th>금액</th>
        <th>비율</th>
      </tr>
    </thead>
    <tbody>
      ${categoryRows}
    </tbody>
  </table>

  <h3>거래 상세 내역</h3>
  <table>
    <thead>
      <tr>
        <th>날짜</th>
        <th>상인명</th>
        <th>카테고리</th>
        <th>금액</th>
      </tr>
    </thead>
    <tbody>
      ${transactionRows}
    </tbody>
  </table>

  ${
    reportData.transactions.length > 50
      ? `<p style="font-size: 12px; color: #666;">* 상위 50개 거래만 표시됩니다. 전체 거래는 앱에서 확인하세요.</p>`
      : ''
  }

  <div class="notes">
    <h4>주의사항</h4>
    <ul>
      ${reportData.notes.map((note) => `<li>${note}</li>`).join('')}
    </ul>
  </div>

  <div class="footer">
    <p>이 보고서는 Finance Compass 앱에서 자동 생성되었습니다.</p>
    <p>정확성을 위해 원본 거래 기록과 대조하시기 바랍니다.</p>
  </div>
</body>
</html>
  `;

  return html;
}

/**
 * 모의 PDF 생성 (실제 구현은 서버에서 처리)
 */
export async function generatePDF(reportData: ReportData): Promise<Blob> {
  const html = generateReportHTML(reportData);

  // 실제 구현: 서버의 manus-md-to-pdf 또는 weasyprint 사용
  // 현재는 HTML을 Blob으로 반환
  return new Blob([html], { type: 'text/html' });
}
