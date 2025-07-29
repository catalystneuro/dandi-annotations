# DANDI External Resources Annotations

This repository provides tools for creating and managing external resource annotations for DANDI datasets, including a Flask web application with a user-friendly interface.

## Project Structure

```
dandi-annotations/
├── pyproject.toml              # Modern Python project configuration
├── environment.yml             # Conda environment specification
└── src/                        # Source code directory
    └── dandiannotations/       # Main package
        ├── __init__.py         # Package initialization
        ├── models/             # Pydantic models
        │   └── models.py       # ExternalResource and AnnotationContributor models
        ├── scripts/            # Command-line scripts
        │   ├── create_resource_from_code.py
        │   └── create_resource_from_yaml.py
        ├── external_resources/ # YAML data storage
        │   └── external_resources.yaml
        └── webapp/             # Flask web application
            ├── __init__.py     # Webapp package initialization
            ├── app.py          # Main Flask application
            ├── templates/      # HTML templates
            ├── static/         # CSS, JavaScript, assets
            └── utils/          # Utility modules
                ├── schema_utils.py
                └── yaml_handler.py
```

## Quick Start

### 1. Environment Setup

**Option A: Update existing environment**
```bash
conda activate dandi_annotations_env
pip install -e .
```

**Option B: Create new environment from file**
```bash
conda env create -f environment.yml
conda activate dandi_annotations_env
```

### 2. Run the Web Application

```bash
cd src/dandiannotations/webapp
python app.py
```

### 3. Access the Application

Open your web browser and navigate to: `http://127.0.0.1:5000`

## Web Application Features

- **Submission-Focused Interface**: Clean, streamlined form for submitting external resource annotations
- **Professional UI**: Responsive Bootstrap 5 styling with DANDI design principles
- **Review Workflow Integration**: Submissions are saved for review via pull request process
- **Pydantic Integration**: Uses existing `ExternalResource` and `AnnotationContributor` models
- **YAML Storage**: Saves data in the same format as `external_resources.yaml`
- **Automatic Backups**: Creates timestamped backups before modifications
- **Comprehensive Validation**: Client-side and server-side validation with helpful error messages
- **Auto-save**: Preserves form data in browser localStorage

## Form Fields

The webapp includes a streamlined submission form with the following fields:

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

## Submission Workflow

1. **Form Submission**: User fills out and submits the form for review
2. **Validation**: Data is validated using Pydantic models
3. **Backup**: Current YAML file is backed up with timestamp
4. **Storage**: New resource is appended to `external_resources.yaml`
5. **Review Process**: Submission goes through pull request review before official integration
6. **Confirmation**: Success page confirms submission and explains review process

## Validation Features

- **Email Format**: Validates proper email structure
- **URL Format**: Ensures valid HTTP/HTTPS URLs
- **ORCID Format**: Validates ORCID identifier format
- **Required Fields**: Enforces required field completion
- **Pydantic Integration**: Uses existing models for comprehensive validation

## Development

The project uses modern Python development practices:

- **pyproject.toml**: Modern dependency management and project configuration
- **Conda Integration**: Works with existing `dandi_annotations_env` environment
- **Code Quality Tools**: Pre-configured black, isort, mypy, and pytest
- **Type Hints**: Full type annotation support

### Adding New Fields

1. Update the form template (`src/dandiannotations/webapp/templates/form.html`)
2. Add validation in `src/dandiannotations/webapp/app.py`
3. Update the Pydantic models if needed
4. Add any new schema options to `src/dandiannotations/webapp/utils/schema_utils.py`

### Customizing Styles

Edit `src/dandiannotations/webapp/static/css/style.css` to modify the appearance. The design uses Bootstrap 5 with custom overrides.

## Integration with DANDI

This webapp seamlessly integrates with your existing DANDI annotation workflow:

1. **Model Compatibility**: Uses existing `ExternalResource` and `AnnotationContributor` models
2. **YAML Format**: Outputs data compatible with existing `external_resources.yaml`
3. **Safe Operations**: Creates automatic backups before file modifications
4. **Schema Compliance**: Ensures all data meets DANDI schema requirements

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the virtual environment is activated
2. **YAML File Not Found**: The app will create the file on first use
3. **Validation Errors**: Check that your Pydantic models are compatible
4. **Port Already in Use**: Change the port in `src/dandiannotations/webapp/app.py` or stop other Flask apps

### Debug Mode

The app runs in debug mode by default for development. To disable:

```python
app.run(debug=False, host='127.0.0.1', port=5000)
```

## Security Notes

- Change the secret key in `src/dandiannotations/webapp/app.py` for production use
- Consider adding authentication for production deployment
- Validate all user inputs (already implemented)
- Use HTTPS in production environments

## Command Line Tools

The repository also includes command-line tools for working with external resources:

- `src/dandiannotations/scripts/create_resource_from_code.py`: Create resources programmatically
- `src/dandiannotations/scripts/create_resource_from_yaml.py`: Create resources from YAML files

### Running the Scripts

```bash
# Create a resource programmatically
python src/dandiannotations/scripts/create_resource_from_code.py

# Create resources from YAML file
python src/dandiannotations/scripts/create_resource_from_yaml.py
```

## License

See LICENSE file for details.
