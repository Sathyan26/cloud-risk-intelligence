import AssistantChat from "./components/AssistantChat";
import KpiCards from "./components/KpiCards";
import RejectionBreakdown from "./components/RejectionBreakdown";
import TopAnomaliesTable from "./components/TopAnomaliesTable";
import TopChurnRisksTable from "./components/TopChurnRisksTable";
import TopSpendersTable from "./components/TopSpendersTable";
import WeeklyTrendsChart from "./components/WeeklyTrendsChart";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Cloud Risk Intelligence Platform</h1>
        <p>Data quality, risk scoring, and churn monitoring</p>
      </header>

      <KpiCards />

      <div className="grid-2col">
        <WeeklyTrendsChart />
        <RejectionBreakdown />
      </div>

      <div className="grid-2col">
        <TopAnomaliesTable />
        <TopChurnRisksTable />
      </div>

      <TopSpendersTable />

      <AssistantChat />
    </div>
  );
}
