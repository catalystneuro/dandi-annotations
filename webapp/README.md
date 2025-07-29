# DANDI External Resources Web App

A Flask-based web application for creating and managing external resource annotations for DANDI datasets. This webapp provides a user-friendly interface that replicates the DANDI resource input form and integrates seamlessly with your existing Pydantic models and YAML storage system.

## Features

- **Intuitive Form Interface**: Matches the design and functionality of the DANDI resource form
- **Comprehensive Validation**: Uses your existing Pydantic models for robust data validation
- **YAML Integration**: Saves data in the same format as your existing `external_resources.yaml`
- **Automatic Backups**: Creates timestamped backups before modifying files
- **Real-time Validation**: Client-side and server-side validation with helpful error messages
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-save**: Preserves form data in browser localStorage

## Project Structure

```
webapp/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── setup.py              # Setup script
├── README.md             # This file
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── form.html         # Main resource input form
│   └── success.html      # Success page
├── static/
│   ├── css/
│   │   └── style.css     # Custom styling
│   └── js/
│       └── form.js       # Form interactions and validation
└── utils/
    ├── yaml_handler.py   # YAML file operations
    └── schema_utils.py   # DANDI schema integration
```

## Quick Start

### 1. Setup

Run the setup script to create a virtual environment and install dependencies:

```bash
cd webapp
python setup.py
```

### 2. Run the Application

Activate the virtual environment and start the Flask server:

**On macOS/Linux:**
```bash
source venv/bin/activate
python app.py
```

**On Windows:**
```bash
venv\Scripts\activate
python app.py
```

### 3. Access the Web App

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

## Form Fields

The webapp includes all the fields from your DANDI resource form:

### Resource Information
- **Identifier**: Optional identifier for the resource
- **Title**: Name/title of the resource (required)
- **URL**: Web address of the resource (required)
- **Repository**: Name of the hosting repository (required)
- **Resource Relation**: Relationship to the dataset (dropdown, required)
- **Resource Type**: Type of resource (dropdown, required)

### Annotation Contributor
- **Name**: Contributor's full name (required)
- **Email**: Contributor's email address (required)
- **ORCID**: Optional ORCID identifier (auto-formatted)
- **URL**: Optional contributor website

### Additional Information
- **GitHub PR URL**: Optional link to related pull request

## Data Flow

1. **Form Submission**: User fills out and submits the form
2. **Validation**: Data is validated using your Pydantic models
3. **Backup**: Current YAML file is backed up with timestamp
4. **Storage**: New resource is appended to `external_resources.yaml`
5. **Confirmation**: Success page confirms the operation

## Validation Features

- **Email Format**: Validates proper email structure
- **URL Format**: Ensures valid HTTP/HTTPS URLs
- **ORCID Format**: Validates ORCID identifier format
- **Required Fields**: Enforces required field completion
- **Pydantic Integration**: Uses your existing models for comprehensive validation

## File Operations

- **Automatic Backups**: Creates `.backup_YYYYMMDD_HHMMSS` files before changes
- **YAML Preservation**: Maintains existing file structure and formatting
- **Error Handling**: Graceful handling of file operation errors

## Browser Features

- **Auto-save**: Form data is saved to localStorage as you type
- **Keyboard Shortcuts**: 
  - `Ctrl/Cmd + Enter`: Submit form
  - `Escape`: Clear form
- **Tooltips**: Helpful information on hover
- **Responsive Design**: Works on all screen sizes

## Development

### Adding New Fields

1. Update the form template (`templates/form.html`)
2. Add validation in `app.py`
3. Update the Pydantic models if needed
4. Add any new schema options to `utils/schema_utils.py`

### Customizing Styles

Edit `static/css/style.css` to modify the appearance. The design uses Bootstrap 5 with custom overrides.

### Adding Features

The codebase is structured for easy extension:
- Add new routes in `app.py`
- Create new templates in `templates/`
- Add utility functions in `utils/`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the virtual environment is activated
2. **YAML File Not Found**: The app will create the file on first use
3. **Validation Errors**: Check that your Pydantic models are compatible
4. **Port Already in Use**: Change the port in `app.py` or stop other Flask apps

### Debug Mode

The app runs in debug mode by default for development. To disable:

```python
app.run(debug=False, host='127.0.0.1', port=5000)
```

### Logs

Check the terminal output for detailed error messages and request logs.

## Security Notes

- Change the secret key in `app.py` for production use
- Consider adding authentication for production deployment
- Validate all user inputs (already implemented)
- Use HTTPS in production environments

## Integration with DANDI

This webapp is designed to work seamlessly with your existing DANDI annotation workflow:

1. **Model Compatibility**: Uses your existing `ExternalResource` and `AnnotationContributor` models
2. **YAML Format**: Outputs data in the exact format expected by your system
3. **Validation**: Ensures all data meets DANDI schema requirements
4. **Backup Safety**: Protects existing data with automatic backups

## Future Enhancements

Potential features for future development:
- Edit existing resources
- Bulk import/export
- User authentication
- Resource search and filtering
- API endpoints for programmatic access
- Integration with DANDI API

## Support

For issues or questions:
1. Check the terminal output for error messages
2. Verify your Pydantic models are working correctly
3. Ensure all dependencies are installed
4. Check file permissions for YAML file operations
