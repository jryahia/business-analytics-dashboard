import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, LayoutDashboard, Copy, Trash2, ChevronRight } from "lucide-react";
import { useDashboardStore } from "@/store/dashboardStore";
import { dashboardsApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function DashboardList() {
  const { dashboards, fetchDashboards, deleteDashboard, duplicateDashboard, isLoading } = useDashboardStore();
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    fetchDashboards();
  }, [fetchDashboards]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const res = await dashboardsApi.create({ name: newName.trim() });
      setShowCreate(false);
      setNewName("");
      navigate(`/dashboards/${res.data.id}`);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this dashboard?")) return;
    await deleteDashboard(id);
  };

  const handleDuplicate = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const clone = await duplicateDashboard(id);
    navigate(`/dashboards/${clone.id}`);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Dashboards</h1>
          <p className="text-dark-400 text-sm mt-1">{dashboards.length} dashboard{dashboards.length !== 1 ? "s" : ""}</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" /> New Dashboard
        </button>
      </div>

      {showCreate && (
        <div className="card mb-6 border-brand-500/30">
          <h3 className="font-semibold text-dark-100 mb-3">Create Dashboard</h3>
          <div className="flex gap-2">
            <input
              className="input"
              placeholder="Dashboard name..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              autoFocus
            />
            <button className="btn-primary whitespace-nowrap" onClick={handleCreate} disabled={creating}>
              {creating ? "Creating..." : "Create"}
            </button>
            <button className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse h-36 bg-dark-800" />
          ))}
        </div>
      ) : dashboards.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <LayoutDashboard className="w-16 h-16 text-dark-600 mb-4" />
          <p className="text-dark-400 text-lg">No dashboards yet</p>
          <p className="text-dark-500 text-sm mt-1">Create your first dashboard to get started</p>
          <button className="btn-primary mt-4" onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4 inline mr-2" />Create Dashboard
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((d) => (
            <div
              key={d.id}
              className="card cursor-pointer hover:border-brand-500/50 hover:bg-dark-750 transition-all group"
              onClick={() => navigate(`/dashboards/${d.id}`)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-brand-500/20 rounded-lg flex items-center justify-center">
                    <LayoutDashboard className="w-4 h-4 text-brand-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-dark-100 group-hover:text-brand-400 transition-colors">{d.name}</h3>
                    <p className="text-xs text-dark-500">{d.charts.length} chart{d.charts.length !== 1 ? "s" : ""}</p>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    className="p-1.5 text-dark-400 hover:text-dark-100 hover:bg-dark-700 rounded"
                    onClick={(e) => handleDuplicate(d.id, e)}
                    title="Duplicate"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                  <button
                    className="p-1.5 text-dark-400 hover:text-danger hover:bg-dark-700 rounded"
                    onClick={(e) => handleDelete(d.id, e)}
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              {d.description && <p className="text-dark-400 text-sm mb-3 line-clamp-2">{d.description}</p>}
              <div className="flex items-center justify-between text-xs text-dark-500 mt-auto pt-3 border-t border-dark-700">
                <span>Updated {formatDate(d.updated_at)}</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
