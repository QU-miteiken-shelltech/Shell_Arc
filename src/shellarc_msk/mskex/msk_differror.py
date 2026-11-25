class MSKDiffError(Exception):
    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.msg)

class MSKDiff_NonComparableError(MSKDiffError):
    def __init__(self, msg: str):
        super().__init__(msg)

class MSKDiff_SettingsContradictionError(MSKDiffError):
    def __init__(self, msg: str):
        super().__init__(msg)
