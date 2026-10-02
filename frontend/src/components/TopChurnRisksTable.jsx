import { useEffect, useState } from "react";
import { api } from "../api";

export default function TopChurnRisksTable() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getTopChurnRisks(10).then(setRows).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load churn risks: {error}</div>;

  return (
    <div className="card">
      <h3>Highest Churn Risk</h3>
      <table>
        <thead>
          <tr>
            <th>Customer</th>
            <th>Region</th>
            <th>Churn Probability</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.customer_id}>
              <td>{r.customer_id}</td>
              <td>{r.region}</td>
              <td>
                <span className="badge badge-risk">{(r.churn_probability * 100).toFixed(1)}%</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
