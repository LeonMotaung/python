import matplotlib
matplotlib.use('Agg')  # Set the backend before importing pyplot

from flask import Flask, render_template, request, flash, redirect, url_for, send_file, session, Response
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from forms import SignupForm, LoginForm
from extensions import db, login_manager
from models.mongodb import mongodb
import os
from dotenv import load_dotenv
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from models.pdf_generator import generate_pdf
from scipy import stats
import time
import shutil
import numpy as np
from io import BytesIO
from datetime import datetime



# Load environment variables
load_dotenv()

app = Flask(__name__)
from datetime import datetime

@app.route('/')
def index_v2():
    now = datetime.now()
    return render_template('index.html', now=now)
# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'temp'), exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'images'), exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xls', 'xlsx'}

def clean_column_name(name):
    return name.replace(':', '_').replace(' ', '_')

def generate_visualizations(df):
    visualizations = []
    plt.style.use('seaborn')
    
    # Create visualizations for numerical columns
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    timestamp = int(time.time())
    
    for col in numeric_cols:
        col_name = clean_column_name(str(col))
        
        # Histogram
        plt.figure(figsize=(10, 6))
        plt.hist(df[col], bins=30, edgecolor='black')
        plt.title(f'Histogram of {col}')
        plt.xlabel(col)
        plt.ylabel('Frequency')
        img_filename = f'hist_{col_name}_{timestamp}.png'
        img_path = os.path.join(app.config['STATIC_FOLDER'], 'images', img_filename)
        plt.savefig(img_path)
        plt.close()
        visualizations.append({
            'title': f'Histogram of {col}',
            'path': url_for('static', filename=f'images/{img_filename}'),
            'filename': img_filename
        })
        
        # Box plot
        plt.figure(figsize=(10, 6))
        sns.boxplot(y=df[col])
        plt.title(f'Box Plot of {col}')
        img_filename = f'box_{col_name}_{timestamp}.png'
        img_path = os.path.join(app.config['STATIC_FOLDER'], 'images', img_filename)
        plt.savefig(img_path)
        plt.close()
        visualizations.append({
            'title': f'Box Plot of {col}',
            'path': url_for('static', filename=f'images/{img_filename}'),
            'filename': img_filename
        })
        
        # Density plot
        plt.figure(figsize=(10, 6))
        sns.kdeplot(data=df[col], fill=True)
        plt.title(f'Density Plot of {col}')
        img_filename = f'density_{col_name}_{timestamp}.png'
        img_path = os.path.join(app.config['STATIC_FOLDER'], 'images', img_filename)
        plt.savefig(img_path)
        plt.close()
        visualizations.append({
            'title': f'Density Plot of {col}',
            'path': url_for('static', filename=f'images/{img_filename}'),
            'filename': img_filename
        })
        
        # Q-Q plot
        plt.figure(figsize=(10, 6))
        stats.probplot(df[col], dist="norm", plot=plt)
        plt.title(f'Q-Q Plot of {col}')
        img_filename = f'qq_{col_name}_{timestamp}.png'
        img_path = os.path.join(app.config['STATIC_FOLDER'], 'images', img_filename)
        plt.savefig(img_path)
        plt.close()
        visualizations.append({
            'title': f'Q-Q Plot of {col}',
            'path': url_for('static', filename=f'images/{img_filename}'),
            'filename': img_filename
        })
    
    return visualizations

@app.route('/')
@login_required
def index():
    # Get user's files from MongoDB
    user_files = mongodb.get_user_files(current_user.id)
    
    return render_template('index.html',
                         summary_stats=session.get('summary_stats'),
                         visualizations=session.get('visualizations'),
                         pdf_path=session.get('pdf_path'),
                         pdf_filename=session.get('pdf_filename'),
                         user_files=user_files)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            # Save file to MongoDB
            file_id = mongodb.save_file(
                file.read(),
                file.filename,
                current_user.id,
                file.content_type
            )
            
            # Read the file for analysis
            file.seek(0)
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Clean up old images
            images_dir = os.path.join(app.config['STATIC_FOLDER'], 'images')
            for filename in os.listdir(images_dir):
                try:
                    os.remove(os.path.join(images_dir, filename))
                except:
                    pass
            
            # Generate summary statistics
            summary_stats = {
                'Number of Rows': int(len(df)),
                'Number of Columns': int(len(df.columns)),
                'Missing Values': int(df.isnull().sum().sum()),
                'Numeric Columns': int(len(df.select_dtypes(include=['int64', 'float64']).columns)),
                'Categorical Columns': int(len(df.select_dtypes(include=['object']).columns))
            }
            
            # Add descriptive statistics for numeric columns
            numeric_stats = df.describe()
            for col in numeric_stats.columns:
                for stat in ['mean', 'std', 'min', 'max']:
                    value = numeric_stats[col][stat]
                    if isinstance(value, (np.int64, np.int32, np.int16, np.int8)):
                        value = int(value)
                    elif isinstance(value, (np.float64, np.float32)):
                        value = float(value)
                    summary_stats[f'{col} - {stat}'] = round(value, 2)
            
            # Generate visualizations
            visualizations = generate_visualizations(df)
            
            # Generate PDF report
            pdf_filename = f'report_{int(time.time())}.pdf'
            pdf_path = generate_pdf(pdf_filename, df, summary_stats, [viz['path'] for viz in visualizations])
            
            # Save analysis results to MongoDB
            mongodb.save_analysis_results(file_id, summary_stats, visualizations)
            
            # Store results in session
            session['summary_stats'] = summary_stats
            session['visualizations'] = visualizations
            session['pdf_path'] = pdf_path
            session['pdf_filename'] = pdf_filename
            
            flash('File analyzed successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a CSV or Excel file.', 'error')
    return redirect(url_for('index'))

@app.route('/download/<filename>')
@login_required
def download_pdf(filename):
    try:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='report.pdf'
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/file/<file_id>')
@login_required
def get_file(file_id):
    try:
        # Get file from MongoDB
        file = mongodb.get_file(file_id)
        
        # Create response with file data
        return Response(
            file.read(),
            mimetype=file.content_type,
            headers={
                "Content-Disposition": f"attachment;filename={file.filename}"
            }
        )
    except Exception as e:
        flash(f'Error retrieving file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<file_id>')
@login_required
def delete_file(file_id):
    try:
        # Delete file and its analysis results from MongoDB
        mongodb.delete_file(file_id)
        flash('File deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            organization=form.organization.data,
            tax_number=form.tax_number.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Welcome!', 'success')
        return redirect(url_for('index'))
    
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Clear any existing session data
            session.clear()
            
            # Check if this is the user's first login
            login_history = mongodb.get_login_history(user.email)
            is_first_login = len(login_history) == 0
            
            # Record login
            mongodb.record_login(user.email)
            
            # Log the user in
            login_user(user)
            
            if is_first_login:
                flash('Welcome! Please upload a file to start your analysis.', 'info')
            else:
                flash('Welcome back!', 'success')
            
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    # Clear session data
    session.clear()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/signup')
def signup_v2():
    now = datetime.now()
    return render_template('signup.html', now=now)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}
@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

if __name__ == '__main__':
    app.run(debug=True)
