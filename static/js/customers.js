document.addEventListener('DOMContentLoaded', () => {
  loadCustomers();
  
  document.getElementById('search-input').addEventListener('input', debounce(loadCustomers, 300));
  document.getElementById('filter-contract').addEventListener('change', loadCustomers);
  document.getElementById('filter-risk').addEventListener('change', loadCustomers);
  
  document.getElementById('customer-form').addEventListener('submit', handleFormSubmit);
});

let customersData = [];

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

async function loadCustomers() {
  const search = document.getElementById('search-input').value.trim();
  const contract = document.getElementById('filter-contract').value;
  const risk = document.getElementById('filter-risk').value;
  
  const url = new URL('/api/customers', window.location.origin);
  if (search) url.searchParams.append('search', search);
  if (contract) url.searchParams.append('contract', contract);
  if (risk) url.searchParams.append('risk', risk);
  
  try {
    const res = await fetch(url);
    const data = await res.json();
    customersData = data.customers || [];
    renderCustomersTable(customersData);
  } catch (err) {
    console.error("Error loading customers:", err);
  }
}

function renderCustomersTable(list) {
  const tbody = document.getElementById('customers-table-body');
  
  if (!list || list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 32px;">No customer records match your filter criteria.</td></tr>`;
    return;
  }
  
  tbody.innerHTML = list.map(c => {
    let riskBadgeClass = 'badge-low';
    if (c.risk_level === 'High') riskBadgeClass = 'badge-high';
    else if (c.risk_level === 'Medium') riskBadgeClass = 'badge-med';
    
    let churnBadgeClass = c.churn_status === 'Yes' ? 'badge-high' : 'badge-low';
    
    return `
      <tr>
        <td><strong>${c.customer_id}</strong></td>
        <td>
          <div style="font-weight: 600;">${c.name}</div>
          <div style="font-size: 12px; color: var(--text-muted);">${c.email}</div>
        </td>
        <td>${c.age} yrs (${c.gender})</td>
        <td>${c.tenure} mos</td>
        <td>$${c.monthly_charges.toFixed(2)}</td>
        <td><span style="font-size: 12px; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px;">${c.contract}</span></td>
        <td><span class="badge ${c.support_calls >= 3 ? 'badge-high' : 'badge-med'}">${c.support_calls} calls</span></td>
        <td><span class="badge ${churnBadgeClass}">${c.churn_status} (${c.churn_probability}%)</span></td>
        <td><span class="badge ${riskBadgeClass}">${c.risk_level}</span></td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-secondary btn-icon" title="Edit Customer" onclick="openEditModal(${c.id})">
              <i class="fa-solid fa-pen-to-square" style="color: var(--accent-cyan);"></i>
            </button>
            <a href="/predict?id=${c.id}&name=${encodeURIComponent(c.name)}&age=${c.age}&gender=${c.gender}&tenure=${c.tenure}&monthly=${c.monthly_charges}&contract=${encodeURIComponent(c.contract)}&payment=${encodeURIComponent(c.payment_method)}&internet=${encodeURIComponent(c.internet_service)}&services=${c.num_services}&calls=${c.support_calls}" class="btn btn-secondary btn-icon" title="Run Churn Prediction">
              <i class="fa-solid fa-wand-magic-sparkles" style="color: var(--accent-primary);"></i>
            </a>
            <button class="btn btn-secondary btn-icon" title="Delete Customer" onclick="deleteCustomer(${c.id})">
              <i class="fa-solid fa-trash" style="color: var(--accent-rose);"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function openAddModal() {
  document.getElementById('modal-title').innerHTML = `<i class="fa-solid fa-user-plus me-2" style="color: var(--accent-primary);"></i> Add Customer`;
  document.getElementById('cust-id').value = '';
  document.getElementById('customer-form').reset();
  document.getElementById('customer-modal').classList.add('active');
}

function openEditModal(id) {
  const cust = customersData.find(c => c.id === id);
  if (!cust) return;
  
  document.getElementById('modal-title').innerHTML = `<i class="fa-solid fa-user-pen me-2" style="color: var(--accent-cyan);"></i> Edit Customer (${cust.customer_id})`;
  document.getElementById('cust-id').value = cust.id;
  document.getElementById('cust-name').value = cust.name;
  document.getElementById('cust-email').value = cust.email;
  document.getElementById('cust-gender').value = cust.gender;
  document.getElementById('cust-age').value = cust.age;
  document.getElementById('cust-tenure').value = cust.tenure;
  document.getElementById('cust-monthly').value = cust.monthly_charges;
  document.getElementById('cust-contract').value = cust.contract;
  document.getElementById('cust-payment').value = cust.payment_method;
  document.getElementById('cust-internet').value = cust.internet_service;
  document.getElementById('cust-services').value = cust.num_services;
  document.getElementById('cust-calls').value = cust.support_calls;
  
  document.getElementById('customer-modal').classList.add('active');
}

function closeModal() {
  document.getElementById('customer-modal').classList.remove('active');
}

async function handleFormSubmit(e) {
  e.preventDefault();
  
  const id = document.getElementById('cust-id').value;
  const payload = {
    name: document.getElementById('cust-name').value,
    email: document.getElementById('cust-email').value,
    gender: document.getElementById('cust-gender').value,
    age: parseInt(document.getElementById('cust-age').value),
    tenure: parseInt(document.getElementById('cust-tenure').value),
    monthly_charges: parseFloat(document.getElementById('cust-monthly').value),
    contract: document.getElementById('cust-contract').value,
    payment_method: document.getElementById('cust-payment').value,
    internet_service: document.getElementById('cust-internet').value,
    num_services: parseInt(document.getElementById('cust-services').value),
    support_calls: parseInt(document.getElementById('cust-calls').value)
  };
  
  const endpoint = id ? `/api/customers/edit/${id}` : '/api/customers/add';
  
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const result = await res.json();
    if (result.status === 'success') {
      closeModal();
      loadCustomers();
    } else {
      alert("Error: " + result.message);
    }
  } catch (err) {
    console.error("Form submission failed:", err);
  }
}

async function deleteCustomer(id) {
  if (!confirm("Are you sure you want to delete this customer record?")) return;
  
  try {
    const res = await fetch(`/api/customers/delete/${id}`, { method: 'POST' });
    const result = await res.json();
    if (result.status === 'success') {
      loadCustomers();
    }
  } catch (err) {
    console.error("Delete failed:", err);
  }
}
