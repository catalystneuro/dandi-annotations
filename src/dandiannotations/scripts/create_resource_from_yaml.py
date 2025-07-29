import yaml
from dandiannotations.models.models import AnnotationContributor, ExternalResource
from dandischema.models import RelationType, ResourceType

def main():
    with open('src/dandiannotations/external_resources/external_resources.yaml', 'r') as f:
        metadata = yaml.safe_load(f)

    external_resources = []
    for resource_metadata in metadata:
        resource_metadata["annotation_contributor"] = AnnotationContributor(**resource_metadata['annotation_contributor'])
        resource_metadata["relation"] = RelationType(resource_metadata['relation'])
        resource_metadata["resourceType"] = ResourceType(resource_metadata['resourceType'])
        external_resource = ExternalResource(**resource_metadata)
        external_resources.append(external_resource)

    for resource_metadata in external_resources:
        print(resource_metadata.name)

if __name__ == '__main__':
    main()
