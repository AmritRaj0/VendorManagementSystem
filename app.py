
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

# Sample data (In real systems, you'd use a database)
users = []
vehicles = []
drivers = []
documents = []

PERMISSIONS = [
    "add_vehicle",
    "remove_vehicle",
    "assign_driver",
    "view_document_status",
    "disable_vehicle_if_expired"
]

# Sample Roles
ROLE_SUPER_VENDOR = 'Super Vendor'
ROLE_SUB_VENDOR = 'Sub Vendor'
ROLE_DRIVER = 'Driver'

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Secret key for session management

# Helper functions for checking expiry
def check_document_expiry(document_date):
    # Calculate if the document is expired or due for renewal
    expiry_date = document_date + timedelta(days=365)  # Assume one year validity for now
    return expiry_date < datetime.now()

# Helper function to check user permissions
def check_permission(user, permission):
    if user.role == ROLE_SUPER_VENDOR:
        return True  # Super vendors have all permissions
    elif user.role == ROLE_SUB_VENDOR:
        if permission in user.permissions:
            return True
    return False

# Function for validating email format using regex
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Error classes for better exception handling
class InvalidUserError(Exception):
    pass

class VehicleNotFoundError(Exception):
    pass

class DocumentExpiredError(Exception):
    pass

# User class to encapsulate user-related methods
class User:
    def __init__(self, name, email, password, role, parent_id=None, permissions=None, status=None):
        self.id = len(users) + 1
        self.name = name
        self.email = email
        self.password = generate_password_hash(password)
        self.role = role
        self.parent_id = parent_id  # For sub-vendors
        self.permissions = permissions or []
        self.status = status or 'available'  # Default status is available

    def check_permission(self, permission):
        return check_permission(self, permission)

    @staticmethod
    def authenticate(email, password):
        user = next((u for u in users if u.email == email), None)
        if user and check_password_hash(user.password, password):
            return user
        raise InvalidUserError("Invalid username or password")

# Document class to manage document-related operations
class Document:
    def __init__(self, driver_id, doc_type, doc_file):
        self.driver_id = driver_id
        self.doc_type = doc_type
        self.doc_file = doc_file
        self.upload_date = datetime.now()

    def is_expired(self):
        return check_document_expiry(self.upload_date)

# Vehicle class to manage vehicle-related operations
class Vehicle:
    def __init__(self, vehicle_id, driver_id=None, registration_number=None, insurance_expiry=None):
        self.id = vehicle_id
        self.driver_id = driver_id
        self.registration_number = registration_number
        self.insurance_expiry = insurance_expiry
        self.status = 'Active'

    def is_expired(self):
        return check_document_expiry(self.insurance_expiry)

    def disable(self):
        self.status = 'Disabled'

# Flask API Routes

# User registration (Vendor onboarding)
# Vehicle registration
@app.route('/register_vehicle', methods=['POST'])
def register_vehicle():
    try:
        data = request.get_json()

        # Check for required fields
        if not data.get('vehicle_id') or not data.get('registration_number') or not data.get('insurance_expiry'):
            return jsonify({"message": "Missing required fields"}), 400

        # Check if vehicle_id or registration_number already exists
        if any(v.id == data['vehicle_id'] for v in vehicles):
            return jsonify({"message": "Vehicle ID already exists. Choose a unique ID."}), 400

        if any(v.registration_number == data['registration_number'] for v in vehicles):
            return jsonify({"message": "Registration number already exists. Choose a unique registration number."}), 400

        # Insurance expiry date validation
        insurance_expiry = datetime.strptime(data['insurance_expiry'], '%Y-%m-%d')
        # if check_document_expiry(insurance_expiry):
                #     return jsonify({"message": "Vehicle's insurance is expired. Cannot register."}), 400  

        # Registering the vehicle
        vehicle = Vehicle(
            vehicle_id=data['vehicle_id'],
            registration_number=data['registration_number'],
            insurance_expiry=insurance_expiry
        )
        vehicles.append(vehicle)
        return jsonify({"message": f"Vehicle registered successfully with ID: {vehicle.id}"}), 201

    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Route to set driver status (Available/Unavailable)
