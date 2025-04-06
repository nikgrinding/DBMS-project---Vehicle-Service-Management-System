from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Vehicle, User, Service, Admin, ServiceHistory, Payment
from datetime import datetime
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from forms import LoginForm, CustomerRegisterForm, AdminRegisterForm, VehicleForm, ServiceForm, ServiceUpdateForm, PaymentForm, ServiceFilterForm
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "select_user" 

# Add template filter
@app.template_filter('is_admin')
def is_admin(user):
    return isinstance(user, Admin)

@app.route('/',methods=['GET','POST'])
def select_user():
    return render_template('select_user.html')

@app.route('/login_customer', methods=['GET', 'POST'])
def login_customer():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('customer_dashboard'))
            else:
                flash("Invalid email or password", "danger")
        else:
            flash("No account found with this email", "danger")
    return render_template('login_customer.html', form=form)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    form = LoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('dashboard_admin'))
            else:
                flash("Invalid email or password", "danger")
        else:
            flash("No admin account found with this email", "danger")
    return render_template('login_admin.html', form=form)

@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if isinstance(current_user, Admin):
        return redirect(url_for('dashboard_admin'))
    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    upcoming_services = Service.query.filter_by(user_id=current_user.id, status='scheduled').order_by(Service.scheduled_date).all()
    return render_template('customer/dashboard.html', vehicles=vehicles, upcoming_services=upcoming_services)

@app.route('/dashboard_admin', methods=['GET', 'POST'])
@login_required
def dashboard_admin():
    if not isinstance(current_user, Admin):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = ServiceUpdateForm()
    services = Service.query.options(db.joinedload(Service.user), db.joinedload(Service.vehicle)).all()
    
    if form.validate_on_submit():
        service_id = request.form.get('service_id')
        service = Service.query.get_or_404(service_id)
        
        service.status = form.status.data
        service.actual_date = form.actual_date.data
        service.cost = form.cost.data
        service.odometer_reading = form.odometer_reading.data
        service.notes = form.notes.data
        
        if form.status.data == 'completed':
            service.vehicle.last_service_date = service.actual_date
            service.vehicle.next_service_date = service.actual_date.replace(month=service.actual_date.month + 6)
        
        history = ServiceHistory(
            service_id=service.id,
            status=form.status.data,
            notes=f'Status updated to {form.status.data} by admin'
        )
        
        db.session.add(history)
        db.session.commit()
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('dashboard_admin'))
    
    return render_template('admin/dashboard.html', services=services, form=form)

@app.route('/view_vehicles')
@login_required
def view_vehicles():
    if isinstance(current_user, Admin):
        vehicles = Vehicle.query.all()
        return render_template('admin/vehicles.html', vehicles=vehicles)
    else:
        vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
        return render_template('customer/view_vehicles.html', vehicles=vehicles)

@app.route('/view_services')
@login_required
def view_services():
    # Redirect admin users to admin view
    if isinstance(current_user, Admin):
        services = Service.query.order_by(Service.scheduled_date).all()
        print(f"Admin view - Number of services found: {len(services)}")  # Debug print
        for service in services:
            print(f"Service ID: {service.id}, User: {service.user.name if service.user else 'No user'}, Vehicle: {service.vehicle.model if service.vehicle else 'No vehicle'}")  # Debug print
        flash(f"Found {len(services)} services in the system", "info")
        return render_template('admin/services.html', services=services)
    # For regular users, show their services
    services = Service.query.filter_by(user_id=current_user.id).order_by(Service.scheduled_date).all()
    return render_template('customer/services.html', services=services)

@app.route('/service_history')
@login_required
def service_history():
    # Redirect admin users to admin view
    if isinstance(current_user, Admin):
        services = Service.query.order_by(Service.scheduled_date.desc()).all()
        return render_template('admin/history.html', services=services)
    # For regular users, show their service history
    services = Service.query.filter_by(user_id=current_user.id).order_by(Service.scheduled_date.desc()).all()
    return render_template('customer/history.html', services=services)

@app.route('/view_payments')
@login_required
def view_payments():
    # Redirect admin users to admin view
    if isinstance(current_user, Admin):
        services = Service.query.filter(Service.cost.isnot(None)).order_by(Service.scheduled_date.desc()).all()
        return render_template('admin/payments.html', services=services)
    # For regular users, show their payments
    services = Service.query.filter_by(user_id=current_user.id).filter(Service.cost.isnot(None)).order_by(Service.scheduled_date.desc()).all()
    return render_template('customer/payments.html', services=services)

