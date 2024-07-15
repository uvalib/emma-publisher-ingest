"""
Class which uses a jsonSchema to validate some JSON
"""
import json

import iso8601
from iso8601 import ParseError

from jsonschema import Draft7Validator, ValidationError, FormatChecker


class DocValidator:
    def __init__(self, schema_file_name):
        self.validator = Draft7Validator(DocValidator.load_validation_file(schema_file_name),
                                         format_checker=DocValidator.get_format_checker())

    @staticmethod
    def get_format_checker():
        format_checker = FormatChecker()

        @format_checker.checks(format="date")
        def is_iso8601_date(date_string):
            try:
                iso8601.parse_date(date_string)
            except ParseError as e:
                return False
            return True
        return format_checker

    @staticmethod
    def load_validation_file(schema_file_name) -> str:
        """
        Load the jsonSchema for an ingestion record into a data structure
        """
        with open(schema_file_name, 'r') as schema_file:
            data = schema_file.read()
            return json.loads(data)

    def validate(self, doc, doc_count, errors) -> bool:
        """
        Validate the current document against the jsonSchema corresponding to our OpenAPI definition
        If the document fails, return false and save validator error messages to the error list
        """
        try:
            self.validator.validate(doc)
            return True
        except ValidationError:
            error_set = []
            for error in self.validator.iter_errors(doc):
                err_path = map(lambda x: str(x), error.path)
                error_set.append(','.join(err_path) + " : " + error.message)
            errors['document-' + str(doc_count)] = error_set
        return False
