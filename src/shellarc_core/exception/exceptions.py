from enum import Enum


class SA_ExceptionType(Enum):
    DATA_NOTEXIST_ERROR = "Finding data not exist"
    INVALID_USER_QUERY = "Invalid query from user end"
    INVALID_REQUEST_OBJ = "Requesting a non-existing data object"
    EDIT_REJECT = "Avoid user from unintentionally overwriting data"
    SAPYC_SYNTAX_ERROR = "Sapyc expression syntax error"

    STRUCT_ERROR = "Project config fatal structural error"
    SYS_REQUEST_ITEM_NOTEXIST = "System requesting non existing item"
    COMMUN_ERROR = "Communication error with external services"
    AUTH_ERROR = "Auth error with external service"
    LOCAL_IO_ERROR = "Local server file IO error"
    INT_SYNTAX_EREOR = "Internal system syntax error"

