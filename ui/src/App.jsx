
import React, { useState } from 'react';
import DataDownloader from './components/DataDownloader';
import Backtester from './components/Backtester';

function App() {
  const [activeTab, setActiveTab] = useState('data');
  const [theme, setTheme] = useState('dark');

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          AlgoBacktest
        </div>

        <nav className="nav-links">
          <button
            className={`nav-item ${activeTab === 'data' ? 'active' : ''}`}
            onClick={() => setActiveTab('data')}
          >
            Data Downloader
          </button>
          <button
            className={`nav-item ${activeTab === 'backtest' ? 'active' : ''}`}
            onClick={() => setActiveTab('backtest')}
          >
            Backtest Strategy
          </button>
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <button
            onClick={toggleTheme}
            className="nav-item"
            style={{ justifyContent: 'center', border: '1px solid var(--border-color)' }}
          >
            {theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">
            {activeTab === 'data' ? 'Data Management' : 'Strategy Backtesting'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            {activeTab === 'data'
              ? 'Download and manage historical market data for your simulations.'
              : 'Run simulations on historical data to evaluate strategy performance.'}
          </p>
        </div>

        {activeTab === 'data' && <DataDownloader />}
        {activeTab === 'backtest' && <Backtester />}
      </main>
    </div>
  );
}

export default App;
