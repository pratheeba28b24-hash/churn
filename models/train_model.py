import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def train_and_save_model(data_path="dataset/churn_dataset.csv", model_dir="models"):
    os.makedirs(model_dir, exist_ok=True)
    
    if not os.path.exists(data_path):
        from dataset.generate_dataset import generate_sample_dataset
        df = generate_sample_dataset(filepath=data_path)
    else:
        df = pd.read_csv(data_path)
        
    print(f"Loaded dataset with {len(df)} rows.")
    
    # Preprocessing target
    X = df[['Age', 'Gender', 'Tenure', 'MonthlyCharges', 'Contract', 'PaymentMethod', 'InternetService', 'NumberOfServices', 'SupportCalls']]
    y = df['Churn'].map({'Yes': 1, 'No': 0})
    
    numeric_features = ['Age', 'Tenure', 'MonthlyCharges', 'NumberOfServices', 'SupportCalls']
    categorical_features = ['Gender', 'Contract', 'PaymentMethod', 'InternetService']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ]
    )
    
    # Use Gradient Boosting or Random Forest Classifier
    classifier = RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, class_weight='balanced')
    
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model_pipeline.fit(X_train, y_train)
    
    y_pred = model_pipeline.predict(X_test)
    y_pred_proba = model_pipeline.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    # Calculate feature importances
    ohe_categories = model_pipeline.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(categorical_features)
    all_feature_names = numeric_features + list(ohe_categories)
    importances = model_pipeline.named_steps['classifier'].feature_importances_
    
    feature_imp_list = sorted([
        {"feature": name, "importance": round(float(imp), 4)}
        for name, imp in zip(all_feature_names, importances)
    ], key=lambda x: x["importance"], reverse=True)
    
    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": cm,
        "feature_importances": feature_imp_list,
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }
    
    model_path = os.path.join(model_dir, "churn_model.pkl")
    metrics_path = os.path.join(model_dir, "model_metrics.json")
    
    joblib.dump(model_pipeline, model_path)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("Model Training Completed Successfully!")
    print(f"Saved model to: {model_path}")
    print(f"Accuracy: {acc*100:.2f}% | Precision: {prec*100:.2f}% | Recall: {rec*100:.2f}% | F1: {f1*100:.2f}%")
    return model_pipeline, metrics

if __name__ == "__main__":
    train_and_save_model()
