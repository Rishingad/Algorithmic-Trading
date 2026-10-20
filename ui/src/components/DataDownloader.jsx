
import React, { useState } from 'react';
import axios from 'axios';

const DataDownloader = () => {
    const [symbol, setSymbol] = useState('BTCUSDT');
    const [interval, setInterval] = useState('5m');
    const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const handleDownload = async () => {
        setLoading(true);
        setMessage('');
        try {
            const response = await axios.post('http://localhost:8000/api/download', {
                symbol,
                interval,
                start_date: startDate
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            setMessage(response.data.message);
        } catch (error) {
            setMessage('Error: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <h2 style={{ marginTop: 0 }}>Download Historical Data</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Fetch historical OHLCV data from Binance for backtesting.
            </p>

            <div className="grid-2">
                <div className="form-group">
                    <label>Symbol</label>
                    <input
                        type="text"
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                        placeholder="e.g. BTCUSDT"
                    />
                </div>
                <div className="form-group">
                    <label>Interval</label>
                    <select value={interval} onChange={(e) => setInterval(e.target.value)}>
                        <option value="1m">1 Minute</option>
                        <option value="5m">5 Minutes</option>
                        <option value="15m">15 Minutes</option>
                        <option value="1h">1 Hour</option>
                        <option value="4h">4 Hours</option>
                        <option value="1d">1 Day</option>
                    </select>
                </div>
            </div>

            <div className="form-group">
                <label>Start From</label>
                <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                />
            </div>

            <button className="btn-primary" onClick={handleDownload} disabled={loading}>
                {loading ? 'Downloading Data...' : 'Download Data'}
            </button>

            {message && (
                <div style={{
                    marginTop: '1.5rem',
                    padding: '1rem',
                    borderRadius: '8px',
                    backgroundColor: message.includes('Error') ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                    border: message.includes('Error') ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(16, 185, 129, 0.2)',
                    color: message.includes('Error') ? '#fca5a5' : '#6ee7b7'
                }}>
                    {message}
                </div>
            )}
        </div>
    );
};

export default DataDownloader;
