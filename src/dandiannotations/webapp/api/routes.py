"""
API routes for DANDI External Resources webapp
"""

import os
import sys
from flask import request, url_for
from datetime import datetime

# Add the parent directory to the path to import our models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from . import api_bp
from .responses import (
    success_response, error_response, validation_error_response,
    not_found_response, unauthorized_response, forbidden_response,
    internal_error_response, created_response, paginated_response
)
from .serializers import (
    serialize_external_resource, serialize_external_resources,
    serialize_dandiset_info, serialize_dandisets, serialize_user_info,
    serialize_submission_stats, serialize_pagination_info
)
from .validators import (
    validate_json_request, validate_pagination_params, validate_dandiset_id,
    validate_resource_submission, validate_moderator_approval,
    validate_user_registration, validate_content_type
)

from dandiannotations.webapp.utils.submission_handler import SubmissionHandler
from dandiannotations.webapp.utils.auth import AuthManager
from dandiannotations.models.models import ExternalResource, AnnotationContributor


# Initialize handlers (same as in main app)
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'submissions')
submission_handler = SubmissionHandler(SUBMISSIONS_DIR)

MODERATORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'moderators.yaml')
auth_manager = AuthManager(MODERATORS_CONFIG_PATH)




# ============================================================================
# DANDISET ENDPOINTS
# ============================================================================

