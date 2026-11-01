// Minimaler Client für die offizielle GW2-API im Browser.
//
// Sicherheitsregeln:
// * Ziel ist ausschließlich https://api.guildwars2.com (Pfad-Allowlist, keine Redirects).
// * Der API-Key wird nur als Header "Authorization: Bearer …" gesendet, niemals in der URL.
//   Öffentliche Endpunkte (Preise, Items) werden grundsätzlich ohne Key abgefragt.
// * Keine Cookies, kein Referrer, kein Cache; Fehlermeldungen enthalten weder Key noch URL.

export const API_ORIGIN = "https://api.guildwars2.com";
export const MAX_IDS = 200;
const PATH_RE = /^\/v2(\/[a-z]+)+$/;
const PARAM_RE = /^[a-z_]{1,20}$/;
const MAX_BYTES = 5 * 1024 * 1024;
const RETRY_STATUS = new Set([429, 500, 502, 503, 504]);

export class ApiError extends Error {
  constructor(message, kind = "api") {
    super(message);
    this.kind = kind;
  }
}

/** URL für einen API-Pfad bauen. Parameter dürfen nur einfache Werte enthalten. */
export function buildUrl(path, params = {}) {
  if (!PATH_RE.test(path)) throw new ApiError("Ungültiger API-Pfad");
  const url = new URL(API_ORIGIN + path);
  for (const [k, v] of Object.entries(params)) {
    if (!PARAM_RE.test(k) || !/^[0-9,]{1,2000}$/.test(String(v))) {
      throw new ApiError("Ungültiger Parameter");
    }
    url.searchParams.set(k, String(v));
  }
  if (url.origin !== API_ORIGIN) throw new ApiError("Unerlaubtes Ziel");
  return url.toString();
}

const defaultSleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * GET-Anfrage. ``key`` nur für Endpunkte, die ihn brauchen.
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
    emptyOn404 = false,
  } = options;
  const url = buildUrl(path, params);
  const headers = { Accept: "application/json" };
  if (key !== null) {
    if (typeof key !== "string" || !key || url.includes(key)) {
      throw new ApiError("Ungültiger Key");
    }
    headers.Authorization = `Bearer ${key}`;
  }

  for (let attempt = 0; ; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let resp;
    try {
      resp = await fetchImpl(url, {
        method: "GET",
        headers,
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

    if (resp.status === 401 || resp.status === 403) {
      throw new ApiError("Der API-Key ist ungültig oder hat nicht die nötigen Rechte.", "auth");
    }
    if (resp.status === 404 && emptyOn404) return { data: [], pageTotal: 0 };
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

/** Alle Seiten eines paginierten Endpunkts (max. ``maxPages`` × 200 Einträge). */
export async function requestAllPages(path, options = {}) {
  const { maxPages = 10, ...rest } = options;
  const all = [];
  for (let page = 0; page < maxPages; page++) {
    const { data, pageTotal } = await request(path, {
      ...rest,
      params: { page, page_size: MAX_IDS },
      emptyOn404: page === 0,
    });
    if (!Array.isArray(data)) throw new ApiError("Unerwartetes Antwortformat der GW2-API.");
    all.push(...data);
    if (pageTotal === null || page + 1 >= pageTotal || data.length < MAX_IDS) break;
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
      emptyOn404: true,
    });
    if (Array.isArray(data)) out.push(...data);
  }
  return out;
}
