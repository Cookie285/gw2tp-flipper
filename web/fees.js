// Handelsposten-Gebühren in Kupfer, identisch zu src/gw2tp/fees.py:
// Einstellgebühr 5 % und Verkaufssteuer 10 %, jeweils kaufmännisch gerundet, mindestens 1 Kupfer.

const BASIS_POINTS = 10000;
export const LISTING_FEE_BP = 500;
export const EXCHANGE_FEE_BP = 1000;

function fee(amount, bp) {
  if (amount <= 0) return 0;
  return Math.max(1, Math.floor((amount * bp + BASIS_POINTS / 2) / BASIS_POINTS));
}

export const listingFee = (amount) => fee(amount, LISTING_FEE_BP);
export const exchangeFee = (amount) => fee(amount, EXCHANGE_FEE_BP);
export const totalFees = (amount) => listingFee(amount) + exchangeFee(amount);

/** Erlös nach Gebühren für einen Verkauf von ``quantity`` Stück zu ``price``. */
export const netProceeds = (price, quantity) => price * quantity - totalFees(price * quantity);