@api_bp.route('/dandisets', methods=['GET'])
def list_dandisets():
    """
    GET /api/dandisets
    List all dandisets with submission counts
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        is_valid, error_msg, validated_params = validate_pagination_params(page, per_page)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get paginated dandisets
        paginated_dandisets, pagination_info = submission_handler.get_all_dandisets_paginated(
            validated_params['page'], validated_params['per_page']
        )
        
        # Serialize data
        serialized_dandisets = serialize_dandisets(paginated_dandisets)
        serialized_pagination = serialize_pagination_info(pagination_info)
        
        return paginated_response(
            data=serialized_dandisets,
            page=validated_params['page'],
            per_page=validated_params['per_page'],
            total_items=pagination_info['total_items'],
            message="Dandisets retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving dandisets: {str(e)}")


@api_bp.route('/dandisets/<dandiset_id>', methods=['GET'])
def get_dandiset(dandiset_id):
    """
    GET /api/dandisets/{dandiset_id}
    Get specific dandiset information
    """
    try:
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get specific dandiset
        dandiset_info = submission_handler.get_dandiset(dandiset_id)
        
        if not dandiset_info:
            return not_found_response("Dandiset")
        
        # Serialize data
        serialized_dandiset = serialize_dandiset_info(dandiset_info)
        
        return success_response(
            data=serialized_dandiset,
            message="Dandiset information retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving dandiset: {str(e)}")


@api_bp.route('/dandisets/<dandiset_id>/resources', methods=['GET'])
def get_dandiset_resources(dandiset_id):
    """
    GET /api/dandisets/{dandiset_id}/resources
    Get all resources for a specific dandiset
    """
    try:
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        is_valid, error_msg, validated_params = validate_pagination_params(page, per_page)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get all resources (include community submissions only if authenticated)
        include_community = auth_manager.is_authenticated()
        all_resources, pagination_info = submission_handler.get_all_submissions_paginated(
            dandiset_id, validated_params['page'], validated_params['per_page'], include_community
        )
        
        # Serialize data
        serialized_resources = serialize_external_resources(all_resources)
        
        return paginated_response(
            data=serialized_resources,
            page=validated_params['page'],
            per_page=validated_params['per_page'],
            total_items=pagination_info['total_items'],
            message="Dandiset resources retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving dandiset resources: {str(e)}")


@api_bp.route('/dandisets/<dandiset_id>/resources/approved', methods=['GET'])
def get_dandiset_approved_resources(dandiset_id):
    """
    GET /api/dandisets/{dandiset_id}/resources/approved
    Get approved resources for a specific dandiset
    """
    try:
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        is_valid, error_msg, validated_params = validate_pagination_params(page, per_page)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get approved resources
        approved_submissions, pagination_info = submission_handler.get_approved_submissions_paginated(
            dandiset_id, validated_params['page'], validated_params['per_page']
        )
        
        # Serialize data
        serialized_resources = serialize_external_resources(approved_submissions)
        
        return paginated_response(
            data=serialized_resources,
            page=validated_params['page'],
            per_page=validated_params['per_page'],
            total_items=pagination_info['total_items'],
            message="Approved resources retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving approved resources: {str(e)}")


@api_bp.route('/dandisets/<dandiset_id>/resources/pending', methods=['GET'])
def get_dandiset_pending_resources(dandiset_id):
    """
    GET /api/dandisets/{dandiset_id}/resources/pending
    Get pending resources for a specific dandiset (authentication required)
    """
    # Check authentication
    auth_error = auth_manager.require_authentication()
    if auth_error:
        return unauthorized_response(auth_error['error'])
    
    try:
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        is_valid, error_msg, validated_params = validate_pagination_params(page, per_page)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get community (pending) resources
        community_submissions, pagination_info = submission_handler.get_community_submissions_paginated(
            dandiset_id, validated_params['page'], validated_params['per_page']
        )
        
        # Serialize data
        serialized_resources = serialize_external_resources(community_submissions)
        
        return paginated_response(
            data=serialized_resources,
            page=validated_params['page'],
            per_page=validated_params['per_page'],
            total_items=pagination_info['total_items'],
            message="Pending resources retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving pending resources: {str(e)}")


# ============================================================================
# RESOURCE SUBMISSION ENDPOINTS
# ============================================================================

@api_bp.route('/dandisets/<dandiset_id>/resources', methods=['POST'])
def submit_resource(dandiset_id):
    """
    POST /api/dandisets/{dandiset_id}/resources
    Submit a new resource for a dandiset
    """
    try:
        # Validate content type
        is_valid, error_msg = validate_content_type()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Validate JSON request
        is_valid, error_msg = validate_json_request()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get request data
        data = request.get_json()
        
        # Validate resource submission data
        is_valid, error_msg, validation_details = validate_resource_submission(data)
        if not is_valid:
            if validation_details:
                return validation_error_response(validation_details)
            else:
                return validation_error_response(error_msg)
        
        # Create annotation contributor
        contributor_data = {
            'name': data['contributor_name'],
            'email': data['contributor_email'],
            'schemaKey': 'AnnotationContributor'
        }
        
        if data.get('contributor_identifier'):
            contributor_data['identifier'] = data['contributor_identifier']
        
        if data.get('contributor_url'):
            contributor_data['url'] = data['contributor_url']
        
        # Normalize dandiset_id to 6-digit format for Pydantic validation
        normalized_dandiset_id = dandiset_id
        if dandiset_id.startswith('dandiset_'):
            normalized_dandiset_id = dandiset_id.split('_')[1]
        
        # Normalize relation and resourceType to include dcite: prefix if not present
        relation = data['relation']
        if not relation.startswith('dcite:'):
            relation = f"dcite:{relation}"
        
        resource_type = data['resource_type']
        if not resource_type.startswith('dcite:'):
            resource_type = f"dcite:{resource_type}"
        
        # Create external resource data
        resource_data = {
            'dandiset_id': normalized_dandiset_id,
            'annotation_contributor': contributor_data,
            'annotation_date': datetime.now().astimezone().isoformat(),
            'name': data['resource_name'],
            'url': data['resource_url'],
            'repository': data['repository'],
            'relation': relation,
            'resourceType': resource_type,
            'schemaKey': 'ExternalResource'
        }
        
        # Add optional resource identifier if provided
        if data.get('resource_identifier'):
            resource_data['identifier'] = data['resource_identifier']
        
        # Validate using Pydantic models
        try:
            contributor = AnnotationContributor(**contributor_data)
            resource = ExternalResource(**resource_data)
        except Exception as e:
            return validation_error_response(f"Validation error: {str(e)}")
        
        # Save to community submissions folder
        filename = submission_handler.save_community_submission(dandiset_id, resource_data)
        
        # Prepare response data
        response_data = serialize_external_resource(resource_data)
        response_data['filename'] = filename
        response_data['status'] = 'pending'
        
        # Create location header
        location = url_for('api.get_resource', resource_id=filename.replace('.yaml', ''), _external=True)
        
        return created_response(
            data=response_data,
            message="Resource submitted successfully for review",
            location=location
        )
        
    except Exception as e:
        return internal_error_response(f"Error submitting resource: {str(e)}")


@api_bp.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    """
    GET /api/resources/{resource_id}
    Get specific resource details
    """
    try:
        # Find the resource using the new method
        resource = submission_handler.get_resource_by_id(resource_id)
        
        if not resource:
            return not_found_response("Resource")
        
        # Check if user can access community submissions
        if resource.get('_submission_status') == 'community' and not auth_manager.is_authenticated():
            return not_found_response("Resource")
        
        serialized_resource = serialize_external_resource(resource)
        return success_response(
            data=serialized_resource,
            message="Resource retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving resource: {str(e)}")


# ============================================================================
# MODERATION ENDPOINTS
# ============================================================================

@api_bp.route('/submissions/pending', methods=['GET'])
def get_pending_submissions():
    """
    GET /api/submissions/pending
    Get all pending submissions (moderator only)
    """
    # Check moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error['status_code'] == 401:
            return unauthorized_response(auth_error['error'])
        else:
            return forbidden_response(auth_error['error'])
    
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        is_valid, error_msg, validated_params = validate_pagination_params(page, per_page)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get paginated pending submissions
        pending_submissions, pagination_info = submission_handler.get_all_pending_submissions_paginated(
            validated_params['page'], validated_params['per_page']
        )
        
        # Serialize data
        serialized_submissions = serialize_external_resources(pending_submissions)
        
        return paginated_response(
            data=serialized_submissions,
            page=validated_params['page'],
            per_page=validated_params['per_page'],
            total_items=pagination_info['total_items'],
            message="Pending submissions retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving pending submissions: {str(e)}")


@api_bp.route('/submissions/<dandiset_id>/<filename>/approve', methods=['POST'])
def approve_submission(dandiset_id, filename):
    """
    POST /api/submissions/{dandiset_id}/{filename}/approve
    Approve a community submission (moderator only)
    """
    # Check moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error['status_code'] == 401:
            return unauthorized_response(auth_error['error'])
        else:
            return forbidden_response(auth_error['error'])
    
    try:
        # Validate content type
        is_valid, error_msg = validate_content_type()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Validate JSON request
        is_valid, error_msg = validate_json_request()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get request data
        data = request.get_json()
        
        # Validate moderator approval data
        is_valid, error_msg, validation_details = validate_moderator_approval(data)
        if not is_valid:
            if validation_details:
                return validation_error_response(validation_details)
            else:
                return validation_error_response(error_msg)
        
        # Prepare moderator info
        moderator_info = {
            'name': data['moderator_name'],
            'email': data['moderator_email']
        }
        
        if data.get('moderator_identifier'):
            moderator_info['identifier'] = data['moderator_identifier']
        
        if data.get('moderator_url'):
            moderator_info['url'] = data['moderator_url']
        
        # Get submission details before approval
        submission = submission_handler.get_submission_by_filename(dandiset_id, filename, 'community')
        if not submission:
            return not_found_response("Submission")
        
        # Approve the submission
        success = submission_handler.approve_submission(dandiset_id, filename, moderator_info)
        
        if success:
            # Get the approved submission
            approved_submission = submission_handler.get_submission_by_filename(dandiset_id, filename, 'approved')
            serialized_submission = serialize_external_resource(approved_submission) if approved_submission else None
            
            return success_response(
                data=serialized_submission,
                message="Submission approved successfully"
            )
        else:
            return error_response("Failed to approve submission", "APPROVAL_FAILED", 500)
        
    except Exception as e:
        return internal_error_response(f"Error approving submission: {str(e)}")


@api_bp.route('/submissions/user/<user_email>', methods=['GET'])
def get_user_submissions(user_email):
    """
    GET /api/submissions/user/{user_email}
    Get submissions for a specific user (authentication required)
    """
    # Check authentication
    auth_error = auth_manager.require_authentication()
    if auth_error:
        return unauthorized_response(auth_error['error'])
    
    # Users can only view their own submissions
    current_user = auth_manager.get_current_user()
    if current_user['email'] != user_email:
        return forbidden_response("You can only view your own submissions")
    
    try:
        # Get pagination parameters
        community_page = request.args.get('community_page', 1, type=int)
        approved_page = request.args.get('approved_page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination
        is_valid, error_msg, validated_params = validate_pagination_params(community_page, per_page)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get user submissions
        community_submissions, community_pagination, approved_submissions, approved_pagination = \
            submission_handler.get_user_submissions_paginated(
                user_email, community_page, approved_page, per_page
            )
        
        # Serialize data
        serialized_community = serialize_external_resources(community_submissions)
        serialized_approved = serialize_external_resources(approved_submissions)
        
        response_data = {
            'community_submissions': serialized_community,
            'approved_submissions': serialized_approved,
            'community_pagination': serialize_pagination_info(community_pagination),
            'approved_pagination': serialize_pagination_info(approved_pagination)
        }
        
        return success_response(
            data=response_data,
            message="User submissions retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving user submissions: {str(e)}")


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authenticate user and create session
    """
    try:
        # Validate content type
        is_valid, error_msg = validate_content_type()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Validate JSON request
        is_valid, error_msg = validate_json_request()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get request data
        data = request.get_json()
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return validation_error_response("Username and password are required")
        
        # Verify credentials
        user_info = auth_manager.verify_credentials(username, password)
        if user_info:
            auth_manager.login_user(user_info)
            
            # Serialize user info (excluding sensitive data)
            serialized_user = serialize_user_info(user_info)
            
            return success_response(
                data=serialized_user,
                message="Login successful"
            )
        else:
            return error_response("Invalid username or password", "INVALID_CREDENTIALS", 401)
        
    except Exception as e:
        return internal_error_response(f"Error during login: {str(e)}")


