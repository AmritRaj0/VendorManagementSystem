//
// 🌐 Vendor Management App Logic
// ----------------------------------

// Helper Function for Alerts
function showMessage(msg) {
    alert(msg);
}

// --------------------------
// 🚀 Registration Logic
// --------------------------

function toggleFields() {
    const role = document.getElementById('roleSelect').value;
    const parentIdField = document.getElementById('parentIdField');
    const driverFields = document.getElementById('driverFields');

    if (role === 'Sub Vendor') {
        parentIdField.classList.remove('hidden');
        driverFields.classList.add('hidden');
    } else if (role === 'Driver') {
        parentIdField.classList.remove('hidden');
        driverFields.classList.remove('hidden');
    } else {
        parentIdField.classList.add('hidden');
        driverFields.classList.add('hidden');
    }
}

function registerUser() {
    const role = document.getElementById('roleSelect').value;
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const parentId = document.getElementById('parentId').value.trim();
    const licenseNumber = document.getElementById('licenseNumber').value.trim();
    const approvalDate = document.getElementById('approvalDate').value;

    if (!role || !name || !email || !password) {
        showMessage('⚠️ Please fill in all required fields.');
        return;
    }

    let payload = { name, email, password, role };

    if (role === 'Sub Vendor' || role === 'Driver') {
        if (!parentId) {
            showMessage('⚠️ Parent ID is required.');
            return;
        }
        payload.parent_id = parseInt(parentId);
    }

    if (role === 'Driver') {
        if (!licenseNumber || !approvalDate) {
            showMessage('⚠️ License number and approval date are required.');
            return;
        }
        payload.license_number = licenseNumber;
        payload.approval_date = approvalDate;
    }

    fetch('http://127.0.0.1:5000/register_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors', 
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        showMessage(data.message);
        if (data.message.includes('successfully')) {
            window.location.href = 'index.html';
        }
    })
    .catch(err => {
        console.error('Error registering user:', err);
        showMessage('❌ Registration failed.');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const roleSelect = document.getElementById('roleSelect');
    if (roleSelect) roleSelect.addEventListener('change', toggleFields);
});


// --------------------------
// Register Vehicle
// --------------------------
function registerVehicle() {
    const vehicleId = document.getElementById('vehicleId').value.trim();
    const registrationNumber = document.getElementById('registrationNumber').value.trim();
    const insuranceExpiry = document.getElementById('insuranceExpiry').value;

    if (!vehicleId || !registrationNumber || !insuranceExpiry) {
        showMessage('⚠️ Please fill in all fields.');
        return;
    }

    const payload = {
        vehicle_id: parseInt(vehicleId),
        registration_number: registrationNumber,
        insurance_expiry: insuranceExpiry
    };

    fetch('http://127.0.0.1:5000/register_vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        showMessage(`🚗 Vehicle Registration: ${data.message}`);
        window.location.href = 'registration.html';
    })
    .catch(err => {
        console.error('Vehicle Registration Error:', err);
        showMessage('❌ Failed to register vehicle.');
    });
}


function goToVehiclePage() {
    window.location.href = 'registervehicle.html';
}

// --------------------------
// 🔑 Login Logic
// --------------------------

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value.trim();

            if (!email || !password) {
                showMessage('⚠️ Please enter your email and password.');
                return;
            }

            try {
                const response = await fetch('http://127.0.0.1:5000/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    mode: 'cors',
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (response.ok) {
                    showMessage(`✅ Login Successful: ${data.role}`);
                    sessionStorage.setItem('userRole', data.role);
                    sessionStorage.setItem('userEmail', email);

                    redirectToRoleDashboard(data.role);
                } else {
                    showMessage(`⚠️ Login Failed: ${data.message}`);
                }
            } catch (error) {
                console.error('Login error:', error);
                showMessage('❌ Network error.');
            }
        });
    }
});

function redirectToRoleDashboard(role) {
    const pageMapping = {
        'Super Vendor': 'super_vendor.html',
        'Sub Vendor': 'sub_vendor.html',
        'Driver': 'driver.html'
    };

    const targetPage = pageMapping[role] || 'index.html';
    window.location.href = targetPage;
}

// --------------------------
// 🔄 Persistent Role-Based Navigation
// --------------------------

