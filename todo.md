# TODO

1) Move validation into Pydantic models
- Rely on ExternalResource and AnnotationContributor for field and cross-field validation
- Remove duplicate regex checks from services/routes; routes keep only HTTP envelope checks (auth, content-type, JSON presence)
- Services construct models and propagate validation errors upstream

2) Move serialization into Pydantic models
- Services return model_dump outputs from Pydantic models
- Minimize custom serializers; keep only envelopes/pagination formatting if needed

3) Remove filename dependence above repository
- Expose a stable resource_id at API/service layers
- Repository handles filename/storage mapping internally
- Migrate endpoints/templates to use resource_id; keep filename-based paths temporarily for compatibility and deprecate later

4) Remove Redundant Code
- Legacy Endpoints in routes.py
- Unused methods in resource_repository.py
- duplicate validation and serialization logic

5) Add Tests
- Unit tests for Pydantic models (validation and serialization)
- Integration tests for services and routes
- Repository tests for storage and retrieval logic
- Service tests for business logic and error handling
- App tests for end-to-end API functionality

7) Remove excessive try-except blocks