from app.repositories.factory import RepositoryBundle, build_repository_bundle

_repository_bundle: RepositoryBundle | None = None


def get_repository_bundle() -> RepositoryBundle:
    global _repository_bundle
    if _repository_bundle is None:
        _repository_bundle = build_repository_bundle()
    return _repository_bundle


def reset_repository_bundle_for_tests(bundle: RepositoryBundle | None = None) -> None:
    global _repository_bundle
    _repository_bundle = bundle
