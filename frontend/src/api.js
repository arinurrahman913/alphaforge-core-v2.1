// Thin fetch wrappers around the Flask API. In dev, Vite proxies /api to
// http://localhost:5000 (see vite.config.js); in prod, Flask serves this
// same origin so relative paths just work.

async function getJSON(path) {
  const resp = await fetch(path)
  if (!resp.ok) {
    throw new Error(`${path} -> HTTP ${resp.status}`)
  }
  return resp.json()
}

export const api = {
  layer1: () => getJSON('/api/layer1'),
  screening: () => getJSON('/api/screening'),
  evidence: () => getJSON('/api/evidence'),
  knowledge: () => getJSON('/api/knowledge'),
  peer: () => getJSON('/api/peer'),
  confidence: () => getJSON('/api/confidence'),
  risk: () => getJSON('/api/risk'),
  reasoning: () => getJSON('/api/reasoning'),
  aggregator: () => getJSON('/api/aggregator'),
  historical: () => getJSON('/api/historical'),
  ticker: (ticker) => getJSON(`/api/ticker/${encodeURIComponent(ticker)}`),
  liveQuote: (ticker) => getJSON(`/api/ticker/${encodeURIComponent(ticker)}/live`),
}
