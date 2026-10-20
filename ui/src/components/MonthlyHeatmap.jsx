
import React from 'react';

export const MonthlyHeatmap = ({ heatmap }) => {
    if (!heatmap) return null;

    const years = Object.keys(heatmap).sort((a, b) => b - a);
    const months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    const getColor = (value) => {
        if (value === undefined) return 'rgba(255,255,255,0.02)';
        if (value > 0) {
            const opacity = Math.min(value / 10, 1); // Cap at 10% for full green
            return `rgba(16, 185, 129, ${0.2 + opacity * 0.8})`;
        } else {
            const opacity = Math.min(Math.abs(value) / 10, 1);
            return `rgba(239, 68, 68, ${0.2 + opacity * 0.8})`;
        }
    };

    return (
        <div className="card" style={{ overflowX: 'auto' }}>
            <h3>Monthly Returns</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                <thead>
                    <tr>
                        <th style={{ textAlign: 'left', padding: '8px', color: '#94a3b8' }}>Year</th>
                        {monthNames.map(m => <th key={m} style={{ padding: '8px', color: '#94a3b8' }}>{m}</th>)}
                        <th style={{ padding: '8px', color: '#f8fafc' }}>Tot</th>
                    </tr>
                </thead>
                <tbody>
                    {years.map(year => {
                        let total = 0;
                        return (
                            <tr key={year} style={{ borderBottom: '1px solid rgba(148,163,184,0.1)' }}>
                                <td style={{ padding: '8px', fontWeight: 'bold' }}>{year}</td>
                                {months.map(m => {
                                    const val = heatmap[year][m];
                                    if (val !== undefined) total += val;
                                    return (
                                        <td key={m} style={{
                                            padding: '8px',
                                            textAlign: 'center',
                                            backgroundColor: getColor(val),
                                            color: val ? '#fff' : 'transparent',
                                            borderRadius: '4px'
                                        }}>
                                            {val ? val.toFixed(1) + '%' : '-'}
                                        </td>
                                    );
                                })}
                                <td style={{ padding: '8px', textAlign: 'center', fontWeight: 'bold', color: total >= 0 ? '#10b981' : '#ef4444' }}>
                                    {total.toFixed(1)}%
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
