// Minimaler Client für die offizielle GW2-API im Browser.
//
// Umgang mit dem API-Key (bewusste, abgesicherte Ausnahme von „Key nie in URLs“):
// Das GW2-API-Backend unterstützt keine CORS-Preflight-Anfragen. Ein Authorization-Header löst im
// Browser immer einen Preflight aus und scheitert daher. Die offizielle Doku sieht für Browser den
// Parameter ?access_token= vor. Wir nutzen ihn unter diesen Grenzen:
// * nur für die festen Konto-Endpunkte in AUTH_PATHS, nie für öffentliche Daten,
// * nur an https://api.guildwars2.com (Pfad-Allowlist, keine Redirects, CSP connect-src),
// * per fetch ohne Referrer, ohne Cookies, ohne Cache. Die URL erscheint nie in der Adresszeile
//   oder Browser-Historie und wird nicht geloggt; Fehlermeldungen enthalten weder Key noch URL,
// * nur „einfache“ Anfragen (GET mit Accept-Header), damit kein Preflight entsteht.

export const API_ORIGIN = "https://api.guildwars2.com";
export const MAX_IDS = 200;
// Format eines GW2-API-Keys: 8-4-4-4-20-4-4-4-12 Hex-Zeichen.
export const KEY_RE =
  /^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{20}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$/;
// Einzige Endpunkte, an die der Key gesendet wird.
export const AUTH_PATHS = new Set([
  "/v2/tokeninfo",
  "/v2/commerce/delivery",
  "/v2/commerce/transactions/current/buys",
  "/v2/commerce/transactions/current/sells",
  "/v2/commerce/transactions/history/buys",
  "/v2/commerce/transactions/history/sells",
]);
const PATH_RE = /^\/v2(\/[a-z]+)+$/;
const PARAM_RE = /^(ids|page|page_size)$/;
const MAX_BYTES = 5 * 1024 * 1024;
const RETRY_STATUS = new Set([429, 500, 502, 503, 504]);

export class ApiError extends Error {
  constructor(message, kind = "api") {
    super(message);
    this.kind = kind;
  }
}

/** URL bauen. ``key`` nur für Konto-Endpunkte; sonst wird abgebrochen. */
export function buildUrl(path, params = {}, key = null) {
  if (!PATH_RE.test(path)) throw new ApiError("Ungültiger API-Pfad");
  const url = new URL(API_ORIGIN + path);
  for (const [k, v] of Object.entries(params)) {
    if (!PARAM_RE.test(k) || !/^[0-9,]{1,2000}$/.test(String(v))) {
      throw new ApiError("Ungültiger Parameter");
    }
    url.searchParams.set(k, String(v));
  }
  if (key !== null) {
    if (!AUTH_PATHS.has(path)) throw new ApiError("Key nur für Konto-Endpunkte erlaubt");
    if (typeof key !== "string" || !KEY_RE.test(key)) throw new ApiError("Ungültiger Key");
    url.searchParams.set("access_token", key);
  }
  if (url.origin !== API_ORIGIN) throw new ApiError("Unerlaubtes Ziel");
  return url.toString();
}

const defaultSleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * GET-Anfrage. ``key`` nur für Endpunkte aus AUTH_PATHS.
 * ``emptyOnStatus``: Statuscodes, die als leeres Ergebnis gelten (z. B. Seite außerhalb).
 * Rückgabe: ``{ data, pageTotal }``.
 */
export async function request(path, options = {}) {
  const {
    params = {},
    key = null,
    fetchImpl = globalThis.fetch,
    sleep = defaultSleep,
    timeoutMs = 15000,
    retries = 2,
    emptyOnStatus = [],
  } = options;
  const url = buildUrl(path, params, key);

  for (let attempt = 0; ; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let resp;
    try {
      resp = await fetchImpl(url, {
        method: "GET",
        headers: { Accept: "application/json" }, // CORS-safelisted → kein Preflight
        mode: "cors",
        credentials: "omit",
        referrerPolicy: "no-referrer",
        cache: "no-store",
        redirect: "error",
        signal: controller.signal,
      });
    } catch {
      clearTimeout(timer);
      if (attempt < retries) {
        await sleep(1000 * 2 ** attempt);
        continue;
      }
      throw new ApiError(
        "Die GW2-API ist nicht erreichbar oder der Browser hat die Anfrage blockiert.",
        "network",
      );
    }
    clearTimeout(timer);

    if (emptyOnStatus.includes(resp.status)) return { data: [], pageTotal: 0 };
    if (resp.status === 401 || resp.status === 403) {
      throw new ApiError("Der API-Key ist ungültig oder hat nicht die nötigen Rechte.", "auth");
    }
    if (RETRY_STATUS.has(resp.status) && attempt < retries) {
      const after = Number.parseInt(resp.headers?.get?.("Retry-After") ?? "", 10);
      await sleep(Number.isFinite(after) && after >= 0 ? Math.min(after, 30) * 1000 : 1000 * 2 ** attempt);
      continue;
    }
    if (!resp.ok) throw new ApiError(`Die GW2-API antwortet mit Fehler ${resp.status}.`);

    const text = await resp.text();
    if (text.length > MAX_BYTES) throw new ApiError("Antwort der GW2-API ist zu groß.");
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      throw new ApiError("Antwort der GW2-API ist kein gültiges JSON.");
    }
    const total = Number.parseInt(resp.headers?.get?.("X-Page-Total") ?? "", 10);
    return { data, pageTotal: Number.isFinite(total) ? total : null };
  }
}

/**
 * Alle Seiten eines paginierten Endpunkts (max. ``maxPages`` × 200 Einträge).
 * Gibt die API ``X-Page-Total`` per CORS nicht frei, wird weitergeblättert, solange volle Seiten
 * kommen; eine Seite außerhalb des Bereichs (400/404) beendet die Schleife.
 */
export async function requestAllPages(path, options = {}) {
  const { maxPages = 10, ...rest } = options;
  const all = [];
  for (let page = 0; page < maxPages; page++) {
    const { data, pageTotal } = await request(path, {
      ...rest,
      params: { page, page_size: MAX_IDS },
      emptyOnStatus: page === 0 ? [404] : [400, 404],
    });
    if (!Array.isArray(data)) throw new ApiError("Unerwartetes Antwortformat der GW2-API.");
    all.push(...data);
    if (data.length < MAX_IDS) break;
    if (pageTotal !== null && page + 1 >= pageTotal) break;
  }
  return all;
}

/** Öffentliche Daten zu IDs in Blöcken zu 200 abrufen – immer ohne Key. */
export async function requestByIds(path, ids, options = {}) {
  const { key: _ignored, ...rest } = options;
  const unique = [...new Set(ids)].filter((id) => Number.isSafeInteger(id) && id > 0);
  const out = [];
  for (let i = 0; i < unique.length; i += MAX_IDS) {
    const chunk = unique.slice(i, i + MAX_IDS);
    const { data } = await request(path, {
      ...rest,
      params: { ids: chunk.join(",") },
      emptyOnStatus: [404],
    });
    if (Array.isArray(data)) out.push(...data);
  }
  return out;
}
