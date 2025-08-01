"""
Pytest tests to validate that Pydantic model validation matches frontend validation.

This module tests all validation scenarios for the AnnotationContributor and 
ExternalResource models to ensure backend validation aligns with frontend rules.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from dandiannotations.models.models import AnnotationContributor, ExternalResource


class TestAnnotationContributor:
    """Test AnnotationContributor validation rules"""

    @pytest.fixture
    def valid_contributor_data(self):
        """Fixture providing valid contributor data"""
        return {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "identifier": "https://orcid.org/0000-0002-1825-0097",
            "url": "https://johndoe.com"
        }

    def test_valid_contributor_creation(self, valid_contributor_data):
        """Test that valid contributor data creates a contributor successfully"""
        contributor = AnnotationContributor(**valid_contributor_data)
        assert contributor.name == "John Doe"
        assert contributor.email == "john.doe@example.com"
        assert str(contributor.identifier) == "https://orcid.org/0000-0002-1825-0097"

    def test_required_fields_validation(self):
        """Test that required fields are properly validated"""
        # Test missing name
        with pytest.raises(ValidationError) as exc_info:
            AnnotationContributor(email="test@example.com")
        assert "name" in str(exc_info.value)

        # Test missing email
        with pytest.raises(ValidationError) as exc_info:
            AnnotationContributor(name="Test User")
        assert "email" in str(exc_info.value)

        # Test missing both
        with pytest.raises(ValidationError):
            AnnotationContributor()

    def test_invalid_email_validation(self):
        """Test that invalid email formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AnnotationContributor(
                name="John Doe",
                email="invalid-email"
            )
        assert "email" in str(exc_info.value).lower()

    @pytest.mark.parametrize("valid_orcid", [
        "https://orcid.org/0000-0002-1825-0097",
        "https://orcid.org/0000-0000-0000-000X",
        "https://orcid.org/1234-5678-9012-3456"
    ])
    def test_valid_orcid_formats(self, valid_orcid):
        """Test that valid ORCID formats are accepted"""
        contributor = AnnotationContributor(
            name="Test User",
            email="test@example.com",
            identifier=valid_orcid
        )
        assert str(contributor.identifier) == valid_orcid

    @pytest.mark.parametrize("invalid_orcid", [
        "https://orcid.org/0000-0002-1825-009",  # Too short
        "https://orcid.org/0000-0002-1825-00977",  # Too long
        "https://orcid.org/000-0002-1825-0097",  # Wrong format
        "http://orcid.org/0000-0002-1825-0097",  # Wrong protocol
        "orcid.org/0000-0002-1825-0097",  # Missing protocol
        "https://orcid.org/abcd-efgh-ijkl-mnop",  # Non-numeric
    ])
    def test_invalid_orcid_formats(self, invalid_orcid):
        """Test that invalid ORCID formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AnnotationContributor(
                name="Test User",
                email="test@example.com",
                identifier=invalid_orcid
            )
        assert "ORCID" in str(exc_info.value)

    @pytest.mark.parametrize("valid_url", [
        "https://example.com",
        "http://test.org",
        "https://subdomain.example.com/path",
        "https://example.com:8080/path?query=value"
    ])
    def test_valid_url_formats(self, valid_url):
        """Test that valid URL formats are accepted"""
        contributor = AnnotationContributor(
            name="Test User",
            email="test@example.com",
            url=valid_url
        )
        # URL normalization may add trailing slashes, so we check that the URL is accepted
        assert contributor.url is not None
        assert str(contributor.url).startswith(valid_url.split('://')[0] + '://')

    @pytest.mark.parametrize("invalid_url", [
        "ftp://example.com",  # Wrong protocol
        "example.com",  # Missing protocol
        "https://",  # Incomplete
        "not-a-url",  # Not a URL
    ])
    def test_invalid_url_formats(self, invalid_url):
        """Test that invalid URL formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AnnotationContributor(
                name="Test User",
                email="test@example.com",
                url=invalid_url
            )
        assert "URL" in str(exc_info.value)

    def test_optional_fields(self):
        """Test that optional fields can be None"""
        contributor = AnnotationContributor(
            name="Test User",
            email="test@example.com"
        )
        assert contributor.identifier is None
        assert contributor.url is None


