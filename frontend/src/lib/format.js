export function currency(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value || 0);
}

export function labelize(value) {
  return String(value || "").replaceAll("_", " ");
}

export function percent(value) {
  return `${value ?? 0}%`;
}
