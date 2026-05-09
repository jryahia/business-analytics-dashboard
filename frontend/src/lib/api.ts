import axios, { AxiosInstance } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "";

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  register: (email: string, password: string, name: string) =>
    api.post<TokenResponse>("/api/auth/register", { email, password, name }),
  login: (email: string, password: string) =>
    api.post<TokenResponse>("/api/auth/login", { email, password }),
  me: () => api.get<User>("/api/auth/me"),
};

// ── Datasets ──────────────────────────────────────────────────────────────────

export interface Dataset {
  id: string;
  name: string;
  source_type: string;
  table_name: string;
  columns: { columns: Record<string, string>; names: string[] };
  row_count: number;
  status: string;
  created_at: string;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
  total: number;
}

export const datasetsApi = {
  list: () => api.get<Dataset[]>("/api/datasets"),
  get: (id: string) => api.get<Dataset>(`/api/datasets/${id}`),
  preview: (id: string) => api.get<DatasetPreview>(`/api/datasets/${id}/preview`),
  delete: (id: string) => api.delete(`/api/datasets/${id}`),
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<{ id: string; name: string; row_count: number }>("/api/datasets/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
  },
};

// ── DataSources ───────────────────────────────────────────────────────────────

export interface DataSource {
  id: string;
  name: string;
  source_type: string;
  created_at: string;
}

export interface DataSourceCreatePayload {
  name: string;
  source_type: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  filepath?: string;
}

export const datasourcesApi = {
  list: () => api.get<DataSource[]>("/api/datasources"),
  create: (payload: DataSourceCreatePayload) => api.post<DataSource>("/api/datasources", payload),
  sync: (id: string, table_name: string) =>
    api.post<{ id: string; name: string; row_count: number }>(`/api/datasources/${id}/sync?table_name=${table_name}`),
  delete: (id: string) => api.delete(`/api/datasources/${id}`),
};

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface AnalyticsResult {
  data: Record<string, unknown>[];
  columns: string[];
  metadata: Record<string, unknown>;
}

export const analyticsApi = {
  aggregate: (payload: {
    dataset_id: string;
    group_by: string[];
    aggregations: Record<string, string>;
    filters?: Record<string, unknown>;
  }) => api.post<AnalyticsResult>("/api/analytics/aggregate", payload),

  pivot: (payload: {
    dataset_id: string;
    index: string;
    columns: string;
    values: string;
    aggfunc?: string;
  }) => api.post<AnalyticsResult>("/api/analytics/pivot", payload),

  timeseries: (payload: {
    dataset_id: string;
    date_column: string;
    value_column: string;
    frequency?: string;
    aggregation?: string;
  }) => api.post<AnalyticsResult>("/api/analytics/timeseries", payload),

  custom: (payload: { dataset_id: string; expression: string }) =>
    api.post<AnalyticsResult>("/api/analytics/custom", payload),
};

// ── Charts ────────────────────────────────────────────────────────────────────

export interface Chart {
  id: string;
  title: string;
  chart_type: string;
  dataset_id: string;
  dashboard_id: string | null;
  config: Record<string, unknown>;
  plotly_json: Record<string, unknown>;
  created_at: string;
}

export interface ChartGeneratePayload {
  dataset_id: string;
  chart_type: string;
  x_column: string;
  y_column: string;
  title?: string;
  color_column?: string;
  aggregation?: string;
  dashboard_id?: string;
}

export const chartsApi = {
  generate: (payload: ChartGeneratePayload) => api.post<Chart>("/api/charts/generate", payload),
  get: (id: string) => api.get<Chart>(`/api/charts/${id}`),
};

// ── Dashboards ────────────────────────────────────────────────────────────────

export interface Dashboard {
  id: string;
  name: string;
  description: string;
  layout: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  charts: Chart[];
}

export const dashboardsApi = {
  list: () => api.get<Dashboard[]>("/api/dashboards"),
  get: (id: string) => api.get<Dashboard>(`/api/dashboards/${id}`),
  create: (payload: { name: string; description?: string; layout?: Record<string, unknown> }) =>
    api.post<Dashboard>("/api/dashboards", payload),
  update: (id: string, payload: { name?: string; description?: string; layout?: Record<string, unknown> }) =>
    api.put<Dashboard>(`/api/dashboards/${id}`, payload),
  delete: (id: string) => api.delete(`/api/dashboards/${id}`),
  duplicate: (id: string) => api.post<Dashboard>(`/api/dashboards/${id}/duplicate`),
};

// ── Insights ──────────────────────────────────────────────────────────────────

export interface Insight {
  id: string;
  dataset_id: string;
  content: {
    insights: string[];
    summary: string;
    recommendations?: string[];
  };
  created_at: string;
}

export const insightsApi = {
  generate: (payload: { dataset_id?: string; dashboard_id?: string; regenerate?: boolean }) =>
    api.post<Insight>("/api/insights/generate", payload),
  get: (dataset_id: string) => api.get<Insight>(`/api/insights/${dataset_id}`),
};

// ── Export ────────────────────────────────────────────────────────────────────

export const exportApi = {
  dashboardPdf: (dashboard_id: string) =>
    api.get(`/api/export/dashboard/${dashboard_id}/pdf`, { responseType: "blob" }),
  datasetExcel: (dataset_id: string) =>
    api.get(`/api/export/dataset/${dataset_id}/excel`, { responseType: "blob" }),
  datasetCsv: (dataset_id: string) =>
    api.get(`/api/export/dataset/${dataset_id}/csv`, { responseType: "blob" }),
};

export default api;
