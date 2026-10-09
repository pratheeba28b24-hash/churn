document.addEventListener('DOMContentLoaded', () => {
  prefillFromUrlParams();
  
  const form = document.getElementById('predict-form');
  form.addEventListener('submit', handlePredictSubmit);
});

function prefillFromUrlParams() {
  const urlParams = new URLSearchParams(window.location.search);
  
  if (urlParams.has('name')) document.getElementById('p-name').value = urlParams.get('name');
  if (urlParams.has('age')) document.getElementById('p-age').value = urlParams.get('age');
  if (urlParams.has('gender')) document.getElementById('p-gender').value = urlParams.get('gender');
  if (urlParams.has('tenure')) document.getElementById('p-tenure').value = urlParams.get('tenure');
  if (urlParams.has('monthly')) document.getElementById('p-monthly').value = urlParams.get('monthly');
  if (urlParams.has('contract')) document.getElementById('p-contract').value = urlParams.get('contract');
  if (urlParams.has('payment')) document.getElementById('p-payment').value = urlParams.get('payment');
  if (urlParams.has('internet')) document.getElementById('p-internet').value = urlParams.get('internet');
  if (urlParams.has('services')) document.getElementById('p-services').value = urlParams.get('services');
  if (urlParams.has('calls')) document.getElementById('p-calls').value = urlParams.get('calls');
  
  // Auto predict if launched with parameters from table
  if (urlParams.has('name')) {
    document.getElementById('predict-form').dispatchEvent(new Event('submit'));
  }
}

async function handlePredictSubmit(e) {
  e.preventDefault();
  
  const payload = {
    customer_name: document.getElementById('p-name').value || 'Quick Customer',
    gender: document.getElementById('p-gender').value,
    age: parseInt(document.getElementById('p-age').value),
    tenure: parseInt(document.getElementById('p-tenure').value),
    monthly_charges: parseFloat(document.getElementById('p-monthly').value),
    contract: document.getElementById('p-contract').value,
    payment_method: document.getElementById('p-payment').value,
    internet_service: document.getElementById('p-internet').value,
    num_services: parseInt(document.getElementById('p-services').value),
    support_calls: parseInt(document.getElementById('p-calls').value)
  };
  
  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    if (data.status === 'success') {
      renderPredictionResults(data);
    } else {
      alert('Prediction error: ' + (data.message || 'Unknown error'));
    }
  } catch (err) {
    console.error("Prediction request failed:", err);
  }
}

function renderPredictionResults(data) {
  const prob = data.probability;
  const risk = data.risk_level;
  const isChurn = data.prediction === 'Yes';
  
  // Update gauge circle
  const gaugeCircle = document.getElementById('gauge-circle');
  document.getElementById('gauge-prob').innerText = `${prob}%`;
  
  let color = 'var(--accent-emerald)';
  let badgeClass = 'badge-low';
  
  if (risk === 'High') {
    color = 'var(--accent-rose)';
    badgeClass = 'badge-high';
  } else if (risk === 'Medium') {
    color = 'var(--accent-amber)';
    badgeClass = 'badge-med';
  }
  
  gaugeCircle.style.setProperty('--gauge-percent', `${prob}%`);
  gaugeCircle.style.setProperty('--gauge-color', color);
  
  // Update Badge
  const badgeEl = document.getElementById('risk-tier-badge');
  badgeEl.className = `badge ${badgeClass}`;
  badgeEl.innerHTML = `<i class="fa-solid fa-shield-halved me-1"></i> ${risk} Risk Tier`;
  
  // Update Text Status
  const predictText = document.getElementById('churn-prediction-text');
  predictText.innerText = isChurn ? 'High Risk of Leaving' : 'Likely to Stay';
  predictText.style.color = isChurn ? 'var(--accent-rose)' : 'var(--accent-emerald)';
  
  document.getElementById('outcome-text').innerHTML = isChurn ? 
    `<span style="color: var(--accent-rose);"><i class="fa-solid fa-user-xmark me-2"></i> Churn Predicted (Yes)</span>` : 
    `<span style="color: var(--accent-emerald);"><i class="fa-solid fa-user-check me-2"></i> Retained (No Churn)</span>`;
    
  // Update Recommendations
  const recContainer = document.getElementById('recommendations-container');
  if (data.recommendations && data.recommendations.length > 0) {
    recContainer.innerHTML = data.recommendations.map(rec => `
      <div class="recommendation-item">
        <i class="fa-solid fa-square-check" style="color: ${color};"></i>
        <span>${rec}</span>
      </div>
    `).join('');
  }
}
