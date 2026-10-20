
import React from 'react';
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

export const MonteCarlo = ({ data }) => {
    if (!data || !data.scenarios || data.scenarios.length === 0) return null;

    // data.scenarios is list of lists
    // Only plot first 20 for performance
    const scenarios = data.scenarios.slice(0, 20);

    // Create datasets
    const datasets = scenarios.map((scenario, i) => ({
        label: `Sim ${i + 1}`,
        data: scenario,
        borderColor: 'rgba(59, 130, 246, 0.2)',
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.1,
        fill: false
    }));

    const chartData = {
        labels: scenarios[0].map((_, i) => i), // Trade number 1..N
        datasets: datasets
    };

    const options = {
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: true, text: 'Monte Carlo Simulation (20 runs)', color: '#94a3b8' }
        },
        scales: {
            x: {
                title: { display: true, text: 'Trade Count', color: '#94a3b8' },
                grid: { color: 'rgba(255,255,255,0.05)' }
            },
            y: {
                title: { display: true, text: 'Equity', color: '#94a3b8' },
                grid: { color: 'rgba(255,255,255,0.05)' }
            }
        }
    };

    return (
        <div className="card">
            <h3>Risk Analysis (Monte Carlo)</h3>
            <div style={{ height: '300px' }}>
                <Line data={chartData} options={options} />
            </div>
            <div style={{ marginTop: '1rem', color: '#94a3b8', fontSize: '0.9rem' }}>
                Shuffling trade sequence to analyze potential drawdown paths.
            </div>
        </div>
    );
};
