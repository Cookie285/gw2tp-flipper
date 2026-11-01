// Hilfsprogramm für tests/test_dashboard_parity.py: plant mit web/plan.js und gibt das Ergebnis
// als JSON aus. Aufruf: node tests/js/parity.mjs <shopping-list.json> <budget_copper>
import { readFileSync } from "node:fs";

import { plan, validateData } from "../../web/plan.js";

const [file, budget] = process.argv.slice(2);
const data = validateData(JSON.parse(readFileSync(file, "utf-8")));
const out = plan(data, Number(budget)).map((p) => ({
  id: p.id, quantity: p.quantity, expected_profit: p.expected_profit, invest: p.invest,
  score: p.score, risk: p.risk,
}));
process.stdout.write(JSON.stringify({ rejected: data.rejected, positions: out }));
