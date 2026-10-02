import { useEffect, useState } from "react";
import { api } from "../api";

export default function KpiCards() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getDataQuality().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load KPIs: {error}</div>;
  if (!data || !data.latest_snapshot) return <div className="card">Loading KPIs...</div>;

  const s = data.latest_snapshot;

  return (
    <div className="kpi-row">
      <div className="card kpi">
        <div className="kpi-value">{s.total_customers_loaded.toLocaleString()}</div>
        <div className="kpi-label">Customers Loaded</div>
      </div>
      <div className="card kpi">
        <div className="kpi-value">{s.total_transactions_loaded.toLocaleString()}</div>
        <div className="kpi-label">Transactions Loaded</div>
      </div>
      <div className="card kpi">
        <div className="kpi-value">{s.total_rejected_records.toLocaleString()}</div>
        <div className="kpi-label">Records Rejected</div>
      </div>
      <div className="card kpi warn">
        <div className="kpi-value">{s.rejection_rate_pct}%</div>
        <div className="kpi-label">Rejection Rate</div>
      </div>
    </div>
  );
}
