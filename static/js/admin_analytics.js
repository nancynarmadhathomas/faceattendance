/**
 * Admin Analytics — Chart.js Implementation
 * Mixed Bar (Present) + Line (Trend) Chart
 */

let analyticsChart = null;

async function loadAnalytics() {
    const range = document.getElementById('analytics-range').value;
    const ctx   = document.getElementById('analyticsChart')?.getContext('2d');
    if (!ctx) return;

    try {
        const response = await fetch(`/api/admin/analytics?range=${range}`);
        const data     = await response.json();

        if (analyticsChart) {
            analyticsChart.destroy();
        }

        // --- Premium Gradient for Bar ---
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(79, 70, 229, 0.8)');
        gradient.addColorStop(1, 'rgba(79, 70, 229, 0.2)');

        const config = {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        type: 'bar',
                        label: 'Present Employees',
                        data: data.present,
                        backgroundColor: gradient,
                        borderColor: '#4f46e5',
                        borderWidth: 1,
                        borderRadius: 8,
                        barThickness: range === 'today' ? 32 : 18,
                        order: 2
                    },
                    {
                        type: 'line',
                        label: 'Attendance Trend',
                        data: data.present.map((v, i) => v + (data.late[i] || 0)), // Combined Trend
                        borderColor: '#6366f1',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#fff',
                        tension: 0.45,
                        fill: false,
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            usePointStyle: true,
                            font: { family: 'Inter', size: 12, weight: '500' },
                            padding: 20
                        }
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(19, 25, 41, 0.85)',
                        backdropFilter: 'blur(10px)',
                        padding: 14,
                        titleFont: { size: 13, weight: '700' },
                        bodyFont: { size: 12 },
                        cornerRadius: 12,
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y + ' Persons';
                                }
                                return label;
                            },
                            footer: (items) => {
                                // Add a premium note footer for the trend
                                return 'Total Engagement: ' + (items[1]?.parsed.y || items[0]?.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { size: 11, family: 'Inter' },
                            color: '#94a3b8'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255,255,255,0.03)',
                            drawBorder: false
                        },
                        ticks: {
                            stepSize: 1,
                            font: { size: 11, family: 'Inter' },
                            color: '#94a3b8'
                        }
                    }
                }
            }
        };

        analyticsChart = new Chart(ctx, config);

    } catch (error) {
        console.error('Error loading analytics:', error);
        const container = document.getElementById('chart-main');
        if (container) {
            container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--danger);font-size:0.9rem">Analytics load failed</div>';
        }
    }
}

// Ensure first load
document.addEventListener('DOMContentLoaded', () => {
    loadAnalytics();
});
