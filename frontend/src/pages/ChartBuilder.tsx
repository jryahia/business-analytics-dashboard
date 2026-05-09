import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { BarChart3, ArrowLeft, RefreshCw } from "lucide-react";
import { datasetsApi, chartsApi, type Dataset } from "@/lib/api";
import { CHART_TYPES, AGGREGATION_TYPES } from "@/lib/utils";
import ChartCard from "@/components/ChartCard";

export default function ChartBuilder() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const dashboardId = searchParams.get("dashboard_id") || undefined;

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [chartType, setChartType] = useState("bar");
  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState("");
  const [colorColumn, setColorColumn] = useState("");
  const [aggregation, setAggregation] = useState("none");
  const [title, setTitle] = useState("");
  const [generatedChart, setGeneratedChart] = useState<Awaited<ReturnType<typeof chartsApi.generate>>["data"] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    datasetsApi.list().then((r) => setDatasets(r.data));
  }, []);

  const columnNames = selectedDataset?.columns.names || [];

  const handleGenerate = async () => {
    if (!selectedDataset || !xColumn || !yColumn) {
      setError("Please select a dataset, X column, and Y column.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await chartsApi.generate({
        dataset_id: selectedDataset.id,
        chart_type: chartType,
        x_column: xColumn,
        y_column: yColumn,
        color_column: colorColumn || undefined,
        aggregation: aggregation === "none" ? undefined : aggregation,
        title: title || undefined,
        dashboard_id: dashboardId,
      });
      setGeneratedChart(res.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg || "Failed to generate chart");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button
          className="p-2 text-dark-400 hover:text-dark-100 hover:bg-dark-800 rounded-lg transition-colors"
          onClick={() => navigate(dashboardId ? `/dashboards/${dashboardId}` : "/dashboards")}
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Chart Builder</h1>
          <p className="text-dark-400 text-sm">{dashboardId ? "Adding to dashboard" : "Create a standalone chart"}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Config Panel */}
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-dark-100 mb-4">Chart Configuration</h3>

            <div className="space-y-4">
              <div>
                <label className="label">Dataset</label>
                <select
                  className="input"
                  value={selectedDataset?.id || ""}
                  onChange={(e) => {
                    const ds = datasets.find((d) => d.id === e.target.value) || null;
                    setSelectedDataset(ds);
                    setXColumn("");
                    setYColumn("");
                    setColorColumn("");
                  }}
                >
                  <option value="">Select dataset...</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>{d.name} ({d.row_count.toLocaleString()} rows)</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Chart Type</label>
                <div className="grid grid-cols-4 gap-2">
                  {CHART_TYPES.map((ct) => (
                    <button
                      key={ct.value}
                      className={`px-2 py-2 rounded-lg text-xs font-medium transition-colors ${
                        chartType === ct.value
                          ? "bg-brand-500 text-white"
                          : "bg-dark-700 text-dark-300 hover:bg-dark-600"
                      }`}
                      onClick={() => setChartType(ct.value)}
                    >
                      {ct.label}
                    </button>
                  ))}
                </div>
              </div>

              {selectedDataset && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="label">X Axis / Labels</label>
                      <select className="input" value={xColumn} onChange={(e) => setXColumn(e.target.value)}>
                        <option value="">Select column...</option>
                        {columnNames.map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="label">Y Axis / Values</label>
                      <select className="input" value={yColumn} onChange={(e) => setYColumn(e.target.value)}>
                        <option value="">Select column...</option>
                        {columnNames.map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="label">Color / Group By</label>
                      <select className="input" value={colorColumn} onChange={(e) => setColorColumn(e.target.value)}>
                        <option value="">None</option>
                        {columnNames.map((c) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="label">Aggregation</label>
                      <select className="input" value={aggregation} onChange={(e) => setAggregation(e.target.value)}>
                        {AGGREGATION_TYPES.map((a) => <option key={a.value} value={a.value}>{a.label}</option>)}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="label">Chart Title (optional)</label>
                    <input
                      className="input"
                      placeholder="My Chart"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                    />
                  </div>
                </>
              )}

              {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2 text-red-400 text-sm">{error}</div>
              )}

              <button
                className="btn-primary w-full flex items-center justify-center gap-2"
                onClick={handleGenerate}
                disabled={loading || !selectedDataset || !xColumn || !yColumn}
              >
                {loading ? <><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</> : <><BarChart3 className="w-4 h-4" /> Generate Chart</>}
              </button>
            </div>
          </div>
        </div>

        {/* Preview Panel */}
        <div>
          {generatedChart ? (
            <div className="space-y-3">
              <ChartCard chart={generatedChart} />
              <div className="flex gap-2">
                <button className="btn-secondary flex-1 text-sm" onClick={handleGenerate}>Regenerate</button>
                <button
                  className="btn-primary flex-1 text-sm"
                  onClick={() => navigate(dashboardId ? `/dashboards/${dashboardId}` : "/dashboards")}
                >
                  {dashboardId ? "Back to Dashboard" : "Go to Dashboards"}
                </button>
              </div>
            </div>
          ) : (
            <div className="card h-72 flex flex-col items-center justify-center text-center border-dashed">
              <BarChart3 className="w-12 h-12 text-dark-600 mb-3" />
              <p className="text-dark-400">Chart preview will appear here</p>
              <p className="text-dark-500 text-sm mt-1">Select a dataset and columns, then click Generate Chart</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
