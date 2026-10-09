import os
import json
import joblib
import pandas as pd
import numpy as np

class ChurnMLEngine:
    def __init__(self, model_path="models/churn_model.pkl", metrics_path="models/model_metrics.json"):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.model_path = os.path.join(base_dir, model_path)
        self.metrics_path = os.path.join(base_dir, metrics_path)
        self.model = None
        self.metrics = {}
        self.load_model()
        
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print("Loaded trained ML model successfully.")
        else:
            print("Warning: ML model not found. Running training script...")
            from models.train_model import train_and_save_model
            self.model, _ = train_and_save_model()
            
        if os.path.exists(self.metrics_path):
            with open(self.metrics_path, "r") as f:
                self.metrics = json.load(f)
                
    def get_metrics(self):
        return self.metrics
        
    def predict_one(self, data):
        """
        Input data dictionary:
        {
            'Age': int,
            'Gender': str ('Male', 'Female'),
            'Tenure': int (months),
            'MonthlyCharges': float,
            'Contract': str ('Month-to-month', 'One year', 'Two year'),
            'PaymentMethod': str ('Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'),
            'InternetService': str ('DSL', 'Fiber optic', 'No'),
            'NumberOfServices': int,
            'SupportCalls': int
        }
        """
        df = pd.DataFrame([data])
        
        # Ensure column order matches training
        feature_order = ['Age', 'Gender', 'Tenure', 'MonthlyCharges', 'Contract', 'PaymentMethod', 'InternetService', 'NumberOfServices', 'SupportCalls']
        df = df[feature_order]
        
        proba = self.model.predict_proba(df)[0, 1] # Probability of Churn (class 1)
        prob_pct = round(float(proba * 100), 1)
        
        prediction = "Yes" if proba >= 0.50 else "No"
        
        if prob_pct >= 65.0:
            risk_level = "High"
        elif prob_pct >= 35.0:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        # Generate targeted recommendations based on risk factors
        recommendations = []
        if data.get('SupportCalls', 0) >= 3:
            recommendations.append("Priority Support: Customer has high support calls. Assign a dedicated account representative to resolve pending technical issues.")
        if data.get('Contract') == 'Month-to-month':
            recommendations.append("Contract Retention: Switch customer from Month-to-month to a 1-year or 2-year contract with a 15% promotional discount.")
        if data.get('MonthlyCharges', 0) > 85:
            recommendations.append("Price Optimization: High monthly bill detected. Offer customized bundle packages or loyalty billing credits.")
        if data.get('Tenure', 0) <= 6:
            recommendations.append("Onboarding Care: Early-stage customer. Provide proactive onboarding check-ins and product feature walkthroughs.")
        if data.get('PaymentMethod') == 'Electronic check':
            recommendations.append("Payment Convenience: Encourage enrollment in automated credit card or bank transfer payment methods.")
            
        if not recommendations:
            recommendations.append("Customer exhibits strong engagement metrics. Maintain standard retention workflow and periodic satisfaction surveys.")
            
        return {
            "prediction": prediction,
            "probability": prob_pct,
            "risk_level": risk_level,
            "recommendations": recommendations
        }
