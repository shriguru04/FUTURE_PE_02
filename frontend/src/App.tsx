import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppLayout } from './layouts/AppLayout'
import AnalyticsPage from './pages/AnalyticsPage'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import BrandsPage from './pages/BrandsPage'
import CampaignDetail from './pages/CampaignDetail'
import CampaignsPage from './pages/CampaignsPage'
import CampaignWizard from './pages/CampaignWizard'
import Dashboard from './pages/Dashboard'
import EditorPage from './pages/EditorPage'
import ExportPage from './pages/ExportPage'
import GeneratePage from './pages/GeneratePage'
import Landing from './pages/Landing'
import ProductsPage from './pages/ProductsPage'
import SettingsPage from './pages/SettingsPage'
import VersionsPage from './pages/VersionsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="brands" element={<BrandsPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="campaigns" element={<CampaignsPage />} />
          <Route path="campaigns/new" element={<CampaignWizard />} />
          <Route path="campaigns/:id" element={<CampaignDetail />} />
          <Route path="campaigns/:id/generate" element={<GeneratePage />} />
          <Route path="campaigns/:id/editor" element={<EditorPage />} />
          <Route path="campaigns/:id/versions" element={<VersionsPage />} />
          <Route path="campaigns/:id/export" element={<ExportPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
