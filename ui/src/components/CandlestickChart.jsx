
import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

export const CandlestickChart = ({ data, markers }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef();

    useEffect(() => {
        if (!data || data.length === 0) return;

        const handleResize = () => {
            if (chartRef.current) {
                chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { color: '#0f172a' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: 'rgba(148, 163, 184, 0.1)' },
                horzLines: { color: 'rgba(148, 163, 184, 0.1)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 400,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
            }
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        // Ensure data is sorted by time and has no duplicates
        const sortedData = [...data].sort((a, b) => a.time - b.time);
        const uniqueData = [];
        let lastTime = null;
        for (const item of sortedData) {
            if (item.time !== lastTime) {
                uniqueData.push(item);
                lastTime = item.time;
            }
        }
        candlestickSeries.setData(uniqueData);

        // Convert round-trip trades into markers
        // We have entry (buy/sell) and exit (sell/buy)
        // Let's deduce based on round-trip data
        // Actually, we need a flat list of markers.
        // data props: ohlcv array.
        // markers props: round_trips array.

        const chartMarkers = [];
        markers.forEach(rt => {
            const entryTime = new Date(rt.entry_time).getTime() / 1000;
            const exitTime = new Date(rt.exit_time).getTime() / 1000;

            if (!isNaN(entryTime)) {
                chartMarkers.push({
                    time: entryTime,
                    position: rt.size > 0 ? 'belowBar' : 'aboveBar',
                    color: rt.size > 0 ? '#10b981' : '#ef4444',
                    shape: rt.size > 0 ? 'arrowUp' : 'arrowDown',
                    text: 'Entry'
                });
            }
            if (!isNaN(exitTime)) {
                chartMarkers.push({
                    time: exitTime,
                    position: rt.size > 0 ? 'aboveBar' : 'belowBar',
                    color: rt.size > 0 ? '#ef4444' : '#10b981',
                    shape: rt.size > 0 ? 'arrowDown' : 'arrowUp',
                    text: 'Exit'
                });
            }
        });

        // Markers must be sorted by time
        chartMarkers.sort((a, b) => a.time - b.time);

        candlestickSeries.setMarkers(chartMarkers);

        chartRef.current = chart;

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [data, markers]);

    return <div ref={chartContainerRef} style={{ position: 'relative' }} />;
};
