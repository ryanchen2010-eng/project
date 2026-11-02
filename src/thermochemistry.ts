export type ThermoRow = { side: 'reactant' | 'product'; coefficient: number; value: number };
const finite = (value: number, label: string) => { if (!Number.isFinite(value)) throw new Error(`${label} must be a finite number.`); return value; };
export function heat(massGrams: number, capacity: number, deltaC: number, specific: boolean): number {
  finite(capacity, 'Heat capacity'); finite(deltaC, 'Temperature change');
  if (capacity <= 0 || (specific && (!Number.isFinite(massGrams) || massGrams <= 0))) throw new Error('Mass and heat capacity must be positive.');
  return finite((specific ? massGrams : 1) * capacity * deltaC, 'Result');
}
export function reactionChange(rows: ThermoRow[]): number {
  if (!rows.some(r => r.side === 'reactant') || !rows.some(r => r.side === 'product')) throw new Error('Enter at least one reactant and one product.');
  let total = 0;
  for (const row of rows) {
    if (row.side !== 'reactant' && row.side !== 'product') throw new Error('Each species must be a reactant or product.');
    if (!Number.isFinite(row.coefficient) || row.coefficient <= 0 || !Number.isFinite(row.value)) throw new Error('Each coefficient must be positive and each value must be a finite number.');
    total += (row.side === 'product' ? 1 : -1) * row.coefficient * row.value;
  }
  return finite(total, 'Result');
}
export function gibbs(enthalpyKJ: number, entropyJ: number, temperatureK: number): number {
  finite(enthalpyKJ, 'ΔH'); finite(entropyJ, 'ΔS'); finite(temperatureK, 'Temperature');
  if (temperatureK <= 0) throw new Error('Temperature must be above absolute zero.');
  return finite(enthalpyKJ - temperatureK * entropyJ / 1000, 'Result');
}
export function classifyEnthalpy(value: number): string {
  finite(value, 'ΔH'); return value < 0 ? 'Exothermic' : value > 0 ? 'Endothermic' : 'Neither (ΔH = 0)';
}