@app.route('/service_details/<int:service_id>', methods=['GET', 'POST'])
@login_required
def service_details(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Check if user has permission to view the service
    if not isinstance(current_user, Admin) and service.user_id != current_user.id:
        flash('You do not have permission to view this service.', 'error')
        return redirect(url_for('view_services'))
    
    form = ServiceUpdateForm(obj=service)
    
    if form.validate_on_submit():
        # For customers, only allow updating notes
        if not isinstance(current_user, Admin):
            service.notes = form.notes.data
            history = ServiceHistory(
                service_id=service.id,
                status=service.status,
                notes=f'Customer updated notes: {form.notes.data}'
            )
        else:
            # Admin can update all fields
            service.status = form.status.data
            service.actual_date = form.actual_date.data
            service.cost = form.cost.data
            service.odometer_reading = form.odometer_reading.data
            service.notes = form.notes.data
            
            if form.status.data == 'completed':
                service.vehicle.last_service_date = service.actual_date
                service.vehicle.next_service_date = service.actual_date.replace(month=service.actual_date.month + 6)
            
            history = ServiceHistory(
                service_id=service.id,
                status=form.status.data,
                notes=f'Status updated to {form.status.data}'
            )
        
        db.session.add(history)
        db.session.commit()
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('service_details', service_id=service_id))
    
    # Use different templates for admin and customer
    template = 'admin/service_details.html' if isinstance(current_user, Admin) else 'customer/service_details.html'
    return render_template(template, service=service, form=form)

@app.route('/delete_vehicle/<int:vehicle_id>')
@login_required
def delete_vehicle(vehicle_id):
    vehicle_to_delete = Vehicle.query.get_or_404(vehicle_id)
    # Ensure the vehicle belongs to the current user
    if vehicle_to_delete.user_id != current_user.id:
        flash('You do not have permission to delete this vehicle.', 'danger')
        return redirect(url_for('view_vehicles'))
    try:
        db.session.delete(vehicle_to_delete)
        db.session.commit()
        flash('Vehicle deleted successfully!', 'success')
        return redirect(url_for('view_vehicles'))
    except:
        flash('There was an error deleting the vehicle.', 'danger')
        return redirect(url_for('view_vehicles'))

