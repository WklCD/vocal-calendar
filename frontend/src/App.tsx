import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import AuthGuard from './features/auth/AuthGuard';
import CalendarPage from './features/calendar/CalendarPage';
import VoiceHistory from './features/voice/VoiceHistory';
import PublicCalendar from './features/share/PublicCalendar';

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
              <CalendarPage />
            </AuthGuard>
          }
        />
        <Route
          path="/voice-history"
          element={
            <AuthGuard>
              <VoiceHistory />
            </AuthGuard>
          }
        />
        <Route path="/shared/:token" element={<PublicCalendar />} />
        <Route path="/" element={<Navigate to="/calendar" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
