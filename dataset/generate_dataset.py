import os
import numpy as np
import pandas as pd

def generate_sample_dataset(filepath="dataset/churn_dataset.csv", num_samples=1000, seed=42):
    np.random.seed(seed)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    customer_ids = [f"CUST-{1000 + i}" for i in range(num_samples)]
    genders = np.random.choice(["Male", "Female"], size=num_samples)
    ages = np.random.randint(18, 76, size=num_samples)
    tenures = np.random.randint(1, 73, size=num_samples) # 1 to 72 months
    
    contract_choices = ["Month-to-month", "One year", "Two year"]
    contract_probs = [0.55, 0.25, 0.20]
    contracts = np.random.choice(contract_choices, size=num_samples, p=contract_probs)
    
    payment_choices = ["Electronic check", "Mailed check", "Bank transfer", "Credit card"]
    payment_probs = [0.35, 0.20, 0.25, 0.20]
    payment_methods = np.random.choice(payment_choices, size=num_samples, p=payment_probs)
    
    internet_choices = ["DSL", "Fiber optic", "No"]
    internet_probs = [0.35, 0.45, 0.20]
    internet_services = np.random.choice(internet_choices, size=num_samples, p=internet_probs)
    
    num_services = np.random.randint(1, 7, size=num_samples)
    support_calls = np.random.poisson(lam=2.2, size=num_samples)
    support_calls = np.clip(support_calls, 0, 10)
    
    # Base monthly charges depending on internet service and number of services
    base_charge = np.where(internet_services == "Fiber optic", 75,
                  np.where(internet_services == "DSL", 45, 20))
    monthly_charges = base_charge + (num_services * 8.5) + np.random.uniform(-5, 10, size=num_samples)
    monthly_charges = np.round(np.clip(monthly_charges, 18.5, 125.0), 2)
    
    # Logistic function to calculate churn probability based on realistic risk factors
    logit = (
        -0.8
        + 0.04 * (monthly_charges - 60)
        - 0.05 * tenures
        + 0.45 * (support_calls - 2)
        + np.where(contracts == "Month-to-month", 1.2, np.where(contracts == "One year", -0.5, -1.2))
        + np.where(internet_services == "Fiber optic", 0.5, 0.0)
        + np.where(payment_methods == "Electronic check", 0.4, 0.0)
        + 0.015 * (ages - 40)
    )
    
    churn_prob = 1 / (1 + np.exp(-logit))
    churn_labels = (np.random.uniform(0, 1, size=num_samples) < churn_prob).astype(int)
    churn = np.where(churn_labels == 1, "Yes", "No")
    
    df = pd.DataFrame({
        "CustomerID": customer_ids,
        "Gender": genders,
        "Age": ages,
        "Tenure": tenures,
        "MonthlyCharges": monthly_charges,
        "Contract": contracts,
        "PaymentMethod": payment_methods,
        "InternetService": internet_services,
        "NumberOfServices": num_services,
        "SupportCalls": support_calls,
        "Churn": churn
    })
    
    df.to_csv(filepath, index=False)
    print(f"Dataset successfully created at {filepath} with {num_samples} records.")
    print(f"Overall Churn Rate: {(churn_labels.sum()/num_samples)*100:.1f}%")
    return df

if __name__ == "__main__":
    generate_sample_dataset()
