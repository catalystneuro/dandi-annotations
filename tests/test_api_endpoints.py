"""
Unit tests for DANDI External Resources API endpoints
"""

import pytest
import json
from unittest.mock import patch
import yaml


from dandiannotations.webapp.app import app
from dandiannotations.webapp.data.filesystem_repository import FileSystemResourceRepository
from dandiannotations.webapp.services.resource_service import ResourceService
from dandiannotations.webapp.utils.auth import AuthManager


class TestAPIEndpoints:
    """Test class for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    @pytest.fixture
    def mock_submission_folder_path(self, tmp_path):
        """Mock submission test data created programmatically in temporary directory"""
        mock_submission_path = tmp_path / "mock_submissions"
        mock_submission_path.mkdir(parents=True, exist_ok=True)

        # Create the dandiset directory structure
        dandiset_dir = mock_submission_path / "dandiset_000001"
        community_dir = dandiset_dir / "community"
        approved_dir = dandiset_dir / "approved"
        deleted_dir = dandiset_dir / "deleted"
        deleted_approved_dir = deleted_dir / "approved"
        deleted_community_dir = deleted_dir / "community"
        
        # Create all directories
        community_dir.mkdir(parents=True, exist_ok=True)
        approved_dir.mkdir(parents=True, exist_ok=True)
        deleted_approved_dir.mkdir(parents=True, exist_ok=True)
        deleted_community_dir.mkdir(parents=True, exist_ok=True)
        
        # Create approved submission
        approved_submission = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'Moderator One',
                'email': 'moderator1@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0009-0005-8943-5450'
            },
            'annotation_date': '2025-07-30T10:41:59.867521',
            'name': 'Example Resource',
            'url': 'https://www.example.com/',
            'repository': 'Example URLs',
            'relation': 'dcite:IsSupplementTo',
            'resourceType': 'dcite:BookChapter',
            'schemaKey': 'ExternalResource',
            'identifier': '12345678',
            'approval_contributor': {
                'name': 'Administrator',
                'email': 'admin@example.com',
                'identifier': None,
                'url': None,
                'schemaKey': 'AnnotationContributor'
            },
            'approval_date': '2025-07-30T11:05:40.081664'
        }
        
        # Create community submissions
        community_submission_1 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'newuser',
                'email': 'newuser@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0000-0002-1234-5678'
            },
            'annotation_date': '2024-12-01T09:30:00.000000',
            'name': 'Neural Signal Processing Toolkit',
            'url': 'https://github.com/neurosci-lab/neural-signal-toolkit',
            'repository': 'GitHub',
            'relation': 'dcite:IsSupplementTo',
            'resourceType': 'dcite:Software',
            'schemaKey': 'ExternalResource',
            'identifier': 'NST-2024-001'
        }
        
        community_submission_2 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'Moderator One',
                'email': 'moderator1@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0000-0003-2345-6789'
            },
            'annotation_date': '2024-12-03T14:15:00.000000',
            'name': 'Electrophysiology Data Analysis Methods',
            'url': 'https://doi.org/10.1038/s41593-024-01234-5',
            'repository': 'Nature Neuroscience',
            'relation': 'dcite:IsCitedBy',
            'resourceType': 'dcite:JournalArticle',
            'schemaKey': 'ExternalResource',
            'identifier': 'EDAM-2024-002'
        }
        
        community_submission_3 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'newuser',
                'email': 'newuser@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0000-0004-3456-7890'
            },
            'annotation_date': '2024-12-05T10:23:00.000000',
            'name': 'Spike Sorting Algorithm Comparison Dataset',
            'url': 'https://zenodo.org/record/8765432',
            'repository': 'Zenodo',
            'relation': 'dcite:IsReferencedBy',
            'resourceType': 'dcite:Dataset',
            'schemaKey': 'ExternalResource',
            'identifier': 'SSAC-2024-003'
        }
        
        # Write the YAML files
        approved_submission_path = approved_dir / "20250730_104159_submission.yaml"
        with open(approved_submission_path, 'w') as f:
            yaml.dump(approved_submission, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        community_submission_1_path = community_dir / "20241201_093000_submission.yaml"
        with open(community_submission_1_path, 'w') as f:
            yaml.dump(community_submission_1, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        community_submission_2_path = community_dir / "20241203_141500_submission.yaml"
        with open(community_submission_2_path, 'w') as f:
            yaml.dump(community_submission_2, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        community_submission_3_path = community_dir / "20241205_102300_submission.yaml"
        with open(community_submission_3_path, 'w') as f:
            yaml.dump(community_submission_3, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

        return mock_submission_path
    
    @pytest.fixture
    def mock_resource_repository(self, mock_submission_folder_path):
        """Mock resource repository"""
        return FileSystemResourceRepository(base_dir=mock_submission_folder_path)

    @pytest.fixture
    def mock_resource_service(self, mock_resource_repository):
        """Mock resource service"""
        return ResourceService(repository=mock_resource_repository)

    @pytest.fixture
    def mock_auth_manager(self, tmp_path):
        """Mock authentication manager"""
        moderators_data = {
            'moderators': {
                'moderator1': {
                    'username': 'moderator1',
                    'password_hash': '$2b$12$koa/SpEe/k6Y6RU1ejCEpu/Pls94i2uQg69tWAgZnArQvE4iaX87u',  # password: mod123
                    'name': 'Moderator One',
                    'email': 'moderator1@example.com'
                }
            }
        }
        config_path = tmp_path / "moderators.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(moderators_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

        users_data = {
            'users': {
                'newuser@example.com': {
                    'password_hash': '$2b$12$NycLu.n9og.a5jUH51DThO2Wm95cgTBOuXd8vU6XCMTpyH8uzhite',
                    'name': 'newuser',
                    'registration_date': '2025-08-04T14:50:50.901882'
                }
            }
        }
        users_config_path = tmp_path / "users.yaml"
        with open(users_config_path, 'w') as f:
            yaml.dump(users_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        auth = AuthManager(config_path=config_path)
        return auth

    def test_api_dandisets_list(self, client, mock_resource_service):
        """Test GET /api/dandisets"""
        with patch('dandiannotations.webapp.api.routes.resource_service', mock_resource_service):
            response = client.get('/api/dandisets')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert len(data['data']) == 1  # Only dandiset_000001 has submissions
            assert data['data'][0]['dandiset_id'] == 'dandiset_000001'
            assert data['data'][0]['display_id'] == '000001'
            assert data['data'][0]['approved_count'] == 1
            assert data['data'][0]['pending_count'] == 3
            assert data['data'][0]['total_count'] == 4
            assert 'pagination' in data
            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 10
            assert data['pagination']['total_items'] == 1
            assert data['pagination']['total_pages'] == 1
            assert data['pagination']['start_item'] == 1
            assert data['pagination']['end_item'] == 1
            assert data['pagination']['has_prev'] is False
            assert data['pagination']['has_next'] is False
            assert data['pagination']['prev_page'] is None
            assert data['pagination']['next_page'] is None
            assert data['message'] == 'Dandisets retrieved successfully'

    def test_api_dandisets_list_pagination(self, client, mock_resource_service):
        """Test GET /api/dandisets with pagination"""
        with patch('dandiannotations.webapp.api.routes.resource_service', mock_resource_service):
            response = client.get('/api/dandisets?page=1&per_page=1')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert len(data['data']) == 1  # Only dandiset_000001 has submissions
            assert data['data'][0]['dandiset_id'] == 'dandiset_000001'
            assert data['data'][0]['display_id'] == '000001'
            assert data['data'][0]['approved_count'] == 1
            assert data['data'][0]['pending_count'] == 3
            assert data['data'][0]['total_count'] == 4
            assert 'pagination' in data
            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 1
            assert data['pagination']['total_items'] == 1
            assert data['pagination']['total_pages'] == 1
            assert data['pagination']['start_item'] == 1
            assert data['pagination']['end_item'] == 1
            assert data['pagination']['has_prev'] is False
            assert data['pagination']['has_next'] is False
            assert data['pagination']['prev_page'] is None
            assert data['pagination']['next_page'] is None
            assert data['message'] == 'Dandisets retrieved successfully'
    
    def test_api_dandisets_list_invalid_pagination(self, client):
        """Test GET /api/dandisets with invalid pagination"""
        response = client.get('/api/dandisets?page=0&per_page=1000')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data

    def test_api_dandiset_get_resources(self, client, mock_resource_service):
        """Test GET /api/dandisets/{dandiset_id}/resources"""
        with patch('dandiannotations.webapp.api.routes.resource_service', mock_resource_service):
            response = client.get('/api/dandisets/dandiset_000001/resources')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert isinstance(data['data'], list)
            assert len(data['data']) == 1  # Only 1 approved resource for this dandiset
            for resource in data['data']:
                assert resource['dandiset_id'] == 'dandiset_000001'

    # def test_api_dandiset_get(self, client, mock_submission_folder_path):
    #     """Test GET /api/dandisets/{dandiset_id}"""
    #     with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path):
    #         response = client.get('/api/dandisets/dandiset_000001')
            
    #         assert response.status_code == 200
    #         data = json.loads(response.data)
            
    #         assert data['success'] is True
    #         assert data['data']['id'] == 'dandiset_000001'
    #         assert data['data']['display_id'] == 'DANDI:000001'
    #         assert data['data']['approved_count'] == 1
    #         assert data['data']['community_count'] == 3
    #         assert data['data']['total_count'] == 4
    #         assert data['message'] == 'Dandiset information retrieved successfully'
    
    # def test_api_dandiset_get_not_found(self, client, mock_submission_folder_path):
    #     """Test GET /api/dandisets/{dandiset_id} for non-existent dandiset"""
    #     with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path):
    #         response = client.get('/api/dandisets/dandiset_999999')
            
    #         assert response.status_code == 404
    #         data = json.loads(response.data)

    #         assert data['success'] is False
    #         assert 'error' in data
    #         assert data['error']['code'] == 'NOT_FOUND'
    #         assert data['error']['message'] == 'Dandiset not found'
    
    # def test_api_dandiset_get_invalid_id(self, client):
    #     """Test GET /api/dandisets/{dandiset_id} with invalid ID"""
    #     response = client.get('/api/dandisets/invalid_id')
        
    #     assert response.status_code == 400
    #     data = json.loads(response.data)
        
    #     assert data['success'] is False
    #     assert 'error' in data
    #     assert data['error']['code'] == 'VALIDATION_ERROR'
    #     assert data['error']['message'] == 'Validation failed'
    #     assert 'details' in data['error']
    #     assert 'general' in data['error']['details']
    #     assert 'Invalid dandiset ID format' in data['error']['details']['general']
    
    def test_api_submit_resource_valid(self, client, mock_submission_folder_path):
        """Test POST /api/dandisets/{dandiset_id}/resources with valid data"""
        test_data = {
            'resource_name': 'Test Resource',
            'resource_url': 'https://example.com/resource',
            'repository': 'GitHub',
            'relation': 'IsSupplementTo',
            'resource_type': 'Software',
            'contributor_name': 'Test Contributor',
            'contributor_email': 'test@example.com'
        }
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path):
            response = client.post('/api/dandisets/dandiset_000001/resources',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'data' in data
            assert data['data']['name'] == 'Test Resource'
            assert data['data']['url'] == 'https://example.com/resource'
            assert data['data']['repository'] == 'GitHub'
            assert data['data']['relation'] == 'dcite:IsSupplementTo'
            assert data['data']['resourceType'] == 'dcite:Software'
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['data']['status'] == 'pending'
            assert data['data']['schemaKey'] == 'ExternalResource'
            assert data['data']['annotation_contributor']['name'] == 'Test Contributor'
            assert data['data']['annotation_contributor']['email'] == 'test@example.com'
            assert data['data']['annotation_contributor']['schemaKey'] == 'AnnotationContributor'
            assert 'annotation_date' in data['data']
            assert 'filename' in data['data']
            assert data['message'] == 'Resource submitted successfully for review'
    
    def test_api_submit_resource_missing_fields(self, client):
        """Test POST /api/dandisets/{dandiset_id}/resources with missing fields"""
        test_data = {
            'resource_name': 'Test Resource'
            # Missing required fields
        }
        
        response = client.post('/api/dandisets/dandiset_000001/resources',
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'missing_fields' in data['error']['details']
        assert set(data['error']['details']['missing_fields']) == {
            'resource_url', 'repository', 'relation', 'resource_type', 'contributor_name', 'contributor_email'
        }
    
    def test_api_submit_resource_invalid_email(self, client):
        """Test POST /api/dandisets/{dandiset_id}/resources with invalid email"""
        test_data = {
            'resource_name': 'Test Resource',
            'resource_url': 'https://example.com/resource',
            'repository': 'GitHub',
            'relation': 'IsSupplementTo',
            'resource_type': 'Software',
            'contributor_name': 'Test Contributor',
            'contributor_email': 'invalid-email'
        }
        
        response = client.post('/api/dandisets/dandiset_000001/resources',
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'general' in data['error']['details']
        assert data['error']['details']['general'] == 'Invalid contributor email: Invalid email format'

    def test_api_submit_resource_invalid_url(self, client):
        """Test POST /api/dandisets/{dandiset_id}/resources with invalid URL"""
        test_data = {
            'resource_name': 'Test Resource',
            'resource_url': 'not-a-url',
            'repository': 'GitHub',
            'relation': 'IsSupplementTo',
            'resource_type': 'Software',
            'contributor_name': 'Test Contributor',
            'contributor_email': 'test@example.com'
        }
        
        response = client.post('/api/dandisets/dandiset_000001/resources',
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'general' in data['error']['details']
        assert data['error']['details']['general'] == 'Invalid resource URL: Invalid URL format. Must start with http:// or https://'
    
    def test_api_submit_resource_wrong_content_type(self, client):
        """Test POST /api/dandisets/{dandiset_id}/resources with wrong content type"""
        test_data = {
            'resource_name': 'Test Resource'
        }
        
        response = client.post('/api/dandisets/dandiset_000001/resources',
                             data=json.dumps(test_data),
                             content_type='text/plain')
        
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'general' in data['error']['details']
        assert data['error']['details']['general'] == 'Content-Type must be application/json'

    
    def test_api_auth_login_moderator(self, client, mock_auth_manager):
        """Test POST /api/auth/login with valid moderator credentials"""
        test_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }

        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['username'] == 'moderator1'
            assert data['data']['email'] == 'moderator1@example.com'
            assert data['data']['name'] == 'Moderator One'
            assert data['data']['user_type'] == 'moderator'
            assert data['message'] == 'Login successful'

    def test_api_auth_login_user(self, client, mock_auth_manager):
        """Test POST /api/auth/login with valid user credentials"""
        test_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }

        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/auth/login',
                                   data=json.dumps(test_data),
                                   content_type='application/json')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['username'] == 'newuser@example.com'
            assert data['data']['email'] == 'newuser@example.com'
            assert data['data']['name'] == 'newuser'
            assert data['data']['user_type'] == 'user'
            assert data['message'] == 'Login successful'
    
    def test_api_auth_login_invalid(self, client, mock_auth_manager):
        """Test POST /api/auth/login with invalid credentials"""
        test_data = {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/auth/login',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 401
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'INVALID_CREDENTIALS'
            assert data['error']['message'] == 'Invalid username or password'
    
    def test_api_auth_login_missing_fields(self, client):
        """Test POST /api/auth/login with missing fields"""
        test_data = {
            'username': 'test@example.com'
            # Missing password
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'general' in data['error']['details']
        assert data['error']['details']['general'] == 'Username and password are required'
    
    def test_api_auth_register_valid(self, client, mock_auth_manager):
        """Test POST /api/auth/register with valid data"""
        test_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/auth/register',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data']['email'] == 'testuser@example.com'
            assert data['data']['name'] == 'testuser'
            assert data['data']['user_type'] == 'user'
            assert data['data']['username'] == 'testuser@example.com'
            assert data['message'] == 'Registration successful'

    
    def test_api_auth_register_email_exists(self, client, mock_auth_manager):
        """Test POST /api/auth/register with existing email"""
        test_data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/auth/register',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 409
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'EMAIL_EXISTS'
            assert data['error']['message'] == 'Email already exists'
    
    def test_api_auth_register_password_mismatch(self, client):
        """Test POST /api/auth/register with password mismatch"""
        test_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'different_password'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'general' in data['error']['details']
        assert data['error']['details']['general'] == 'Passwords do not match'
    
    def test_api_auth_me_authenticated(self, client, mock_auth_manager):
        """Test GET /api/auth/me when authenticated"""
        test_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            response = client.get('/api/auth/me')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data']['email'] == 'moderator1@example.com'
            assert data['data']['is_moderator'] is True
            assert data['data']['name'] == 'Moderator One'
            assert data['data']['user_type'] == 'moderator'
            assert data['message'] == 'User information retrieved successfully'
    
    def test_api_auth_me_unauthenticated(self, client, mock_auth_manager):
        """Test GET /api/auth/me when not authenticated"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.get('/api/auth/me')
            
            assert response.status_code == 401
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'UNAUTHORIZED'
            assert data['error']['message'] == 'Authentication required'
    
    def test_api_auth_logout_moderator(self, client, mock_auth_manager):
        """Test POST /api/auth/logout"""
        test_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            response = client.post('/api/auth/logout')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data'] is None
            assert data['message'] == 'Logout successful for Moderator One'
    
    def test_api_auth_logout_user(self, client, mock_auth_manager):
        """Test POST /api/auth/logout for user"""
        test_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            response = client.post('/api/auth/logout')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data'] is None
            assert data['message'] == 'Logout successful for newuser'
    
    def test_api_auth_logout_unauthenticated(self, client, mock_auth_manager):
        """Test POST /api/auth/logout when not authenticated"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/auth/logout')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert data['data'] is None
            assert data['message'] == 'Logout successful'

    def test_api_stats_overview(self, client, mock_submission_folder_path):
        """Test GET /api/stats/overview"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path):
            response = client.get('/api/stats/overview')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['total_dandisets'] == 1
            assert data['data']['total_approved_resources'] == 1
            assert data['data']['total_pending_resources'] == 3
            assert data['data']['dandisets_with_resources'] == 1
            assert data['data']['total_resources'] == 4
            assert data['data']['unique_contributors'] == 2
            assert data['message'] == 'Overview statistics retrieved successfully'
    
    def test_api_stats_dandiset(self, client, mock_submission_folder_path):
        """Test GET /api/stats/dandisets/{dandiset_id}"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path):
            response = client.get('/api/stats/dandisets/dandiset_000001')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['data']['display_id'] == 'DANDI:000001'
            assert data['data']['approved_count'] == 1
            assert data['data']['pending_count'] == 3
            assert data['data']['total_count'] == 4
            assert data['data']['unique_contributors'] == 2
            assert 'repositories' in data['data']
            assert data['data']['repositories'] == {
                'Example URLs': 1,
                'GitHub': 1,
                'Nature Neuroscience': 1,
                'Zenodo': 1
            }
            assert 'resource_types' in data['data']
            assert data['data']['resource_types'] == {
                'dcite:BookChapter': 1,
                'dcite:Dataset': 1,
                'dcite:JournalArticle': 1,
                'dcite:Software': 1
            }
            assert data['message'] == 'Dandiset statistics retrieved successfully'
    
    def test_api_pending_submissions_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test GET /api/submissions/pending as moderator"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )

            response = client.get('/api/submissions/pending')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert response.status_code == 200
            assert data['success'] is True
            assert 'data' in data
            assert len(data['data']) == 3  # 3 pending submissions
            assert data['data'][0]['name'] == 'Spike Sorting Algorithm Comparison Dataset'
            assert data['data'][1]['name'] == 'Electrophysiology Data Analysis Methods'
            assert data['data'][2]['name'] == 'Neural Signal Processing Toolkit'
            assert data['pagination']['total_items'] == 3
            assert data['pagination']['total_pages'] == 1
            assert data['message'] == 'Pending submissions retrieved successfully'
    
    def test_api_pending_submissions_non_moderator(self, client, mock_auth_manager):
        """Test GET /api/submissions/pending as non-moderator"""
        login_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.get('/api/submissions/pending')
            
            assert response.status_code == 403
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'FORBIDDEN'
            assert data['error']['message'] == 'Moderator privileges required'
    
    def test_api_pending_submissions_unauthenticated(self, client, mock_auth_manager):
        """Test GET /api/submissions/pending when unauthenticated"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.get('/api/submissions/pending')
            
            assert response.status_code == 401
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'UNAUTHORIZED'
            assert data['error']['message'] == 'Authentication required'
    
    def test_api_approve_submission_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test POST /api/submissions/{dandiset_id}/{filename}/approve as moderator"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.post('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/approve',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['_submission_status'] == 'approved'
            assert data['data']['_submission_filename'] == '20241201_093000_submission.yaml'
            assert data['data']['approval_contributor']['name'] == 'Moderator One'
            assert data['data']['approval_contributor']['email'] == 'moderator1@example.com'
            assert data['data']['approval_contributor']['schemaKey'] == 'AnnotationContributor'
            assert data['data']['name'] == 'Neural Signal Processing Toolkit'
            assert data['data']['url'] == 'https://github.com/neurosci-lab/neural-signal-toolkit'
            assert data['data']['repository'] == 'GitHub'
            assert data['data']['relation'] == 'dcite:IsSupplementTo'
            assert data['data']['resourceType'] == 'dcite:Software'
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['message'] == 'Submission approved successfully'

    def test_api_approve_submission_invalid_user(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test POST /api/submissions/{dandiset_id}/{filename}/approve with invalid user credentials"""
        login_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.post('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/approve',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 403
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'FORBIDDEN'
            assert data['error']['message'] == 'Moderator privileges required'
    
    def test_api_approve_submission_unathenticated(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test POST /api/submissions/{dandiset_id}/{filename}/approve when unauthenticated"""
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/approve',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 401
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'UNAUTHORIZED'
            assert data['error']['message'] == 'Authentication required'
    
    def test_api_approve_submission_not_found(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test POST /api/submissions/{dandiset_id}/{filename}/approve for non-existent submission"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.post('/api/submissions/dandiset_000001/nonexistent.yaml/approve',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'NOT_FOUND'
            assert data['error']['message'] == 'Submission not found'
    
    def test_api_user_submissions_own_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test GET /api/submissions/user/{user_email} for own submissions"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.get('/api/submissions/user/moderator1@example.com')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'community_submissions' in data['data']
            assert 'approved_submissions' in data['data']
            assert len(data['data']['community_submissions']) == 1
            assert len(data['data']['approved_submissions']) == 1
            assert data['data']['community_submissions'][0]['name'] == 'Electrophysiology Data Analysis Methods'
            assert data['data']['community_submissions'][0]['annotation_contributor']['email'] == 'moderator1@example.com'
            assert data['data']['approved_submissions'][0]['name'] == 'Example Resource'
            assert data['data']['approved_submissions'][0]['annotation_contributor']['email'] == 'moderator1@example.com'
            assert 'community_pagination' in data['data']
            assert 'approved_pagination' in data['data']
            assert data['data']['community_pagination']['total_items'] == 1
            assert data['data']['approved_pagination']['total_items'] == 1
            assert data['message'] == 'User submissions retrieved successfully'

    def test_api_user_submissions_own_user(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test GET /api/submissions/user/{user_email} for own submissions as user"""
        login_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.get('/api/submissions/user/newuser@example.com')

            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'community_submissions' in data['data']
            assert 'approved_submissions' in data['data']
            assert len(data['data']['community_submissions']) == 2
            assert len(data['data']['approved_submissions']) == 0
            assert data['data']['community_submissions'][0]['name'] == 'Spike Sorting Algorithm Comparison Dataset'
            assert data['data']['community_submissions'][0]['annotation_contributor']['email'] == 'newuser@example.com'
            assert data['data']['community_submissions'][1]['name'] == 'Neural Signal Processing Toolkit'
            assert data['data']['community_submissions'][1]['annotation_contributor']['email'] == 'newuser@example.com'
            assert 'community_pagination' in data['data']
            assert 'approved_pagination' in data['data']
            assert data['data']['community_pagination']['total_items'] == 2
            assert data['data']['approved_pagination']['total_items'] == 0
            assert data['message'] == 'User submissions retrieved successfully'

    def test_api_user_submissions_other_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test GET /api/submissions/user/{user_email} for other user as moderator"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.get('/api/submissions/user/newuser@example.com')

            assert response.status_code == 403
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'FORBIDDEN'
            assert data['error']['message'] == 'You can only view your own submissions'

    def test_api_user_submissions_other_user(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test GET /api/submissions/user/{user_email} for other user as user"""
        login_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.get('/api/submissions/user/moderator1@example.com')

            assert response.status_code == 403
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'FORBIDDEN'
            assert data['error']['message'] == 'You can only view your own submissions'
    
    def test_api_404_error(self, client):
        """Test 404 error handling for API routes"""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'NOT_FOUND'
        assert data['error']['message'] == 'API endpoint not found'
    
    def test_api_405_error(self, client):
        """Test 405 error handling for API routes"""
        response = client.put('/api/dandisets')  # PUT not allowed
        
        assert response.status_code == 405
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'METHOD_NOT_ALLOWED'
        assert data['error']['message'] == 'Method not allowed'

    def test_api_delete_submission_moderator_community(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete for community submission as moderator"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/delete?status=community',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['data']['filename'] == '20241201_093000_submission.yaml'
            assert data['data']['status'] == 'community'
            assert data['data']['resource_name'] == 'Neural Signal Processing Toolkit'
            assert data['data']['deleted_by'] == 'Moderator One'
            assert 'deletion_date' in data['data']
            assert data['message'] == "Submission 'Neural Signal Processing Toolkit' deleted successfully"

    def test_api_delete_submission_moderator_approved(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete for approved submission as moderator"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/20250730_104159_submission.yaml/delete?status=approved',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['data']['filename'] == '20250730_104159_submission.yaml'
            assert data['data']['status'] == 'approved'
            assert data['data']['resource_name'] == 'Example Resource'
            assert data['data']['deleted_by'] == 'Moderator One'
            assert 'deletion_date' in data['data']
            assert data['message'] == "Submission 'Example Resource' deleted successfully"

    def test_api_delete_submission_missing_status(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete without status parameter"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/delete',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert data['error']['message'] == 'Validation failed'
            assert 'details' in data['error']
            assert 'general' in data['error']['details']
            assert data['error']['details']['general'] == "Status parameter must be 'community' or 'approved'"

    def test_api_delete_submission_invalid_status(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete with invalid status parameter"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/delete?status=invalid',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert data['error']['message'] == 'Validation failed'
            assert 'details' in data['error']
            assert 'general' in data['error']['details']
            assert data['error']['details']['general'] == "Status parameter must be 'community' or 'approved'"

    def test_api_delete_submission_non_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete as non-moderator"""
        login_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/delete?status=community',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 403
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'FORBIDDEN'
            assert data['error']['message'] == 'Moderator privileges required'

    def test_api_delete_submission_unauthenticated(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete when unauthenticated"""
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.delete('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/delete?status=community',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 401
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'UNAUTHORIZED'
            assert data['error']['message'] == 'Authentication required'

    def test_api_delete_submission_not_found(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete for non-existent submission"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/nonexistent.yaml/delete?status=community',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 404
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'NOT_FOUND'
            assert data['error']['message'] == 'Submission not found'

    def test_api_delete_submission_missing_moderator_data(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/submissions/{dandiset_id}/{filename}/delete with missing moderator data"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One'
            # Missing moderator_email
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/submissions/dandiset_000001/20241201_093000_submission.yaml/delete?status=community',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert data['error']['message'] == 'Validation failed'

    def test_api_delete_resource_by_id_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/resources/{resource_id} as moderator"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/resources/20241201_093000_submission',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert data['data']['resource_id'] == '20241201_093000_submission'
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['data']['filename'] == '20241201_093000_submission.yaml'
            assert data['data']['status'] == 'community'
            assert data['data']['resource_name'] == 'Neural Signal Processing Toolkit'
            assert data['data']['deleted_by'] == 'Moderator One'
            assert 'deletion_date' in data['data']
            assert data['message'] == "Resource 'Neural Signal Processing Toolkit' deleted successfully"

    def test_api_delete_resource_by_id_non_moderator(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/resources/{resource_id} as non-moderator"""
        login_data = {
            'username': 'newuser@example.com',
            'password': 'password123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/resources/20241201_093000_submission',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 403
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'FORBIDDEN'
            assert data['error']['message'] == 'Moderator privileges required'

    def test_api_delete_resource_by_id_unauthenticated(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/resources/{resource_id} when unauthenticated"""
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.delete('/api/resources/20241201_093000_submission',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 401
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'UNAUTHORIZED'
            assert data['error']['message'] == 'Authentication required'

    def test_api_delete_resource_by_id_not_found(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/resources/{resource_id} for non-existent resource"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/resources/nonexistent_resource',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 404
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'NOT_FOUND'
            assert data['error']['message'] == 'Resource not found'

    def test_api_delete_resource_by_id_missing_moderator_data(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/resources/{resource_id} with missing moderator data"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One'
            # Missing moderator_email
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/resources/20241201_093000_submission',
                                   data=json.dumps(test_data),
                                   content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert data['error']['message'] == 'Validation failed'

    def test_api_delete_resource_by_id_wrong_content_type(self, client, mock_submission_folder_path, mock_auth_manager):
        """Test DELETE /api/resources/{resource_id} with wrong content type"""
        login_data = {
            'username': 'moderator1',
            'password': 'mod123'
        }
        test_data = {
            'moderator_name': 'Moderator One',
            'moderator_email': 'moderator1@example.com'
        }

        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_folder_path), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            client.post(
                '/api/auth/login',
                data=json.dumps(login_data),
                content_type='application/json'
            )
            response = client.delete('/api/resources/20241201_093000_submission',
                                   data=json.dumps(test_data),
                                   content_type='text/plain')
            
            assert response.status_code == 400
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert data['error']['message'] == 'Validation failed'
            assert 'details' in data['error']
            assert 'general' in data['error']['details']
            assert data['error']['details']['general'] == 'Content-Type must be application/json'


if __name__ == '__main__':
    pytest.main([__file__])
