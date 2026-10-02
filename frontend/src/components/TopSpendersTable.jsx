import { useEffect, useState } from "react";
import { api } from "../api";

export default function TopSpendersTable() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getTopSpenders(10).then(setRows).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load top spenders: {error}</div>;

  return (
    <div className="card">
      <h3>Top Spenders</h3>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Customer</th>
            <th>Region</th>
            <th>Transactions</th>
            <th>Total Spend</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.customer_id}>
              <td>#{r.spending_rank}</td>
              <td>{r.customer_id}</td>
              <td>{r.region}</td>
              <td>{r.transaction_count}</td>
              <td>${Number(r.total_spending).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
