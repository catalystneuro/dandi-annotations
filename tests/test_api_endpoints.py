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

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

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
    def temp_submissions_dir(self):
        """Create temporary submissions directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_submission_handler(self, temp_submissions_dir):
        """Mock submission handler with test data"""
        # Create test dandisets
        test_dandisets = [
            {
                'dandiset_id': 'dandiset_000001',
                'approved_count': 2,
                'community_count': 1
            },
            {
                'dandiset_id': 'dandiset_000002',
                'approved_count': 0,
                'community_count': 3
            }
        ]
        
        # Create a complete mock handler
        handler = MagicMock()
        handler.get_all_dandisets.return_value = test_dandisets
        handler.get_all_dandisets_paginated.return_value = (
            test_dandisets,
            {
                'page': 1, 'per_page': 10, 'total_items': 2, 'total_pages': 1,
                'has_prev': False, 'has_next': False, 'prev_page': None, 'next_page': None,
                'start_item': 1, 'end_item': 2
            }
        )
        handler.get_approved_submissions_paginated.return_value = ([], {'total_items': 0})
        handler.get_community_submissions_paginated.return_value = ([], {'total_items': 0})
        handler.get_approved_submissions.return_value = []
        handler.get_community_submissions.return_value = []
        handler.save_community_submission.return_value = 'test_submission.yaml'
        handler.get_all_pending_submissions.return_value = []
        handler.get_all_pending_submissions_paginated.return_value = ([], {'total_items': 0})
        handler.get_submission_by_filename.return_value = None
        handler.approve_submission.return_value = True
        handler.get_user_submissions_paginated.return_value = ([], {}, [], {})
        
        return handler
    
    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager"""
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_moderator.return_value = True
        auth.get_current_user.return_value = {
            'name': 'Test User',
            'email': 'test@example.com',
            'user_type': 'moderator'
        }
        auth.get_user_type.return_value = 'moderator'
        return auth
    
    def test_api_dandisets_list(self, client, mock_submission_handler):
        """Test GET /api/dandisets"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'data' in data
            assert len(data['data']) == 2
            assert data['data'][0]['dandiset_id'] == 'dandiset_000001'
            assert 'pagination' in data
    
    def test_api_dandisets_list_pagination(self, client, mock_submission_handler):
        """Test GET /api/dandisets with pagination"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets?page=1&per_page=1')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['pagination']['page'] == 1
            assert data['pagination']['per_page'] == 1
    
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
            assert data['data']['dandiset_id'] == 'dandiset_000001'
    
    def test_api_dandiset_get_not_found(self, client, mock_submission_handler):
        """Test GET /api/dandisets/{dandiset_id} for non-existent dandiset"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            response = client.get('/api/dandisets/dandiset_999999')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
    def test_api_dandiset_get_invalid_id(self, client):
        """Test GET /api/dandisets/{dandiset_id} with invalid ID"""
        response = client.get('/api/dandisets/invalid_id')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
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
            mock_submission_handler.save_community_submission.return_value = 'test_submission.yaml'
            
            response = client.post('/api/dandisets/dandiset_000001/resources',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'data' in data
            assert data['data']['name'] == 'Test Resource'
    
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
    
    def test_api_auth_login_valid(self, client, mock_auth_manager):
        """Test POST /api/auth/login with valid credentials"""
        test_data = {
            'username': 'test@example.com',
            'password': 'password123'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.verify_credentials.return_value = {
                'name': 'Test User',
                'email': 'test@example.com',
                'user_type': 'moderator'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data']['email'] == 'test@example.com'
    
    def test_api_auth_login_invalid(self, client, mock_auth_manager):
        """Test POST /api/auth/login with invalid credentials"""
        test_data = {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.verify_credentials.return_value = None
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 401
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
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
    
    def test_api_auth_register_valid(self, client, mock_auth_manager):
        """Test POST /api/auth/register with valid data"""
        test_data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.register_user.return_value = True
            mock_auth_manager.verify_credentials.return_value = {
                'name': 'New User',
                'email': 'newuser@example.com',
                'user_type': 'user'
            }
            
            response = client.post('/api/auth/register',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data']['email'] == 'newuser@example.com'
    
    def test_api_auth_register_email_exists(self, client, mock_auth_manager):
        """Test POST /api/auth/register with existing email"""
        test_data = {
            'email': 'existing@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.register_user.return_value = False
            
            response = client.post('/api/auth/register',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 409
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
    def test_api_auth_register_password_mismatch(self, client):
        """Test POST /api/auth/register with password mismatch"""
        test_data = {
            'email': 'newuser@example.com',
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
    
    def test_api_auth_me_authenticated(self, client, mock_auth_manager):
        """Test GET /api/auth/me when authenticated"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.get('/api/auth/me')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data']['email'] == 'test@example.com'
            assert data['data']['is_moderator'] is True
    
    def test_api_auth_me_unauthenticated(self, client, mock_auth_manager):
        """Test GET /api/auth/me when not authenticated"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.is_authenticated.return_value = False
            
            response = client.get('/api/auth/me')
            
            assert response.status_code == 401
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
    def test_api_auth_logout(self, client, mock_auth_manager):
        """Test POST /api/auth/logout"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            response = client.post('/api/auth/logout')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            mock_auth_manager.logout_user.assert_called_once()
    
    def test_api_stats_overview(self, client, mock_submission_handler):
        """Test GET /api/stats/overview"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            mock_submission_handler.get_all_pending_submissions.return_value = [
                {'annotation_contributor': {'name': 'User 1'}},
                {'annotation_contributor': {'name': 'User 2'}},
                {'annotation_contributor': {'name': 'User 1'}}  # Duplicate
            ]
            
            response = client.get('/api/stats/overview')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'data' in data
            assert data['data']['total_dandisets'] == 2
            assert data['data']['total_approved_resources'] == 2
            assert data['data']['total_pending_resources'] == 4
    
    def test_api_stats_dandiset(self, client, mock_submission_handler):
        """Test GET /api/stats/dandisets/{dandiset_id}"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            mock_submission_handler.get_approved_submissions.return_value = [
                {'resourceType': 'Software', 'repository': 'GitHub'},
                {'resourceType': 'Dataset', 'repository': 'Zenodo'}
            ]
            mock_submission_handler.get_community_submissions.return_value = [
                {'resourceType': 'Software', 'repository': 'GitHub'}
            ]
            
            response = client.get('/api/stats/dandisets/dandiset_000001')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data']['dandiset_id'] == 'dandiset_000001'
            assert data['data']['approved_count'] == 2
            assert data['data']['pending_count'] == 1
    
    def test_api_pending_submissions_moderator(self, client, mock_submission_handler, mock_auth_manager):
        """Test GET /api/submissions/pending as moderator"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            mock_submission_handler.get_all_pending_submissions_paginated.return_value = (
                [{'name': 'Test Resource'}],
                {'page': 1, 'total_items': 1, 'total_pages': 1}
            )
            
            response = client.get('/api/submissions/pending')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert len(data['data']) == 1
    
    def test_api_pending_submissions_non_moderator(self, client, mock_auth_manager):
        """Test GET /api/submissions/pending as non-moderator"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.is_moderator.return_value = False
            
            response = client.get('/api/submissions/pending')
            
            assert response.status_code == 403
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
    def test_api_approve_submission_moderator(self, client, mock_submission_handler, mock_auth_manager):
        """Test POST /api/submissions/{dandiset_id}/{filename}/approve as moderator"""
        test_data = {
            'moderator_name': 'Test Moderator',
            'moderator_email': 'moderator@example.com'
        }
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            mock_submission_handler.get_submission_by_filename.return_value = {
                'name': 'Test Resource'
            }
            mock_submission_handler.approve_submission.return_value = True
            
            response = client.post('/api/submissions/dandiset_000001/test.yaml/approve',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
    
    def test_api_approve_submission_not_found(self, client, mock_submission_handler, mock_auth_manager):
        """Test POST /api/submissions/{dandiset_id}/{filename}/approve for non-existent submission"""
        test_data = {
            'moderator_name': 'Test Moderator',
            'moderator_email': 'moderator@example.com'
        }
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            mock_submission_handler.get_submission_by_filename.return_value = None
            
            response = client.post('/api/submissions/dandiset_000001/nonexistent.yaml/approve',
                                 data=json.dumps(test_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
    def test_api_user_submissions_own(self, client, mock_submission_handler, mock_auth_manager):
        """Test GET /api/submissions/user/{user_email} for own submissions"""
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            mock_submission_handler.get_user_submissions_paginated.return_value = (
                [{'name': 'Community Resource'}],  # community
                {'page': 1, 'total_items': 1},     # community pagination
                [{'name': 'Approved Resource'}],   # approved
                {'page': 1, 'total_items': 1}      # approved pagination
            )
            
            response = client.get('/api/submissions/user/test@example.com')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'community_submissions' in data['data']
            assert 'approved_submissions' in data['data']
    
    def test_api_user_submissions_other_non_moderator(self, client, mock_auth_manager):
        """Test GET /api/submissions/user/{user_email} for other user as non-moderator"""
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            mock_auth_manager.is_moderator.return_value = False
            
            response = client.get('/api/submissions/user/other@example.com')
            
            assert response.status_code == 403
            data = json.loads(response.data)
            
            assert data['success'] is False
            assert 'error' in data
    
    def test_api_404_error(self, client):
        """Test 404 error handling for API routes"""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data
    
    def test_api_405_error(self, client):
        """Test 405 error handling for API routes"""
        response = client.put('/api/dandisets')  # PUT not allowed
        
        assert response.status_code == 405
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__])
