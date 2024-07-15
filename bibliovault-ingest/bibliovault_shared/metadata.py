import logging
import re
from bibliovault_shared import config
from shared.helpers import exists, listify, get_language

logger = logging.getLogger()
logger.setLevel(logging.INFO)

namespaces = {'onix': 'http://ns.editeur.org/onix/3.0/reference'}

STD_ID_CLEANUP_REGEX = r'([a-zA-Z]{0,3}[0-9Xx\-]{1,14})[^0-9x]*'

def transform_records(records, sentdate, doc_validator):
    """
    Transform a list of Internet Archive records into EMMA Federated Index ingestion records.
    """
    total_get_item = 0
    emma_record_list = []
    doc_count = [ 0 ]

    errors = {}
    for incoming_record in records:
        idval = incoming_record.find('onix:ProductIdentifier[onix:ProductIDType = "01"]/onix:IDValue', namespaces).text
        if not idval is None :
            emma_records = [];
            num_get_item = transform_record(incoming_record, sentdate, emma_records, errors, doc_validator, doc_count)
            total_get_item += num_get_item
            if emma_records is None or len(emma_records) < 1:
                for error in errors :
                    logger.info("error : " + idval + ",".join(errors[error]))
            emma_record_list.extend(emma_records)
        else:
            logger.info("Skipped record with no identifier")
    # logger.info("called get_item " + str(total_get_item) + " times for the "+ str(len(records)) + " records")
    return emma_record_list

def transform_record(incoming_record, sentdate, transformed_records, errors, doc_validator, doc_count):
    """
    Transform Internet Archive search result and get_item result to EMMA Federated Index ingestion records
    """
    num_get_item = 0
    ia_item = None
    emma_record = get_title_field_record(incoming_record, sentdate, ia_item)
    if (emma_record != None) :
        emma_record['dc_format'] = 'epub'
        num_get_item += 1
        append_record(transformed_records, emma_record, doc_count, errors, doc_validator)
    else :
        ia_item = 'error'
        emma_record = get_title_field_record(incoming_record, sentdate, ia_item)

    return num_get_item

def append_record(transformed_records, doc, doc_count, errors, doc_validator) :
    if (doc != None and (doc_validator == None or doc_validator.validate(doc, doc_count, errors))) :
        transformed_records.append(doc)
    doc_count[0] += 1

def get_first_element_or_string(item):
    if isinstance(item, list):
        # If item is a list (array), return the first element
        return str(item[0]) if item else None
    else:
        # If item is not a list, return the item as a string
        return str(item)

def get_title_field_record(record, sentdate, ia_item):
    """
    Copy all title-level fields (as opposed to artifact-level) from the Internet Archive record
    to the EMMA Federated Index ingestion record.
    AKA "Item Level" in Internet Archive terminology.
    """
    global namespaces 
    emma_record = {}
    emma_record['emma_repository'] = config.BV_REPOSITORY_NAME
    emma_record['emma_repositoryMetadataUpdateDate'] =  sentdate

    "emma_recordId"
    try:
        emma_record['emma_collection'] = ['biblioVault', 'epub']
        recordreference = record.find('.//onix:RecordReference', namespaces).text
        recordrefparts = recordreference.split("bibliovault.")
        if len(recordrefparts) > 1 :
            recordretrievallink = "https://bibliovault-transfer-staging.s3.amazonaws.com/" + recordrefparts[1] + ".epub"
        else :
            return None
        idval = record.find('.//onix:ProductIdentifier[onix:ProductIDType = "01"]/onix:IDValue', namespaces).text
        if not idval is None:            
            emma_record['emma_repositoryRecordId'] = idval
        # emma_record['emma_webPageLink'] = 'no web page'
        
        emma_record['emma_retrievalLink'] = recordretrievallink 
        
