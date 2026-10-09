from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Starting Customer Churn Prediction & Analytics Dashboard...")
    print("Access application at: http://127.0.0.1:5000")
    print("Default Admin Login: admin / admin123")
    app.run(host='0.0.0.0', port=5000, debug=True)
