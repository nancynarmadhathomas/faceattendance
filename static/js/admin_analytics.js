// Admin Dashboard Analytics - Powered by ApexCharts
document.addEventListener('DOMContentLoaded', function() {
    // Only run if we are on a page/tab that contains the charts
    const chartContainer = document.querySelector("#chart-org-trend");
    if (!chartContainer || !window.ADMIN_DATA) {
        return;
    }
    
    const { trend, details } = window.ADMIN_DATA;

    // Safety check for empty data
    if (!trend || !trend.labels || trend.labels.length === 0) {
        console.warn("No analytics data available to render charts.");
        return;
    }

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

    // 1. Total Attendance Trend (Line)
    if (document.querySelector("#chart-org-trend")) {
        new ApexCharts(document.querySelector("#chart-org-trend"), {
            ...commonOptions,
            series: [
                { name: 'Present', data: trend.present || [] },
                { name: 'Absent', data: trend.absent || [] },
                { name: 'On Leave', data: trend.on_leave || [] }
            ],
            chart: { ...commonOptions.chart, type: 'line', height: 320 },
            colors: ['#10b981', '#ef4444', '#8b5cf6'],
            xaxis: { categories: trend.labels || [], axisBorder: { show: false } },
            legend: { position: 'top', horizontalAlign: 'right' }
        }).render();
    }

    // 2. Weekly Attendance (Bar)
    if (document.querySelector("#chart-weekly-att") && details.weekly_att) {
        new ApexCharts(document.querySelector("#chart-weekly-att"), {
            ...commonOptions,
            series: [{ name: 'Present', data: details.weekly_att.data }],
            chart: { ...commonOptions.chart, type: 'bar', height: 250 },
            colors: ['#6366f1'],
            plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } },
            xaxis: { categories: details.weekly_att.labels, axisBorder: { show: false } }
        }).render();
    }

    // 3. Late Employees per Week (Bar)
    if (document.querySelector("#chart-weekly-late") && details.weekly_late) {
        new ApexCharts(document.querySelector("#chart-weekly-late"), {
            ...commonOptions,
            series: [{ name: 'Late', data: details.weekly_late.data }],
            chart: { ...commonOptions.chart, type: 'bar', height: 250 },
            colors: ['#f59e0b'],
            plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } },
            xaxis: { categories: details.weekly_late.labels, axisBorder: { show: false } }
        }).render();
    }

    // 4. Leave Type Breakdown (Donut)
    if (document.querySelector("#chart-leave-donut") && details.leave_donut) {
        new ApexCharts(document.querySelector("#chart-leave-donut"), {
            ...commonOptions,
            series: details.leave_donut.data,
            labels: details.leave_donut.labels,
            chart: { ...commonOptions.chart, type: 'donut', height: 250 },
            colors: ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#10b981'],
            stroke: { show: false },
            legend: { position: 'bottom' },
            plotOptions: { pie: { donut: { size: '65%' } } }
        }).render();
    }

    // 5. Attendance Distribution (Donut)
    if (document.querySelector("#chart-att-dist") && details.dist_donut) {
        new ApexCharts(document.querySelector("#chart-att-dist"), {
            ...commonOptions,
            series: details.dist_donut.data,
            labels: details.dist_donut.labels,
            chart: { ...commonOptions.chart, type: 'donut', height: 250 },
            colors: ['#10b981', '#ef4444', '#8b5cf6'],
            stroke: { show: false },
            legend: { position: 'bottom' },
            plotOptions: { pie: { donut: { size: '65%' } } }
        }).render();
    }
});
