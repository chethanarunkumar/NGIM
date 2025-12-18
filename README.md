# 📦 NGIM – Next-Gen Inventory Management System

NGIM (Next-Gen Inventory Management System) is a cloud-based, AI-powered inventory solution designed for shop owners and small businesses to efficiently manage stock, sales, expiry alerts, and data-driven decisions.

---

## 🚀 Features

- 📊 Inventory & Stock Management  
- 🧾 Billing & Sales Tracking  
- ⏰ Expiry Alerts (Next 30 Days)  
- 🔁 Auto Reorder System (low-stock based restocking support)  
- 📈 Monthly Revenue Analytics  
- 🧠 AI-based Product Forecasting  
- 🔗 Product Bundle Recommendations (Owner-focused)  

---

## 🧠 AI & Analytics Module

The system integrates intelligent models to assist business owners:

- **XGBoost** – Monthly sales forecasting  
- **FP-Growth / Apriori** – Product bundle & combo recommendations  
- **Statistical Analytics** – Identification of fast-moving and slow-moving products  

> AI recommendations are designed **for shop owners**, not end customers.

---

## 🛠️ Tech Stack

### Backend
- Python (Flask)
- PostgreSQL
- SQLAlchemy / Psycopg2

### Frontend
- HTML
- CSS
- JavaScript

### AI / ML
- XGBoost
- Pandas, NumPy
- MLXtend (FP-Growth)

---

## ☁️ Deployment

- **Application Server:** Render  
- **Backend Framework:** Flask  
- **Database:** PostgreSQL (Render)  

The frontend is rendered using Flask templates (HTML, CSS, JavaScript) and served directly from the backend.

All sensitive configurations (database URL, secrets) are managed using environment variables.


---

## 📁 Project Structure

```text
NGIM/
├── NextGen/
│   ├── app/
│   │   ├── routes/
│   │   ├── templates/
│   │   ├── static/
│   │   └── ai_engine.py
│   ├── data/
│   └── run.py
├── requirements.txt
└── README.md
```
---

## 🎓 Academic Context

This project is developed as part of a **Engineering project**, focusing on:
- Real-world inventory management challenges  
- AI-driven business intelligence  
- Cloud-based scalable deployment  

---

## 👨‍💻 Author

**Chethan**  
Information Science & Engineering  
Aspiring Data Scientist & Full-Stack Developer  

---

## 📌 Note

This repository does **not** contain any credentials or sensitive data.  
All secrets are securely managed via environment variables.
