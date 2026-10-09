document.addEventListener('DOMContentLoaded', () => {
  loadAnalyticsData();
});

let charts = {};

async function loadAnalyticsData() {
  try {
    const res = await fetch('/api/analytics-data');
    const data = await res.json();
    
    renderContractChart(data.contract || []);
    renderAgeChart(data.age_group || []);
    renderPaymentChart(data.payment || []);
    renderTenureChart(data.tenure || []);
    renderChargesChart(data.charges_vs_churn || []);
    renderRiskDistChart(data.risk_dist || []);
  } catch (err) {
    console.error("Error loading analytics charts data:", err);
  }
}

function destroyChart(name) {
  if (charts[name]) {
    charts[name].destroy();
  }
}

// 1. Churn by Contract Type (Grouped Bar Chart)
function renderContractChart(contractData) {
  destroyChart('contract');
  const ctx = document.getElementById('chart-contract').getContext('2d');
  
  const labels = contractData.map(d => d.contract);
  const activeData = contractData.map(d => d.total - d.churned);
  const churnedData = contractData.map(d => d.churned);
  
  charts['contract'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'Active Customers', data: activeData, backgroundColor: 'rgba(16, 185, 129, 0.75)', borderRadius: 6 },
        { label: 'Churned Customers', data: churnedData, backgroundColor: 'rgba(244, 63, 94, 0.75)', borderRadius: 6 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#f8fafc' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

// 2. Churn by Age Group (Line / Area Chart)
function renderAgeChart(ageData) {
  destroyChart('age');
  const ctx = document.getElementById('chart-age').getContext('2d');
  
  const labels = ageData.map(d => d.age_group);
  const churnRates = ageData.map(d => d.total > 0 ? ((d.churned / d.total) * 100).toFixed(1) : 0);
  
  charts['age'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Churn Rate (%)',
        data: churnRates,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.15)',
        fill: true,
        tension: 0.3,
        pointBackgroundColor: '#06b6d4',
        pointRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#f8fafc' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, min: 0, max: 100 }
      }
    }
  });
}

// 3. Churn by Payment Method (Horizontal Bar)
function renderPaymentChart(paymentData) {
  destroyChart('payment');
  const ctx = document.getElementById('chart-payment').getContext('2d');
  
  const labels = paymentData.map(d => d.payment_method);
  const churnRates = paymentData.map(d => d.total > 0 ? ((d.churned / d.total) * 100).toFixed(1) : 0);
  
  charts['payment'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Churn Rate (%)',
        data: churnRates,
        backgroundColor: 'rgba(245, 158, 11, 0.75)',
        borderColor: '#f59e0b',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, max: 100 },
        y: { grid: { display: false }, ticks: { color: '#f8fafc' } }
      }
    }
  });
}

// 4. Churn by Tenure Bracket (Bar Chart)
function renderTenureChart(tenureData) {
  destroyChart('tenure');
  const ctx = document.getElementById('chart-tenure').getContext('2d');
  
  const labels = tenureData.map(d => d.tenure_group);
  const churnRates = tenureData.map(d => d.total > 0 ? ((d.churned / d.total) * 100).toFixed(1) : 0);
  
  charts['tenure'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Churn Rate (%)',
        data: churnRates,
        backgroundColor: 'rgba(16, 185, 129, 0.75)',
        borderColor: '#10b981',
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#f8fafc' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' }, max: 100 }
      }
    }
  });
}

// 5. Monthly Charges vs Churn (Histogram / Scatter-like bins)
function renderChargesChart(chargesData) {
  destroyChart('charges');
  const ctx = document.getElementById('chart-charges').getContext('2d');
  
  // Bin monthly charges into intervals
  const bins = { '$18-$40': { active: 0, churned: 0 }, '$41-$70': { active: 0, churned: 0 }, '$71-$100': { active: 0, churned: 0 }, '$100+': { active: 0, churned: 0 } };
  
  chargesData.forEach(d => {
    const fee = d.monthly_charges;
    let key = '$100+';
    if (fee <= 40) key = '$18-$40';
    else if (fee <= 70) key = '$41-$70';
    else if (fee <= 100) key = '$71-$100';
    
    if (d.churn_status === 'Yes') bins[key].churned++;
    else bins[key].active++;
  });
  
  charts['charges'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Object.keys(bins),
      datasets: [
        { label: 'Retained', data: Object.values(bins).map(b => b.active), backgroundColor: 'rgba(99, 102, 241, 0.75)', borderRadius: 6 },
        { label: 'Churned', data: Object.values(bins).map(b => b.churned), backgroundColor: 'rgba(244, 63, 94, 0.75)', borderRadius: 6 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8' } } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#f8fafc' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

// 6. Risk Distribution Donut
function renderRiskDistChart(riskData) {
  destroyChart('risk_dist');
  const ctx = document.getElementById('chart-risk-dist').getContext('2d');
  
  const map = { Low: 0, Medium: 0, High: 0 };
  riskData.forEach(r => { map[r.risk_level] = r.count; });
  
  charts['risk_dist'] = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Low Risk', 'Medium Risk', 'High Risk'],
      datasets: [{
        data: [map['Low'], map['Medium'], map['High']],
        backgroundColor: ['#10b981', '#f59e0b', '#f43f5e'],
        borderColor: '#0f172a',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8' } }
      }
    }
  });
}
