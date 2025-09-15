from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from ai import (
    generate_experience_description, 
    generate_project_description, 
    generate_summary_options
)
from weasyprint import HTML
import json # Import json for handling skills

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a-very-secret-key-for-flash-messages'
db = SQLAlchemy(app)

# --- Database Models (MODIFIED) ---
class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    about_me = db.Column(db.Text, nullable=False) # Summary
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.Text, nullable=True) # Stored as a JSON string
    
    educations = db.relationship('Education', backref='user', lazy=True, cascade="all, delete-orphan")
    projects = db.relationship('Project', backref='user', lazy=True, cascade="all, delete-orphan")
    experiences = db.relationship('Experience', backref='user', lazy=True, cascade="all, delete-orphan")
    certificates = db.relationship('Certificate', backref='user', lazy=True, cascade="all, delete-orphan")

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String(100), nullable=False)
    university = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    date_range = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    grade_type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_details.id'), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)
    date_range = db.Column(db.String(50), nullable=True)
    link = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False) # Technologies Used
    user_id = db.Column(db.Integer, db.ForeignKey('user_details.id'), nullable=False)

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    date_range = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_details.id'), nullable=False)

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    issuer = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=True)
    link = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_details.id'), nullable=False)


# --- Form Display Routes ---
@app.route('/create')
def create_portfolio_form():
    return render_template("form2.html", data={})

@app.route('/edit/<int:user_id>')
def edit_portfolio_form(user_id):
    user_to_edit = UserDetails.query.get_or_404(user_id)
    try:
        skills_data = json.loads(user_to_edit.skills or '{}')
    except json.JSONDecodeError:
        skills_data = {}
        
    data_dict = {
        'id': user_to_edit.id, 'name': user_to_edit.name, 'title': user_to_edit.title,
        'profile_picture': user_to_edit.profile_picture, 'email': user_to_edit.email,
        'location': user_to_edit.location, 'phone': user_to_edit.phone, 'about_me': user_to_edit.about_me,
        'linkedin_url': user_to_edit.linkedin_url, 'github_url': user_to_edit.github_url, 'skills': skills_data,
        'experiences': [{'role': exp.role, 'company': exp.company, 'location': exp.location, 'date_range': exp.date_range, 'description': exp.description} for exp in user_to_edit.experiences],
        'educations': [{'program_name': edu.program_name, 'university': edu.university, 'location': edu.location, 'date_range': edu.date_range, 'grade': edu.grade, 'grade_type': edu.grade_type} for edu in user_to_edit.educations],
        'projects': [{'project_name': proj.project_name, 'date_range': proj.date_range, 'link': proj.link, 'description': proj.description, 'skills': proj.skills} for proj in user_to_edit.projects],
        'certificates': [{'name': cert.name, 'issuer': cert.issuer, 'date': cert.date, 'link': cert.link} for cert in user_to_edit.certificates]
    }
    return render_template("form2.html", data=data_dict)

# --- Data Handling Route (MODIFIED) ---
@app.route('/save', methods=['POST'])
def save_portfolio():
    user_id = request.form.get('user_id')
    if user_id:
        user = UserDetails.query.get_or_404(user_id)
        flash_message = 'Your portfolio has been updated successfully!'
    else:
        user = UserDetails()
        flash_message = 'Your portfolio has been created successfully!'

    # Basic Info & Social Links
    user.name, user.title, user.email, user.location, user.phone, user.about_me = \
        request.form['name'], request.form['title'], request.form['email'], \
        request.form['location'], request.form['phone'], request.form['about_me']
    user.profile_picture = request.form.get('profile_picture')
    user.linkedin_url = request.form.get('linkedin_url')
    user.github_url = request.form.get('github_url')

    # Skills
    skill_categories = request.form.getlist('skill_category[]')
    skill_names = request.form.getlist('skill_names[]')
    skills_dict = {cat: name for cat, name in zip(skill_categories, skill_names) if cat and name}
    user.skills = json.dumps(skills_dict)

    if not user_id: 
        db.session.add(user)
    
    # Use direct assignment to leverage cascade="all, delete-orphan" for easy updates
    user.educations = [Education(program_name=request.form[f'program_name_{i}'], university=request.form[f'university_{i}'], location=request.form.get(f'education_location_{i}'), date_range=request.form[f'education_date_range_{i}'], grade=request.form[f'grade_{i}'], grade_type=request.form[f'grade_type_{i}']) for i in range(1, 10) if request.form.get(f'program_name_{i}')]
    user.projects = [Project(project_name=request.form[f'project_name_{i}'], date_range=request.form.get(f'project_date_range_{i}'), link=request.form.get(f'project_link_{i}'), description=request.form[f'description_{i}'], skills=request.form[f'skills_{i}']) for i in range(1, 10) if request.form.get(f'project_name_{i}')]
    user.experiences = [Experience(role=request.form[f'experience_role_{i}'], company=request.form[f'experience_company_{i}'], location=request.form.get(f'experience_location_{i}'), date_range=request.form[f'experience_date_range_{i}'], description=request.form[f'experience_description_{i}']) for i in range(1, 10) if request.form.get(f'experience_role_{i}')]
    user.certificates = [Certificate(name=request.form[f'certificate_name_{i}'], issuer=request.form[f'certificate_issuer_{i}'], date=request.form.get(f'certificate_date_{i}'), link=request.form.get(f'certificate_link_{i}')) for i in range(1, 10) if request.form.get(f'certificate_name_{i}')]
    
    db.session.commit()
    flash(flash_message, 'success')
    return redirect(url_for('index', id=user.id))

# --- AI & Other Routes (Unchanged) ---
@app.route('/generate-experience-description', methods=['POST'])
def generate_experience_route(): return jsonify({'description': generate_experience_description(request.json.get('keywords', ''))})
@app.route('/generate-project-description', methods=['POST'])
def generate_project_route(): return jsonify({'description': generate_project_description(request.json.get('brief', ''))})
@app.route('/generate-summary-options', methods=['POST'])
def generate_summary_options_route(): return jsonify({'summaries': generate_summary_options(request.json)})
@app.route('/')
def landing_page(): return render_template("index.html")
@app.route('/view-portfolio/<int:id>')
def index(id): return render_template("portfolio.html", user=UserDetails.query.get_or_404(id))
@app.route('/login', methods=['POST'])
def login():
    user = UserDetails.query.filter_by(name=request.form['name'], phone=request.form['phone']).first()
    if user: return redirect(url_for('edit_portfolio_form', user_id=user.id))
    flash('No portfolio found.', 'danger')
    return redirect(url_for('landing_page'))
@app.route('/search-users')
def search_users():
    query = request.args.get('name', '')
    if len(query) < 2: return jsonify([])
    users = UserDetails.query.filter(UserDetails.name.like(f'%{query}%')).limit(5).all()
    results = [{'id': user.id, 'name': user.name, 'title': user.title} for user in users]
    return jsonify(results)
@app.route('/submit-form', methods=['POST'])
def submit_from():
    flash(f"Thank you, {request.form.get('name')}! Your message has been received.", 'success')
    return redirect(url_for('index', id=request.form.get('user_id')))
@app.route('/download-resume/<int:id>/<template_name>')
def download_resume(id, template_name):
    if template_name not in ['classic', 'modern', 'compact']: abort(404)
    user_data = UserDetails.query.get_or_404(id)
    html = render_template(f'resume_template_{template_name}.html', user=user_data)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={user_data.name}_{template_name}_resume.pdf'
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)