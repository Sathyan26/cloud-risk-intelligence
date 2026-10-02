const API_BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  return response.json();
}

export const api = {
  getDataQuality: () => request("/analytics/data-quality"),
  getWeeklyTrends: (region) =>
    request(`/analytics/weekly-trends${region ? `?region=${encodeURIComponent(region)}` : ""}`),
  getTopSpenders: (limit = 10) => request(`/analytics/top-spenders?limit=${limit}`),
  getTopAnomalies: (limit = 10) => request(`/risk/anomalies?limit=${limit}`),
  getTopChurnRisks: (limit = 10) => request(`/risk/churn?limit=${limit}`),
  askAssistant: (question) =>
    request("/assistant/ask", { method: "POST", body: JSON.stringify({ question }) }),
};
