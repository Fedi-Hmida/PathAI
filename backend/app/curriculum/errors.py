class CurriculumError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CurriculumNotFoundError(CurriculumError):
    def __init__(self, curriculum_id: str) -> None:
        super().__init__(
            code="curriculum_not_found",
            message=f"Curriculum '{curriculum_id}' was not found.",
            status_code=404,
        )


class CurriculumInputError(CurriculumError):
    pass