document.addEventListener('DOMContentLoaded', () => {
    const userRole = sessionStorage.getItem('userRole');
    const currentPage = window.location.pathname.split('/').pop();

    if (currentPath === '/registervehicle.html') return;

    // Prevent redirection if on registration or index page
    if (currentPage === 'registration.html' || currentPage === 'index.html') {
        return;
    }

    const expectedPage = userRole ? `${userRole.toLowerCase().replace(' ', '_')}.html` : 'index.html';

    if (currentPage !== expectedPage) {
        window.location.href = expectedPage;
    }
});

// --------------------------
// 📊 Dashboard Logic
// --------------------------

function fetchVendorHierarchy() {
    fetch('http://127.0.0.1:5000/vendor_hierarchy', { mode: 'cors' })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            const hierarchyList = document.getElementById('vendorHierarchy');
            hierarchyList.innerHTML = '';
            if (data.sub_vendors.length === 0) {
                hierarchyList.innerHTML = '<li class="status-message">⚠️ No sub vendors found.</li>';
            } else {
                data.sub_vendors.forEach(sv => {
                    const li = document.createElement('li');
                    li.textContent = `👥 ${sv.sub_vendor.name} (ID: ${sv.sub_vendor.id})`;
                    hierarchyList.appendChild(li);
                });
            }
        })
        .catch(err => console.error('Failed to fetch hierarchy:', err));
}

// --------------------------
// Add Sub Vendor
// --------------------------
function addSubVendor() {
    const name = document.getElementById('subVendorName').value.trim();
    const email = document.getElementById('subVendorEmail').value.trim();
    const password = document.getElementById('subVendorPassword').value.trim();

    if (!name || !email || !password) {
        alert('Please fill in all fields.');
        return;
    }

    const payload = { name, email, password, role: 'Sub Vendor', parent_id: 1 };

    fetch('http://127.0.0.1:5000/register_user', {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        fetchVendorHierarchy();
    })
    .catch(err => console.error('Error adding sub vendor:', err));
}

// --------------------------
// Manage Permissions
// --------------------------
function managePermissions() {
    const subVendorId = document.getElementById('subVendorId').value;
    const permissions = document.getElementById('permissions').value.split(',');
    const action = document.getElementById('permissionAction').value;

    if (!subVendorId || permissions.length === 0) {
        alert('Please provide Sub Vendor ID and permissions.');
        return;
    }

    const endpoint = action === 'assign' ? '/assign_permissions' : '/revoke_permissions';
    const payload = {
        user_id: 1,
        sub_vendor_id: parseInt(subVendorId),
        permissions: permissions.map(p => p.trim())
    };

    fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        fetchVendorHierarchy();
    })
    .catch(err => console.error('Error managing permissions:', err));
}

// --------------------------
// Fetch Fleet Status
// --------------------------
function fetchFleetStatus() {
    fetch('http://127.0.0.1:5000/vendor_hierarchy', { mode: 'cors' })
        .then(response => response.json())
        .then(data => {
            const fleetStatusDiv = document.getElementById('fleetStatus');
            fleetStatusDiv.innerHTML = '';
            if (data.fleet_status.length === 0) {
                fleetStatusDiv.textContent = '⚠️ No fleet data available.';
            } else {
                data.fleet_status.forEach(vehicle => {
                    const statusText = `🚘 Vehicle ID: ${vehicle.vehicle_id}, Status: ${vehicle.status}`;
                    const statusEl = document.createElement('div');
                    statusEl.textContent = statusText;
                    fleetStatusDiv.appendChild(statusEl);
                });
            }
        })
        .catch(err => console.error('Failed to fetch fleet status:', err));
}

function fetchSubVendorData() {
    fetch('http://127.0.0.1:5000/sub_vendor_dashboard', { mode: 'cors' })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            const statusDisplay = document.getElementById('statusDisplay');
            if (data.drivers.length === 0 && data.fleet_status.length === 0) {
                statusDisplay.innerHTML = `<p>No data available for this sub-vendor.</p>`;
                return;
            }

            let html = `<h4>👥 Drivers:</h4>`;
            data.drivers.forEach(driver => {
                html += `<p>ID: ${driver.id} | Name: ${driver.name} | Status: ${driver.status}</p>`;
            });

            html += `<h4>🚗 Fleet Status:</h4>`;
            data.fleet_status.forEach(vehicle => {
                html += `<p>Vehicle ID: ${vehicle.vehicle_id} | Status: ${vehicle.status}</p>`;
            });

            statusDisplay.innerHTML = html;
        })
        .catch(err => {
            console.error('Error fetching Sub Vendor data:', err);
            document.getElementById('statusDisplay').innerHTML = '❌ Failed to load data.';
        });
}

