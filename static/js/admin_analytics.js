// Admin Dashboard Analytics - Powered by Chart.js
document.addEventListener('DOMContentLoaded', function() {
    if (!window.ADMIN_DATA || !window.ADMIN_DATA.details) {
        console.warn("Admin analytics data missing or incomplete.");
        return;
    }
    
    const { trend, details } = window.ADMIN_DATA;
    
    // Global Chart.js Defaults for Dark Theme
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = '#1e293b';
    Chart.defaults.plugins.tooltip.titleColor = '#fff';
    Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                    drawBorder: false
                },
                ticks: {
                    font: { size: 11 }
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: { size: 11 }
                }
            }
        }
    };

    // 1. Attendance Breakdown (Donut)
    const ctxDonut = document.getElementById('chart-att-dist');
    if (ctxDonut) {
        const stats = details.dist_donut || { data: [0, 0, 0], labels: ['Present', 'Absent', 'On Leave'] };
        new Chart(ctxDonut, {
            type: 'doughnut',
            data: {
                labels: stats.labels,
                datasets: [{
                    data: stats.data,
                    backgroundColor: ['#10b981', '#ef4444', '#8b5cf6'],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    // 2. Weekly Attendance (Bar)
    const ctxWeekly = document.getElementById('chart-weekly-att');
    if (ctxWeekly && details.weekly_att) {
        new Chart(ctxWeekly, {
            type: 'bar',
            data: {
                labels: details.weekly_att.labels,
                datasets: [{
                    label: 'PresentCount',
                    data: details.weekly_att.data,
                    backgroundColor: '#6366f1',
                    borderRadius: 6,
                    barThickness: 20
                }]
            },
            options: commonOptions
        });
    }

    // 3. Weekly Late Arrivals (Line)
    const ctxLate = document.getElementById('chart-late-trend');
    if (ctxLate && details.weekly_late) {
        new Chart(ctxLate, {
            type: 'line',
            data: {
                labels: details.weekly_late.labels,
                datasets: [{
                    label: 'Late Arrivals',
                    data: details.weekly_late.data,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#f59e0b',
                    pointBorderColor: '#1e293b',
                    pointBorderWidth: 2
                }]
            },
            options: commonOptions
        });
    }

    // 4. Total Working Hours (Horizontal Bar)
    const ctxHours = document.getElementById('chart-working-hours');
    if (ctxHours && details.avg_hours_analytics) {
        new Chart(ctxHours, {
            type: 'bar',
            data: {
                labels: details.avg_hours_analytics.labels,
                datasets: [{
                    label: 'Total Hours',
                    data: details.avg_hours_analytics.data,
                    backgroundColor: '#8b5cf6',
                    borderRadius: 4,
                    barThickness: 15
                }]
            },
            options: {
                ...commonOptions,
                indexAxis: 'y',
                scales: {
                    ...commonOptions.scales,
                    x: {
                        ...commonOptions.scales.y,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        ...commonOptions.scales.x,
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // 5. Leave Distribution (Bar)
    const ctxLeave = document.getElementById('chart-leave-dist');
    if (ctxLeave && details.leave_type_analytics) {
        new Chart(ctxLeave, {
            type: 'bar',
            data: {
                labels: details.leave_type_analytics.labels,
                datasets: [{
                    label: 'Total Days',
                    data: details.leave_type_analytics.data,
                    backgroundColor: '#ec4899',
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: commonOptions
        });
    }
});
