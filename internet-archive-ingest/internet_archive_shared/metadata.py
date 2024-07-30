import logging
import re
from internet_archive_shared import config
from shared.helpers import exists, listify, stringify, get_languages

logger = logging.getLogger()
logger.setLevel(logging.INFO)

IA_FORMAT_TRANSLATION = {
    "EPUB": "epub",
    "Text PDF": "pdf",
    "Grayscale LuraTech PDF": "grayscalePdf",
    "Word Document": "word"
}

IA_OTHER_FORMATS = {
    "EPUB": "epub",
    "Grayscale LuraTech PDF": "grayscalePdf",
    "Word Document": "word"
}

IA_FORMAT_FILENAME_TRANSLATION = {
    "EPUB": ".epub",
    "Text PDF": ".pdf",
    "Grayscale LuraTech PDF": "_BW.pdf",
    "Word Document": ".docx"
}

STD_ID_CLEANUP_REGEX = r'([a-zA-Z]{0,3}[0-9Xx\-]{1,14})[^0-9x]*'
ARCHIVE_ORG_URL = "https://archive.org"
DOWNLOAD_URL = ARCHIVE_ORG_URL + "/download/"
DETAILS_URL = ARCHIVE_ORG_URL + "/details/"


def transform_records(records, session, doc_validator):
    """
    Transform a list of Internet Archive records into EMMA Federated Index ingestion records.
    """
    total_get_item = 0
    emma_record_list = []
    doc_count = [ 0 ]

    errors = []
    for incoming_record in records:
        if exists(incoming_record, 'identifier'):
            emma_records = [];
            num_get_item = transform_record(incoming_record, session, emma_records, errors, doc_validator, doc_count)
            total_get_item += num_get_item
            if emma_records is None or len(emma_records) < 1:
                msg = str(incoming_record['identifier']) + " yielded no loadable records."
                if exists(incoming_record, 'format'):
                    msg = msg + " Available formats: " + ','.join(incoming_record['format'])
                logger.info(str(incoming_record['identifier']) + " yielded no loadable records.")
            emma_record_list.extend(emma_records)
        else:
            logger.info("Skipped record with no identifier")
    logger.info("called get_item " + str(total_get_item) + " times for the "+ str(len(records)) + " records")
    return emma_record_list


def transform_record(incoming_record, session, transformed_records, errors, doc_validator, doc_count):
    """
    Transform Internet Archive search result and get_item result to EMMA Federated Index ingestion records
    """
    num_get_item = 0
    format_file_map = None
    ia_item = None
    if exists(incoming_record, 'format'):
        incoming_formats = incoming_record['format']
        for incoming_format in incoming_formats:
            if incoming_format in IA_FORMAT_TRANSLATION:
                if (incoming_format == "Text PDF") :
                    # num_get_item = num_get_item + 1
                    # logger.info("Calling get_item")
                    # ia_item = session.get_item(str(incoming_record['identifier']))
                    # format_file_map = get_format_file_map(ia_item.files)
                    # emma_record = get_title_field_record(incoming_record, ia_item)
                    # emma_record['emma_retrievalLink'] = get_download_file_link(incoming_format, incoming_record, format_file_map)
                    emma_record = get_title_field_record(incoming_record, ia_item)
                    emma_record['emma_retrievalLink'] = get_download_file_link(incoming_format, incoming_record, None)
                elif incoming_format in IA_OTHER_FORMATS:
                    num_get_item = num_get_item + 1
                    logger.info("Calling get_item")
                    ia_item = session.get_item(str(incoming_record['identifier']))
                    format_file_map = get_format_file_map(ia_item.files)
                    emma_record = get_title_field_record(incoming_record, ia_item)
                    if incoming_format in format_file_map:
                        emma_record['emma_retrievalLink'] = get_download_file_link(incoming_format, incoming_record, format_file_map)
                else :
                    logger.info("format in scrape not in format in ia/metadata ")
                emma_record['dc_format'] = IA_FORMAT_TRANSLATION[incoming_format]
                append_record(transformed_records, emma_record, doc_count, errors, doc_validator)
        '''
        According to email from Internet Archive, these are indicators of automatically created 
        EPUB and DAISY files.  (Andrea Mills <andrea@archive.org> 2020-01-02)
        '''
        if 'DjVuTXT' in incoming_formats and 'Abbyy GZ' in incoming_formats:
            append_record(transformed_records, get_autogen_daisy(incoming_record, ia_item), doc_count, errors, doc_validator)
            if 'EPUB' not in incoming_formats:
                append_record(transformed_records, get_autogen_epub(incoming_record, ia_item), doc_count, errors, doc_validator)

    return num_get_item


def append_record(transformed_records, doc, doc_count, errors, doc_validator) :
    if (doc_validator == None or doc_validator.validate(doc, doc_count, errors)) :
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
        imputed_name = incoming_record['identifier'] + IA_FORMAT_FILENAME_TRANSLATION[incoming_format]
        result = DOWNLOAD_URL + incoming_record['identifier'] + "/" + imputed_name
    elif exists(incoming_record, 'identifier') and exists(format_file_map, incoming_format) and \
           (exists(format_file_map[incoming_format], 'name')) :
        name = format_file_map[incoming_format]['name']
        result = DOWNLOAD_URL + incoming_record['identifier'] + "/" + name
    else :
        logger.info("download file link if failed")
        result = ""
    return result

