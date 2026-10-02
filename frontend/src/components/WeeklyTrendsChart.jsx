import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";

const COLORS = ["#2563eb", "#16a34a", "#dc2626", "#ca8a04", "#7c3aed", "#0891b2"];

export default function WeeklyTrendsChart() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getWeeklyTrends().then(setRows).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="card error">Failed to load trends: {error}</div>;
  if (!rows.length) return <div className="card">Loading trends...</div>;

  const regions = [...new Set(rows.map((r) => r.region))];
  const byWeek = {};
  rows.forEach((r) => {
    byWeek[r.week_start] = byWeek[r.week_start] || { week_start: r.week_start };
    byWeek[r.week_start][r.region] = r.total_amount;
  });
  const chartData = Object.values(byWeek).sort((a, b) => a.week_start.localeCompare(b.week_start));

  return (
    <div className="card">
      <h3>Weekly Transaction Volume by Region</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="week_start" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
          <Legend />
          {regions.map((region, i) => (
            <Line
              key={region}
              type="monotone"
              dataKey={region}
              stroke={COLORS[i % COLORS.length]}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
