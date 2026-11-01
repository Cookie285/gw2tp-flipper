// Speicher für den persönlichen GW2-API-Key – nur im Browser.
//
// * "session": sessionStorage, wird beim Schließen des Tabs gelöscht (Standard, empfohlen)
// * "local":   localStorage, bleibt auf diesem Gerät, bis der Nutzer ihn löscht
//
// Der Key wird nirgends sonst abgelegt, nicht geloggt und nur an die Konto-Endpunkte von
// https://api.guildwars2.com gesendet (siehe gw2api.js).

export const STORAGE_KEY = "gw2tp.apiKey";
export const MODES = ["session", "local"];

function storages(win) {
  const out = {};
  for (const [mode, name] of [["session", "sessionStorage"], ["local", "localStorage"]]) {
    try {
      out[mode] = win[name];
    } catch {
      out[mode] = null; // z. B. blockierte Website-Daten
    }
  }
  return out;
}

export function createKeyStore(win = globalThis) {
  const st = storages(win);
  return {
    /** Gespeicherten Key laden: ``{ key, mode }`` oder ``null``. */
    load() {
      for (const mode of MODES) {
        try {
          const key = st[mode]?.getItem(STORAGE_KEY);
          if (key) return { key, mode };
        } catch {
          /* ignorieren */
        }
      }
      return null;
    },
    /** Key speichern; der jeweils andere Speicher wird geleert. */
    save(key, mode) {
      if (!MODES.includes(mode)) throw new Error("Unbekannter Speicherort");
      this.clear();
      const target = st[mode];
      if (!target) throw new Error("Speicher im Browser nicht verfügbar");
      target.setItem(STORAGE_KEY, key);
    },
    /** Key aus beiden Speichern entfernen. */
    clear() {
      for (const mode of MODES) {
        try {
          st[mode]?.removeItem(STORAGE_KEY);
        } catch {
          /* ignorieren */
        }
      }
    },
  };
}
