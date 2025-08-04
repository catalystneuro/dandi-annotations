"""
Integration tests for DANDI External Resources API workflows
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


class TestAPIIntegration:
    """Integration tests for complete API workflows"""
    
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
        """Mock submission handler with realistic test data"""
        # Create comprehensive test data
        test_dandisets = [
            {
                'dandiset_id': 'dandiset_000001',
                'approved_count': 3,
                'community_count': 2
            },
            {
                'dandiset_id': 'dandiset_000002',
                'approved_count': 1,
                'community_count': 1
            },
            {
                'dandiset_id': 'dandiset_000003',
                'approved_count': 0,
                'community_count': 0
            }
        ]
        
        approved_resources = [
            {
                'name': 'Analysis Code Repository',
                'url': 'https://github.com/user/analysis-code',
                'repository': 'GitHub',
                'relation': 'IsSupplementTo',
                'resourceType': 'Software',
                'annotation_contributor': {
                    'name': 'John Doe',
                    'email': 'john@example.com'
                },
                '_filename': 'approved_resource_1.yaml',
                '_dandiset_id': 'dandiset_000001'
            },
            {
                'name': 'Dataset on Zenodo',
                'url': 'https://zenodo.org/record/123456',
                'repository': 'Zenodo',
                'relation': 'IsReferencedBy',
                'resourceType': 'Dataset',
                'annotation_contributor': {
                    'name': 'Jane Smith',
                    'email': 'jane@example.com'
                },
                '_filename': 'approved_resource_2.yaml',
                '_dandiset_id': 'dandiset_000001'
            }
        ]
        
        community_resources = [
            {
                'name': 'Pending Analysis Script',
                'url': 'https://github.com/user/pending-script',
                'repository': 'GitHub',
                'relation': 'IsSupplementTo',
                'resourceType': 'Software',
                'annotation_contributor': {
                    'name': 'Bob Wilson',
                    'email': 'bob@example.com'
                },
                '_filename': 'pending_resource_1.yaml',
                '_dandiset_id': 'dandiset_000001'
            }
        ]
        
        # Create a complete mock handler
        handler = MagicMock()
        handler.get_all_dandisets.return_value = test_dandisets
        handler.get_all_dandisets_paginated.return_value = (
            test_dandisets,
            {
                'page': 1, 'per_page': 10, 'total_items': 3, 'total_pages': 1,
                'has_prev': False, 'has_next': False, 'prev_page': None, 'next_page': None,
                'start_item': 1, 'end_item': 3
            }
        )
        
        handler.get_approved_submissions.return_value = approved_resources
        handler.get_approved_submissions_paginated.return_value = (
            approved_resources,
            {
                'page': 1, 'per_page': 10, 'total_items': 2, 'total_pages': 1,
                'has_prev': False, 'has_next': False, 'prev_page': None, 'next_page': None,
                'start_item': 1, 'end_item': 2
            }
        )
        
        handler.get_community_submissions.return_value = community_resources
        handler.get_community_submissions_paginated.return_value = (
            community_resources,
            {
                'page': 1, 'per_page': 10, 'total_items': 1, 'total_pages': 1,
                'has_prev': False, 'has_next': False, 'prev_page': None, 'next_page': None,
                'start_item': 1, 'end_item': 1
            }
        )
        
        handler.get_all_pending_submissions.return_value = community_resources
        handler.get_all_pending_submissions_paginated.return_value = (
            community_resources,
            {
                'page': 1, 'per_page': 10, 'total_items': 1, 'total_pages': 1,
                'has_prev': False, 'has_next': False, 'prev_page': None, 'next_page': None,
                'start_item': 1, 'end_item': 1
            }
        )
        
        handler.save_community_submission.return_value = 'new_submission.yaml'
        handler.approve_submission.return_value = True
        handler.get_submission_by_filename.return_value = community_resources[0]
        handler.get_user_submissions_paginated.return_value = ([], {}, [], {})
        
        return handler
    
    @pytest.fixture
    def mock_auth_manager(self):
        """Mock authentication manager with different user types"""
        auth = MagicMock()
        
        # Default to authenticated moderator
        auth.is_authenticated.return_value = True
        auth.is_moderator.return_value = True
        auth.get_current_user.return_value = {
            'name': 'Test Moderator',
            'email': 'moderator@example.com',
            'user_type': 'moderator'
        }
        auth.get_user_type.return_value = 'moderator'
        
        return auth
    
    def test_complete_submission_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test complete workflow: submit resource -> view pending -> approve -> view approved"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Step 1: Submit a new resource
            submission_data = {
                'resource_name': 'Integration Test Resource',
                'resource_url': 'https://github.com/test/integration',
                'repository': 'GitHub',
                'relation': 'IsSupplementTo',
                'resource_type': 'Software',
                'contributor_name': 'Integration Tester',
                'contributor_email': 'tester@example.com'
            }
            
            response = client.post('/api/dandisets/dandiset_000001/resources',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            submission_result = json.loads(response.data)
            assert submission_result['success'] is True
            assert submission_result['data']['name'] == 'Integration Test Resource'
            
            # Step 2: View pending submissions (as moderator)
            response = client.get('/api/submissions/pending')
            assert response.status_code == 200
            pending_result = json.loads(response.data)
            assert pending_result['success'] is True
            assert len(pending_result['data']) >= 1
            
            # Step 3: Approve the submission
            approval_data = {
                'moderator_name': 'Test Moderator',
                'moderator_email': 'moderator@example.com'
            }
            
            response = client.post('/api/submissions/dandiset_000001/pending_resource_1.yaml/approve',
                                 data=json.dumps(approval_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            approval_result = json.loads(response.data)
            assert approval_result['success'] is True
            
            # Step 4: View approved resources
            response = client.get('/api/dandisets/dandiset_000001/resources/approved')
            assert response.status_code == 200
            approved_result = json.loads(response.data)
            assert approved_result['success'] is True
            assert len(approved_result['data']) >= 1
    
    def test_authentication_workflow(self, client, mock_auth_manager):
        """Test complete authentication workflow: register -> login -> access protected -> logout"""
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Step 1: Register new user
            registration_data = {
                'email': 'newuser@example.com',
                'password': 'securepassword123',
                'confirm_password': 'securepassword123'
            }
            
            new_user_info = {
                'name': 'New User',
                'email': 'newuser@example.com',
                'user_type': 'user'
            }
            
            mock_auth_manager.register_user.return_value = True
            mock_auth_manager.verify_credentials.return_value = new_user_info
            
            response = client.post('/api/auth/register',
                                 data=json.dumps(registration_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            register_result = json.loads(response.data)
            assert register_result['success'] is True
            assert register_result['data']['email'] == 'newuser@example.com'
            
            # Step 2: Login with new credentials
            login_data = {
                'username': 'newuser@example.com',
                'password': 'securepassword123'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            login_result = json.loads(response.data)
            assert login_result['success'] is True
            assert login_result['data']['email'] == 'newuser@example.com'
            
            # Step 3: Access protected endpoint (get current user info)
            # Update mock to return the new user for the /me endpoint
            mock_auth_manager.get_current_user.return_value = new_user_info
            mock_auth_manager.is_moderator.return_value = False
            mock_auth_manager.get_user_type.return_value = 'user'
            
            response = client.get('/api/auth/me')
            assert response.status_code == 200
            me_result = json.loads(response.data)
            assert me_result['success'] is True
            assert me_result['data']['email'] == 'newuser@example.com'
            
            # Step 4: Logout
            response = client.post('/api/auth/logout')
            assert response.status_code == 200
            logout_result = json.loads(response.data)
            assert logout_result['success'] is True
    
    def test_moderation_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test moderation workflow: view all pending -> filter by dandiset -> approve multiple"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Step 1: View all pending submissions
            response = client.get('/api/submissions/pending')
            assert response.status_code == 200
            all_pending = json.loads(response.data)
            assert all_pending['success'] is True
            
            # Step 2: View pending for specific dandiset
            response = client.get('/api/dandisets/dandiset_000001/resources/pending')
            assert response.status_code == 200
            dandiset_pending = json.loads(response.data)
            assert dandiset_pending['success'] is True
            
            # Step 3: Get detailed stats before approval
            response = client.get('/api/stats/dandisets/dandiset_000001')
            assert response.status_code == 200
            stats_before = json.loads(response.data)
            assert stats_before['success'] is True
            
            # Step 4: Approve submission
            approval_data = {
                'moderator_name': 'Test Moderator',
                'moderator_email': 'moderator@example.com'
            }
            
            response = client.post('/api/submissions/dandiset_000001/pending_resource_1.yaml/approve',
                                 data=json.dumps(approval_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            approval_result = json.loads(response.data)
            assert approval_result['success'] is True
            
            # Step 5: Verify stats updated (would show different counts in real scenario)
            response = client.get('/api/stats/dandisets/dandiset_000001')
            assert response.status_code == 200
            stats_after = json.loads(response.data)
            assert stats_after['success'] is True
    
    def test_user_submission_tracking_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test user submission tracking: submit -> track own submissions -> view status"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Set up regular user (not moderator)
            mock_auth_manager.is_moderator.return_value = False
            mock_auth_manager.get_current_user.return_value = {
                'name': 'Regular User',
                'email': 'user@example.com',
                'user_type': 'user'
            }
            
            # Step 1: Submit resource as regular user
            submission_data = {
                'resource_name': 'User Submitted Resource',
                'resource_url': 'https://github.com/user/resource',
                'repository': 'GitHub',
                'relation': 'IsSupplementTo',
                'resource_type': 'Software',
                'contributor_name': 'Regular User',
                'contributor_email': 'user@example.com'
            }
            
            response = client.post('/api/dandisets/dandiset_000001/resources',
                                 data=json.dumps(submission_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            submission_result = json.loads(response.data)
            assert submission_result['success'] is True
            
            # Step 2: Track own submissions
            mock_submission_handler.get_user_submissions_paginated.return_value = (
                [submission_result['data']],  # community submissions
                {'page': 1, 'total_items': 1, 'total_pages': 1},  # community pagination
                [],  # approved submissions
                {'page': 1, 'total_items': 0, 'total_pages': 1}   # approved pagination
            )
            
            response = client.get('/api/submissions/user/user@example.com')
            assert response.status_code == 200
            user_submissions = json.loads(response.data)
            assert user_submissions['success'] is True
            assert len(user_submissions['data']['community_submissions']) == 1
            assert len(user_submissions['data']['approved_submissions']) == 0
            
            # Step 3: Try to access other user's submissions (should fail)
            response = client.get('/api/submissions/user/other@example.com')
            assert response.status_code == 403
            forbidden_result = json.loads(response.data)
            assert forbidden_result['success'] is False
    
    def test_pagination_workflow(self, client, mock_submission_handler):
        """Test pagination across multiple endpoints"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            
            # Create large dataset for pagination testing
            large_dandiset_list = [
                {'dandiset_id': f'dandiset_{i:06d}', 'approved_count': i, 'community_count': i//2}
                for i in range(1, 26)  # 25 dandisets
            ]
            
            # Test dandisets pagination
            mock_submission_handler.get_all_dandisets_paginated.return_value = (
                large_dandiset_list[:10],  # First 10
                {
                    'page': 1, 'per_page': 10, 'total_items': 25, 'total_pages': 3,
                    'has_prev': False, 'has_next': True, 'prev_page': None, 'next_page': 2,
                    'start_item': 1, 'end_item': 10
                }
            )
            
            # Step 1: Get first page
            response = client.get('/api/dandisets?page=1&per_page=10')
            assert response.status_code == 200
            page1_result = json.loads(response.data)
            assert page1_result['success'] is True
            assert len(page1_result['data']) == 10
            assert page1_result['pagination']['page'] == 1
            assert page1_result['pagination']['has_next'] is True
            assert page1_result['pagination']['has_prev'] is False
            
            # Step 2: Get second page
            mock_submission_handler.get_all_dandisets_paginated.return_value = (
                large_dandiset_list[10:20],  # Second 10
                {
                    'page': 2, 'per_page': 10, 'total_items': 25, 'total_pages': 3,
                    'has_prev': True, 'has_next': True, 'prev_page': 1, 'next_page': 3,
                    'start_item': 11, 'end_item': 20
                }
            )
            
            response = client.get('/api/dandisets?page=2&per_page=10')
            assert response.status_code == 200
            page2_result = json.loads(response.data)
            assert page2_result['success'] is True
            assert len(page2_result['data']) == 10
            assert page2_result['pagination']['page'] == 2
            assert page2_result['pagination']['has_next'] is True
            assert page2_result['pagination']['has_prev'] is True
            
            # Step 3: Get last page
            mock_submission_handler.get_all_dandisets_paginated.return_value = (
                large_dandiset_list[20:25],  # Last 5
                {
                    'page': 3, 'per_page': 10, 'total_items': 25, 'total_pages': 3,
                    'has_prev': True, 'has_next': False, 'prev_page': 2, 'next_page': None,
                    'start_item': 21, 'end_item': 25
                }
            )
            
            response = client.get('/api/dandisets?page=3&per_page=10')
            assert response.status_code == 200
            page3_result = json.loads(response.data)
            assert page3_result['success'] is True
            assert len(page3_result['data']) == 5
            assert page3_result['pagination']['page'] == 3
            assert page3_result['pagination']['has_next'] is False
            assert page3_result['pagination']['has_prev'] is True
    
    def test_error_handling_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test error handling across different scenarios"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Test 1: Invalid dandiset ID
            response = client.get('/api/dandisets/invalid_id')
            assert response.status_code == 400
            error_result = json.loads(response.data)
            assert error_result['success'] is False
            assert 'error' in error_result
            
            # Test 2: Non-existent dandiset
            response = client.get('/api/dandisets/dandiset_999999')
            assert response.status_code == 404
            error_result = json.loads(response.data)
            assert error_result['success'] is False
            
            # Test 3: Invalid submission data
            invalid_submission = {
                'resource_name': 'Test',
                'resource_url': 'not-a-url',  # Invalid URL
                'repository': 'GitHub',
                'relation': 'IsSupplementTo',
                'resource_type': 'Software',
                'contributor_name': 'Test',
                'contributor_email': 'invalid-email'  # Invalid email
            }
            
            response = client.post('/api/dandisets/dandiset_000001/resources',
                                 data=json.dumps(invalid_submission),
                                 content_type='application/json')
            
            assert response.status_code == 400
            error_result = json.loads(response.data)
            assert error_result['success'] is False
            assert 'error' in error_result
            
            # Test 4: Unauthorized access to protected endpoint
            mock_auth_manager.is_authenticated.return_value = False
            
            response = client.get('/api/auth/me')
            assert response.status_code == 401
            error_result = json.loads(response.data)
            assert error_result['success'] is False
            
            # Test 5: Forbidden access (non-moderator accessing moderator endpoint)
            mock_auth_manager.is_authenticated.return_value = True
            mock_auth_manager.is_moderator.return_value = False
            
            response = client.get('/api/submissions/pending')
            assert response.status_code == 403
            error_result = json.loads(response.data)
            assert error_result['success'] is False
    
    def test_statistics_workflow(self, client, mock_submission_handler):
        """Test statistics gathering workflow"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            
            # Step 1: Get overall platform statistics
            response = client.get('/api/stats/overview')
            assert response.status_code == 200
            overview_stats = json.loads(response.data)
            assert overview_stats['success'] is True
            assert 'total_dandisets' in overview_stats['data']
            assert 'total_approved_resources' in overview_stats['data']
            assert 'total_pending_resources' in overview_stats['data']
            
            # Step 2: Get specific dandiset statistics
            response = client.get('/api/stats/dandisets/dandiset_000001')
            assert response.status_code == 200
            dandiset_stats = json.loads(response.data)
            assert dandiset_stats['success'] is True
            assert dandiset_stats['data']['dandiset_id'] == 'dandiset_000001'
            assert 'approved_count' in dandiset_stats['data']
            assert 'pending_count' in dandiset_stats['data']
            assert 'resource_types' in dandiset_stats['data']
            assert 'repositories' in dandiset_stats['data']
            
            # Step 3: Compare statistics across dandisets
            response = client.get('/api/stats/dandisets/dandiset_000002')
            assert response.status_code == 200
            dandiset2_stats = json.loads(response.data)
            assert dandiset2_stats['success'] is True
            assert dandiset2_stats['data']['dandiset_id'] == 'dandiset_000002'
            
            # Verify different dandisets have different stats
            assert dandiset_stats['data']['dandiset_id'] != dandiset2_stats['data']['dandiset_id']


if __name__ == '__main__':
    pytest.main([__file__])
