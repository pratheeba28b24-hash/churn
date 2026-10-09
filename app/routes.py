import csv
import io
from functools import wraps
from flask import render_template, request, redirect, url_for, session, jsonify, Response, flash
from werkzeug.security import check_password_hash
from app.db import get_db_connection
from app.ml_engine import ChurnMLEngine

ml_engine = ChurnMLEngine()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Invalid username or password. (Default: admin / admin123)")
                
        return render_template('login.html')
        
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
        
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', username=session.get('username', 'Admin'))

    @app.route('/api/stats')
    @login_required
    def api_stats():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM customers')
        total_customers = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT COUNT(*) as churned FROM customers WHERE churn_status = 'Yes'")
        churned_customers = cursor.fetchone()['churned'] or 0
        
        active_customers = total_customers - churned_customers
        churn_rate = round((churned_customers / total_customers * 100), 1) if total_customers > 0 else 0.0
        
        cursor.execute("SELECT COUNT(*) as high_risk FROM customers WHERE risk_level = 'High'")
        high_risk_customers = cursor.fetchone()['high_risk'] or 0
        
        cursor.execute('SELECT AVG(tenure) as avg_tenure FROM customers')
        avg_tenure = cursor.fetchone()['avg_tenure'] or 0.0
        avg_tenure = round(avg_tenure, 1)
        
        cursor.execute('SELECT AVG(monthly_charges) as avg_charges FROM customers')
        avg_charges = cursor.fetchone()['avg_charges'] or 0.0
        avg_charges = round(avg_charges, 2)
        
        # High risk customers list for widget
        cursor.execute("SELECT * FROM customers WHERE risk_level = 'High' ORDER BY churn_probability DESC LIMIT 5")
        high_risk_list = [dict(row) for row in cursor.fetchall()]
        
        # ML metrics
        model_metrics = ml_engine.get_metrics()
        
        conn.close()
        
        return jsonify({
            "total_customers": total_customers,
            "churned_customers": churned_customers,
            "active_customers": active_customers,
            "churn_rate": churn_rate,
            "high_risk_customers": high_risk_customers,
            "avg_tenure": avg_tenure,
            "avg_charges": avg_charges,
            "high_risk_list": high_risk_list,
            "model_metrics": model_metrics
        })

    @app.route('/customers')
    @login_required
    def customers():
        return render_template('customers.html')

    @app.route('/api/customers')
    @login_required
    def api_customers():
        search = request.args.get('search', '').strip()
        contract_filter = request.args.get('contract', '')
        risk_filter = request.args.get('risk', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM customers WHERE 1=1"
        params = []
        
        if search:
            query += " AND (name LIKE ? OR email LIKE ? OR customer_id LIKE ?)"
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
            
        if contract_filter:
            query += " AND contract = ?"
            params.append(contract_filter)
            
        if risk_filter:
            query += " AND risk_level = ?"
            params.append(risk_filter)
            
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"customers": rows})

    @app.route('/api/customers/add', methods=['POST'])
    @login_required
    def add_customer():
        data = request.json or request.form
        
        name = data.get('name')
        email = data.get('email')
        gender = data.get('gender', 'Male')
        age = int(data.get('age', 30))
        tenure = int(data.get('tenure', 12))
        monthly_charges = float(data.get('monthly_charges', 50.0))
        contract = data.get('contract', 'Month-to-month')
        payment_method = data.get('payment_method', 'Electronic check')
        internet_service = data.get('internet_service', 'DSL')
        num_services = int(data.get('num_services', 2))
        support_calls = int(data.get('support_calls', 1))
        
        # Calculate ML churn prediction
        pred = ml_engine.predict_one({
            'Age': age, 'Gender': gender, 'Tenure': tenure, 'MonthlyCharges': monthly_charges,
            'Contract': contract, 'PaymentMethod': payment_method, 'InternetService': internet_service,
            'NumberOfServices': num_services, 'SupportCalls': support_calls
        })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        count = cursor.fetchone()['count'] + 1001
        cust_id = f"CUST-{count}"
        
        cursor.execute('''
            INSERT INTO customers (
                customer_id, name, email, gender, age, tenure, monthly_charges,
                contract, payment_method, internet_service, num_services, support_calls,
                churn_status, churn_probability, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cust_id, name, email, gender, age, tenure, monthly_charges, contract,
              payment_method, internet_service, num_services, support_calls,
              pred['prediction'], pred['probability'], pred['risk_level']))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Customer added successfully!", "customer_id": cust_id})

    @app.route('/api/customers/edit/<int:id>', methods=['POST'])
    @login_required
    def edit_customer(id):
        data = request.json or request.form
        
        name = data.get('name')
        email = data.get('email')
        gender = data.get('gender')
        age = int(data.get('age'))
        tenure = int(data.get('tenure'))
        monthly_charges = float(data.get('monthly_charges'))
        contract = data.get('contract')
        payment_method = data.get('payment_method')
        internet_service = data.get('internet_service')
        num_services = int(data.get('num_services'))
        support_calls = int(data.get('support_calls'))
        
        pred = ml_engine.predict_one({
            'Age': age, 'Gender': gender, 'Tenure': tenure, 'MonthlyCharges': monthly_charges,
            'Contract': contract, 'PaymentMethod': payment_method, 'InternetService': internet_service,
            'NumberOfServices': num_services, 'SupportCalls': support_calls
        })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers SET
                name=?, email=?, gender=?, age=?, tenure=?, monthly_charges=?,
                contract=?, payment_method=?, internet_service=?, num_services=?, support_calls=?,
                churn_status=?, churn_probability=?, risk_level=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (name, email, gender, age, tenure, monthly_charges, contract,
              payment_method, internet_service, num_services, support_calls,
              pred['prediction'], pred['probability'], pred['risk_level'], id))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Customer updated successfully!"})

    @app.route('/api/customers/delete/<int:id>', methods=['POST', 'DELETE'])
    @login_required
    def delete_customer(id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customers WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Customer deleted successfully!"})

    @app.route('/predict')
    @login_required
    def predict_page():
        return render_template('predict.html')

    @app.route('/api/predict', methods=['POST'])
    @login_required
    def api_predict():
        data = request.json or request.form
        
        customer_name = data.get('customer_name', 'Quick Customer Predict')
        age = int(data.get('age', 35))
        gender = data.get('gender', 'Male')
        tenure = int(data.get('tenure', 12))
        monthly_charges = float(data.get('monthly_charges', 65.0))
        contract = data.get('contract', 'Month-to-month')
        payment_method = data.get('payment_method', 'Electronic check')
        internet_service = data.get('internet_service', 'Fiber optic')
        num_services = int(data.get('num_services', 3))
        support_calls = int(data.get('support_calls', 2))
        
        res = ml_engine.predict_one({
            'Age': age, 'Gender': gender, 'Tenure': tenure, 'MonthlyCharges': monthly_charges,
            'Contract': contract, 'PaymentMethod': payment_method, 'InternetService': internet_service,
            'NumberOfServices': num_services, 'SupportCalls': support_calls
        })
        
        # Save prediction into SQLite predictions table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions (
                customer_name, age, gender, tenure, monthly_charges, contract,
                payment_method, internet_service, num_services, support_calls,
                prediction_result, churn_probability, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_name, age, gender, tenure, monthly_charges, contract,
              payment_method, internet_service, num_services, support_calls,
              res['prediction'], res['probability'], res['risk_level']))
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "prediction": res['prediction'],
            "probability": res['probability'],
            "risk_level": res['risk_level'],
            "recommendations": res['recommendations']
        })

    @app.route('/analytics')
    @login_required
    def analytics():
        return render_template('analytics.html')

    @app.route('/api/analytics-data')
    @login_required
    def api_analytics_data():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Churn by Contract Type
        cursor.execute('''
            SELECT contract, 
                   COUNT(*) as total, 
                   SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) as churned 
            FROM customers GROUP BY contract
        ''')
        contract_data = [dict(row) for row in cursor.fetchall()]
        
        # 2. Churn by Payment Method
        cursor.execute('''
            SELECT payment_method, 
                   COUNT(*) as total, 
                   SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) as churned 
            FROM customers GROUP BY payment_method
        ''')
        payment_data = [dict(row) for row in cursor.fetchall()]
        
        # 3. Churn by Internet Service
        cursor.execute('''
            SELECT internet_service, 
                   COUNT(*) as total, 
                   SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) as churned 
            FROM customers GROUP BY internet_service
        ''')
        internet_data = [dict(row) for row in cursor.fetchall()]
        
        # 4. Churn by Age Group
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN age < 30 THEN '18-29'
                    WHEN age BETWEEN 30 AND 45 THEN '30-45'
                    WHEN age BETWEEN 46 AND 60 THEN '46-60'
                    ELSE '60+'
                END as age_group,
                COUNT(*) as total,
                SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) as churned
            FROM customers GROUP BY age_group ORDER BY age_group
        ''')
        age_group_data = [dict(row) for row in cursor.fetchall()]
        
        # 5. Churn by Tenure Bracket
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN tenure <= 12 THEN '0-1 Yr'
                    WHEN tenure BETWEEN 13 AND 24 THEN '1-2 Yrs'
                    WHEN tenure BETWEEN 25 AND 48 THEN '2-4 Yrs'
                    ELSE '4+ Yrs'
                END as tenure_group,
                COUNT(*) as total,
                SUM(CASE WHEN churn_status = 'Yes' THEN 1 ELSE 0 END) as churned
            FROM customers GROUP BY tenure_group ORDER BY tenure_group
        ''')
        tenure_data = [dict(row) for row in cursor.fetchall()]
        
        # 6. Risk Distribution
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count FROM customers GROUP BY risk_level
        ''')
        risk_dist = [dict(row) for row in cursor.fetchall()]
        
        # 7. Monthly charges vs Churn (Sample for Scatter / Distribution)
        cursor.execute('''
            SELECT monthly_charges, churn_status, risk_level FROM customers LIMIT 200
        ''')
        charges_vs_churn = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "contract": contract_data,
            "payment": payment_data,
            "internet": internet_data,
            "age_group": age_group_data,
            "tenure": tenure_data,
            "risk_dist": risk_dist,
            "charges_vs_churn": charges_vs_churn
        })

    @app.route('/history')
    @login_required
    def history():
        return render_template('history.html')

    @app.route('/api/history')
    @login_required
    def api_history():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM predictions ORDER BY id DESC')
        predictions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({"predictions": predictions})

    @app.route('/api/history/clear', methods=['POST'])
    @login_required
    def clear_history():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM predictions')
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Prediction history cleared!"})

    @app.route('/reports')
    @login_required
    def reports():
        return render_template('reports.html')

    @app.route('/reports/export/customers')
    @login_required
    def export_customers_csv():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY id ASC')
        rows = cursor.fetchall()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if rows:
            writer.writerow(rows[0].keys()) # Header
            for row in rows:
                writer.writerow(tuple(row))
                
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=customer_churn_dataset.csv"}
        )

    @app.route('/reports/export/predictions')
    @login_required
    def export_predictions_csv():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM predictions ORDER BY id ASC')
        rows = cursor.fetchall()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if rows:
            writer.writerow(rows[0].keys()) # Header
            for row in rows:
                writer.writerow(tuple(row))
                
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=prediction_history_report.csv"}
        )

    @app.route('/reports/export/summary')
    @login_required
    def export_summary_csv():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM customers')
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as churned FROM customers WHERE churn_status = 'Yes'")
        churned = cursor.fetchone()['churned']
        
        cursor.execute("SELECT COUNT(*) as high_risk FROM customers WHERE risk_level = 'High'")
        high_risk = cursor.fetchone()['high_risk']
        
        cursor.execute("SELECT SUM(monthly_charges) as revenue_at_risk FROM customers WHERE churn_status = 'Yes'")
        rev_risk = cursor.fetchone()['revenue_at_risk'] or 0.0
        
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Customers", total])
        writer.writerow(["Churned Customers", churned])
        writer.writerow(["Active Customers", total - churned])
        writer.writerow(["Overall Churn Rate (%)", round((churned/total*100), 2) if total > 0 else 0])
        writer.writerow(["High-Risk Customers Count", high_risk])
        writer.writerow(["Estimated Monthly Revenue at Risk ($)", round(rev_risk, 2)])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=churn_executive_summary.csv"}
        )