# <TitleDetail>
#  <TitleType>01</TitleType>
#  <TitleElement>
#   <SequenceNumber>1</SequenceNumber>
#   <TitleElementLevel>01</TitleElementLevel>
#   <NoPrefix />
#   <TitleWithoutPrefix>Bodies on the Front Lines</TitleWithoutPrefix>
#   <Subtitle>Performance, Gender, and Sexuality in Latin America and the Caribbean</Subtitle>
#  </TitleElement>
#  <TitleStatement><![CDATA[Bodies on the Front Lines: Performance, Gender, and Sexuality in Latin America and the Caribbean]]></TitleStatement>
# </TitleDetail>
        title = record.find(".//onix:TitleDetail[onix:TitleType = '01']/onix:TitleElement/onix:TitleWithoutPrefix", namespaces)
        subtitle = record.find(".//onix:TitleDetail[onix:TitleType = '01']/onix:TitleElement/onix:Subtitle", namespaces)
        if title is not None:
            if subtitle is not None:
                full_title = title.text + " : " + subtitle.text
            else :
                full_title = title.text
        else :
            full_title = 'No Title'
        emma_record['dc_title'] = full_title
        
        emma_record['dc_identifier'] = get_identifiers(record)
        # if exists(record, 'doi'):
        #     emma_record['dc_relation'] = ['doi:'+ record['doi']]
        
        emma_record['dc_creator'] = get_authors(record)
       
        emma_record['dc_description'] = get_description(record)
        
        emma_record['dc_subject'] = get_subjects(record)
        
        emma_record['dcterms_dateCopyright'] = get_publication_year(record)
        
        emma_record['dc_publisher'] = get_publisher(record)

        emma_record['dcterms_dateAccepted'] = get_publication_date(record)
        
        emma_record['dc_language'] = get_languages(record)
        # if exists(record, 'primary_location'):
        #     rights = get_rights(record)
        #     if not (rights is None) : 
        #         emma_record['dc_rights'] = rights
        return emma_record
    except Exception as e:
        logger.exception("Exception thrown in get_title_field_record")
        logger.error(record)



# <Contributor>
#  <SequenceNumber>1</SequenceNumber>
#  <ContributorRole>B01</ContributorRole>
#  <PersonName>Brenda Werth</PersonName>
#  <PersonNameInverted>Werth, Brenda</PersonNameInverted>
#  <NamesBeforeKey>Brenda</NamesBeforeKey>
#  <KeyNames>Werth</KeyNames>
# </Contributor>

def get_authors(record):
    authors = []
    contributors = record.findall('.//onix:Contributor', namespaces)
    for contributor in contributors :
        dname = contributor.find("onix:PersonName", namespaces)
        if (dname is not None) :
            authors.append(dname.text)
    return authors


    # <Subject>
    #  <SubjectSchemeIdentifier>04</SubjectSchemeIdentifier>
    #  <SubjectCode>Social change -- Latin America.</SubjectCode>
    # </Subject>

def get_subjects(record):
    subjects = []
    subjectfields = record.findall(".//onix:Subject[onix:SubjectSchemeIdentifier = '04']", namespaces)
    for subjectfield in subjectfields :
        dname = subjectfield.find("onix:SubjectCode", namespaces)
        if (dname is not None) :
            subjects.append(dname.text)
    return subjects


# <CollateralDetail>
#  <TextContent>
#   <TextType>03</TextType>
#   <ContentAudience>00</ContentAudience>
#   <Text textformat="02"><![CDATA[<div><i>Ghosts and the Overplus</i> is a celebration of lyric poetry in the twenty-first century and how lyric poetry incorporates the voices of our age as well as the poetic “ghosts” from the past. Acclaimed poet and award-winning teacher Christina Pugh is fascinated by how poems continually look backward into literary history. Her essays find new resonance in poets ranging from Emily Dickinson to Gwendolyn Brooks to the poetry of the present. Some of these essays also consider the way that poetry interacts with the visual arts, dance, and the decision to live life as a nonconformist. This wide-ranging collection showcases the critical discussions around poetry that took place in America over the first two decades of our current millennium. Essay topics include poetic forms continually in migration, such as the sonnet; poetic borrowings across visual art and dance; and the idiosyncrasies of poets who lived their lives against the grain of literary celebrity and trend. What unites all of these essays is a drive to dig more deeply into the poetic word and act: to go beyond surface reading in order to reside longer with poems. In essays both discursive and personal, Pugh shows that poetry asks us to think differently—in a way that gathers feeling into the realm of thought, thereby opening the mysteries that reside in us and in the world around us.</div>]]></Text>
#  </TextContent>

