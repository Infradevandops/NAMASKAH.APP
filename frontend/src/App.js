import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext';
import { useAuth } from './hooks/useAuth';
import LoadingSpinner from './components/atoms/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';
import SimpleLanding from './components/pages/SimpleLanding';
import './App.css';

function App() {
  // Simplified app without auth for now
  const loading = false;

  return (
    <ErrorBoundary>
      <NotificationProvider>
        <Router>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<SimpleLanding />} />
              <Route path="*" element={<SimpleLanding />} />
            </Routes>
        </Router>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;