@app.route('/update_vehicle/<int:vehicle_id>', methods=["GET", "POST"])
@login_required
def update_vehicle(vehicle_id):
    vehicle_to_update = Vehicle.query.get_or_404(vehicle_id)
    # Ensure the vehicle belongs to the current user
    if vehicle_to_update.user_id != current_user.id:
        flash('You do not have permission to update this vehicle.', 'danger')
        return redirect(url_for('view_vehicles'))
    
    form = VehicleForm(obj=vehicle_to_update)
    
    if form.validate_on_submit():
        try:
            vehicle_to_update.model = form.model.data
            vehicle_to_update.year = form.year.data
            vehicle_to_update.odo_reading = form.odo_reading.data
            vehicle_to_update.license_plate = form.license_plate.data
            vehicle_to_update.vin = form.vin.data
            if form.notes.data:  # Only update notes if provided
                vehicle_to_update.notes = form.notes.data

            db.session.commit()
            flash('Vehicle updated successfully!', 'success')
            return redirect(url_for('view_vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error updating the vehicle: {str(e)}', 'danger')
            return redirect(url_for('update_vehicle', vehicle_id=vehicle_id))
    
    return render_template('customer/update_vehicle.html', vehicle=vehicle_to_update, form=form)

@app.route('/update_customer', methods=["GET", "POST"])
@login_required
def update_user_details():
    if not isinstance(current_user, User):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    user = User.query.get_or_404(current_user.id)

    if request.method == "POST":
        try:
            user.name = request.form['name']
            user.phone = request.form['phone']
            user.address = request.form['address']
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('customer_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
            return redirect(url_for('update_user_details'))

    return render_template('customer/update_customer.html', user=user)

@app.route('/book_service/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def book_service(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = ServiceForm()
    
    if form.validate_on_submit():
        service = Service(
            vehicle_id=vehicle_id,
            user_id=current_user.id,
            service_type=form.service_type.data,
            scheduled_date=form.scheduled_date.data,
            notes=form.notes.data,
            odometer_reading=form.odo_reading.data,
            status='scheduled'
        )
        
        try:
            db.session.add(service)
            
            # Create initial service history
            history = ServiceHistory(
                service_id=service.id,
                status='scheduled',
                notes='Service scheduled'
            )
            db.session.add(history)
            
            db.session.commit()
            flash('Service booked successfully!', 'success')
            return redirect(url_for('view_services'))
        except Exception as e:
            db.session.rollback()
            flash('Error booking service. Please try again.', 'error')
            return redirect(url_for('book_service', vehicle_id=vehicle_id))
    
    return render_template('customer/book_service.html', form=form, vehicle=vehicle)

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('select_user'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_vehicles = Vehicle.query.count()
    total_services = Service.query.count()
    pending_services = Service.query.filter_by(status='scheduled').count()
    completed_services = Service.query.filter_by(status='completed').count()
    
    return render_template('admin/dashboard.html',
                         total_vehicles=total_vehicles,
                         total_services=total_services,
                         pending_services=pending_services,
                         completed_services=completed_services)

@app.route('/admin/vehicles')
@login_required
@admin_required
def admin_vehicles():
    form = ServiceFilterForm()
    vehicles = Vehicle.query.all()
    return render_template('admin/vehicles.html', vehicles=vehicles, form=form)

@app.route('/admin/services')
@login_required
@admin_required
def admin_services():
    form = ServiceFilterForm()
    services = Service.query.order_by(Service.scheduled_date).all()
    return render_template('admin/services.html', services=services, form=form)

@app.route('/admin/service/<int:service_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_service_details(service_id):
    service = Service.query.get_or_404(service_id)
    form = ServiceUpdateForm(obj=service)
    
    if form.validate_on_submit():
        service.status = form.status.data
        service.actual_date = form.actual_date.data
        service.cost = form.cost.data
        service.odometer_reading = form.odometer_reading.data
        service.notes = form.notes.data
        
        if form.status.data == 'completed':
            service.vehicle.last_service_date = service.actual_date
            service.vehicle.next_service_date = service.actual_date.replace(month=service.actual_date.month + 6)
        
        history = ServiceHistory(
            service_id=service.id,
            status=form.status.data,
            notes=f'Status updated to {form.status.data}'
        )
        db.session.add(history)
        db.session.commit()
        
        flash('Service updated successfully!', 'success')
        return redirect(url_for('main.admin_service_details', service_id=service_id))
    
    return render_template('admin/service_details.html', service=service, form=form)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    form = ServiceFilterForm()
    services = Service.query.order_by(Service.scheduled_date).all()
    return render_template('admin/reports.html', services=services, form=form)

@login_manager.user_loader
def load_user(user_id):
    # Try to load as Admin first
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    # If not found as Admin, try as User
    return User.query.get(int(user_id))

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('select_user'))

@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    form = CustomerRegisterForm()

    if form.validate_on_submit():
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash("This email is already registered.", "danger")
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, password=hashed_password,
                        name=form.name.data, phone=form.phone.data,
                        address=form.address.data)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for('login_customer'))

    
    return render_template('register.html', form=form)

@app.route('/register_admin',methods=['GET','POST'])
def register_admin():
    form = AdminRegisterForm()
    if form.validate_on_submit():
        existing_email = Admin.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash("This email is already registered.", "danger")
            return redirect(url_for('admin_register'))
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_admin = Admin(email=form.email.data, password=hashed_password,
                        name=form.name.data)
        db.session.add(new_admin)
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for('login_admin'))

    return render_template('register_admin.html', form=form)

@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        model = form.model.data
        year = form.year.data
        odo_reading = form.odo_reading.data
        license_plate = form.license_plate.data
        vin = form.vin.data

        existing_vehicle = Vehicle.query.filter_by(license_plate=license_plate).first()

        if existing_vehicle:
            flash("Error: License plate already exists!", "danger")
            return redirect(url_for('add_vehicle'))
        
        vehicle = Vehicle(user_id=current_user.id,
                        model=model,
                        year=year,  
                        odo_reading=odo_reading,
                        license_plate=license_plate,
                        vin=vin)   
        db.session.add(vehicle)
        db.session.commit()
        flash("Vehicle Added Successfully", "success")
        return redirect(url_for('view_vehicles'))

    return render_template('add_vehicle.html', form=form)

@app.route('/cancel_service/<int:service_id>', methods=['POST'])
@login_required
def cancel_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Ensure the service belongs to the current user
    if service.user_id != current_user.id:
        flash('You do not have permission to cancel this service.', 'danger')
        return redirect(url_for('view_services'))
    
    # Only allow cancellation of scheduled services
    if service.status != 'scheduled':
        flash('Only scheduled services can be cancelled.', 'danger')
        return redirect(url_for('view_services'))
    
    # Update service status
    service.status = 'cancelled'
    
    # Create service history entry
    history = ServiceHistory(
        service_id=service.id,
        status='cancelled',
        notes='Service cancelled by customer'
    )
    
    db.session.add(history)
    db.session.commit()
    
    flash('Service cancelled successfully!', 'success')
    return redirect(url_for('view_services'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    if not isinstance(current_user, User):
        flash('Only customers can delete their accounts.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    try:
        # Delete all vehicles associated with the user
        vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
        for vehicle in vehicles:
            db.session.delete(vehicle)
        
        # Delete all services associated with the user
        services = Service.query.filter_by(user_id=current_user.id).all()
        for service in services:
            db.session.delete(service)
        
        # Delete the user account
        db.session.delete(current_user)
        db.session.commit()
        
        logout_user()
        flash('Your account has been successfully deleted.', 'success')
        return redirect(url_for('select_user'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting your account. Please try again.', 'danger')
        return redirect(url_for('customer_dashboard'))

@app.route('/modify_service/<int:service_id>', methods=['GET', 'POST'])
@login_required
def modify_service(service_id):
    if not isinstance(current_user, Admin):
        flash('You do not have permission to modify services.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    service = Service.query.get_or_404(service_id)
    form = ServiceUpdateForm(obj=service)
    
    if form.validate_on_submit():
        try:
            # Update service details
            service.status = form.status.data
            service.scheduled_date = form.scheduled_date.data
            service.actual_date = form.actual_date.data
            service.cost = form.cost.data
            service.notes = form.notes.data
            
            # If service is completed, update vehicle's last service date
            if form.status.data == 'completed' and form.actual_date.data:
                service.vehicle.last_service_date = form.actual_date.data
                service.vehicle.next_service_date = form.actual_date.data.replace(month=form.actual_date.data.month + 6)
            
            # Create service history entry
            history = ServiceHistory(
                service_id=service.id,
                status=form.status.data,
                notes=f'Service modified by admin: {form.notes.data}'
            )
            
            db.session.add(history)
            db.session.commit()
            
            flash('Service updated successfully!', 'success')
            return redirect(url_for('view_services'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating service: {str(e)}', 'danger')
            return redirect(url_for('modify_service', service_id=service_id))
    
    return render_template('admin/modify_service.html', service=service, form=form)

@app.route('/make_payment/<int:service_id>', methods=['GET', 'POST'])
@login_required
def make_payment(service_id):
    service = Service.query.get_or_404(service_id)
    
    # Check if user has permission to make payment
    if not isinstance(current_user, Admin) and service.user_id != current_user.id:
        flash('You do not have permission to make this payment.', 'danger')
        return redirect(url_for('view_services'))
    
    # Check if service is completed and has a cost
    if service.status != 'completed' or not service.cost:
        flash('Service is not ready for payment.', 'danger')
        return redirect(url_for('service_details', service_id=service_id))
    
    # Check if payment already exists
    if service.payment and service.payment.status == 'completed':
        flash('Payment has already been made for this service.', 'info')
        return redirect(url_for('service_details', service_id=service_id))
    
    form = PaymentForm()
    form.amount.data = service.cost  # Pre-fill the amount
    
    if form.validate_on_submit():
        try:
            # Create or update payment
            if service.payment:
                payment = service.payment
            else:
                payment = Payment(service_id=service_id)
            
            payment.amount = form.amount.data
            payment.payment_method = form.payment_method.data
            payment.transaction_id = form.transaction_id.data
            payment.status = 'completed'
            payment.payment_date = datetime.utcnow()
            
            if not service.payment:
                db.session.add(payment)
            
            db.session.commit()
            flash('Payment processed successfully!', 'success')
            return redirect(url_for('service_details', service_id=service_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payment: {str(e)}', 'danger')
    
    return render_template('customer/make_payment.html', service=service, form=form)

@app.route('/admin/payments')
@login_required
@admin_required
def admin_payments():
    services = Service.query.filter(Service.status == 'completed').all()
    return render_template('admin/payments.html', services=services)

@app.route('/admin/payment_details/<int:service_id>')
@login_required
@admin_required
def admin_payment_details(service_id):
    service = Service.query.get_or_404(service_id)
    if service.status != 'completed':
        flash('Service is not completed.', 'danger')
        return redirect(url_for('admin_payments'))
    return render_template('admin/payment_details.html', service=service)