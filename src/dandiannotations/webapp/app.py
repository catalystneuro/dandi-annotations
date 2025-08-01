"""
Flask web application for DANDI External Resources annotation
"""
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_session import Session
from datetime import datetime, timedelta
import re

# Add the parent directory to the path to import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dandiannotations.webapp.utils.yaml_handler import YAMLHandler
from dandiannotations.webapp.utils.submission_handler import SubmissionHandler
from dandiannotations.webapp.utils.schema_utils import get_resource_relation_options, get_resource_type_options
from dandiannotations.webapp.utils.auth import AuthManager, login_required
from dandiannotations.models.models import ExternalResource, AnnotationContributor

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Session configuration for 24-hour sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'dandi_auth:'

# Initialize session
Session(app)

# Configuration
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'submissions')
submission_handler = SubmissionHandler(SUBMISSIONS_DIR)

# Keep old YAML handler for backward compatibility if needed
YAML_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'external_resources', 'external_resources.yaml')
yaml_handler = YAMLHandler(YAML_FILE_PATH)

# Authentication configuration
MODERATORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'moderators.yaml')
auth_manager = AuthManager(MODERATORS_CONFIG_PATH)

@app.context_processor
def inject_auth_status():
    """Make authentication status available to all templates"""
    return {
        'is_authenticated': auth_manager.is_authenticated(),
        'current_user': auth_manager.get_current_user()
    }

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_url(url):
    """Basic URL validation"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None

def validate_orcid(orcid):
    """Validate ORCID format"""
    if not orcid:
        return True  # ORCID is optional
    pattern = r'^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    return re.match(pattern, orcid) is not None

def validate_dandiset_id(dandiset_id):
    """Validate DANDI set ID format"""
    if not dandiset_id:
        return False
    # Accept either 6-digit format (000001) or full format (dandiset_000001)
    pattern = r'^(dandiset_)?[0-9]{6}$'
    return re.match(pattern, dandiset_id) is not None

@app.route('/')
def index():
    """Homepage showing all dandisets with submission counts"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10  # 10 dandisets per page
        
        # Get paginated dandisets with their submission counts
        paginated_dandisets, pagination_info = submission_handler.get_all_dandisets_paginated(page, per_page)
        
        # Get all dandisets for total statistics (not paginated)
        all_dandisets = submission_handler.get_all_dandisets()
        
        # Calculate total statistics
        total_community = sum(ds['community_count'] for ds in all_dandisets)
        total_endorsed = sum(ds['endorsed_count'] for ds in all_dandisets)
        total_dandisets = len(all_dandisets)
        
        return render_template('homepage.html',
                             all_dandisets=paginated_dandisets,
                             pagination=pagination_info,
                             total_community=total_community,
                             total_endorsed=total_endorsed,
                             total_dandisets=total_dandisets)
    except Exception as e:
        flash(f'Error loading homepage: {str(e)}', 'error')
        return render_template('homepage.html',
                             all_dandisets=[],
                             pagination={'page': 1, 'total_pages': 1, 'has_prev': False, 'has_next': False},
                             total_community=0,
                             total_endorsed=0,
                             total_dandisets=0)

@app.route('/submit')
def submit_form():
    """Submission form page"""
    relation_options = get_resource_relation_options()
    type_options = get_resource_type_options()
    
    return render_template('form.html', 
                         relation_options=relation_options,
                         type_options=type_options)

@app.route('/how-it-works')
def how_it_works():
    """How it works information page"""
    return render_template('how_it_works.html')

