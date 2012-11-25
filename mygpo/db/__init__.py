

class DatabaseBackendException(Exception):
    """ Generic database backend exception """


class QueryParameterMissing(DatabaseBackendException):
    """ A mandatory parameter to a query is missing """
