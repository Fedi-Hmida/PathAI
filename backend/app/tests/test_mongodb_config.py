from app.core.config import Settings
from app.db.mongodb import _mongodb_client_options


def test_mongodb_client_options_use_certifi_for_atlas_uri() -> None:
    settings = Settings(mongodb_uri="mongodb+srv://example.invalid/pathai")

    options = _mongodb_client_options(settings)

    assert options["serverSelectionTimeoutMS"] == settings.mongodb_server_selection_timeout_ms
    assert "tlsCAFile" in options


def test_mongodb_client_options_do_not_force_tls_for_local_uri() -> None:
    settings = Settings(mongodb_uri="mongodb://localhost:27017")

    options = _mongodb_client_options(settings)

    assert options["serverSelectionTimeoutMS"] == settings.mongodb_server_selection_timeout_ms
    assert "tlsCAFile" not in options
