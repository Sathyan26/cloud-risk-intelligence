import { useEffect, useState } from "react";
import { api } from "../api";

export default function TopAnomaliesTable() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getTopAnomalies(10).then(setRows).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load anomalies: {error}</div>;

  return (
    <div className="card">
      <h3>Top Flagged Transactions</h3>
      <table>
        <thead>
          <tr>
            <th>Transaction</th>
            <th>Customer</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.transaction_id}>
              <td>{r.transaction_id}</td>
              <td>{r.customer_id}</td>
              <td>${Number(r.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
              <td>{r.merchant_category}</td>
              <td>
                <span className="badge badge-risk">{Number(r.anomaly_score).toFixed(3)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
