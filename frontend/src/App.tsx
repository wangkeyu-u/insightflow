import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

const DashboardLayout = lazy(() => import("@/layouts/DashboardLayout"));
const Login = lazy(() => import("@/pages/Login"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Orders = lazy(() => import("@/pages/Orders"));
const Customers = lazy(() => import("@/pages/Customers"));
const Products = lazy(() => import("@/pages/Products"));
const Inventory = lazy(() => import("@/pages/Inventory"));
const Analytics = lazy(() => import("@/pages/Analytics"));
const AIAssistant = lazy(() => import("@/pages/AIAssistant"));
const Reports = lazy(() => import("@/pages/Reports"));
const AdminUsers = lazy(() => import("@/pages/AdminUsers"));
const AuditLogs = lazy(() => import("@/pages/AuditLogs"));

function PageFallback() {
  return (
    <div className="flex min-h-64 items-center justify-center" role="status">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
      <span className="sr-only">Loading page</span>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/products" element={<Products />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/ai-assistant" element={<AIAssistant />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/audit-logs" element={<AuditLogs />} />
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
