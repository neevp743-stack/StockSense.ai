/**
 * StockSense AI — Formatting Utilities
 */

export function getCurrencySymbol(symbol) {
  if (!symbol) return '$';
  const sym = symbol.toUpperCase();
  if (sym.includes('INR') || ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', '^NSEI', '^NSEBANK'].includes(sym)) {
    return '₹';
  }
  if (sym.includes('JPY')) return '¥';
  if (sym.includes('EUR')) return '€';
  if (sym.includes('GBP')) return '£';
  return '$';
}

export function formatPrice(price, symbol, defaultVal = 'N/A') {
  if (price === null || price === undefined || price === 'N/A' || isNaN(Number(price))) {
    return defaultVal;
  }
  const curr = getCurrencySymbol(symbol);
  const num = Number(price);
  return `${curr}${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
