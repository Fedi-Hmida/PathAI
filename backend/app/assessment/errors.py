class AssessmentError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AssessmentNotFoundError(AssessmentError):
    def __init__(self, session_id: str) -> None:
        super().__init__(
            code="assessment_session_not_found",
            message=f"Assessment session '{session_id}' was not found.",
            status_code=404,
        )


class AssessmentStateError(AssessmentError):
    pass
