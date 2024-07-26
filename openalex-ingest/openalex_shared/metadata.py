import logging
import re
from openalex_shared import config
from shared.helpers import exists, listify, stringify, get_languages, get_values_by_key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

OA_FORMAT_FILENAME_TRANSLATION = {
    "Text PDF": ".pdf",
}

STD_ID_CLEANUP_REGEX = r'([a-zA-Z]{0,3}[0-9Xx\-]{1,14})[^0-9x]*'
OPENALEX_URL = "https://api.openalex.org"
DOWNLOAD_URL = OPENALEX_URL + "/download/"
DETAILS_URL = OPENALEX_URL + "/details/"


def transform_records(records, doc_validator):
    """
    Transform a list of Internet Archive records into EMMA Federated Index ingestion records.
    """
    total_get_item = 0
    emma_record_list = []
    doc_count = [ 0 ]

    errors = {}
    for incoming_record in records:
        if exists(incoming_record, 'id'):
            emma_records = [];
            num_get_item = transform_record(incoming_record, emma_records, errors, doc_validator, doc_count)
            total_get_item += num_get_item
            if emma_records is None or len(emma_records) < 1:
                msg = str(incoming_record['id']) + " yielded no loadable records."
                if exists(incoming_record, 'format'):
                    msg = msg + " Available formats: " + ','.join(incoming_record['format'])
                logger.info(str(incoming_record['id']) + " yielded no loadable records.")
            emma_record_list.extend(emma_records)
        else:
            logger.info("Skipped record with no identifier")
    # logger.info("called get_item " + str(total_get_item) + " times for the "+ str(len(records)) + " records")
    return emma_record_list


def transform_record(incoming_record, transformed_records, errors, doc_validator, doc_count):
    """
    Transform Internet Archive search result and get_item result to EMMA Federated Index ingestion records
    """
    num_get_item = 0
    emma_record = get_title_field_record(incoming_record)
    if (emma_record != None) :
        emma_record['dc_format'] = 'pdf'
        num_get_item += 1
        append_record(transformed_records, emma_record, doc_count, errors, doc_validator)

    return num_get_item


def append_record(transformed_records, doc, doc_count, errors, doc_validator) :
    if (doc != None and (doc_validator == None or doc_validator.validate(doc, doc_count, errors))) :
        transformed_records.append(doc)
    doc_count[0] += 1


def get_format_file_map(file_list):
    """
    Take the list of files and return of map of format to file
    """
    return dict((i['format'], i) for i in file_list)

def get_download_file_link(incoming_format, incoming_record, format_file_map):
    result = ""
    if exists(incoming_record, 'identifier') and (format_file_map is None) : 
        imputed_name = incoming_record['identifier'] + OA_FORMAT_FILENAME_TRANSLATION[incoming_format]
        result = DOWNLOAD_URL + incoming_record['identifier'] + "/" + imputed_name
    elif exists(incoming_record, 'identifier') and exists(format_file_map, incoming_format) and \
           (exists(format_file_map[incoming_format], 'name')) :
        name = format_file_map[incoming_format]['name']
        result = DOWNLOAD_URL + incoming_record['identifier'] + "/" + name
    else :
        logger.info("download file link if failed")
        result = ""
    return result

def get_first_element_or_string(item):
    if isinstance(item, list):
        # If item is a list (array), return the first element
        return str(item[0]) if item else None
    else:
        # If item is not a list, return the item as a string
        return str(item)

def get_title_field_record(record):
    """
    Copy all title-level fields (as opposed to artifact-level) from the Internet Archive record
    to the EMMA Federated Index ingestion record.
    AKA "Item Level" in Internet Archive terminology.
    """
    emma_record = {}
    emma_record['emma_repository'] = config.OA_REPOSITORY_NAME
    emma_record['emma_repositoryMetadataUpdateDate'] = record['updated_date']
    "emma_recordId"
    try:
        emma_record['emma_collection'] = ['openalex_openaccess', record['type']]
        if exists(record, 'id'):
            idstring = str(record['id'])
            recId = idstring[len("https://openalex.org/"):]
            emma_record['emma_repositoryRecordId'] = recId
            emma_record['emma_webPageLink'] = idstring
        if exists(record, 'best_oa_location'):
            location = record['best_oa_location']
            if exists(location, 'pdf_url'):
                emma_record['emma_retrievalLink'] = location['pdf_url']
            elif exists(location, 'landing_page_url'):
                emma_record['emma_retrievalLink'] = location['landing_page_url']
            else:
                emma_record['emma_retrievalLink'] = 'no_url'
        elif exists(record, 'primary_location'):
            location = record['primary_location']
            if exists(location, 'pdf_url'):
                emma_record['emma_retrievalLink'] = location['pdf_url']
            elif exists(location, 'landing_page_url'):
                emma_record['emma_retrievalLink'] = location['landing_page_url']
            else:
                emma_record['emma_retrievalLink'] = 'no_url'
        else:
            emma_record['emma_retrievalLink'] = 'no_oa_location'
        if exists(record, 'title'):
            emma_record['dc_title'] = get_first_element_or_string(record['title'])
        else :
            emma_record['dc_title'] = 'No Title'
        emma_record['dc_identifier'] = get_identifiers(record)
        if exists(record, 'doi'):
            emma_record['dc_relation'] = ['doi:'+ record['doi']]
        if exists(record, 'authorships'):
            emma_record['dc_creator'] = get_authors(record['authorships'])
        if exists(record, 'abstract_inverted_index'):
            emma_record['dc_description'] = abstractulate(record['abstract_inverted_index'])
        if exists(record, 'topics'):
            emma_record['dc_subject'] = get_values_by_key(record['topics'], 'display_name')
        if exists(record, 'publication_year'):
            emma_record['dcterms_dateCopyright'] = get_first_element_or_string(record['publication_year'])
        if exists(record, 'primary_location'):
            location = record['primary_location']
            if (exists(location, 'source') and exists(location['source'], 'display_name')):
                emma_record['dc_publisher'] = stringify(record['primary_location']['source']['display_name'])
            else : 
                publisher = 'unassigned' 
        if exists(record, 'primary_location'):
            rights = get_rights(record)
            if not (rights is None) : 
                emma_record['dc_rights'] = rights
        if exists(record, 'publication_date'):
            emma_record['dcterms_dateAccepted'] = record['publication_date']
        if exists(record, 'language'):
            emma_record['dc_language'] = get_languages(record)
        return emma_record
    except Exception as e:
        logger.exception("Exception thrown in get_title_field_record")
        logger.error(record)

