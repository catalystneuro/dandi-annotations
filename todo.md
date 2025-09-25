# TODO

1) Move validation into Pydantic models
- Rely on ExternalResource and AnnotationContributor for field and cross-field validation
- Remove duplicate regex checks from services/routes; routes keep only HTTP envelope checks (auth, content-type, JSON presence)
- Services construct models and propagate validation errors upstream

4) Remove Redundant Code
- Legacy Endpoints in routes.py
- Unused methods in resource_repository.py
- duplicate validation

5) Add Tests
- Unit tests for Pydantic models (validation and serialization)
- Integration tests for services and routes
- Repository tests for storage and retrieval logic
- Service tests for business logic and error handling
- App tests for end-to-end API functionality

7) Remove excessive try-except blocks and excessive .get(x, None) usage

8) Update docstrings to numpy style

9) Update functions/methods to keyword-only

10) ResourceService.get_all_dandisets breaks its contract by digging into the internals of file system storage, rather than relying on external methods from `ResourceRepository`.