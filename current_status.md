# DANDI External Resources – Current Status (End of Week)

Goal
- Decouple UI/API/service from filesystem details by using a programmatic UUID as the stable resource identifier instead of storage filenames.
- Push Repository layer toward Pydantic model usage for validation/serialization.
- Reduce redundant/implicit metadata and keep domain models clean.

Why (justification)
- Filenames are a storage implementation detail. Exposing them to services, APIs, and templates creates tight coupling and makes storage changes risky.
- A programmatic UUID embedded in the ExternalResource is stable, explicit, and portable across storage backends.

Key changes implemented
1) Pydantic-first moderation flows in Repository
   - approve_submission now takes an AnnotationContributor and loads/saves via ExternalResource (Pydantic).
   - delete_submission now takes an AnnotationContributor, validates via ExternalResource, and writes deletion audit while validating moderator identity.
   - get_resources_by_dandiset reads YAML → ExternalResource.model_validate → model_dump; removed redundant _submission_status/status; retained _submission_filename temporarily for compatibility.

2) UUID introduced and flowing end-to-end
   - ExternalResource now includes a required uuid field (readOnly).
   - Service submit_resource generates resource_data["uuid"] = uuid4() before Pydantic validation.
   - Repository save_resource now uses external_resource.uuid for filenames (<uuid>.yaml) and returns the uuid string.
   - YAML fixtures updated to include uuid (no hack required in scripts).

3) UI (Flask app) updated to use UUID
   - App routes now accept resource_uuid instead of filename for approve/delete. The app maps uuid → filename only at the very edge when calling current API endpoints.
   - Templates updated (dandiset_resources.html, moderation.html, approve_form.html) to build URLs/actions using resource.uuid, not filenames.
   - confirmDelete JS now posts to /delete/<dandiset_id>/<resource_uuid>/<status>.

4) API moderation routes converted to UUID
   - GET/DELETE/POST moderation endpoints under /api/moderation/submissions now accept resource_uuid instead of filename.
   - Each route maps resource_uuid → <uuid>.yaml when calling existing service methods (service signatures unchanged for now).

5) Scripts/fixtures
   - create_resource_from_code.py now assigns uuid=uuid4() and prints it.
   - create_resource_from_yaml.py no longer generates uuid; expects it in YAML.
   - Two sample YAML files updated with uuid fields.

Smaller improvements
- Consolidated error handling in get_resources_by_dandiset; explicit ValidationError/YAMLError catches.
- Serializer now prefers uuid as id when present; retains filename-derived id as legacy fallback only if uuid is missing.

What’s left (priority-ordered plan)
1) Replace filename in service/repository APIs with uuid
   - Add service methods using UUID directly (e.g., get_submission_by_id) and internally map to filename (<uuid>.yaml) for repository calls.
   - Migrate callers to new UUID-based service methods, then retire get_submission_by_filename and other filename-based APIs.

2) Repository read paths to models and remove filename leakage
   - get_resource_by_filename → get_resource_by_uuid (load from approved/pending by computing filepath).
   - get_all_resources and get_resources_by_user should parse YAML → ExternalResource then model_dump, avoid adding _submission_status/status. Remove _submission_filename once all consumers no longer need it.

3) Serializer/templating cleanup
   - Remove filename fallbacks in serializers once UUID is fully adopted across all consumers.
   - Ensure all templates assume id == uuid and never rely on filename.

4) Deferred: Tests (after architecture stabilizes)
   - Current tests are non-functional; do not update or rely on them now.
   - Once the architecture is stable, repair/add tests for UUID-based flows and model validation.

5) Optional refactors (after stabilization)
   - Consider a lightweight SubmissionRecord wrapper (resource: ExternalResource, id: UUID) inside repository/service boundaries if we want to return models instead of dicts consistently.
   - Centralize display-identifier formatting (DANDI:XXXXXX) in a helper.

Files touched (high level)
- models/models.py: added uuid to ExternalResource (required)
- webapp/repositories/resource_repository.py: approve/delete/read paths via Pydantic; save uses uuid filename; reduced redundant metadata
- webapp/services/resource_service.py: submission generates uuid; serializer prefers uuid
- webapp/app.py: routes converted to resource_uuid; mapping to filename happens here for now
- webapp/api/moderation_routes.py: endpoints now take resource_uuid and map to filename internally
- templates: updated links/actions to use resource.uuid; stop passing filenames
- scripts: updated to handle uuid; fixtures edited to include uuid

Known remaining filename references
- Service: get_submission_by_filename and delete_submission still accept filename; these should gain uuid variants and callers migrated.
- Repository: get_resource_by_filename and remaining methods still add/use filename metadata; migrate to uuid and remove _submission_filename when no longer needed.
- Serializer retains filename fallback for id; remove when no longer needed.

Risk notes / migration reminders
- After UUID migration, ensure no legacy code paths compute id from _submission_filename.
- Keep a single place where uuid → filename is computed (preferably repository), then remove fallback mappers elsewhere.
- Existing stored records lacking uuid will fail validation; we’ve updated sample YAMLs, but data directories in other environments may need a one-time migration to add uuid.

Quick status TL;DR
- UUID identity is implemented and flows through UI and API moderation endpoints.
- Approve/delete are Pydantic-model driven; lists are partially model-driven.
- Filename leakage is largely removed from UI/API; service/repository still use filenames in some methods and will be migrated next.
- Scripts/fixtures updated; tests deferred until the architecture stabilizes.
