import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import AuthGuard from './features/auth/AuthGuard';

function CalendarPlaceholder() {
  return <div style={{ padding: '2rem' }}><h1>日历页面 — 即将实现</h1></div>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/calendar"
          element={
            <AuthGuard>
              <CalendarPlaceholder />
            </AuthGuard>
          }
        />
        <Route path="/" element={<Navigate to="/calendar" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
