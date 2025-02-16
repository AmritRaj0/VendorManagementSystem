Overview:

The Vendor Management System API is a Flask-based RESTful web service designed to manage users, vehicles, drivers,
and document status within a structured permission system. The API supports role-based access control (RBAC) with three primary roles: Super Vendor, Sub Vendor, and Driver.

Features:

User Management (Registration & Authentication)
Vehicle Registration & Management
Driver Registration & Status Updates
Document Expiry Handling
Role-Based Access Control (RBAC)
Session-Based Authentication


Folder Structure:

vendor_management_api/
│── app.py                    # Main Flask application file
│── requirements.txt           # Required dependencies
│── config.py                  # Configuration settings (future enhancement)
│── models/
│   ├── user.py                # User class & authentication methods
│   ├── vehicle.py             # Vehicle class & operations
│   ├── driver.py              # Driver class & operations
│   ├── document.py            # Document handling & expiry checks
│── routes/
│   ├── auth_routes.py         # User authentication routes
│   ├── vehicle_routes.py      # Vehicle-related API endpoints
│   ├── driver_routes.py       # Driver-related API endpoints
│   ├── document_routes.py     # Document management routes
│── utils/
│   ├── validators.py          # Validation functions (email, password, etc.)
│   ├── permissions.py         # RBAC permission handling


Role-Based Access Control (RBAC):

Super Vendor:
Full Access (Manage all vehicles, drivers, and users)

Sub Vendor:
Limited Access (Can manage assigned drivers and vehicles)

Driver:
Restricted Access (Can update status, view documents)



Security & Validation:

Password Hashing: Uses werkzeug.security to securely hash and verify passwords.
Email Validation: Ensures valid email format using regex.
Password Strength: Requires at least 8 characters, one uppercase letter, one special character, and one digit.
Session-Based Authentication: Utilizes Flask sessions to manage user logins.
Document Expiry Check: Ensures insurance and license documents are valid before allowing registration.


Future Enhancements:

Implement a database (PostgreSQL or MongoDB) for persistent storage.
Add JWT-based authentication for better security.
Extend the document management system to allow file uploads.
