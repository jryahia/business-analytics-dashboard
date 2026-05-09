import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import DashboardList from "@/pages/DashboardList";
import DashboardView from "@/pages/DashboardView";
import Datasets from "@/pages/Datasets";
import ChartBuilder from "@/pages/ChartBuilder";
import Settings from "@/pages/Settings";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore();
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const { token, fetchMe } = useAuthStore();

  useEffect(() => {
    if (token) fetchMe();
  }, [token, fetchMe]);

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboards" replace />} />
        <Route path="dashboards" element={<DashboardList />} />
        <Route path="dashboards/:id" element={<DashboardView />} />
        <Route path="datasets" element={<Datasets />} />
        <Route path="charts/new" element={<ChartBuilder />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
