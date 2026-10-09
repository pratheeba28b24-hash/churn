# Customer Churn Prediction & Analytics Dashboard

A machine-learning-powered web application built with **Flask**, **Scikit-Learn**, **SQLite**, and **Chart.js**. It enables business managers to predict customer churn risks, analyze behavioral drivers, manage customer records, track prediction audit logs, and export executive CSV reports.

---

## Key Features

1. **Secure Admin Authentication**:
   - Modern glassmorphism login portal (`admin` / `admin123`).
2. **Executive Analytics Dashboard**:
   - Total, Churned, Active Customers, Churn Rate %, High-Risk Customer counts, and Average Tenure.
   - ML performance metrics (Accuracy, Precision, Recall, F1 Score).
   - Interactive Churn Distribution Donut Chart and ML Feature Importance Leaderboard.
   - High-Risk Customer Watchlist table.
3. **Customer Data Management (CRUD)**:
   - Full tabular customer database with real-time search, contract filters, and risk tier badges.
   - Modal forms to Add, Edit, or Delete customer records.
4. **Machine Learning Churn Predictor**:
   - Real-time inference based on 9 key customer indicators (Age, Gender, Tenure, Monthly Fee, Contract, Payment Method, Internet Service, Active Services, Support Calls).
   - Conic probability gauge animation (0-100%) and Risk Tier classification (Low / Medium / High).
   - AI-driven strategic retention recommendations.
5. **Interactive Analytics Module**:
   - 6 multidimensional Chart.js charts:
     - Churn Rate by Contract Type
     - Churn Rate by Age Demographics
     - Churn Rate by Payment Method
     - Churn Rate by Tenure Duration
     - Monthly Charges vs Churn Status
     - Customer Risk Distribution
6. **Prediction Audit Logs**:
   - SQLite history logging of every prediction attempt with timestamps and export features.
7. **Reports & CSV Data Exporter**:
   - One-click CSV downloads for Customer Dataset, Prediction Logs, and Executive Summary.

---

## Project Structure

```
churn/
├── app/
│   ├── __init__.py
│   ├── routes.py            # Main application routes & REST JSON APIs
│   ├── db.py                # SQLite database helper & schema setup
│   └── ml_engine.py         # ML model loader & prediction pipeline
├── templates/
│   ├── base.html            # Master layout with sidebar & topbar
│   ├── login.html           # Login screen
│   ├── dashboard.html       # Analytics overview & KPI cards
│   ├── customers.html       # Customer list, search, modal forms
│   ├── predict.html         # ML prediction interface & conic gauge
│   ├── analytics.html       # Multidimensional interactive charts
│   ├── history.html         # SQLite prediction history log
│   └── reports.html         # Executive reporting & CSV exporter
├── static/
│   ├── css/
│   │   └── style.css        # Dark Glassmorphism design system
│   ├── js/
│   │   ├── dashboard.js     # Dashboard stats & Chart.js logic
│   │   ├── analytics.js     # Multidimensional analytics charts
│   │   ├── predict.js       # Live prediction visual gauge logic
│   │   └── customers.js     # Data table filtering & AJAX modal CRUD
│   └── images/
├── dataset/
│   ├── generate_dataset.py  # Synthetic dataset generator
│   └── churn_dataset.csv    # Sample customer churn dataset
├── models/
│   ├── train_model.py       # Scikit-Learn training pipeline script
│   ├── churn_model.pkl      # Trained Random Forest model pipeline
│   └── model_metrics.json   # Model evaluation metrics & feature importances
├── database/
│   └── churn_dashboard.db   # SQLite database file
├── requirements.txt         # Dependencies list
├── README.md                # Project documentation
└── app.py                   # Flask entry point
```

---

## Setup & Running Instructions

### 1. Requirements
Ensure Python 3.9+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Dataset & Train ML Model
```bash
# Generate sample dataset (1,000 customer records)
python dataset/generate_dataset.py

# Train ML Model & save model pipeline
python models/train_model.py
```

### 4. Run the Web Application
```bash
python app.py
```

Open your browser and navigate to:
**`http://127.0.0.1:5000`**

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

---

## Machine Learning Details

- **Algorithm**: `RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42)`
- **Preprocessing**: `ColumnTransformer` with `StandardScaler` for numeric variables and `OneHotEncoder` for categorical features.
- **Evaluation**: Standard 80/20 train/test split. Average accuracy: ~79-82%, F1 Score: ~70-75%.
