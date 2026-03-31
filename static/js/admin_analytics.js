// ── Dashboard Analytics ───────────────────────
let analyticsChart = null;

async function loadAnalytics() {
  const canvas = document.getElementById('analyticsChart');
  if (!canvas) return;

  try {
    // We target the 'performance' type for employee-name based analytics
    const res = await fetch('/api/admin/analytics?type=performance');
    const data = await res.json();

    if (!data || !data.names || data.names.length === 0) {
      console.warn("No analytics data received");
      return;
    }

    const ctx = canvas.getContext('2d');
    
    // Create Premium Gradients
    const gradientBar = ctx.createLinearGradient(0, 0, 0, 300);
    gradientBar.addColorStop(0, 'rgba(79, 70, 229, 0.85)'); // Primary
    gradientBar.addColorStop(1, 'rgba(79, 70, 229, 0.15)');

    const chartData = {
      labels: data.names,
      datasets: [
        {
          type: 'bar',
          label: 'Days Present',
          data: data.counts,
          backgroundColor: gradientBar,
          borderColor: '#6366f1',
          borderWidth: 1,
          borderRadius: 8,
          barThickness: 24,
          order: 2
        },
        {
          type: 'line',
          label: 'Performance Trend',
          data: data.counts,
          borderColor: '#10b981', // Success green
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          borderWidth: 3,
          tension: 0.45,
          pointRadius: 4,
          pointBackgroundColor: '#10b981',
          pointBorderColor: '#fff',
          pointHoverRadius: 7,
          fill: true,
          order: 1
        }
      ]
    };

    if (analyticsChart) {
      analyticsChart.destroy();
    }

    analyticsChart = new Chart(ctx, {
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            titleFont: { size: 14, weight: '700', family: 'Inter' },
            bodyFont: { size: 13, family: 'Inter' },
            padding: 14,
            cornerRadius: 12,
            displayColors: true,
            callbacks: {
              label: function(context) {
                return ` ${context.dataset.label}: ${context.raw} Days`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { 
              color: 'rgba(148, 163, 184, 0.8)',
              font: { size: 11, family: 'Inter', weight: '500' }
            }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(148, 163, 184, 0.1)', borderDash: [5, 5] },
            ticks: { 
              color: 'rgba(148, 163, 184, 0.8)',
              font: { size: 11, family: 'Inter' },
              stepSize: 1
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    });

  } catch (err) {
    console.error("Chart initialization failed:", err);
  }
}

// Initial Load
document.addEventListener('DOMContentLoaded', loadAnalytics);