@app.route('/submit', methods=['POST'])
def submit_resource():
    """Handle form submission"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Validate required fields (including dandiset_id)
        required_fields = ['dandiset_id', 'resource_name', 'resource_url', 'repository', 
                          'relation', 'resource_type', 'contributor_name', 
                          'contributor_email']
        
        for field in required_fields:
            if not form_data.get(field, '').strip():
                flash(f'Error: {field.replace("_", " ").title()} is required', 'error')
                return redirect(url_for('index'))
        
        # Validate dandiset_id format
        if not validate_dandiset_id(form_data['dandiset_id']):
            flash('Error: Invalid DANDI set ID format. Use 6 digits (e.g., 000001) or full format (e.g., dandiset_000001)', 'error')
            return redirect(url_for('index'))
        
        # Validate email format
        if not validate_email(form_data['contributor_email']):
            flash('Error: Invalid email format', 'error')
            return redirect(url_for('index'))
        
        # Validate URLs
        if not validate_url(form_data['resource_url']):
            flash('Error: Invalid resource URL format', 'error')
            return redirect(url_for('index'))
        
        if form_data.get('contributor_url') and not validate_url(form_data['contributor_url']):
            flash('Error: Invalid contributor URL format', 'error')
            return redirect(url_for('index'))
        
        # Validate ORCID if provided
        if not validate_orcid(form_data.get('contributor_identifier')):
            flash('Error: Invalid ORCID format. Should be like: https://orcid.org/0000-0000-0000-0000', 'error')
            return redirect(url_for('index'))
        
        # Create annotation contributor
        contributor_data = {
            'name': form_data['contributor_name'],
            'email': form_data['contributor_email'],
            'schemaKey': 'AnnotationContributor'
        }
        
        if form_data.get('contributor_identifier'):
            contributor_data['identifier'] = form_data['contributor_identifier']
        
        if form_data.get('contributor_url'):
            contributor_data['url'] = form_data['contributor_url']
        
        # Create external resource data (including dandiset_id)
        resource_data = {
            'dandiset_id': form_data['dandiset_id'],
            'annotation_contributor': contributor_data,
            'annotation_date': datetime.now().astimezone().isoformat(),
            'name': form_data['resource_name'],
            'url': form_data['resource_url'],
            'repository': form_data['repository'],
            'relation': form_data['relation'],
            'resourceType': form_data['resource_type'],
            'schemaKey': 'ExternalResource'
        }
        
        # Add optional resource identifier if provided
        if form_data.get('resource_identifier'):
            resource_data['identifier'] = form_data['resource_identifier']
        
        # Validate using Pydantic models
        try:
            contributor = AnnotationContributor(**contributor_data)
            resource = ExternalResource(**resource_data)
        except Exception as e:
            flash(f'Validation error: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Save to community submissions folder using new submission handler
        filename = submission_handler.save_community_submission(form_data['dandiset_id'], resource_data)
        
        flash('Resource successfully submitted for community review!', 'success')
        return redirect(url_for('success', dandiset_id=form_data['dandiset_id']))
        
    except Exception as e:
        flash(f'Error saving resource: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/success')
def success():
    """Success page after form submission"""
    dandiset_id = request.args.get('dandiset_id')
    return render_template('success.html', dandiset_id=dandiset_id)

@app.route('/dandiset/<dandiset_id>')
def dandiset_resources(dandiset_id):
    """Display resources for a specific dandiset"""
    try:
        # Get pagination parameters
        endorsed_page = request.args.get('endorsed_page', 1, type=int)
        community_page = request.args.get('community_page', 1, type=int)
        per_page = 9  # 9 resources per page for 3x3 grid
        
        # Get paginated submissions
        community_submissions, community_pagination = submission_handler.get_community_submissions_paginated(
            dandiset_id, community_page, per_page)
        endorsed_submissions, endorsed_pagination = submission_handler.get_endorsed_submissions_paginated(
            dandiset_id, endorsed_page, per_page)
        
        # Get all dandisets for navigation
        all_dandisets = submission_handler.get_all_dandisets()
        
        # Format display ID as DANDI:XXXXXX
        display_id = f"DANDI:{dandiset_id.split('_')[1]}" if '_' in dandiset_id else f"DANDI:{dandiset_id.zfill(6)}"
        
        return render_template('dandiset_resources.html',
                             dandiset_id=dandiset_id,
                             display_id=display_id,
                             community_submissions=community_submissions,
                             endorsed_submissions=endorsed_submissions,
                             community_pagination=community_pagination,
                             endorsed_pagination=endorsed_pagination,
                             all_dandisets=all_dandisets)
    except Exception as e:
        flash(f'Error loading resources: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/moderate')
def moderate():
    """Moderation interface for all pending submissions"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 9  # 9 submissions per page for 3x3 grid
        
        # Get paginated pending community submissions across all dandisets
        pending_submissions, pagination_info = submission_handler.get_all_pending_submissions_paginated(page, per_page)
        
        # Get all dandisets for navigation
        all_dandisets = submission_handler.get_all_dandisets()
        
        return render_template('moderation.html',
                             pending_submissions=pending_submissions,
                             pagination=pagination_info,
                             all_dandisets=all_dandisets)
    except Exception as e:
        flash(f'Error loading pending submissions: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/endorse/<dandiset_id>/<filename>', methods=['GET', 'POST'])
