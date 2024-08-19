import pytz
import iso639
import string
from datetime import datetime, timezone

def get_doc_id(doc) -> str:
    """
    Create a document ID from the properties we expect to be unique to a metadata record
    """
    if 'emma_recordId' in doc:
        return doc['emma_recordId']
    doc_id = doc['emma_repository'] + "-" + \
        doc['emma_repositoryRecordId'] + "-" + doc['dc_format']
    if 'emma_formatVersion' in doc:
        doc_id = doc_id + "-" + doc['emma_formatVersion']
    return doc_id


def get_doc_id_prefix(doc) -> str:
    """
    Create a document ID prefix (ID without format) from the properties we expect to be unique to a metadata record
    """
    if 'emma_recordId' in doc:
        parts =  doc['emma_recordId'].split('-')
        parts = parts[0:-1]
        return '-'.join(parts)
    doc_id = doc['emma_repository'] + "-" + \
        doc['emma_repositoryRecordId']
    return doc_id

"""
Date/Time 
We'll work in PST since that's Bookshare's Point of View
"""
def get_now_iso8601_date_pst():
    utc_dt = datetime.now(timezone.utc)
    PST = pytz.timezone('US/Pacific')
    return utc_dt.astimezone(PST).date().isoformat()


def get_now_datetime_pst():
    utc_dt = datetime.now(timezone.utc)
    PST = pytz.timezone('US/Pacific')
    return utc_dt.astimezone(PST)


def get_today_iso8601_datetime_pst():
    return get_now_datetime_pst().isoformat()

def get_now_iso8601_datetime_utc():
    """
    UTC instead of PST for Internet Archive
    """
    utc_dt = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return utc_dt

def get_now_iso8601_date_utc():
    """
    UTC instead of PST for Internet Archive
    """
    utc_dt = datetime.utcnow().strftime("%Y-%m-%d")
    return utc_dt

def is_today(date_str):
    # Parse the date string into a datetime object
    input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # Get today's date
    today = datetime.today().date()
    
    # Return True if the dates are equal, otherwise False
    return input_date == today

# 2024-07-23T16:20:26Z
def is_today_utc(date_time_str):
    # Parse the date string into a datetime object
    input_date = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%SZ").date()
    
    # Get today's date
    today = datetime.today().date()
    
    # Return True if the dates are equal, otherwise False
    return input_date == today

def string_after(s, delimiter):
    """
    Returns the part of the string after the given delimiter.
    If the delimiter is not found, it returns an empty string.
    
    :param s: The original string.
    :param delimiter: The substring after which we want to get the part of the string.
    :return: The part of the string after the delimiter.
    """
    pos = s.find(delimiter)
    if pos != -1:
        return s[pos + len(delimiter):]
    else:
        return ''

def get_languages(record):
    """
    I saw multiple language formats for language from different sources,
    so this attempts to translate all to the ISO 639-2 3-character code
    """
    if exists(record, 'language') and len(record['language']) > 0:
        incoming_language_list = listify(record['language'])
        language_list = []
        for incoming_language in incoming_language_list:
            language = get_language(incoming_language)
            if language is not None and len(language) > 0:
                language_list.append(language)
        return language_list


def get_language(incoming_language):
    """
    Translate the incoming language code into ISO 639-2 3-character code if possible
    The iso639 library is not great about handling keys that don't exist, hence
    all of the exception handling.
    """
    language = None
    try:
        language = iso639.languages.get(part1=incoming_language.lower())
    except KeyError:
        pass
    if language is None:
        try:
            language = iso639.languages.get(part3=incoming_language.lower())
        except KeyError:
            pass
    if language is None:
        try:
            language = iso639.languages.get(part2b=incoming_language.lower())
        except KeyError:
            pass
    if language is None:
        try:
            language = iso639.languages.get(part2t=incoming_language.lower())
        except KeyError:
            pass
    if language is None:
        try:
            language = iso639.languages.get(name=string.capwords(incoming_language))
        except KeyError:
            pass
    if language is not None:
        return language.part2b
    return None

def get_values_by_key(dict_list, key):
    return [d[key] for d in dict_list if key in d]

def get_values_by_key_and_subkey(dict_list, key, subkey):
    return [d[key][subkey] for d in dict_list if key in d]


def exists(record, field_name):
    """
    Our definition of whether a field exists in a Python dict 
    """
    return field_name in record and record[field_name] is not None

def listify(prop):
    """
    If a single property is not  a list but should be, convert to a single-element list
    """
    return prop if isinstance(prop, list) else [prop] 

def stringify(prop):
    """
    If a single property is not  a string but should be, convert to a string
    """
    return prop if not isinstance(prop, list) else " ".join(prop)

