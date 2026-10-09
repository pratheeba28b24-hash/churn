document.addEventListener('DOMContentLoaded', () => {
  fetchDashboardStats();
});

let churnChart = null;
let featureChart = null;

async function fetchDashboardStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    
    // Update metric counters
    document.getElementById('stat-total').innerText = data.total_customers.toLocaleString();
    document.getElementById('stat-churned').innerText = data.churned_customers.toLocaleString();
    document.getElementById('stat-active').innerText = data.active_customers.toLocaleString();
    document.getElementById('stat-rate').innerText = `${data.churn_rate}%`;
    document.getElementById('stat-high-risk').innerText = data.high_risk_customers.toLocaleString();
    document.getElementById('stat-tenure').innerText = `${data.avg_tenure} mo`;
    
    // Update ML Metrics
    if (data.model_metrics) {
      document.getElementById('ml-acc').innerText = `${(data.model_metrics.accuracy * 100).toFixed(1)}%`;
      document.getElementById('ml-prec').innerText = `${(data.model_metrics.precision * 100).toFixed(1)}%`;
      document.getElementById('ml-rec').innerText = `${(data.model_metrics.recall * 100).toFixed(1)}%`;
      document.getElementById('ml-f1').innerText = `${(data.model_metrics.f1_score * 100).toFixed(1)}%`;
      
      renderFeatureImportanceChart(data.model_metrics.feature_importances || []);
    }
    
    renderChurnDistChart(data.active_customers, data.churned_customers);
    renderWatchlist(data.high_risk_list || []);
  } catch (err) {
    console.error("Failed to load dashboard metrics:", err);
  }
}

function renderChurnDistChart(activeCount, churnedCount) {
  const ctx = document.getElementById('chart-churn-dist').getContext('2d');
  
  if (churnChart) churnChart.destroy();
  
  churnChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Active Customers', 'Churned Customers'],
      datasets: [{
        data: [activeCount, churnedCount],
        backgroundColor: ['#10b981', '#f43f5e'],
        borderColor: '#0f172a',
        borderWidth: 3,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 13 } }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1
        }
      },
      cutout: '70%'
    }
  });
}

function renderFeatureImportanceChart(features) {
  const ctx = document.getElementById('chart-feature-imp').getContext('2d');
  
  const topFeatures = features.slice(0, 7);
  const labels = topFeatures.map(f => f.feature.replace('cat__', '').replace('num__', ''));
  const values = topFeatures.map(f => (f.importance * 100).toFixed(1));
  
  if (featureChart) featureChart.destroy();
  
  featureChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Importance Weight (%)',
        data: values,
        backgroundColor: 'rgba(99, 102, 241, 0.75)',
        borderColor: '#6366f1',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#f8fafc',
          bodyColor: '#94a3b8'
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#94a3b8' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f8fafc', font: { size: 12 } }
        }
      }
    }
  });
}

function renderWatchlist(list) {
  const tbody = document.getElementById('watchlist-body');
  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 20px; color: var(--text-muted);">No high risk customers detected.</td></tr>`;
    return;
  }
  
  tbody.innerHTML = list.map(c => `
    <tr>
      <td><strong>${c.customer_id}</strong></td>
      <td>${c.name}</td>
      <td>${c.contract}</td>
      <td>${c.tenure} mos</td>
      <td>$${c.monthly_charges.toFixed(2)}</td>
      <td><span class="badge ${c.support_calls >= 3 ? 'badge-high' : 'badge-med'}">${c.support_calls} calls</span></td>
      <td><strong style="color: var(--accent-rose);">${c.churn_probability}%</strong></td>
      <td><span class="badge badge-high"><i class="fa-solid fa-triangle-exclamation me-1"></i> High</span></td>
      <td>
        <a href="/predict?id=${c.id}&name=${encodeURIComponent(c.name)}&age=${c.age}&gender=${c.gender}&tenure=${c.tenure}&monthly=${c.monthly_charges}&contract=${encodeURIComponent(c.contract)}&payment=${encodeURIComponent(c.payment_method)}&internet=${encodeURIComponent(c.internet_service)}&services=${c.num_services}&calls=${c.support_calls}" class="btn btn-primary btn-sm">
          <i class="fa-solid fa-wand-magic-sparkles"></i> Predict
        </a>
      </td>
    </tr>
  `).join('');
}