@login_required
def endorse_submission(dandiset_id, filename):
    """Endorse a community submission"""
    if request.method == 'GET':
        # Show endorsement form
        try:
            submission = submission_handler.get_submission_by_filename(dandiset_id, filename, 'community')
            if not submission:
                flash('Submission not found', 'error')
                return redirect(url_for('moderate'))
            
            return render_template('endorse_form.html',
                                 submission=submission,
                                 dandiset_id=dandiset_id,
                                 filename=filename)
        except Exception as e:
            flash(f'Error loading submission: {str(e)}', 'error')
            return redirect(url_for('moderate'))
    
    elif request.method == 'POST':
        # Process endorsement
        try:
            # Get moderator information from form
            moderator_info = {
                'name': request.form.get('moderator_name', '').strip(),
                'email': request.form.get('moderator_email', '').strip(),
                'identifier': request.form.get('moderator_identifier', '').strip(),
                'url': request.form.get('moderator_url', '').strip()
            }
            
            # Validate required moderator fields
            if not moderator_info['name']:
                flash('Moderator name is required', 'error')
                return redirect(url_for('endorse_submission', dandiset_id=dandiset_id, filename=filename))
            
            if not moderator_info['email']:
                flash('Moderator email is required', 'error')
                return redirect(url_for('endorse_submission', dandiset_id=dandiset_id, filename=filename))
            
            # Validate email format
            if not validate_email(moderator_info['email']):
                flash('Invalid moderator email format', 'error')
                return redirect(url_for('endorse_submission', dandiset_id=dandiset_id, filename=filename))
            
            # Validate ORCID if provided
            if moderator_info['identifier'] and not validate_orcid(moderator_info['identifier']):
                flash('Invalid ORCID format', 'error')
                return redirect(url_for('endorse_submission', dandiset_id=dandiset_id, filename=filename))
            
            # Validate URL if provided
            if moderator_info['url'] and not validate_url(moderator_info['url']):
                flash('Invalid moderator URL format', 'error')
                return redirect(url_for('endorse_submission', dandiset_id=dandiset_id, filename=filename))
            
            # Remove empty fields
            moderator_info = {k: v for k, v in moderator_info.items() if v}
            
            # Get submission details for better success message
            submission = submission_handler.get_submission_by_filename(dandiset_id, filename, 'community')
            
            success = submission_handler.endorse_submission(dandiset_id, filename, moderator_info)
            if success:
                if submission:
                    resource_name = submission.get('name', 'Unknown Resource')
                    display_id = f"DANDI:{dandiset_id.split('_')[1]}" if '_' in dandiset_id else f"DANDI:{dandiset_id.zfill(6)}"
                    flash(f'Successfully endorsed "{resource_name}" for {display_id}', 'success')
                else:
                    flash(f'Successfully endorsed submission: {filename}', 'success')
            else:
                flash(f'Failed to endorse submission: {filename}', 'error')
        except Exception as e:
            flash(f'Error endorsing submission: {str(e)}', 'error')
        
        # Redirect back to moderation page
        return redirect(url_for('moderate'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for moderators"""
    if request.method == 'GET':
        # Show login form
        return render_template('login.html')
    
    elif request.method == 'POST':
        # Process login
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Verify credentials
        user_info = auth_manager.verify_credentials(username, password)
        if user_info:
            auth_manager.login_user(user_info)
            flash(f'Welcome, {user_info["name"]}!', 'success')
            
            # Redirect to next page if specified, otherwise to homepage
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout current user"""
    user_info = auth_manager.get_current_user()
    auth_manager.logout_user()
    
    if user_info:
        flash(f'Goodbye, {user_info["name"]}!', 'success')
    else:
        flash('You have been logged out', 'success')
    
    return redirect(url_for('index'))

@app.route('/clear', methods=['POST'])
def clear_form():
    """Handle clear form request"""
    return redirect(url_for('index'))

def main():
    """Main entry point for the webapp."""
    app.run(debug=True, host='127.0.0.1', port=5000)


if __name__ == '__main__':
    main()
