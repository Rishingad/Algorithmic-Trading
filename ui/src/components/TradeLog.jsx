
import React from 'react';

export const TradeLog = ({ trades }) => {
    if (!trades || trades.length === 0) return null;

    // Sort by exit time descending
    const sortedTrades = [...trades].sort((a, b) => new Date(b.exit_time) - new Date(a.exit_time));

    return (
        <div className="card">
            <h3>Trade Log</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead style={{ position: 'sticky', top: 0, background: '#1e293b' }}>
                        <tr>
                            <th style={{ padding: '8px', textAlign: 'left', color: '#94a3b8' }}>Entry Time</th>
                            <th style={{ padding: '8px', textAlign: 'left', color: '#94a3b8' }}>Type</th>
                            <th style={{ padding: '8px', textAlign: 'right', color: '#94a3b8' }}>Price</th>
                            <th style={{ padding: '8px', textAlign: 'right', color: '#94a3b8' }}>Exit Price</th>
                            <th style={{ padding: '8px', textAlign: 'right', color: '#94a3b8' }}>PnL</th>
                            <th style={{ padding: '8px', textAlign: 'right', color: '#94a3b8' }}>ROI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedTrades.map((t, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                <td style={{ padding: '8px' }}>{t.entry_time ? new Date(t.entry_time).toLocaleString() : '-'}</td>
                                <td style={{ padding: '8px', color: t.size > 0 ? '#10b981' : '#ef4444' }}>
                                    {t.size > 0 ? 'LONG' : 'SHORT'}
                                </td>
                                <td style={{ padding: '8px', textAlign: 'right' }}>{t.entry_price != null ? t.entry_price.toFixed(2) : '-'}</td>
                                <td style={{ padding: '8px', textAlign: 'right' }}>{t.exit_price != null ? t.exit_price.toFixed(2) : '-'}</td>
                                <td style={{ padding: '8px', textAlign: 'right', color: (t.pnl || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                    {t.pnl != null ? `$${t.pnl.toFixed(2)}` : '-'}
                                </td>
                                <td style={{ padding: '8px', textAlign: 'right', color: (t.roi || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                                    {t.roi != null ? `${t.roi.toFixed(2)}%` : '-'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
