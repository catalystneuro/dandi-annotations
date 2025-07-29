"""
Flask web application for DANDI External Resources annotation
"""
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
import re

# Add the parent directory to the path to import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dandiannotations.webapp.utils.yaml_handler import YAMLHandler
from dandiannotations.webapp.utils.schema_utils import get_resource_relation_options, get_resource_type_options
from dandiannotations.models.models import ExternalResource, AnnotationContributor

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
YAML_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'external_resources', 'external_resources.yaml')
yaml_handler = YAMLHandler(YAML_FILE_PATH)

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

@app.route('/')
def index():
    """Main form page"""
    relation_options = get_resource_relation_options()
    type_options = get_resource_type_options()
    
    return render_template('form.html', 
                         relation_options=relation_options,
                         type_options=type_options)

@app.route('/submit', methods=['POST'])
def submit_resource():
    """Handle form submission"""
    try:
        # Get form data
        form_data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['resource_name', 'resource_url', 'repository', 
                          'relation', 'resource_type', 'contributor_name', 
                          'contributor_email']
        
        for field in required_fields:
            if not form_data.get(field, '').strip():
                flash(f'Error: {field.replace("_", " ").title()} is required', 'error')
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
        
        # Create external resource data
        resource_data = {
            'annotation_contributor': contributor_data,
            'annotation_date': datetime.now().isoformat(),
            'name': form_data['resource_name'],
            'url': form_data['resource_url'],
            'repository': form_data['repository'],
            'relation': form_data['relation'],
            'resourceType': form_data['resource_type'],
            'schemaKey': 'ExternalResource'
        }
        
        # Add GitHub PR URL if provided
        if form_data.get('github_pr_url'):
            if validate_url(form_data['github_pr_url']):
                resource_data['github_pr_url'] = form_data['github_pr_url']
            else:
                flash('Error: Invalid GitHub PR URL format', 'error')
                return redirect(url_for('index'))
        
        # Validate using Pydantic models
        try:
            contributor = AnnotationContributor(**contributor_data)
            resource = ExternalResource(**resource_data)
        except Exception as e:
            flash(f'Validation error: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Save to YAML file
        yaml_handler.add_resource(resource_data)
        
        flash('Resource successfully added!', 'success')
        return redirect(url_for('success'))
        
    except Exception as e:
        flash(f'Error saving resource: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/success')
def success():
    """Success page after form submission"""
    return render_template('success.html')

@app.route('/clear', methods=['POST'])
def clear_form():
    """Handle clear form request"""
    return redirect(url_for('index'))

def main():
    """Main entry point for the webapp."""
    app.run(debug=True, host='127.0.0.1', port=5000)


if __name__ == '__main__':
    main()
