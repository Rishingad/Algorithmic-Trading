
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CandlestickChart } from './CandlestickChart';
import { MonthlyHeatmap } from './MonthlyHeatmap';
import { TradeLog } from './TradeLog';
import { MonteCarlo } from './MonteCarlo';

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const Backtester = () => {
    const [files, setFiles] = useState([]);
    const [strategies, setStrategies] = useState([]);
    const [selectedFile, setSelectedFile] = useState('');
    const [selectedStrategy, setSelectedStrategy] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const filesRes = await axios.get('http://localhost:8000/api/files');
                setFiles(filesRes.data.files);
                if (filesRes.data.files.length > 0) setSelectedFile(filesRes.data.files[0]);

                const strategiesRes = await axios.get('http://localhost:8000/api/strategies');
                setStrategies(strategiesRes.data.strategies);
                if (strategiesRes.data.strategies.length > 0) setSelectedStrategy(strategiesRes.data.strategies[0]);
            } catch (err) {
                console.error("Failed to load options", err);
            }
        };
        fetchData();
    }, []);

    const handleRun = async () => {
        setLoading(true);
        setError('');
        setResults(null);
        try {
            const response = await axios.post('http://localhost:8000/api/backtest', {
                strategy_name: selectedStrategy,
                data_file: selectedFile
            });
            setResults(response.data);
        } catch (err) {
            setError('Error: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const equityChartData = {
        labels: results?.equity_curve?.map(d => d.time) || [],
        datasets: [
            {
                label: 'Equity Curve',
                data: results?.equity_curve?.map(d => d.value) || [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1,
                fill: true
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: true, text: 'Equity Curve', color: '#94a3b8' }
        },
        scales: {
            x: { ticks: { maxTicksLimit: 10, color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        },
        interaction: { mode: 'index', intersect: false }
    };

    // Helper to get simple metrics for top cards
    const getMetric = (key) => {
        if (!results?.metrics || typeof results.metrics !== 'object') return '-';
        return results.metrics[key];
    }

    const displayMetric = (val, isPct = false) => {
        if (val === undefined || val === null) return '-';
        if (typeof val !== 'number') return val;
        return isPct ? (val * 100).toFixed(2) + '%' : val.toFixed(2);
    }

    // Winrate is already multiplied by 100 in backend
    const displayWinRate = (val) => {
        if (val === undefined || val === null) return '-';
        return val.toFixed(2) + '%';
    }

    return (
        <div>
            <div className="card">
                <h2 style={{ marginTop: 0 }}>Run Backtest</h2>
                <div className="grid-2">
                    <div className="form-group">
                        <label>Data File</label>
                        {files.length > 0 ? (
                            <select value={selectedFile} onChange={(e) => setSelectedFile(e.target.value)}>
                                {files.map(f => <option key={f} value={f}>{f}</option>)}
                            </select>
                        ) : (
                            <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', color: '#fca5a5' }}>
                                No CSV files found. Go to 'Data Downloader' tab.
                            </div>
                        )}
                    </div>
                    <div className="form-group">
                        <label>Strategy</label>
                        {strategies.length > 0 ? (
                            <select value={selectedStrategy} onChange={(e) => setSelectedStrategy(e.target.value)}>
                                {strategies.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        ) : (
                            <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', color: '#fca5a5' }}>
                                No strategies found.
                            </div>
                        )}
                    </div>
                </div>
                <button className="btn-primary" onClick={handleRun} disabled={loading}>
                    {loading ? 'Running...' : 'Run Backtest'}
                </button>
                {error && <div style={{ marginTop: '1rem', color: '#fca5a5' }}>{error}</div>}
            </div>

            {results && (
                <div className="results-container">
                    {/* Top Metrics Cards */}
                    <div className="grid-3" style={{ marginBottom: '2rem' }}>
                        <div className="metric-card">
                            <div className="metric-label">Total Return</div>
                            <div className="metric-value" style={{ color: getMetric('total_return') >= 0 ? '#10b981' : '#ef4444' }}>
                                {displayMetric(getMetric('total_return'), true)}
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">Sharpe Ratio</div>
                            <div className="metric-value">{displayMetric(getMetric('sharpe_ratio'))}</div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">Max Drawdown</div>
                            <div className="metric-value" style={{ color: '#ef4444' }}>
                                {displayMetric(getMetric('max_drawdown'), true)}
                            </div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-label">Win Rate</div>
                            <div className="metric-value">{displayWinRate(getMetric('win_rate'))}</div>
                        </div>
                    </div>

                    {/* Chart Section */}
                    <div className="card">
                        <h3>Strategy Performance</h3>
                        <div style={{ height: '350px' }}>
                            <Line data={equityChartData} options={chartOptions} />
                        </div>
                    </div>

                    {/* Candlestick Chart Removed due to stability issues */}

                    {/* Heatmap & Monte Carlo */}
                    <div className="grid-2">
                        <MonthlyHeatmap heatmap={results.metrics?.monthly_heatmap} />
                        <MonteCarlo data={results.metrics?.monte_carlo} />
                    </div>

                    {/* Trade Log */}
                    <TradeLog trades={results.metrics?.round_trips} />
                </div>
            )}
        </div>
    );
};

export default Backtester;
