import { create } from "zustand";
import { dashboardsApi, datasetsApi, type Dashboard, type Dataset } from "@/lib/api";

interface DashboardState {
  dashboards: Dashboard[];
  currentDashboard: Dashboard | null;
  datasets: Dataset[];
  isLoading: boolean;
  fetchDashboards: () => Promise<void>;
  fetchDashboard: (id: string) => Promise<void>;
  fetchDatasets: () => Promise<void>;
  deleteDashboard: (id: string) => Promise<void>;
  duplicateDashboard: (id: string) => Promise<Dashboard>;
}

export const useDashboardStore = create<DashboardState>()((set, get) => ({
  dashboards: [],
  currentDashboard: null,
  datasets: [],
  isLoading: false,

  fetchDashboards: async () => {
    set({ isLoading: true });
    try {
      const res = await dashboardsApi.list();
      set({ dashboards: res.data });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchDashboard: async (id) => {
    set({ isLoading: true });
    try {
      const res = await dashboardsApi.get(id);
      set({ currentDashboard: res.data });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchDatasets: async () => {
    const res = await datasetsApi.list();
    set({ datasets: res.data });
  },

  deleteDashboard: async (id) => {
    await dashboardsApi.delete(id);
    set((s) => ({ dashboards: s.dashboards.filter((d) => d.id !== id) }));
  },

  duplicateDashboard: async (id) => {
    const res = await dashboardsApi.duplicate(id);
    set((s) => ({ dashboards: [res.data, ...s.dashboards] }));
    return res.data;
  },
}));
