import DecisionLogTable from '../../components/log/DecisionLogTable';
import LogFilters from '../../components/log/LogFilters';
import PortfolioInsightsPanel from '../../components/log/PortfolioInsightsPanel';

export default function LogPage() {
  return (
    <main className="min-h-screen bg-bg-base text-text-primary p-8">
      <LogFilters />
      <DecisionLogTable />
      <PortfolioInsightsPanel />
    </main>
  );
}