@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    Logout current user
    """
    try:
        user_info = auth_manager.get_current_user()
        auth_manager.logout_user()
        
        message = f"Logout successful"
        if user_info:
            message = f"Logout successful for {user_info['name']}"
        
        return success_response(
            data=None,
            message=message
        )
        
    except Exception as e:
        return internal_error_response(f"Error during logout: {str(e)}")


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Register a new user
    """
    try:
        # Validate content type
        is_valid, error_msg = validate_content_type()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Validate JSON request
        is_valid, error_msg = validate_json_request()
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get request data
        data = request.get_json()
        
        # Validate registration data
        is_valid, error_msg, validation_details = validate_user_registration(data)
        if not is_valid:
            if validation_details:
                return validation_error_response(validation_details)
            else:
                return validation_error_response(error_msg)
        
        email = data['email']
        password = data['password']
        
        # Attempt to register user
        if auth_manager.register_user(email, password):
            # Auto-login after successful registration
            user_info = auth_manager.verify_credentials(email, password)
            if user_info:
                auth_manager.login_user(user_info)
                
                # Serialize user info (excluding sensitive data)
                serialized_user = serialize_user_info(user_info)
                
                return created_response(
                    data=serialized_user,
                    message="Registration successful"
                )
            else:
                return success_response(
                    data=None,
                    message="Registration successful. Please log in."
                )
        else:
            return error_response("Email already exists", "EMAIL_EXISTS", 409)
        
    except Exception as e:
        return internal_error_response(f"Error during registration: {str(e)}")


