"""
Utility functions for extracting schema options from DANDI schema
"""

def get_resource_relation_options():
    """Get valid options for resource relation field"""
    # Common DCITE relation types used in DANDI
    return [
        ("dcite:IsCitedBy", "Is Cited By"),
        ("dcite:Cites", "Cites"),
        ("dcite:IsSupplementedBy", "Is Supplemented By"),
        ("dcite:Supplements", "Supplements"),
        ("dcite:IsReferencedBy", "Is Referenced By"),
        ("dcite:References", "References"),
        ("dcite:IsDocumentedBy", "Is Documented By"),
        ("dcite:Documents", "Documents"),
        ("dcite:IsCompiledBy", "Is Compiled By"),
        ("dcite:Compiles", "Compiles"),
        ("dcite:IsVariantFormOf", "Is Variant Form Of"),
        ("dcite:IsOriginalFormOf", "Is Original Form Of"),
        ("dcite:IsIdenticalTo", "Is Identical To"),
        ("dcite:HasMetadata", "Has Metadata"),
        ("dcite:IsMetadataFor", "Is Metadata For"),
        ("dcite:HasVersion", "Has Version"),
        ("dcite:IsVersionOf", "Is Version Of"),
        ("dcite:IsNewVersionOf", "Is New Version Of"),
        ("dcite:IsPreviousVersionOf", "Is Previous Version Of"),
        ("dcite:IsPartOf", "Is Part Of"),
        ("dcite:HasPart", "Has Part"),
        ("dcite:IsReplacedBy", "Is Replaced By"),
        ("dcite:Replaces", "Replaces"),
        ("dcite:IsRequiredBy", "Is Required By"),
        ("dcite:Requires", "Requires"),
        ("dcite:Obsoletes", "Obsoletes"),
        ("dcite:IsObsoletedBy", "Is Obsoleted By")
    ]

def get_resource_type_options():
    """Get valid options for resource type field"""
    # Common DCITE resource types used in DANDI
    return [
        ("dcite:Audiovisual", "Audiovisual"),
        ("dcite:Book", "Book"),
        ("dcite:BookChapter", "Book Chapter"),
        ("dcite:Collection", "Collection"),
        ("dcite:ComputationalNotebook", "Computational Notebook"),
        ("dcite:ConferencePaper", "Conference Paper"),
        ("dcite:ConferenceProceeding", "Conference Proceeding"),
        ("dcite:DataPaper", "Data Paper"),
        ("dcite:Dataset", "Dataset"),
        ("dcite:Dissertation", "Dissertation"),
        ("dcite:Event", "Event"),
        ("dcite:Image", "Image"),
        ("dcite:InteractiveResource", "Interactive Resource"),
        ("dcite:JournalArticle", "Journal Article"),
        ("dcite:Model", "Model"),
        ("dcite:OutputManagementPlan", "Output Management Plan"),
        ("dcite:PeerReview", "Peer Review"),
        ("dcite:PhysicalObject", "Physical Object"),
        ("dcite:Preprint", "Preprint"),
        ("dcite:Report", "Report"),
        ("dcite:Service", "Service"),
        ("dcite:Software", "Software"),
        ("dcite:Sound", "Sound"),
        ("dcite:Standard", "Standard"),
        ("dcite:Text", "Text"),
        ("dcite:Workflow", "Workflow"),
        ("dcite:Other", "Other")
    ]