def get_description(record):
    description = ""
    clean = re.compile('<.*?>')
    clean2 = re.compile('(&nbsp|\n|\r)')
    clean3 = re.compile('[ ][ ]+')
    
    descriptionfield = record.find(".//onix:CollateralDetail/onix:TextContent[onix:TextType = '03']/onix:Text", namespaces)
    if descriptionfield is not None :
        data = descriptionfield.text
        data = re.sub(clean, '', data)
        data = re.sub(clean2, ' ', data)
        data = re.sub(clean3, ' ', data)
        if (data is not None) :
            description = data
    return description

# <PublishingDetail>
#  <Imprint>
#   <ImprintName>University of Michigan Press</ImprintName>
#  </Imprint>
#  <Publisher>
#   <PublishingRole>01</PublishingRole>
#   <PublisherName>University of Michigan Press</PublisherName>
#   <Website>
#    <WebsiteLink>http://www.press.umich.edu</WebsiteLink>
#   </Website>
#  </Publisher>
#  <PublishingStatus>04</PublishingStatus>
#  <PublishingDate>
#   <PublishingDateRole>01</PublishingDateRole>
#   <Date>20240424</Date>
#  </PublishingDate>
#  <CopyrightStatement>
#   <CopyrightYear>2024</CopyrightYear>
#  </CopyrightStatement>

def get_publication_year(record):
    publicationyear = ""
    publicationyearfield = record.find(".//onix:PublishingDetail/onix:CopyrightStatement/onix:CopyrightYear", namespaces)
    if (publicationyearfield is not None) :
        publicationyear = publicationyearfield.text
    return publicationyear

def get_publisher(record):
    publisher = ""
    publisherfield = record.find(".//onix:PublishingDetail/onix:Publisher/onix:PublisherName", namespaces)
    if (publisherfield is not None) :
        publisher = publisherfield.text
    return publisher

def get_publication_date(record):
    publicationdate = ""
    publicationdatefield = record.find(".//onix:PublishingDetail/onix:PublishingDate/onix:Date", namespaces)
    if (publicationdatefield is not None) :
        publicationdate = publicationdatefield.text
    return publicationdate

# <Language>
#  <LanguageRole>01</LanguageRole>
#  <LanguageCode>eng</LanguageCode>
# </Language>

def get_languages(record):
    languages = []
    languagefields = record.findall(".//onix:Language/onix:LanguageCode", namespaces)
    for languagefield in languagefields :
        language = languagefield.text
        language = get_language(language)
        languages.append(language)
    return languages

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

# <ProductIdentifier>
#  <ProductIDType>03</ProductIDType>
#  <IDValue>9780472221684</IDValue>
# </ProductIdentifier>
# <ProductIdentifier>
#  <ProductIDType>15</ProductIDType>
#  <IDValue>9780472221684</IDValue>
# </ProductIdentifier>
# <ProductIdentifier>
#  <ProductIDType>06</ProductIDType>
#  <IDValue>10.3998/mpub.12587385</IDValue>
# </ProductIdentifier>

def get_identifiers(record):
    """
    Look in the search result record and the get_item record to try to find standard identifiers
    """
    id_fields = {'isbn' : ['03', '15'], 'doi' : ['06']}
    identifiers = []
    for id_key in id_fields :
        record_ids = set()
        record_ids.update(set(get_std_ids(record, id_key, id_fields[id_key])))
        identifiers.extend(record_ids)
    identifiers = list(set(identifiers))
    return identifiers


def get_std_ids(record, field, types):
    """
    Normalize standard IDs
    """
    identifiers = []
    doi_pattern = r'(http[s]?://doi.org/)[0-9.]+/[0-9a-zA-Z.]+'
    
    for typeval in types :
        xpath = "./onix:ProductIdentifier[onix:ProductIDType = '" + typeval + "' ]/onix:IDValue"
        ident_fields = record.findall(xpath, namespaces)
        for ident_field in ident_fields : 
            identifier = ident_field.text
            # identifier = remove_trailing_letters(identifier)
            identifier = re.sub(r'[^0-9a-zA-Z://.]', '', identifier)
            if (validate_std_id(identifier, field)) :
                # Add prefix like isbn: depending on field name
                if (field == 'doi' and not re.match(doi_pattern, identifier )):
                    identifier = 'https://doi.org/' + identifier
                identifiers.append(field + ":" + identifier)
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
        pattern = r'(http[s]?://doi.org/)?[0-9.]+/[0-9a-zA-Z.]+'
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


