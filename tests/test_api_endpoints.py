"""
Unit tests for DANDI External Resources API endpoints
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
import yaml


from dandiannotations.webapp.app import app
from dandiannotations.webapp.utils.submission_handler import SubmissionHandler
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
    def mock_submission_handler(self, tmp_path):
        """Mock submission handler with test data created programmatically in temporary directory"""
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
                'name': 'Paul',
                'email': 'paul.wesley.adkisson@gmail.com',
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
                'name': 'Dr. Sarah Chen',
                'email': 's.chen@neuroscience.edu',
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
                'name': 'Prof. Michael Rodriguez',
                'email': 'm.rodriguez@brainlab.org',
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
                'name': 'Dr. Emily Watson',
                'email': 'e.watson@computational.bio',
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
        
        # Create submission handler with the temporary directory
        submission_handler = SubmissionHandler(base_submissions_dir=mock_submission_path)

        return submission_handler

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager"""
        config_path = "/Users/pauladkisson/Documents/CatalystNeuro/DANDI/dandi-annotations/src/dandiannotations/webapp/config/moderators.yaml"
        auth = AuthManager(config_path=config_path)
        return auth
    
    def test_api_dandisets_list(self, client, mock_submission_handler):
        """Test GET /api/dandisets"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert len(data['data']) == 1  # Only dandiset_000001 has submissions
            assert data['data'][0]['id'] == 'dandiset_000001'
            assert data['data'][0]['display_id'] == 'DANDI:000001'
            assert data['data'][0]['approved_count'] == 1
            assert data['data'][0]['community_count'] == 3
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
    
    def test_api_dandisets_list_pagination(self, client, mock_submission_handler):
        """Test GET /api/dandisets with pagination"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets?page=1&per_page=1')
            
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['success'] is True
            assert 'data' in data
            assert len(data['data']) == 1  # Only dandiset_000001 has submissions
            assert data['data'][0]['id'] == 'dandiset_000001'
            assert data['data'][0]['display_id'] == 'DANDI:000001'
            assert data['data'][0]['approved_count'] == 1
            assert data['data'][0]['community_count'] == 3
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
    
    def test_api_dandiset_get(self, client, mock_submission_handler):
        """Test GET /api/dandisets/{dandiset_id}"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets/dandiset_000001')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data']['id'] == 'dandiset_000001'
            assert data['data']['display_id'] == 'DANDI:000001'
            assert data['data']['approved_count'] == 1
            assert data['data']['community_count'] == 3
            assert data['data']['total_count'] == 4
            assert data['message'] == 'Dandiset information retrieved successfully'
    
    def test_api_dandiset_get_not_found(self, client, mock_submission_handler):
        """Test GET /api/dandisets/{dandiset_id} for non-existent dandiset"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets/dandiset_999999')
            
            assert response.status_code == 404
            data = json.loads(response.data)

            assert data['success'] is False
            assert 'error' in data
            assert data['error']['code'] == 'NOT_FOUND'
            assert data['error']['message'] == 'Dandiset not found'
    
    def test_api_dandiset_get_invalid_id(self, client):
        """Test GET /api/dandisets/{dandiset_id} with invalid ID"""
        response = client.get('/api/dandisets/invalid_id')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
        assert data['error']['code'] == 'VALIDATION_ERROR'
        assert data['error']['message'] == 'Validation failed'
        assert 'details' in data['error']
        assert 'general' in data['error']['details']
        assert 'Invalid dandiset ID format' in data['error']['details']['general']
    
    def test_api_submit_resource_valid(self, client, mock_submission_handler):
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
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
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

    
#     def test_api_auth_login_valid(self, client, mock_auth_manager):
#         """Test POST /api/auth/login with valid credentials"""
#         test_data = {
#             'username': 'test@example.com',
#             'password': 'password123'
#         }
        
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.verify_credentials.return_value = {
#                 'name': 'Test User',
#                 'email': 'test@example.com',
#                 'user_type': 'moderator'
#             }
            
#             response = client.post('/api/auth/login',
#                                  data=json.dumps(test_data),
#                                  content_type='application/json')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert data['data']['email'] == 'test@example.com'
    
#     def test_api_auth_login_invalid(self, client, mock_auth_manager):
#         """Test POST /api/auth/login with invalid credentials"""
#         test_data = {
#             'username': 'test@example.com',
#             'password': 'wrongpassword'
#         }
        
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.verify_credentials.return_value = None
            
#             response = client.post('/api/auth/login',
#                                  data=json.dumps(test_data),
#                                  content_type='application/json')
            
#             assert response.status_code == 401
#             data = json.loads(response.data)
            
#             assert data['success'] is False
#             assert 'error' in data
    
#     def test_api_auth_login_missing_fields(self, client):
#         """Test POST /api/auth/login with missing fields"""
#         test_data = {
#             'username': 'test@example.com'
#             # Missing password
#         }
        
#         response = client.post('/api/auth/login',
#                              data=json.dumps(test_data),
#                              content_type='application/json')
        
#         assert response.status_code == 400
#         data = json.loads(response.data)
        
#         assert data['success'] is False
#         assert 'error' in data
    
#     def test_api_auth_register_valid(self, client, mock_auth_manager):
#         """Test POST /api/auth/register with valid data"""
#         test_data = {
#             'email': 'newuser@example.com',
#             'password': 'password123',
#             'confirm_password': 'password123'
#         }
        
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.register_user.return_value = True
#             mock_auth_manager.verify_credentials.return_value = {
#                 'name': 'New User',
#                 'email': 'newuser@example.com',
#                 'user_type': 'user'
#             }
            
#             response = client.post('/api/auth/register',
#                                  data=json.dumps(test_data),
#                                  content_type='application/json')
            
#             assert response.status_code == 201
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert data['data']['email'] == 'newuser@example.com'
    
#     def test_api_auth_register_email_exists(self, client, mock_auth_manager):
#         """Test POST /api/auth/register with existing email"""
#         test_data = {
#             'email': 'existing@example.com',
#             'password': 'password123',
#             'confirm_password': 'password123'
#         }
        
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.register_user.return_value = False
            
#             response = client.post('/api/auth/register',
#                                  data=json.dumps(test_data),
#                                  content_type='application/json')
            
#             assert response.status_code == 409
#             data = json.loads(response.data)
            
#             assert data['success'] is False
#             assert 'error' in data
    
#     def test_api_auth_register_password_mismatch(self, client):
#         """Test POST /api/auth/register with password mismatch"""
#         test_data = {
#             'email': 'newuser@example.com',
#             'password': 'password123',
#             'confirm_password': 'different_password'
#         }
        
#         response = client.post('/api/auth/register',
#                              data=json.dumps(test_data),
#                              content_type='application/json')
        
#         assert response.status_code == 400
#         data = json.loads(response.data)
        
#         assert data['success'] is False
#         assert 'error' in data
    
#     def test_api_auth_me_authenticated(self, client, mock_auth_manager):
#         """Test GET /api/auth/me when authenticated"""
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             response = client.get('/api/auth/me')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert data['data']['email'] == 'test@example.com'
#             assert data['data']['is_moderator'] is True
    
#     def test_api_auth_me_unauthenticated(self, client, mock_auth_manager):
#         """Test GET /api/auth/me when not authenticated"""
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.is_authenticated.return_value = False
            
#             response = client.get('/api/auth/me')
            
#             assert response.status_code == 401
#             data = json.loads(response.data)
            
#             assert data['success'] is False
#             assert 'error' in data
    
#     def test_api_auth_logout(self, client, mock_auth_manager):
#         """Test POST /api/auth/logout"""
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             response = client.post('/api/auth/logout')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             mock_auth_manager.logout_user.assert_called_once()
    
#     def test_api_stats_overview(self, client, mock_submission_handler):
#         """Test GET /api/stats/overview"""
#         with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
#             mock_submission_handler.get_all_pending_submissions.return_value = [
#                 {'annotation_contributor': {'name': 'User 1'}},
#                 {'annotation_contributor': {'name': 'User 2'}},
#                 {'annotation_contributor': {'name': 'User 1'}}  # Duplicate
#             ]
            
#             response = client.get('/api/stats/overview')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert 'data' in data
#             assert data['data']['total_dandisets'] == 2
#             assert data['data']['total_approved_resources'] == 2
#             assert data['data']['total_pending_resources'] == 4
    
#     def test_api_stats_dandiset(self, client, mock_submission_handler):
#         """Test GET /api/stats/dandisets/{dandiset_id}"""
#         with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
#             mock_submission_handler.get_approved_submissions.return_value = [
#                 {'resourceType': 'Software', 'repository': 'GitHub'},
#                 {'resourceType': 'Dataset', 'repository': 'Zenodo'}
#             ]
#             mock_submission_handler.get_community_submissions.return_value = [
#                 {'resourceType': 'Software', 'repository': 'GitHub'}
#             ]
            
#             response = client.get('/api/stats/dandisets/dandiset_000001')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert data['data']['dandiset_id'] == 'dandiset_000001'
#             assert data['data']['approved_count'] == 2
#             assert data['data']['pending_count'] == 1
    
#     def test_api_pending_submissions_moderator(self, client, mock_submission_handler, mock_auth_manager):
#         """Test GET /api/submissions/pending as moderator"""
#         with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
#              patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
#             mock_submission_handler.get_all_pending_submissions_paginated.return_value = (
#                 [{'name': 'Test Resource'}],
#                 {'page': 1, 'total_items': 1, 'total_pages': 1}
#             )
            
#             response = client.get('/api/submissions/pending')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert len(data['data']) == 1
    
#     def test_api_pending_submissions_non_moderator(self, client, mock_auth_manager):
#         """Test GET /api/submissions/pending as non-moderator"""
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.is_moderator.return_value = False
            
#             response = client.get('/api/submissions/pending')
            
#             assert response.status_code == 403
#             data = json.loads(response.data)
            
#             assert data['success'] is False
#             assert 'error' in data
    
#     def test_api_approve_submission_moderator(self, client, mock_submission_handler, mock_auth_manager):
#         """Test POST /api/submissions/{dandiset_id}/{filename}/approve as moderator"""
#         test_data = {
#             'moderator_name': 'Test Moderator',
#             'moderator_email': 'moderator@example.com'
#         }
        
#         with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
#              patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
#             mock_submission_handler.get_submission_by_filename.return_value = {
#                 'name': 'Test Resource'
#             }
#             mock_submission_handler.approve_submission.return_value = True
            
#             response = client.post('/api/submissions/dandiset_000001/test.yaml/approve',
#                                  data=json.dumps(test_data),
#                                  content_type='application/json')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
    
#     def test_api_approve_submission_not_found(self, client, mock_submission_handler, mock_auth_manager):
#         """Test POST /api/submissions/{dandiset_id}/{filename}/approve for non-existent submission"""
#         test_data = {
#             'moderator_name': 'Test Moderator',
#             'moderator_email': 'moderator@example.com'
#         }
        
#         with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
#              patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
#             mock_submission_handler.get_submission_by_filename.return_value = None
            
#             response = client.post('/api/submissions/dandiset_000001/nonexistent.yaml/approve',
#                                  data=json.dumps(test_data),
#                                  content_type='application/json')
            
#             assert response.status_code == 404
#             data = json.loads(response.data)
            
#             assert data['success'] is False
#             assert 'error' in data
    
#     def test_api_user_submissions_own(self, client, mock_submission_handler, mock_auth_manager):
#         """Test GET /api/submissions/user/{user_email} for own submissions"""
#         with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
#              patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
#             mock_submission_handler.get_user_submissions_paginated.return_value = (
#                 [{'name': 'Community Resource'}],  # community
#                 {'page': 1, 'total_items': 1},     # community pagination
#                 [{'name': 'Approved Resource'}],   # approved
#                 {'page': 1, 'total_items': 1}      # approved pagination
#             )
            
#             response = client.get('/api/submissions/user/test@example.com')
            
#             assert response.status_code == 200
#             data = json.loads(response.data)
            
#             assert data['success'] is True
#             assert 'community_submissions' in data['data']
#             assert 'approved_submissions' in data['data']
    
#     def test_api_user_submissions_other_non_moderator(self, client, mock_auth_manager):
#         """Test GET /api/submissions/user/{user_email} for other user as non-moderator"""
#         with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
#             mock_auth_manager.is_moderator.return_value = False
            
#             response = client.get('/api/submissions/user/other@example.com')
            
#             assert response.status_code == 403
#             data = json.loads(response.data)
            
#             assert data['success'] is False
#             assert 'error' in data
    
#     def test_api_404_error(self, client):
#         """Test 404 error handling for API routes"""
#         response = client.get('/api/nonexistent')
        
#         assert response.status_code == 404
#         data = json.loads(response.data)
        
#         assert data['success'] is False
#         assert 'error' in data
    
#     def test_api_405_error(self, client):
#         """Test 405 error handling for API routes"""
#         response = client.put('/api/dandisets')  # PUT not allowed
        
#         assert response.status_code == 405
#         data = json.loads(response.data)
        
#         assert data['success'] is False
#         assert 'error' in data


# if __name__ == '__main__':
#     pytest.main([__file__])
