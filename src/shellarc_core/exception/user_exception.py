from datetime import datetime

from shellarc_core.exception.exceptions import SA_ExceptionType


class ShellArcException(Exception):
    def __init__(self,
                 error_log: str,
                 error_type: SA_ExceptionType,
                 frontend_msg: str | None=None
                 ):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_log = f"{now} : {error_type.value} - {error_log}"
        super().__init__(error_log)
        self.frontend_msg = frontend_msg if frontend_msg is not None else error_log

class SA_DataNotExist(ShellArcException):
    def __init__(self, 
                 error_log: str, 
                 frontend_msg: str | None=None
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.DATA_NOTEXIST_ERROR, 
            frontend_msg=frontend_msg
            )
        
class SA_InvalidUserQuery(ShellArcException):
    def __init__(self, 
                 error_log: str,
                 frontend_msg: str | None=None
                 ):
        super().__init__(
            error_log=error_log,
             error_type=SA_ExceptionType.INVALID_USER_QUERY, 
             frontend_msg=frontend_msg
             )
        
class SA_InvalidRequestObj(ShellArcException):
    def __init__(self, 
                 error_log: str,
                 frontend_msg: str | None=None
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.INVALID_REQUEST_OBJ, 
            frontend_msg=frontend_msg
            )
        
class SA_EditingRejection(ShellArcException):
    def __init__(self, 
                 error_log,
                 frontend_msg: str | None=None
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.EDIT_REJECT, 
            frontend_msg=frontend_msg
            )
        
class SA_SapycSyntaxError(ShellArcException):
    def __init__(self, 
                 error_log,
                 frontend_msg: str | None=None
                 ):
        super().__init__(
            error_log=error_log, 
            error_type=SA_ExceptionType.SAPYC_SYNTAX_ERROR, 
            frontend_msg=frontend_msg
            )
        
        
