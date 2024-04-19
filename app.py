from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Database models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bookings = db.relationship('Booking', backref='student', lazy=True)

class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    computers = db.relationship('Computer', backref='lab', lazy=True)

class Computer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    computer_id = db.Column(db.Integer, db.ForeignKey('computer.id'), nullable=False)
    booking_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

# Populate the labs and computers
def populate_labs():
    with app.app_context():
        Lab.query.delete()
        db.session.commit()
        existing_labs = Lab.query.all()
        existing_lab_names = [lab.name for lab in existing_labs]

        labs_data = [
            {"name": "Lab 120", "computers": 20},
            {"name": "Lab L44", "computers": 15},
            {"name": "Lab 170", "computers": 10},
            {"name": "Lab 210", "computers": 10},
            {"name": "Lab 128", "computers": 10},
            # Add more labs as needed
        ]

        for lab_info in labs_data:
            if lab_info["name"] not in existing_lab_names:
                lab = Lab(name=lab_info["name"])
                db.session.add(lab)
                db.session.commit()
                for _ in range(lab_info["computers"]):
                    computer = Computer(lab_id=lab.id)
                    db.session.add(computer)
                db.session.commit()

# Call the populate_labs function to populate the database
populate_labs()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        student = get_student_by_email(form.email.data)
        if student:
            if check_password(student.password, form.password.data):
                session['id'] = student.id
                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect email or password', 'danger')
        else:
            flash('Student with this email does not exist', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password
        hashed_password = generate_password_hash(form.password.data)
        # Create a new student record
        new_student = Student(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )
        db.session.add(new_student)
        db.session.commit()
        flash('Registration successful, please login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
def dashboard():
    # Fetch available labs and display on dashboard
    labs = Lab.query.all()
    
    # Fetch user's bookings if logged in
    user_bookings = None
    if 'id' in session:
        user_id = session['id']
        user_bookings = Booking.query.filter_by(student_id=user_id).all()
        
    return render_template('dashboard.html', labs=labs, user_bookings=user_bookings)


@app.route('/book/<int:computer_id>', methods=['POST'])
def book_computer(computer_id):
    # Check if the user is logged in
    if 'id' in session:
        student_id = session['id']
        
        # Check if the student already has a booking
        existing_booking = Booking.query.filter_by(student_id=student_id).first()
        if existing_booking:
            flash('You already have an active booking', 'warning')
            return redirect(url_for('dashboard'))
        
        # Check if the computer is available
        computer = Computer.query.get(computer_id)
        if computer and not computer.is_booked:
            # Mark the computer as booked
            computer.is_booked = True
            db.session.commit()
            # Create a new booking record
            new_booking = Booking(
                student_id=student_id,
                computer_id=computer_id
            )
            db.session.add(new_booking)
            db.session.commit()
            flash('Computer booked successfully', 'success')
        else:
            flash('Computer is already booked', 'danger')
    else:
        flash('You must be logged in to book a computer', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/lab_details/<int:lab_id>')
def lab_details(lab_id):
    lab = Lab.query.get_or_404(lab_id)
    available_computers = Computer.query.filter_by(lab_id=lab_id, is_booked=False).all()
    return render_template('lab_details.html', lab=lab, available_computers=available_computers)

@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'id' in session:
        # Retrieve student's data from database
        student_id = session['id']
        student = Student.query.get(student_id)
        if student:
            return render_template('profile.html', student=student)
        else:
            flash('Student not found', 'danger')
            return redirect(url_for('login'))
    else:
        flash('You must be logged in to view this page', 'warning')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('id', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

def get_student_by_email(email):
    return Student.query.filter_by(email=email).first()

def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password) 

@app.route('/search')
def search():
    query = request.args.get('query')

    if query:
        matching_labs = Lab.query.filter(Lab.name.ilike(f'%{query}%')).all()

        try:
            # Attempt to convert the query to an integer to search by computer ID
            query_int = int(query)
            matching_computers = Computer.query.filter_by(id=query_int).all()
        except ValueError:
            # If the query cannot be converted to an integer, search by lab names
            matching_computers = Computer.query.filter(Computer.lab_id.in_([lab.id for lab in matching_labs])).all()
    else:
        matching_labs = Lab.query.all()
        matching_computers = Computer.query.all()

    return render_template('dashboard.html', labs=matching_labs, matching_computers=matching_computers)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    # Check if the user is logged in
    if 'id' in session:
        student_id = session['id']
        booking = Booking.query.get(booking_id)
        if booking and booking.student_id == student_id:
            # Mark the booking as cancelled
            booking.is_cancelled = True
            db.session.commit()
            # Mark the corresponding computer as available
            computer = Computer.query.get(booking.computer_id)
            if computer:
                computer.is_booked = False
                db.session.commit()
            flash('Booking cancelled successfully', 'success')
        else:
            flash('You are not authorized to cancel this booking', 'danger')
    else:
        flash('You must be logged in to cancel a booking', 'warning')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
