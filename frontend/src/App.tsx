import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { ManuscriptForm } from './pages/ManuscriptForm';
import { ManuscriptDetail } from './pages/ManuscriptDetail';
import { Ebooks } from './pages/Ebooks';
import { Genres } from './pages/Genres';
import { Tags } from './pages/Tags';
import { Profile } from './pages/Profile';

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/manuscripts/new"
          element={
            <ProtectedRoute>
              <ManuscriptForm />
            </ProtectedRoute>
          }
        />
        <Route
          path="/manuscripts/:id"
          element={
            <ProtectedRoute>
              <ManuscriptDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ebooks"
          element={
            <ProtectedRoute>
              <Ebooks />
            </ProtectedRoute>
          }
        />

        <Route path="/genres" element={<Genres />} />

        <Route
          path="/tags"
          element={
            <ProtectedRoute>
              <Tags />
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