def get_authors(authorships):
    authors = []
    for author in authorships :
        dname=author['author']['display_name']
        authors.append(dname);
    return authors

def abstractulate(abstract_inverted_index):
    words = []
    for key in abstract_inverted_index.keys() :
        positions = abstract_inverted_index[key]
        for position in positions :
            words.insert(position, key)
    abstract = stringify(words)
    return abstract

def get_related_identifiers(record):
    """
    Using the related-external-id field in search results, create related identifier list
    """
    if exists(record, 'related-external-id'):
        identifiers = []
        related_ids = listify(record['related-external-id'])
        for related_id in related_ids:
            if related_id.startswith('urn:'):
                if related_id.startswith('urn:isbn:') or related_id.startswith('urn:oclc:') or related_id.startswith('urn:lccn:'):
                    identifiers.append(related_id[4:])
        return identifiers


def get_identifiers(record):
    """
    Look in the search result record and the get_item record to try to find standard identifiers
    """
    id_fields = ['isbn', 'oclc', 'lccn', 'doi']
    identifiers = []
    for id_field in id_fields:
        record_ids = set()
        record_ids.update(set(get_std_ids(record, id_field)))
        identifiers.extend(record_ids)
    identifiers = list(set(identifiers))
    return identifiers


def get_std_ids(record, field):
    """
    Normalize standard IDs
    """
    identifiers = []
    if exists(record, field):
        std_ids = listify(record[field])
        for std_id in std_ids:
            # Remove prefix like isbn: if it exists
            if std_id.startswith(field + ":"):
                std_id = std_id[5:]
            # Remove trailing characters after last digit in a alphanumeric sequence
            std_id = remove_trailing_letters(std_id)
            # Remove non alphanumeric characters
            std_id = re.sub(r'[^0-9a-zA-Z://.]', '', std_id)
            if (validate_std_id(std_id, field)) :
                # Add prefix like isbn: depending on field name
                identifiers.append(field + ":" + std_id)
    return identifiers

""" taken from schema
"pattern": "^((isbn|upc|issn):[0-9Xx]{8,14}|lccn:[a-zA-Z0-9]{1,12}|oclc:[0-9]{1,14})$"
"""
def validate_std_id(std_id, field):
    if (field == 'lccn') : 
        pattern = r'^[a-zA-Z0-9]{1,12}$'
    elif (field == 'oclc') :
        pattern = r'^[0-9]{1,14}$'
    elif (field == 'isbn') :
        pattern = r'^[0-9Xx]{8,14}$'
    elif (field == 'doi') :
        pattern = r'http[s]?://doi.org/[0-9.]+/[0-9a-zA-Z.]+'
    else :
        return False
    match = re.match(pattern, std_id)
    return match

def remove_trailing_letters(dirty_id):
    """
    Some Internet Archive records have nonstandard characters after the LCCN
    """
    groups = re.match(STD_ID_CLEANUP_REGEX, dirty_id)
    if groups is not None and len(groups.groups()) > 0 :
        return groups.group(1)
    return dirty_id


def get_rights(record):
    """
    Convert to our controlled rights vocabulary (creativeCommons,publicDomain)
    I didn't see any values for "copyrighted" so that's not included here yet.
    """
    if exists(record, 'primary_location') and exists(record['primary_location'], 'license') :
        rights = record['primary_location']['license']
        if re.match(r'^CC', rights, re.IGNORECASE):
            return 'creativeCommons'
        elif re.match(r'creative commons', rights, re.IGNORECASE):
            return 'creativeCommons'
        elif re.match(r'public', rights, re.IGNORECASE):
            return 'publicDomain'
        else :
            return 'other'