@api_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """
    GET /api/auth/me
    Get current authenticated user information
    """
    # Check authentication
    auth_error = auth_manager.require_authentication()
    if auth_error:
        return unauthorized_response(auth_error['error'])
    
    try:
        current_user = auth_manager.get_current_user()
        
        # Serialize user info (excluding sensitive data)
        serialized_user = serialize_user_info(current_user)
        
        # Add additional user context
        serialized_user['is_moderator'] = auth_manager.is_moderator()
        serialized_user['user_type'] = auth_manager.get_user_type()
        
        return success_response(
            data=serialized_user,
            message="User information retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving user information: {str(e)}")


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@api_bp.route('/stats/overview', methods=['GET'])
def get_overview_stats():
    """
    GET /api/stats/overview
    Get overall platform statistics
    """
    try:
        # Get all dandisets for statistics
        all_dandisets = submission_handler.get_all_dandisets()
        
        # Calculate statistics
        total_dandisets = len(all_dandisets)
        total_approved = sum(ds.get('approved_count', 0) for ds in all_dandisets)
        total_community = sum(ds.get('community_count', 0) for ds in all_dandisets)
        
        # Get all pending submissions for additional stats
        all_pending = submission_handler.get_all_pending_submissions()
        unique_contributors = len(set(
            submission.get('annotation_contributor', {}).get('name')
            for submission in all_pending
            if submission.get('annotation_contributor', {}).get('name')
        ))
        
        stats = {
            'total_dandisets': total_dandisets,
            'total_approved_resources': total_approved,
            'total_pending_resources': total_community,
            'total_resources': total_approved + total_community,
            'unique_contributors': unique_contributors,
            'dandisets_with_resources': len([ds for ds in all_dandisets if ds.get('approved_count', 0) > 0])
        }
        
        # Serialize statistics
        serialized_stats = serialize_submission_stats(stats)
        
        return success_response(
            data=serialized_stats,
            message="Overview statistics retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving overview statistics: {str(e)}")


@api_bp.route('/stats/dandisets/<dandiset_id>', methods=['GET'])
def get_dandiset_stats(dandiset_id):
    """
    GET /api/stats/dandisets/{dandiset_id}
    Get statistics for a specific dandiset
    """
    try:
        # Validate dandiset ID
        is_valid, error_msg = validate_dandiset_id(dandiset_id)
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Get dandiset statistics using the new method
        stats = submission_handler.get_dandiset_stats(dandiset_id)
        
        # Serialize statistics
        serialized_stats = serialize_submission_stats(stats)
        
        return success_response(
            data=serialized_stats,
            message="Dandiset statistics retrieved successfully"
        )
        
    except Exception as e:
        return internal_error_response(f"Error retrieving dandiset statistics: {str(e)}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@api_bp.errorhandler(404)
def api_not_found(error):
    """Handle 404 errors for API routes"""
    return not_found_response("API endpoint")


@api_bp.errorhandler(405)
def api_method_not_allowed(error):
    """Handle 405 errors for API routes"""
    return error_response("Method not allowed", "METHOD_NOT_ALLOWED", 405)


@api_bp.errorhandler(500)
def api_internal_error(error):
    """Handle 500 errors for API routes"""
    return internal_error_response("Internal server error")
