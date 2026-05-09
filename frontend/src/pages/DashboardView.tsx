import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Plus, Download, RefreshCw, Lightbulb } from "lucide-react";
import { useDashboardStore } from "@/store/dashboardStore";
import { insightsApi, exportApi, type Insight } from "@/lib/api";
import ChartCard from "@/components/ChartCard";
import ExportButton from "@/components/ExportButton";
import { downloadBlob } from "@/lib/utils";

export default function DashboardView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentDashboard, fetchDashboard, isLoading } = useDashboardStore();
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [showInsight, setShowInsight] = useState(false);

  useEffect(() => {
    if (id) fetchDashboard(id);
  }, [id, fetchDashboard]);

  const handleInsights = async () => {
    if (!currentDashboard || !currentDashboard.charts.length) return;
    setLoadingInsight(true);
    setShowInsight(true);
    try {
      const datasetId = currentDashboard.charts[0].dataset_id;
      const res = await insightsApi.generate({ dataset_id: datasetId });
      setInsight(res.data);
    } finally {
      setLoadingInsight(false);
    }
  };

  const handleExportPdf = async () => {
    if (!id) return;
    const res = await exportApi.dashboardPdf(id);
    downloadBlob(res.data as Blob, `${currentDashboard?.name || "dashboard"}.pdf`);
  };

  if (isLoading || !currentDashboard) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-dark-800 rounded w-64" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-72 bg-dark-800 rounded-xl" />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button className="p-2 text-dark-400 hover:text-dark-100 hover:bg-dark-800 rounded-lg transition-colors" onClick={() => navigate("/dashboards")}>
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-dark-100">{currentDashboard.name}</h1>
          {currentDashboard.description && <p className="text-dark-400 text-sm">{currentDashboard.description}</p>}
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary flex items-center gap-2 text-sm" onClick={handleInsights} disabled={loadingInsight}>
            <Lightbulb className="w-4 h-4" />
            {loadingInsight ? "Analyzing..." : "AI Insights"}
          </button>
          <button
            className="btn-secondary flex items-center gap-2 text-sm"
            onClick={() => navigate(`/charts/new?dashboard_id=${id}`)}
          >
            <Plus className="w-4 h-4" /> Add Chart
          </button>
          <ExportButton onExportPdf={handleExportPdf} />
        </div>
      </div>

      {showInsight && (
        <div className="card border-brand-500/30 mb-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-brand-400" />
              <h3 className="font-semibold text-dark-100">AI Business Insights</h3>
            </div>
            <button className="text-dark-500 hover:text-dark-300 text-sm" onClick={() => setShowInsight(false)}>✕</button>
          </div>
          {loadingInsight ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <div key={i} className="h-4 bg-dark-700 rounded animate-pulse" />)}
            </div>
          ) : insight ? (
            <div className="space-y-3">
              <p className="text-dark-300 text-sm italic">{insight.content.summary}</p>
              <ul className="space-y-2">
                {insight.content.insights.map((ins, i) => (
                  <li key={i} className="flex gap-2 text-sm text-dark-200">
                    <span className="text-brand-400 font-semibold shrink-0">{i + 1}.</span>
                    <span>{ins}</span>
                  </li>
                ))}
              </ul>
              {insight.content.recommendations && (
                <div className="mt-3 pt-3 border-t border-dark-700">
                  <p className="text-xs text-dark-400 font-medium mb-2 uppercase tracking-wide">Recommendations</p>
                  <ul className="space-y-1">
                    {insight.content.recommendations.map((r, i) => (
                      <li key={i} className="text-sm text-dark-300 flex gap-2">
                        <span className="text-success">→</span>{r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {currentDashboard.charts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center card">
          <Plus className="w-16 h-16 text-dark-600 mb-4" />
          <p className="text-dark-400 text-lg">No charts yet</p>
          <p className="text-dark-500 text-sm mt-1">Add your first chart to start visualizing data</p>
          <button className="btn-primary mt-4" onClick={() => navigate(`/charts/new?dashboard_id=${id}`)}>
            Add Chart
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-4">
          {currentDashboard.charts.map((chart) => (
            <ChartCard key={chart.id} chart={chart} />
          ))}
        </div>
      )}
    </div>
  );
}
