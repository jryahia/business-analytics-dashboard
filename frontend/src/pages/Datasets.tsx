import { useEffect, useState } from "react";
import { Database, Upload, Trash2, Eye, Download, RefreshCw } from "lucide-react";
import { datasetsApi, exportApi, type Dataset, type DatasetPreview } from "@/lib/api";
import UploadZone from "@/components/UploadZone";
import DataTable from "@/components/DataTable";
import SourceForm from "@/components/SourceForm";
import ExportButton from "@/components/ExportButton";
import { formatDate, formatNumber, downloadBlob } from "@/lib/utils";

type Tab = "datasets" | "upload" | "sources";

export default function Datasets() {
  const [tab, setTab] = useState<Tab>("datasets");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<{ dataset: Dataset; data: DatasetPreview } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await datasetsApi.list();
      setDatasets(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this dataset?")) return;
    await datasetsApi.delete(id);
    setDatasets((prev) => prev.filter((d) => d.id !== id));
    if (preview?.dataset.id === id) setPreview(null);
  };

  const handlePreview = async (dataset: Dataset) => {
    setPreviewLoading(true);
    try {
      const res = await datasetsApi.preview(dataset.id);
      setPreview({ dataset, data: res.data });
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExportCsv = async (id: string, name: string) => {
    const res = await exportApi.datasetCsv(id);
    downloadBlob(res.data as Blob, `${name}.csv`);
  };

  const handleExportExcel = async (id: string, name: string) => {
    const res = await exportApi.datasetExcel(id);
    downloadBlob(res.data as Blob, `${name}.xlsx`);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Datasets</h1>
          <p className="text-dark-400 text-sm mt-1">{datasets.length} dataset{datasets.length !== 1 ? "s" : ""}</p>
        </div>
        <button className="btn-secondary flex items-center gap-2 text-sm" onClick={load}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="flex gap-1 mb-6 bg-dark-800 p-1 rounded-lg w-fit">
        {(["datasets", "upload", "sources"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t ? "bg-brand-500 text-white" : "text-dark-400 hover:text-dark-100"
            }`}
            onClick={() => setTab(t)}
          >
            {t === "datasets" ? "My Datasets" : t === "upload" ? "Upload CSV" : "Connect Source"}
          </button>
        ))}
      </div>

      {tab === "upload" && (
        <UploadZone onUploaded={(ds) => { setDatasets((p) => [ds, ...p]); setTab("datasets"); }} />
      )}

      {tab === "sources" && (
        <SourceForm onConnected={() => { setTab("datasets"); load(); }} />
      )}

      {tab === "datasets" && (
        <div className="space-y-4">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-16 card animate-pulse" />)
          ) : datasets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 card text-center">
              <Database className="w-16 h-16 text-dark-600 mb-4" />
              <p className="text-dark-400 text-lg">No datasets yet</p>
              <p className="text-dark-500 text-sm mt-1">Upload a CSV or connect an external data source</p>
              <button className="btn-primary mt-4" onClick={() => setTab("upload")}>
                <Upload className="w-4 h-4 inline mr-2" />Upload CSV
              </button>
            </div>
          ) : (
            datasets.map((ds) => (
              <div key={ds.id} className="card hover:border-dark-600 transition-all">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-dark-700 rounded-lg flex items-center justify-center">
                      <Database className="w-4 h-4 text-brand-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-dark-100">{ds.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${ds.status === "ready" ? "bg-success/20 text-success" : "bg-warning/20 text-warning"}`}>
                          {ds.status}
                        </span>
                        <span className="text-xs bg-dark-700 text-dark-400 px-2 py-0.5 rounded-full">{ds.source_type}</span>
                      </div>
                      <div className="text-sm text-dark-400 mt-0.5">
                        {formatNumber(ds.row_count, 0)} rows · {Object.keys(ds.columns.columns || {}).length} columns · {formatDate(ds.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      className="p-2 text-dark-400 hover:text-dark-100 hover:bg-dark-700 rounded-lg transition-colors"
                      onClick={() => handlePreview(ds)}
                      title="Preview"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      className="p-2 text-dark-400 hover:text-dark-100 hover:bg-dark-700 rounded-lg transition-colors"
                      onClick={() => handleExportCsv(ds.id, ds.name)}
                      title="Download CSV"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    <button
                      className="p-2 text-dark-400 hover:text-danger hover:bg-dark-700 rounded-lg transition-colors"
                      onClick={() => handleDelete(ds.id)}
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {preview?.dataset.id === ds.id && (
                  <div className="mt-4 pt-4 border-t border-dark-700">
                    {previewLoading ? (
                      <div className="animate-pulse h-32 bg-dark-700 rounded" />
                    ) : (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-dark-400">First 50 rows · {preview.data.total.toLocaleString()} total</span>
                          <ExportButton
                            onExportCsv={() => handleExportCsv(ds.id, ds.name)}
                            onExportExcel={() => handleExportExcel(ds.id, ds.name)}
                          />
                        </div>
                        <DataTable columns={preview.data.columns} rows={preview.data.rows} />
                      </>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
