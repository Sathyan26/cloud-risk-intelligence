import { useEffect, useState } from "react";
import { api } from "../api";

export default function RejectionBreakdown() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getDataQuality().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load breakdown: {error}</div>;
  if (!data) return <div className="card">Loading...</div>;

  return (
    <div className="card">
      <h3>Rejection Reasons</h3>
      <table>
        <thead>
          <tr>
            <th>Source</th>
            <th>Reason</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {data.rejection_breakdown.map((r, i) => (
            <tr key={i}>
              <td>{r.source_table}</td>
              <td>{r.reason_category}</td>
              <td>{r.occurrences}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
