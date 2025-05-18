# Vehicle Service and Repair Management System (VSRMS)

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![MySQL](https://img.shields.io/badge/mysql-8.0+-orange.svg)

A comprehensive web application designed to streamline operations in vehicle service centers. VSRMS enables efficient management of customer data, vehicle information, service scheduling, and payment processing.

## 📋 Features

### For Customers
- Register and manage personal accounts
- Add and update vehicle information
- Schedule service appointments
- Track service history and status
- Make payments for completed services
- View upcoming maintenance recommendations

### For Administrators
- Dashboard with overview of all services and statistics
- Manage customer accounts and vehicle information
- Update service status (scheduled, in-progress, completed)
- Process payments and generate invoices
- View comprehensive service history

## 🚀 Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: MySQL
- **Authentication**: Flask-Login
- **Forms**: WTForms with Flask-WTF
- **Password Security**: Bcrypt

## 📦 Installation

### Prerequisites
- Python 3.7+
- MySQL Server 8.0+
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/vsrms.git
   cd vsrms
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database**
   - Create a MySQL database
   - Update the database connection string in `app.py`:
     ```python
     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost:3306/vehicle_management'
     ```

5. **Initialize the database**
   ```bash
   python app.py
   ```
   This will create all necessary tables in your database.

## 🏃‍♂️ Running the Application

1. Start the application
   ```bash
   python app.py
   ```

2. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

## 👥 User Types

### Customer
- Register a new account
- Login with email and password
- Manage vehicles and schedule services

### Administrator
- Access the admin panel via admin login
- Manage services and customer accounts
- Update service status and process payments

## 📱 Application Structure

```
vsrms/
├── app.py              # Main application entry point
├── db.py               # Database configuration
├── forms.py            # Form definitions
├── models.py           # Database models
├── routes.py           # Route definitions
├── requirements.txt    # Project dependencies
├── static/             # Static files (CSS, JS)
└── templates/          # HTML templates
    ├── admin/          # Admin templates
    └── customer/       # Customer templates
```

## 🔒 Security Features

- Password hashing with Bcrypt
- User authentication with Flask-Login
- Route protection with login_required decorator
- Role-based access control

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

