class MSKObjectError(Exception):
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.msg)

class MSKObject_NoneCreationError(MSKObjectError):
    def __init__(self, msg: str):
        super().__init__(msg)

class MSKObject_FormatError(MSKObjectError):
    def __init__(self, msg: str):
        super().__init__(msg)

class MSKObject_ValidationError(MSKObjectError):
    def __init__(self, msg: str):
        super().__init__(msg)

class MSKObject_ExistenceError(MSKObjectError):
    def __init__(self, msg: str):
        super().__init__(msg)

class MSKObject_CachingError(MSKObjectError):
    def __init__(self, msg: str):
        super().__init__(msg)

class MSKObject_QueryLogicError(MSKObjectError):
    def __init__(self, msg: str):
        super().__init__(msg)