// Assign Driver to Vehicle
function assignDriver() {
    const vehicleId = document.getElementById('assignVehicleId').value;
    const driverId = document.getElementById('assignDriverId').value;

    if (!vehicleId || !driverId) {
        alert('⚠️ Please provide both Vehicle ID and Driver ID.');
        return;
    }

    const payload = { vehicle_id: parseInt(vehicleId), driver_id: parseInt(driverId) };

    fetch('http://127.0.0.1:5000/assign_driver_to_vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors',
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        alert(`ℹ️ ${data.message}`);
        fetchSubVendorData();
    })
    .catch(err => console.error('Error assigning driver:', err));
}

// Disable Vehicle
function disableVehicle() {
    const vehicleId = document.getElementById('disableVehicleId').value;

    if (!vehicleId) {
        alert('⚠️ Please provide a Vehicle ID.');
        return;
    }

    const payload = { vehicle_id: parseInt(vehicleId) };

    fetch('http://127.0.0.1:5000/disable_vehicle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors',
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        alert(`ℹ️ ${data.message}`);
        fetchSubVendorData();
    })
    .catch(err => console.error('Error disabling vehicle:', err));
}

// --------------------------------------
// Driver Dashboard Logic
// --------------------------------------

// Fetch Driver Status
function fetchDriverStatus() {
    fetch('http://127.0.0.1:5000/sub_vendor_dashboard', { mode: 'cors' })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            const driverStatusDiv = document.getElementById('driverStatus');
            const currentUserId = sessionStorage.getItem('user_id');

            const driver = data.drivers.find(d => d.id == currentUserId);
            if (driver) {
                driverStatusDiv.innerHTML = `
                    <strong>Name:</strong> ${driver.name}<br>
                    <strong>Status:</strong> ${driver.status}<br>
                    <strong>Email:</strong> ${driver.email}
                `;
            } else {
                driverStatusDiv.innerHTML = "❌ Driver information not found.";
            }
        })
        .catch(err => {
            console.error('Error fetching driver status:', err);
            document.getElementById('driverStatus').innerHTML = "⚠️ Failed to load status.";
        });
}

// Update Driver Status
function updateDriverStatus() {
    const selectedStatus = document.getElementById('statusSelect').value;

    fetch('http://127.0.0.1:5000/set_driver_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: selectedStatus })
    })
    .then(response => response.json())
    .then(data => {
        alert(`🚦 ${data.message}`);
        fetchDriverStatus();
    })
    .catch(err => {
        console.error('Error updating driver status:', err);
        alert('❌ Failed to update status.');
    });
}

// Fetch Driver Documents
function fetchDriverDocuments() {
    fetch('http://127.0.0.1:5000/vendor_hierarchy', { mode: 'cors' })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            const docDiv = document.getElementById('documentInfo');
            const currentUserId = sessionStorage.getItem('user_id');

            const driverDocs = data.driver_availability.find(d => d.driver_id == currentUserId);
            if (driverDocs) {
                docDiv.innerHTML = `
                    <strong>Document Status:</strong> ${driverDocs.status}<br>
                    <strong>Last Updated:</strong> ${new Date(driverDocs.updated_at).toLocaleString()}
                `;
            } else {
                docDiv.innerHTML = "⚠️ No document info available.";
            }
        })
        .catch(err => {
            console.error('Error fetching documents:', err);
            document.getElementById('documentInfo').innerHTML = "⚠️ Failed to load documents.";
        });
}


function logout() {
    fetch('http://127.0.0.1:5000/logout', { method: 'POST', mode: 'cors' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            sessionStorage.clear();
            window.location.href = 'index.html';
        })
        .catch(err => console.error('Logout failed:', err));
}