@app.route('/set_driver_status', methods=['POST'])
def set_driver_status():
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('status'):
            return jsonify({"message": "Missing required fields"}), 400

        # Validate the status value (available/unavailable)
        if data['status'] not in ['available', 'unavailable']:
            return jsonify({"message": "Invalid status value. It should be 'available' or 'unavailable'."}), 400

        # Get the logged-in driver
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "User not logged in."}), 401

        driver = next((user for user in users if user.id == user_id and user.role == ROLE_DRIVER), None)
        if not driver:
            return jsonify({"message": "Driver not found."}), 404

        # Update driver status
        driver.status = data['status']
        return jsonify({"message": f"Driver status updated to {data['status']}."}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/register_user', methods=['POST'])
def register_user():
    try:
        data = request.get_json()

        # Check for required fields
        if not data.get('name') or not data.get('email') or not data.get('password') or not data.get('role'):
            return jsonify({"message": "Missing required fields"}), 400

        # Email validation
        if not is_valid_email(data['email']):
            return jsonify({"message": "Invalid email format"}), 400

        # Ensure the email is unique
        if any(user.email == data['email'] for user in users):
            return jsonify({"message": "Email is already registered"}), 400

        # Password validation (at least 8 chars, one uppercase, one digit, one special character)
        if not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", data['password']):
            return jsonify({
                "message": "Password must be at least 8 characters long, contain one uppercase letter, "
                           "one special character, and at least one digit."
            }), 400

        # Registering a Super Vendor
        if data['role'] == ROLE_SUPER_VENDOR:
            user = User(
                name=data['name'],
                email=data['email'],
                password=data['password'],
                role=data['role'],
                parent_id=None,
                permissions=PERMISSIONS,  
            )
            users.append(user)
            return jsonify({"message": f"Super Vendor registered successfully with User ID: {user.id}"}), 201

        # Registering a Sub Vendor
        elif data['role'] == ROLE_SUB_VENDOR:
            parent_id = data.get('parent_id')
            if not parent_id:
                return jsonify({"message": "Parent ID is required for Sub Vendor registration"}), 400
            parent_user = next((user for user in users if user.id == parent_id), None)
            if not parent_user or parent_user.role != ROLE_SUPER_VENDOR:
                return jsonify({"message": "Parent ID must correspond to a Super Vendor"}), 400
            user = User(
                name=data['name'],
                email=data['email'],
                password=data['password'],
                role=data['role'],
                parent_id=parent_id,
                permissions=[],  
            )
            users.append(user)
            return jsonify({"message": f"Sub Vendor registered successfully with User ID: {user.id} under Super Vendor {parent_user.id}"}), 201

        # Registering a Driver
        elif data['role'] == ROLE_DRIVER:
            parent_id = data.get('parent_id')
            license_number = data.get('license_number')
            approval_date = data.get('approval_date')

            if not parent_id or not license_number or not approval_date:
                return jsonify({"message": "Missing required fields for driver registration"}), 400
            
            parent_user = next((user for user in users if user.id == parent_id and user.role == ROLE_SUB_VENDOR), None)

            if not parent_user:
                return jsonify({"message": "Parent ID must belong to a Sub Vendor"}), 400

            # Check if the driver's license is expired
            approval_date = datetime.strptime(approval_date, '%Y-%m-%d')
            if check_document_expiry(approval_date):
                return jsonify({"message": "Driver's license is expired. Cannot register."}), 400

            driver = User(
                name=data['name'],
                email=data['email'],
                password=data['password'],
                role=data['role'],
                parent_id=parent_id,
                permissions=[],  
            )
            drivers.append(driver)
            users.append(driver)
            documents.append({"driver_id": driver.id, "license_number": license_number, "approval_date": approval_date})
            return jsonify({"message": f"Driver registered successfully with ID: {driver.id} under Sub Vendor {parent_user.id}"}), 201

        return jsonify({"message": "Invalid role"}), 400

    except Exception as e:
        return jsonify({"message": str(e)}), 500


# User login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return jsonify({"message": "Missing required fields"}), 400
        
        # Email validation
        if not is_valid_email(data['email']):
            return jsonify({"message": "Invalid email format"}), 400

        # Authenticate user
        user = User.authenticate(data['email'], data['password'])
        
        session['user_id'] = user.id  # Store user ID in session
        return jsonify({"message": "Login successful", "role": user.role}), 200

    except InvalidUserError as e:   
        return jsonify({"message": str(e)}), 401


@app.route('/vendor_hierarchy', methods=['GET'])
def get_vendor_hierarchy():
    try:
        user_id = session.get('user_id')
        if not user_id:
            raise InvalidUserError("User not authenticated")

        user = next((u for u in users if u.id == user_id), None)
        if not user or user.role != ROLE_SUPER_VENDOR:
            raise InvalidUserError("Unauthorized access or invalid user")

        # Fetch all sub-vendors
        sub_vendors = [u for u in users if u.parent_id == user_id]

        # Prepare sub-vendor data without exposing passwords
        sub_vendors_data = []
        for sub_vendor in sub_vendors:
            sub_vendor_dict = {**sub_vendor.__dict__}  # Create a copy of the object as a dictionary
            sub_vendor_dict.pop("password", None)  # Remove the password field
            sub_vendors_data.append({"sub_vendor": sub_vendor_dict})

        fleet_status = [{'vehicle_id': v.id, 'status': v.status} for v in vehicles]
        driver_availability = [{'driver_id': d.id, 'status': 'Available', 'parent_id': d.parent_id if d.id not in [v.driver_id for v in vehicles] else 'Unavailable'} for d in drivers]

        return jsonify({
            "sub_vendors": sub_vendors_data,
            "fleet_status": fleet_status,
            "driver_availability": driver_availability
        })

    except InvalidUserError as e:
        return jsonify({"message": str(e)}), 403 


# Assign permissions to sub-vendor
@app.route('/assign_permissions', methods=['POST'])
def assign_permissions():
    try:
        data = request.get_json()
        if not data.get('user_id') or not data.get('sub_vendor_id') or not data.get('permissions'):
            return jsonify({"message": "Missing required fields"}), 400

        user = next((u for u in users if u.id == data['user_id']), None)
        if not user or user.role != ROLE_SUPER_VENDOR:
            return jsonify({"message": "Unauthorized access"}), 403  # ❌ Deny access to non-Super Vendors

        sub_vendor = next((u for u in users if u.id == data['sub_vendor_id'] and u.parent_id == data['user_id']), None)
        if not sub_vendor:
            return jsonify({"message": "Sub-vendor not found"}), 404

        # Assign specific permissions to the sub-vendor
        sub_vendor.permissions = list(set(sub_vendor.permissions + data['permissions']))
        return jsonify({"message": "Permissions assigned successfully"})
    
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# Revoke permissions from a sub-vendor (Super Vendor only)
@app.route('/revoke_permissions', methods=['POST'])
def revoke_permissions():
    try:
        data = request.get_json()
        if not data.get('user_id') or not data.get('sub_vendor_id') or not data.get('permissions'):
            return jsonify({"message": "Missing required fields"}), 400

        user = next((u for u in users if u.id == data['user_id']), None)
        
        # ✅ Strict check: Only Super Vendors can revoke permissions
        if not user or user.role != ROLE_SUPER_VENDOR:
            return jsonify({"message": "Unauthorized access"}), 403  

        sub_vendor = next((u for u in users if u.id == data['sub_vendor_id'] and u.parent_id == data['user_id']), None)

        if not sub_vendor:
            return jsonify({"message": "Sub-vendor not found"}), 404

        # ✅ Revoke specific permissions from the sub-vendor
        sub_vendor.permissions = [perm for perm in sub_vendor.permissions if perm not in data['permissions']]
        return jsonify({"message": "Permissions revoked successfully"})
    
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# Other routes remain the same...
# Document upload (for drivers)
@app.route('/upload_document', methods=['POST'])
def upload_document():
    try:
        data = request.get_json()
        if not data.get('driver_id') or not data.get('doc_type') or not data.get('doc_file'):
            return jsonify({"message": "Missing required fields"}), 400

        document = Document(
            driver_id=data['driver_id'],
            doc_type=data['doc_type'],
            doc_file=data['doc_file']
        )
        documents.append(document)
        is_expired = document.is_expired()
        return jsonify({"message": "Document uploaded", "is_expired": is_expired})

    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Disable vehicle if document is expired
@app.route('/disable_vehicle', methods=['POST'])
def disable_vehicle():
    try:
        data = request.get_json()
        vehicle_id = data.get('vehicle_id')

        if not vehicle_id:
            return jsonify({"message": "Vehicle ID is required"}), 400

        # Find the vehicle by ID
        vehicle = next((v for v in vehicles if v.id == vehicle_id), None)
        if not vehicle:
            return jsonify({"message": "Vehicle not found"}), 404

        # Check if the user has permission
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "User not logged in."}), 401

        user = next((u for u in users if u.id == user_id), None)
        if not user or not user.check_permission("disable_vehicle_if_expired"):
            return jsonify({"message": "Unauthorized access"}), 403  # Permission check

        # Check if the document for the vehicle is expired
        document = next((doc for doc in vehicles if vehicle_id == doc.id), None)
        if not document:
            return jsonify({"message": "No document found for this vehicle"}), 404

        if document.is_expired():
            document.disable()
            return jsonify({"message": f"Vehicle {document.id} has been disabled due to expired document"}), 200
        else:
            return jsonify({"message": f"Vehicle {document.id} is operational as the document is valid"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/assign_driver_to_vehicle', methods=['POST'])
def assign_driver_to_vehicle():
    try:
        data = request.get_json()

        # Check for required fields
        if not data.get('vehicle_id') or not data.get('driver_id'):
            return jsonify({"message": "Missing required fields"}), 400

        # Get the logged-in user (either Super Vendor or Sub Vendor)
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "User not logged in."}), 401

        user = next((u for u in users if u.id == user_id), None)
        if not user or user.role not in [ROLE_SUPER_VENDOR, ROLE_SUB_VENDOR] or not user.check_permission("assign_driver"):
            return jsonify({"message": "Unauthorized access"}), 403

        # Get the vehicle and driver based on IDs
        vehicle = next((v for v in vehicles if v.id == data['vehicle_id']), None)
        driver = next((d for d in users if d.id == data['driver_id'] and d.role == ROLE_DRIVER), None)

        if not vehicle:
            return jsonify({"message": "Vehicle not found"}), 404
        if not driver:
            return jsonify({"message": "Driver not found"}), 404

        # Check if the vehicle and driver are available
        if vehicle.status != 'Active':
            return jsonify({"message": "Vehicle is not available"}), 400
        if driver.status != 'available':
            return jsonify({"message": "Driver is not available"}), 400

        # Assign the driver to the vehicle
        vehicle.driver_id = driver.id
        
        # Set the statuses to Busy for both vehicle and driver
        vehicle.status = 'Busy'
        driver.status = 'Busy'

        return jsonify({"message": f"Driver {driver.name} assigned to vehicle {vehicle.id}. Both are now marked as Busy."}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Function to find available drivers
def get_available_drivers():
    available_drivers = [driver.id for driver in users if driver.role == ROLE_DRIVER and driver.status == 'available']
    return available_drivers

# Function to find available vehicles
def get_available_vehicles():
    available_vehicles = [vehicle.id for vehicle in vehicles if vehicle.status == 'Active' and vehicle.driver_id is None]
    return available_vehicles

# Example route to view available drivers
@app.route('/available_drivers', methods=['GET'])
def available_drivers():
    try:
        available_drivers = get_available_drivers()
        return jsonify({"available_drivers": available_drivers}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# Example route to view available vehicles
@app.route('/available_vehicles', methods=['GET'])
def available_vehicles():
    try:
        available_vehicles = get_available_vehicles()
        return jsonify({"available_vehicles": available_vehicles}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# Sub Vendor Dashboard
@app.route('/sub_vendor_dashboard', methods=['GET'])
def sub_vendor_dashboard():
    try:
        # Ensure the user is authenticated
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"message": "User not logged in."}), 401

        # Fetch the user details (sub-vendor)
        user = next((u for u in users if u.id == user_id), None)
        if not user or user.role != ROLE_SUB_VENDOR:
            return jsonify({"message": "Unauthorized access."}), 403

        # Fetch drivers under this sub-vendor
        drivers_under_sub_vendor = [u for u in users if u.parent_id == user.id and u.role == ROLE_DRIVER]
        
        # Fetch vehicles associated with the sub-vendor's drivers
        vehicles_under_sub_vendor = [v for v in vehicles if v.driver_id in [d.id for d in drivers_under_sub_vendor]]

        drivers_under_sub_vendor_data=[]
        for sub_vendor in drivers_under_sub_vendor:
            drivers_under_sub_vendor_data_dict = {**sub_vendor.__dict__}  # Create a copy of the object as a dictionary
            drivers_under_sub_vendor_data_dict.pop("password", None)  # Remove the password field
            drivers_under_sub_vendor_data.append({"sub_vendor": drivers_under_sub_vendor_data_dict})
        # Check driver availability (whether the driver is assigned to a vehicle or not)
        driver_availability = [
            {'driver_id': d.id, 'status': 'Available' if not any(v.driver_id == d.id for v in vehicles_under_sub_vendor) else 'Unavailable'}
            for d in drivers_under_sub_vendor
        ]

        # Prepare the response with the data specific to the sub-vendor
        return jsonify({
            "drivers": drivers_under_sub_vendor_data,
            "fleet_status": [{"vehicle_id": v.id, "status": v.status} for v in vehicles_under_sub_vendor],
            "driver_availability": driver_availability
        })

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logout successful"}), 200


CORS(app)
# Running the app
if __name__ == "__main__":
    app.run(debug=True)
