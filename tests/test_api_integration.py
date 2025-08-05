"""
Integration tests for DANDI External Resources API workflows
"""

import pytest
import json
from unittest.mock import patch
import yaml

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
    def mock_submission_handler(self, tmp_path):
        """Real submission handler with test data created programmatically in temporary directory"""
        mock_submission_path = tmp_path / "mock_submissions"
        mock_submission_path.mkdir(parents=True, exist_ok=True)

        # Create multiple dandiset directory structures for integration testing
        for dandiset_num in ['000001', '000002', '000003']:
            dandiset_dir = mock_submission_path / f"dandiset_{dandiset_num}"
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
        
        # Create approved submissions for dandiset_000001
        approved_submission_1 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'John Doe',
                'email': 'john@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0009-0005-8943-5450'
            },
            'annotation_date': '2025-07-30T10:41:59.867521',
            'name': 'Analysis Code Repository',
            'url': 'https://github.com/user/analysis-code',
            'repository': 'GitHub',
            'relation': 'dcite:IsSupplementTo',
            'resourceType': 'dcite:Software',
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
        
        approved_submission_2 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0009-0005-8943-5451'
            },
            'annotation_date': '2025-07-30T12:41:59.867521',
            'name': 'Dataset on Zenodo',
            'url': 'https://zenodo.org/record/123456',
            'repository': 'Zenodo',
            'relation': 'dcite:IsReferencedBy',
            'resourceType': 'dcite:Dataset',
            'schemaKey': 'ExternalResource',
            'identifier': '12345679',
            'approval_contributor': {
                'name': 'Administrator',
                'email': 'admin@example.com',
                'identifier': None,
                'url': None,
                'schemaKey': 'AnnotationContributor'
            },
            'approval_date': '2025-07-30T13:05:40.081664'
        }
        
        # Create community submissions for dandiset_000001
        community_submission_1 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'Bob Wilson',
                'email': 'bob@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0000-0002-1234-5678'
            },
            'annotation_date': '2024-12-01T09:30:00.000000',
            'name': 'Pending Analysis Script',
            'url': 'https://github.com/user/pending-script',
            'repository': 'GitHub',
            'relation': 'dcite:IsSupplementTo',
            'resourceType': 'dcite:Software',
            'schemaKey': 'ExternalResource',
            'identifier': 'NST-2024-001'
        }
        
        community_submission_2 = {
            'dandiset_id': '000001',
            'annotation_contributor': {
                'name': 'Test Moderator',
                'email': 'moderator@example.com',
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
        
        # Create approved submission for dandiset_000002
        approved_submission_3 = {
            'dandiset_id': '000002',
            'annotation_contributor': {
                'name': 'Alice Cooper',
                'email': 'alice@example.com',
                'schemaKey': 'AnnotationContributor',
                'identifier': 'https://orcid.org/0009-0005-8943-5452'
            },
            'annotation_date': '2025-07-30T14:41:59.867521',
            'name': 'Research Paper',
            'url': 'https://doi.org/10.1038/s41593-024-01234-6',
            'repository': 'Nature Neuroscience',
            'relation': 'dcite:IsCitedBy',
            'resourceType': 'dcite:JournalArticle',
            'schemaKey': 'ExternalResource',
            'identifier': '12345680',
            'approval_contributor': {
                'name': 'Administrator',
                'email': 'admin@example.com',
                'identifier': None,
                'url': None,
                'schemaKey': 'AnnotationContributor'
            },
            'approval_date': '2025-07-30T15:05:40.081664'
        }
        
        # Create community submission for dandiset_000002
        community_submission_3 = {
            'dandiset_id': '000002',
            'annotation_contributor': {
                'name': 'Charlie Brown',
                'email': 'charlie@example.com',
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
        
        # Write the YAML files for dandiset_000001
        dandiset_001_approved_dir = mock_submission_path / "dandiset_000001" / "approved"
        dandiset_001_community_dir = mock_submission_path / "dandiset_000001" / "community"
        
        approved_submission_1_path = dandiset_001_approved_dir / "20250730_104159_submission.yaml"
        with open(approved_submission_1_path, 'w') as f:
            yaml.dump(approved_submission_1, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        approved_submission_2_path = dandiset_001_approved_dir / "20250730_124159_submission.yaml"
        with open(approved_submission_2_path, 'w') as f:
            yaml.dump(approved_submission_2, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        community_submission_1_path = dandiset_001_community_dir / "20241201_093000_submission.yaml"
        with open(community_submission_1_path, 'w') as f:
            yaml.dump(community_submission_1, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        community_submission_2_path = dandiset_001_community_dir / "20241203_141500_submission.yaml"
        with open(community_submission_2_path, 'w') as f:
            yaml.dump(community_submission_2, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        # Write the YAML files for dandiset_000002
        dandiset_002_approved_dir = mock_submission_path / "dandiset_000002" / "approved"
        dandiset_002_community_dir = mock_submission_path / "dandiset_000002" / "community"
        
        approved_submission_3_path = dandiset_002_approved_dir / "20250730_144159_submission.yaml"
        with open(approved_submission_3_path, 'w') as f:
            yaml.dump(approved_submission_3, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        community_submission_3_path = dandiset_002_community_dir / "20241205_102300_submission.yaml"
        with open(community_submission_3_path, 'w') as f:
            yaml.dump(community_submission_3, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        # Create submission handler with the temporary directory
        submission_handler = SubmissionHandler(base_submissions_dir=mock_submission_path)

        return submission_handler

    @pytest.fixture
    def mock_auth_manager(self, tmp_path):
        """Real authentication manager with test configuration"""
        moderators_data = {
            'moderators': {
                'moderator1': {
                    'username': 'moderator1',
                    'password_hash': '$2b$12$koa/SpEe/k6Y6RU1ejCEpu/Pls94i2uQg69tWAgZnArQvE4iaX87u',  # password: mod123
                    'name': 'Test Moderator',
                    'email': 'moderator@example.com'
                }
            }
        }
        config_path = tmp_path / "moderators.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(moderators_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)

        users_data = {
            'users': {
                'user@example.com': {
                    'password_hash': '$2b$12$NycLu.n9og.a5jUH51DThO2Wm95cgTBOuXd8vU6XCMTpyH8uzhite',
                    'name': 'Regular User',
                    'registration_date': '2025-08-04T14:50:50.901882'
                },
                'newuser@example.com': {
                    'password_hash': '$2b$12$NycLu.n9og.a5jUH51DThO2Wm95cgTBOuXd8vU6XCMTpyH8uzhite',
                    'name': 'New User',
                    'registration_date': '2025-08-04T14:50:50.901882'
                }
            }
        }
        users_config_path = tmp_path / "users.yaml"
        with open(users_config_path, 'w') as f:
            yaml.dump(users_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, indent=2)
        
        auth = AuthManager(config_path=config_path)
        return auth
    
    def test_complete_submission_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test complete workflow: submit resource -> view pending -> approve -> view approved"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Login as moderator first
            login_data = {
                'username': 'moderator1',
                'password': 'mod123'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
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
            
            # Capture the filename of the submitted resource
            submitted_filename = submission_result['data']['filename']
            
            # Step 2: View pending submissions (as moderator)
            response = client.get('/api/submissions/pending')
            assert response.status_code == 200
            pending_result = json.loads(response.data)
            assert pending_result['success'] is True
            assert len(pending_result['data']) >= 1
            
            # Step 3: Approve the SAME submission that was just submitted
            approval_data = {
                'moderator_name': 'Test Moderator',
                'moderator_email': 'moderator@example.com'
            }
            
            response = client.post(f'/api/submissions/dandiset_000001/{submitted_filename}/approve',
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
            
            # Find the approved resource that matches our submitted resource
            approved_resource = None
            for resource in approved_result['data']:
                if resource['name'] == 'Integration Test Resource':
                    approved_resource = resource
                    break
            
            # Comprehensive assertions on the approved resource
            assert approved_resource is not None, "Submitted resource not found in approved resources"
            
            # Verify original submission data is preserved
            assert approved_resource['name'] == 'Integration Test Resource'
            assert approved_resource['url'] == 'https://github.com/test/integration'
            assert approved_resource['repository'] == 'GitHub'
            assert approved_resource['relation'] == 'dcite:IsSupplementTo'
            assert approved_resource['resourceType'] == 'dcite:Software'
            assert approved_resource['dandiset_id'] == 'dandiset_000001'
            assert approved_resource['schemaKey'] == 'ExternalResource'
            
            # Verify contributor information
            assert approved_resource['annotation_contributor']['name'] == 'Integration Tester'
            assert approved_resource['annotation_contributor']['email'] == 'tester@example.com'
            assert approved_resource['annotation_contributor']['schemaKey'] == 'AnnotationContributor'
            
            # Verify approval information
            assert approved_resource['approval_contributor']['name'] == 'Test Moderator'
            assert approved_resource['approval_contributor']['email'] == 'moderator@example.com'
            assert approved_resource['approval_contributor']['schemaKey'] == 'AnnotationContributor'
            
            # Verify metadata fields exist
            assert 'annotation_date' in approved_resource
            assert 'approval_date' in approved_resource
            assert '_submission_filename' in approved_resource
            assert '_submission_status' in approved_resource
            assert approved_resource['_submission_status'] == 'approved'
            assert approved_resource['_submission_filename'] == submitted_filename
    
    def test_authentication_workflow(self, client, mock_auth_manager):
        """Test complete authentication workflow: register -> login -> access protected -> logout"""
        
        with patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Step 1: Register new user
            registration_data = {
                'email': 'testuser@example.com',
                'password': 'securepassword123',
                'confirm_password': 'securepassword123'
            }
            
            response = client.post('/api/auth/register',
                                 data=json.dumps(registration_data),
                                 content_type='application/json')
            
            assert response.status_code == 201
            register_result = json.loads(response.data)
            assert register_result['success'] is True
            assert register_result['data']['email'] == 'testuser@example.com'
            
            # Step 2: Login with new credentials
            login_data = {
                'username': 'testuser@example.com',
                'password': 'securepassword123'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            login_result = json.loads(response.data)
            assert login_result['success'] is True
            assert login_result['data']['email'] == 'testuser@example.com'
            
            # Step 3: Access protected endpoint (get current user info)
            response = client.get('/api/auth/me')
            assert response.status_code == 200
            me_result = json.loads(response.data)
            assert me_result['success'] is True
            assert me_result['data']['email'] == 'testuser@example.com'
            
            # Step 4: Logout
            response = client.post('/api/auth/logout')
            assert response.status_code == 200
            logout_result = json.loads(response.data)
            assert logout_result['success'] is True
    
    def test_moderation_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test moderation workflow: view all pending -> filter by dandiset -> approve -> verify changes"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Login as moderator first
            login_data = {
                'username': 'moderator1',
                'password': 'mod123'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            # Step 1: View all pending submissions
            response = client.get('/api/submissions/pending')
            assert response.status_code == 200
            all_pending = json.loads(response.data)
            assert all_pending['success'] is True
            assert len(all_pending['data']) >= 1
            
            # Step 2: View pending for specific dandiset and extract a submission to approve
            response = client.get('/api/dandisets/dandiset_000001/resources/pending')
            assert response.status_code == 200
            dandiset_pending = json.loads(response.data)
            assert dandiset_pending['success'] is True
            assert len(dandiset_pending['data']) >= 1
            
            # Extract the first pending submission for approval
            pending_submission = dandiset_pending['data'][0]
            submission_filename = pending_submission['_submission_filename']
            submission_name = pending_submission['name']
            
            # Step 3: Get detailed stats before approval
            response = client.get('/api/stats/dandisets/dandiset_000001')
            assert response.status_code == 200
            stats_before = json.loads(response.data)
            assert stats_before['success'] is True
            
            # Capture counts before approval
            approved_count_before = stats_before['data']['approved_count']
            pending_count_before = stats_before['data']['pending_count']
            total_count_before = stats_before['data']['total_count']
            
            # Step 4: Approve the specific submission from the pending list
            approval_data = {
                'moderator_name': 'Test Moderator',
                'moderator_email': 'moderator@example.com'
            }
            
            response = client.post(f'/api/submissions/dandiset_000001/{submission_filename}/approve',
                                 data=json.dumps(approval_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            approval_result = json.loads(response.data)
            assert approval_result['success'] is True
            
            # Comprehensive assertions on the approval result
            approved_resource = approval_result['data']
            assert approved_resource['_submission_status'] == 'approved'
            assert approved_resource['_submission_filename'] == submission_filename
            assert approved_resource['name'] == submission_name
            assert approved_resource['dandiset_id'] == 'dandiset_000001'
            assert approved_resource['schemaKey'] == 'ExternalResource'
            
            # Verify approval metadata was added
            assert approved_resource['approval_contributor']['name'] == 'Test Moderator'
            assert approved_resource['approval_contributor']['email'] == 'moderator@example.com'
            assert approved_resource['approval_contributor']['schemaKey'] == 'AnnotationContributor'
            assert 'approval_date' in approved_resource
            
            # Verify original submission data is preserved
            assert approved_resource['name'] == pending_submission['name']
            assert approved_resource['url'] == pending_submission['url']
            assert approved_resource['repository'] == pending_submission['repository']
            assert approved_resource['relation'] == pending_submission['relation']
            assert approved_resource['resourceType'] == pending_submission['resourceType']
            assert approved_resource['annotation_contributor'] == pending_submission['annotation_contributor']
            
            # Step 5: Verify stats updated correctly
            response = client.get('/api/stats/dandisets/dandiset_000001')
            assert response.status_code == 200
            stats_after = json.loads(response.data)
            assert stats_after['success'] is True
            
            # Assert that counts changed as expected
            assert stats_after['data']['approved_count'] == approved_count_before + 1
            assert stats_after['data']['pending_count'] == pending_count_before - 1
            assert stats_after['data']['total_count'] == total_count_before  # Total should remain the same
            
            # Step 6: Verify the resource appears in approved list and not in pending
            response = client.get('/api/dandisets/dandiset_000001/resources/approved')
            assert response.status_code == 200
            approved_list = json.loads(response.data)
            assert approved_list['success'] is True
            
            # Find the approved resource in the approved list
            found_approved = None
            for resource in approved_list['data']:
                if resource['name'] == submission_name:
                    found_approved = resource
                    break
            
            assert found_approved is not None, f"Approved resource '{submission_name}' not found in approved list"
            assert found_approved['_submission_status'] == 'approved'
            assert found_approved['_submission_filename'] == submission_filename
            
            # Step 7: Verify the resource no longer appears in pending list
            response = client.get('/api/dandisets/dandiset_000001/resources/pending')
            assert response.status_code == 200
            updated_pending = json.loads(response.data)
            assert updated_pending['success'] is True
            
            # Ensure the approved resource is no longer in pending
            for resource in updated_pending['data']:
                assert resource['name'] != submission_name, f"Approved resource '{submission_name}' still appears in pending list"
    
    def test_user_submission_tracking_workflow(self, client, mock_submission_handler, mock_auth_manager):
        """Test user submission tracking: submit -> track own submissions -> view status"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler), \
             patch('dandiannotations.webapp.api.routes.auth_manager', mock_auth_manager):
            
            # Login as regular user first
            login_data = {
                'username': 'user@example.com',
                'password': 'password123'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
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
            response = client.get('/api/submissions/user/user@example.com')
            assert response.status_code == 200
            user_submissions = json.loads(response.data)
            assert user_submissions['success'] is True
            
            # Step 3: Try to access other user's submissions (should fail)
            response = client.get('/api/submissions/user/other@example.com')
            assert response.status_code == 403
            forbidden_result = json.loads(response.data)
            assert forbidden_result['success'] is False
    
    def test_pagination_workflow(self, client, mock_submission_handler):
        """Test pagination across multiple endpoints"""
        
        with patch('dandiannotations.webapp.api.routes.submission_handler', mock_submission_handler):
            
            # Step 1: Get first page of dandisets
            response = client.get('/api/dandisets?page=1&per_page=10')
            assert response.status_code == 200
            page1_result = json.loads(response.data)
            assert page1_result['success'] is True
            assert 'pagination' in page1_result
            
            # Step 2: Get second page if available
            if page1_result['pagination']['has_next']:
                response = client.get('/api/dandisets?page=2&per_page=10')
                assert response.status_code == 200
                page2_result = json.loads(response.data)
                assert page2_result['success'] is True
                assert page2_result['pagination']['page'] == 2
            
            # Step 3: Test pagination with different page sizes
            response = client.get('/api/dandisets?page=1&per_page=5')
            assert response.status_code == 200
            small_page_result = json.loads(response.data)
            assert small_page_result['success'] is True
            assert small_page_result['pagination']['per_page'] == 5

if __name__ == '__main__':
    pytest.main([__file__])
