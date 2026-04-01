// Admin Dashboard Analytics - Powered by ApexCharts
document.addEventListener('DOMContentLoaded', function() {
    if (!window.ADMIN_DATA || !window.ADMIN_DATA.details) {
        console.warn("Admin analytics data missing or incomplete.");
        return;
    }
    
    const { trend, details } = window.ADMIN_DATA;
    const todayIdx = (new Date().getDay() + 6) % 7; // 0=Mon, ..., 6=Sun
    const totalEmployees = details.dist_donut.data.reduce((a, b) => a + b, 0);

    const commonOptions = {
        chart: { 
            foreColor: '#94a3b8', 
            toolbar: { show: false }, 
            background: 'transparent',
            fontFamily: 'Inter, sans-serif'
        },
        theme: { mode: 'dark' },
        grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
        stroke: { width: 3, curve: 'smooth' }
    };

    // 1. Attendance Breakdown (Donut)
    // Map: Present, Late, Absent, On Leave
    if (document.querySelector("#chart-att-dist")) {
        const stats = details.dist_donut || { data: [0,0,0], labels: ['Present', 'Absent', 'On Leave'] };
        new ApexCharts(document.querySelector("#chart-att-dist"), {
            ...commonOptions,
            series: stats.data, 
            labels: stats.labels,
            chart: { ...commonOptions.chart, type: 'donut', height: 300 },
            colors: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
            stroke: { show: false },
            legend: { position: 'bottom' },
            plotOptions: { 
                pie: { 
                    donut: { 
                        size: '75%', 
                        labels: { 
                            show: true, 
                            total: { 
                                show: true, 
                                label: 'Total', 
                                color: '#94a3b8',
                                fontSize: '14px',
                                formatter: (w) => {
                                    return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                }
                            } 
                        } 
                    } 
                } 
            }
        }).render();
    }

    // 2. Weekly Attendance (Present Employees)
    if (document.querySelector("#chart-monthly-trend") && details.weekly_att) {
        const attColors = Array(7).fill('#6366f1');
        attColors[todayIdx] = '#4f46e5'; // Highlight Today

        new ApexCharts(document.querySelector("#chart-monthly-trend"), {
            ...commonOptions,
            series: [{ name: 'Present', data: details.weekly_att.data }],
            chart: { ...commonOptions.chart, type: 'bar', height: 300 },
            colors: attColors,
            plotOptions: { 
                bar: { 
                    borderRadius: 6, 
                    columnWidth: '25%', 
                    distributed: true 
                } 
            },
            xaxis: { 
                categories: details.weekly_att.labels, 
                axisBorder: { show: false } 
            },
            yaxis: { 
                min: 0,
                max: totalEmployees,
                tickAmount: totalEmployees,
                forceNiceScale: true,
                decimalsInFloat: 0,
                title: { 
                    text: 'Employee Count',
                    style: { color: '#64748b' }
                },
                labels: {
                    formatter: (val) => Math.floor(val)
                }
            },
            legend: { show: false }
        }).render();
    }

    // 3. Weekly Late Arrivals (Area)
    if (document.querySelector("#chart-late-trend") && details.weekly_late) {
        new ApexCharts(document.querySelector("#chart-late-trend"), {
            ...commonOptions,
            series: [{ name: 'Late Arrivals', data: details.weekly_late.data }],
            chart: { ...commonOptions.chart, type: 'area', height: 250 },
            colors: ['#f59e0b'],
            stroke: { curve: 'smooth', width: 3 },
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.45,
                    opacityTo: 0.05,
                    stops: [20, 100]
                }
            },
            markers: {
                size: 5,
                colors: ['#f59e0b'],
                strokeColors: '#1e293b',
                strokeWidth: 2,
                hover: { size: 7 },
                discrete: [{
                    seriesIndex: 0,
                    dataPointIndex: todayIdx,
                    fillColor: '#ea580c',
                    strokeColor: '#fff',
                    size: 7,
                    shape: "circle"
                }]
            },
            xaxis: { 
                categories: details.weekly_late.labels, 
                axisBorder: { show: false } 
            },
            yaxis: { 
                min: 0,
                forceNiceScale: true,
                decimalsInFloat: 0,
                labels: {
                    formatter: (val) => Math.floor(val)
                }
            },
            legend: { show: false }
        }).render();
    }

    // 4. Total Working Hours (This Month)
    if (document.querySelector("#chart-working-hours") && details.avg_hours_analytics) {
        new ApexCharts(document.querySelector("#chart-working-hours"), {
            ...commonOptions,
            series: [{ name: 'Total Hours', data: details.avg_hours_analytics.data }],
            chart: { ...commonOptions.chart, type: 'bar', height: 300 },
            colors: ['#8b5cf6'],
            plotOptions: { 
                bar: { 
                    borderRadius: 4, 
                    horizontal: true, 
                    barHeight: '40%',
                    dataLabels: { position: 'top' }
                } 
            },
            dataLabels: {
                enabled: true,
                formatter: (val) => val + "h",
                style: { fontSize: '11px', colors: ['#fff'] }
            },
            xaxis: { 
                categories: details.avg_hours_analytics.labels, 
                axisBorder: { show: false },
                labels: { formatter: (val) => val + "h" }
            },
            tooltip: { y: { formatter: (val) => val + " hours" } }
        }).render();
    }

    // 5. Leave Tracking (Bar)
    if (document.querySelector("#chart-leave-bar") && details.leave_type_analytics) {
        new ApexCharts(document.querySelector("#chart-leave-bar"), {
            ...commonOptions,
            series: [{ name: 'Total Days', data: details.leave_type_analytics.data }],
            chart: { ...commonOptions.chart, type: 'bar', height: 350 },
            colors: ['#ec4899'],
            plotOptions: { bar: { borderRadius: 6, columnWidth: '45%', distributed: true } },
            xaxis: { categories: details.leave_type_analytics.labels, axisBorder: { show: false } },
            legend: { show: false }
        }).render();
    }
});