def get_first_element_or_string(item, default = None):
    if isinstance(item, list):
        # If item is a list (array), return the first element
        return str(item[0]) if item else default
    elif isinstance(item, str):
        # If item is not a list, return the item as a string
        return str(item)
    else:
        return default

def get_title_field_record(record, ia_item):
    """
    Copy all title-level fields (as opposed to artifact-level) from the Internet Archive record
    to the EMMA Federated Index ingestion record.
    AKA "Item Level" in Internet Archive terminology.
    """
    emma_record = {}
    emma_record['emma_repository'] = config.IA_REPOSITORY_NAME
    emma_record['emma_repositoryMetadataUpdateDate'] = record[config.DATE_BOUNDARY_FIELD]
    try:
        if exists(record, 'collection'):
            emma_record['emma_collection'] = listify(record['collection'])
        if exists(record, 'identifier'):
            recId = str(record['identifier'])
            emma_record['emma_repositoryRecordId'] = recId
            emma_record['emma_retrievalLink'] = DOWNLOAD_URL + recId
            emma_record['emma_webPageLink'] = DETAILS_URL + recId
        if exists(record, 'title'):
            emma_record['dc_title'] = get_first_element_or_string(record['title'], 'Untitled')
        else : 
            emma_record['dc_title'] = 'Untitled'
        emma_record['dc_identifier'] = get_identifiers(record, ia_item)
        if exists(record, 'related-external-id'):
            emma_record['dc_relation'] = get_related_identifiers(record)
        if exists(record, 'creator'):
            emma_record['dc_creator'] = listify(record['creator'])
        if exists(record, 'description'):
            emma_record['dc_description'] = stringify(record['description'])
        if exists(record, 'subject'):
            emma_record['dc_subject'] = listify(record['subject'])
        if exists(record, 'date'):
            emma_record['dcterms_dateCopyright'] = get_first_element_or_string(record['date'])[:4]
        if exists(record, 'publisher'):
            emma_record['dc_publisher'] = stringify(record['publisher'])
        if exists(record, 'rights'):
            rights = get_rights(record)
            if not (rights is None) : 
                emma_record['dc_rights'] = rights
        if exists(record, 'publicdate'):
            emma_record['dcterms_dateAccepted'] = record['publicdate']
        if exists(record, 'language'):
            emma_record['dc_language'] = get_languages(record)
        return emma_record
    except Exception as e:
        logger.exception("Exception thrown in get_title_field_record" + e )
        logger.error(record)


def get_autogen_daisy(record, ia_item):
    """
    Inject data known to be true about autogenerated Internet Archive DAISY file
    """
    emma_record = get_title_field_record(record, ia_item)
    emma_record['dc_format'] = 'daisy'
    # Format of DAISY retrieval link per email Andrea Mills <andrea@archive.org> 1/17/2020
    emma_record['emma_retrievalLink'] = DOWNLOAD_URL + record['identifier'] + "/" + record['identifier'] + "_daisy.zip"

    return emma_record


def get_autogen_epub(record, ia_item):
    """
    Inject data known to be true about autogenerated Internet Archive EPUBs
    """
    emma_record = get_title_field_record(record, ia_item)
    emma_record['dc_format'] = 'epub'
    '''
    These fields are taken directly from an autogenerated Internet Archive EPUB.
    '''
    emma_record['s_accessibilityFeature'] = [
        'printPageNumbers', 'tableOfContents']
    emma_record['s_accessMode'] = ['visual', 'textual']
    emma_record['s_accessModeSufficient'] = ['visual', 'textual']
    emma_record['s_accessibilityHazard'] = [
        'noFlashingHazard', 'noMotionSimulationHazard', 'noSoundHazard']
    emma_record['s_accessibilityControl'] = ['fullKeyboardControl',
                                             'fullMouseControl', 'fullSwitchControl', 'fullTouchControl', 'fullVoiceControl']
    emma_record['s_accessibilitySummary'] = 'The publication was generated using automated character recognition, therefore it may not be an accurate rendition of the original text, and it may not offer the correct reading sequence.This publication is missing meaningful alternative text.The publication otherwise meets WCAG 2.0 Level A.'
    emma_record['emma_formatVersion'] = "3.0"
    # Format of DAISY retrieval link per email Andrea Mills <andrea@archive.org> 1/17/2020
    emma_record['emma_retrievalLink'] = DOWNLOAD_URL + record['identifier'] + "/" + record['identifier'] + ".epub"

    return emma_record


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


def get_identifiers(record, item):
    """
    Look in the search result record and the get_item record to try to find standard identifiers
    """
    id_fields = ['isbn', 'oclc', 'lccn']
    identifiers = []
    for id_field in id_fields:
        record_ids = set()
        record_ids.update(set(get_std_ids(record, id_field)))
        if not(item is None) :
            item_ids = set()
            item_ids.update(set(get_std_ids(item.metadata, id_field)))
            if (item_ids != record_ids):
                logger.info("item_ids different from record_ids")
            identifiers.extend(item_ids)
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
            std_id = re.sub(r'[^0-9a-zA-Z]', '', std_id)
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
    if exists(record, 'rights'):
        rights = record['rights']
        if re.match(r'^CC', rights, re.IGNORECASE):
            return 'creativeCommons'
        elif re.match(r'creative commons', rights, re.IGNORECASE):
            return 'creativeCommons'
        elif re.match(r'public', rights, re.IGNORECASE):
            return 'publicDomain'
        else :
            return 'other'


