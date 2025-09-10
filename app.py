from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS (Define these FIRST) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True, nullable=False)
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(150), nullable=False)
    dob = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    github = db.Column(db.String(200), nullable=True)
    about = db.Column(db.Text, nullable=True)
    college = db.Column(db.String(200), nullable=True)
    qualification = db.Column(db.String(100), nullable=True)
    stream = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    interests = db.Column(db.Text, nullable=True)
    photo = db.Column(db.Text, nullable=True)
    applications = db.relationship('Application', backref='applicant', lazy=True)
    shortlists = db.relationship('Shortlist', backref='user', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    internship_id = db.Column(db.Integer, nullable=False)
    internship_title = db.Column(db.String(200), nullable=False)
    internship_org = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Applied')
    why_hire = db.Column(db.Text, nullable=True)
    work_sample = db.Column(db.String(300), nullable=True)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)

class Shortlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    internship_id = db.Column(db.Integer, nullable=False)

# --- CREATE DATABASE TABLES (AFTER models are defined) ---
with app.app_context():
    db.create_all()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

# ... (All your other routes like @app.route('/signup'), @app.route('/login'), etc. go here unchanged) ...
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user: return jsonify({'message': 'Email address already exists'}), 409
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(full_name=data['name'], email=data['email'], mobile=data['mobile'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    session['user_id'] = new_user.id
    return jsonify({'message': 'Signup successful', 'redirect': url_for('dashboard')}), 201
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']): return jsonify({'message': 'Invalid credentials'}), 401
    session['user_id'] = user.id
    if user.college: return jsonify({'message': 'Login successful', 'redirect': url_for('recommendations')}), 200
    else: return jsonify({'message': 'Login successful', 'redirect': url_for('dashboard')}), 200
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('dashboard.html')
@app.route('/application-form')
def application_form():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('application-form.html')
@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('recommendations.html')
@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('profile.html')
@app.route('/internship-details')
def internship_details():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('internship-details.html')
@app.route('/my-applications')
def my_applications():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('my-applications.html')
@app.route('/application-thank-you')
def application_thank_you():
    if 'user_id' not in session: return redirect(url_for('index'))
    return render_template('application-thank-you.html')
@app.route('/submit_application', methods=['POST'])
def submit_application():
    if 'user_id' not in session: return jsonify({'message': 'User not logged in'}), 401
    user = User.query.get(session['user_id'])
    if not user: return jsonify({'message': 'User not found'}), 404
    data = request.get_json()
    try:
        user.full_name = data.get('fullName', user.full_name)
        user.dob = data.get('dob')
        user.phone = data.get('phone', user.mobile)
        user.state = data.get('state')
        user.city = data.get('city')
        user.linkedin = data.get('linkedin')
        user.github = data.get('github')
        user.about = data.get('about')
        user.college = data.get('college')
        user.qualification = data.get('qualification')
        user.stream = data.get('stream')
        user.year = data.get('year')
        user.location = data.get('location')
        user.skills = json.dumps(data.get('skills', []))
        user.interests = json.dumps(data.get('interests', []))
        user.photo = data.get('photo', user.photo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500
    return jsonify({'message': 'Application saved!', 'redirect': url_for('recommendations')}), 200
@app.route('/get_user_details', methods=['GET'])
def get_user_details():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    if not user: return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'name': user.full_name, 'skills': json.loads(user.skills) if user.skills else [], 'photo': user.photo, 'stream': user.stream, 'interests': json.loads(user.interests) if user.interests else []
    })
@app.route('/get_application_data', methods=['GET'])
def get_application_data():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    if not user: return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'fullName': user.full_name, 'email': user.email, 'dob': user.dob, 'phone': user.phone or user.mobile, 'state': user.state, 'city': user.city, 'linkedin': user.linkedin, 'github': user.github, 'about': user.about, 'college': user.college, 'qualification': user.qualification, 'stream': user.stream, 'year': user.year, 'location': user.location, 'skills': json.loads(user.skills) if user.skills else [], 'interests': json.loads(user.interests) if user.interests else [], 'photo': user.photo
    })
@app.route('/apply', methods=['POST'])
def apply():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    user_id = session['user_id']
    internship_id = data.get('internship_id')
    existing_application = Application.query.filter_by(user_id=user_id, internship_id=internship_id).first()
    if existing_application: return jsonify({'error': 'You have already applied for this internship.'}), 409
    new_application = Application(user_id=user_id, internship_id=internship_id, internship_title=data.get('internship_title'), internship_org=data.get('internship_org'), why_hire=data.get('why_hire'), work_sample=data.get('work_sample'))
    db.session.add(new_application)
    db.session.commit()
    return jsonify({'message': 'Application submitted successfully!', 'redirect': url_for('application_thank_you')}), 200
@app.route('/get_my_applications', methods=['GET'])
def get_my_applications():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    apps = Application.query.filter_by(user_id=session['user_id']).order_by(Application.applied_on.desc()).all()
    applications_list = []
    for app in apps:
        days_since_applied = (datetime.utcnow() - app.applied_on).days
        status = app.status
        if days_since_applied > 14: status = 'Shortlisted'
        elif days_since_applied > 7: status = 'Under Review'
        applications_list.append({
            'id': app.internship_id, 'title': app.internship_title, 'org': app.internship_org, 'status': status, 'applied_on': app.applied_on.strftime('%d %b, %Y')
        })
    return jsonify(applications_list)
@app.route('/shortlist', methods=['GET'])
def get_shortlist():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    shortlisted_ids = [item.internship_id for item in user.shortlists]
    return jsonify(shortlisted_ids)
@app.route('/shortlist/<int:internship_id>', methods=['POST'])
def add_to_shortlist(internship_id):
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    existing = Shortlist.query.filter_by(user_id=session['user_id'], internship_id=internship_id).first()
    if not existing:
        new_shortlist_item = Shortlist(user_id=session['user_id'], internship_id=internship_id)
        db.session.add(new_shortlist_item)
        db.session.commit()
    return jsonify({'message': 'Added to shortlist'}), 201
@app.route('/shortlist/<int:internship_id>', methods=['DELETE'])
def remove_from_shortlist(internship_id):
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    item = Shortlist.query.filter_by(user_id=session['user_id'], internship_id=internship_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({'message': 'Removed from shortlist'}), 200

# --- RUN APP ---
if __name__ == '__main__':
    app.run(debug=True)