class TestExternalResource:
    """Test ExternalResource validation rules"""

    @pytest.fixture
    def valid_contributor(self):
        """Fixture providing a valid contributor for testing"""
        return AnnotationContributor(
            name="John Doe",
            email="john.doe@example.com"
        )

    @pytest.fixture
    def valid_resource_data(self, valid_contributor):
        """Fixture providing valid external resource data"""
        return {
            "dandiset_id": "000001",
            "name": "Test Resource",
            "url": "https://example.com/resource",
            "repository": "GitHub",
            "relation": "dcite:IsSupplementTo",
            "annotation_contributor": valid_contributor,
            "annotation_date": datetime.now()
        }

    def test_valid_external_resource_creation(self, valid_resource_data):
        """Test that valid external resource data creates a resource successfully"""
        resource = ExternalResource(**valid_resource_data)
        assert resource.dandiset_id == "000001"
        assert resource.name == "Test Resource"
        assert str(resource.url) == "https://example.com/resource"

    @pytest.mark.parametrize("valid_dandiset_id", [
        "000001",
        "123456",
        "999999"
    ])
    def test_valid_dandiset_id_formats(self, valid_dandiset_id, valid_contributor):
        """Test that valid DANDI Set ID formats are accepted"""
        resource = ExternalResource(
            dandiset_id=valid_dandiset_id,
            name="Test Resource",
            url="https://example.com/resource",
            repository="GitHub",
            relation="dcite:IsSupplementTo",
            annotation_contributor=valid_contributor,
            annotation_date=datetime.now()
        )
        assert resource.dandiset_id == valid_dandiset_id

    @pytest.mark.parametrize("invalid_dandiset_id", [
        "1",  # Too short
        "1234567",  # Too long
        "00000a",  # Non-numeric
        "dandiset_000001",  # Old format no longer supported
        "DANDISET_000001",  # Wrong case
        "",  # Empty
        "000-001",  # Wrong format
    ])
    def test_invalid_dandiset_id_formats(self, invalid_dandiset_id, valid_contributor):
        """Test that invalid DANDI Set ID formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ExternalResource(
                dandiset_id=invalid_dandiset_id,
                name="Test Resource",
                url="https://example.com/resource",
                repository="GitHub",
                relation="dcite:IsSupplementTo",
                annotation_contributor=valid_contributor,
                annotation_date=datetime.now()
            )
        assert "DANDI set ID" in str(exc_info.value)

    def test_custom_validation_only(self, valid_contributor):
        """Test that our custom validation (dandiset_id) works correctly"""
        # We only test our custom validation since parent Resource class handles other fields
        # This test ensures our dandiset_id validation is working
        
        # Test that valid dandiset_id works
        resource = ExternalResource(
            dandiset_id="000001",
            name="Test Resource",
            url="https://example.com/resource",
            repository="GitHub",
            relation="dcite:IsSupplementTo",
            annotation_contributor=valid_contributor,
            annotation_date=datetime.now()
        )
        assert resource.dandiset_id == "000001"
        
        # Test that invalid dandiset_id fails
        with pytest.raises(ValidationError) as exc_info:
            ExternalResource(
                dandiset_id="invalid",
                name="Test Resource",
                url="https://example.com/resource",
                repository="GitHub",
                relation="dcite:IsSupplementTo",
                annotation_contributor=valid_contributor,
                annotation_date=datetime.now()
            )
        assert "DANDI set ID" in str(exc_info.value)


class TestIntegrationScenarios:
    """Test integration scenarios with both models"""

    def test_complete_valid_scenario(self):
        """Test complete integration scenario with all valid data"""
        contributor = AnnotationContributor(
            name="Dr. Jane Smith",
            email="jane.smith@university.edu",
            identifier="https://orcid.org/0000-0002-1825-0097",
            url="https://janesmith.university.edu"
        )
        
        resource = ExternalResource(
            dandiset_id="000123",  # Updated to use 6-digit format only
            name="Analysis Code for Neural Data",
            url="https://github.com/janesmith/neural-analysis",
            repository="GitHub",
            relation="dcite:IsSupplementTo",
            annotation_contributor=contributor,
            annotation_date=datetime.now()
        )
        
        assert resource.name == "Analysis Code for Neural Data"
        assert resource.dandiset_id == "000123"
        assert resource.annotation_contributor.name == "Dr. Jane Smith"
        assert str(resource.annotation_contributor.identifier) == "https://orcid.org/0000-0002-1825-0097"

    def test_resource_with_approval(self):
        """Test resource creation with approval contributor"""
        contributor = AnnotationContributor(
            name="Dr. Jane Smith",
            email="jane.smith@university.edu",
            identifier="https://orcid.org/0000-0002-1825-0097"
        )
        
        approver = AnnotationContributor(
            name="Dr. Bob Wilson",
            email="bob.wilson@institute.org"
        )
        
        resource = ExternalResource(
            dandiset_id="000456",
            name="Supplementary Analysis",
            url="https://zenodo.org/record/123456",
            repository="Zenodo",
            relation="dcite:IsReferencedBy",
            annotation_contributor=contributor,
            annotation_date=datetime.now(),
            approval_contributor=approver,
            approval_date=datetime.now()
        )
        
        assert resource.approval_contributor is not None
        assert resource.approval_contributor.name == "Dr. Bob Wilson"
        assert resource.approval_date is not None

    def test_minimal_valid_data(self):
        """Test creation with minimal required data"""
        contributor = AnnotationContributor(
            name="Minimal User",
            email="minimal@example.com"
        )
        
        resource = ExternalResource(
            dandiset_id="000789",
            name="Minimal Resource",
            url="https://example.com/minimal",
            repository="Example Repo",
            relation="dcite:IsSupplementTo",
            annotation_contributor=contributor,
            annotation_date=datetime.now()
        )
        
        assert resource.annotation_contributor.identifier is None
        assert resource.annotation_contributor.url is None
        assert resource.approval_contributor is None
        assert resource.approval_date is None


# Pytest configuration and helper functions
def test_models_import_successfully():
    """Test that the models can be imported without errors"""
    from dandiannotations.models.models import AnnotationContributor, ExternalResource
    assert AnnotationContributor is not None
    assert ExternalResource is not None


if __name__ == "__main__":
    # Allow running with pytest or directly
    pytest.main([__file__, "-v"])
