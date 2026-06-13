from pathlib import Path


def test_env_example_does_not_contain_real_secret_patterns() -> None:
    env_example = Path(".env.example")
    text = env_example.read_text(encoding="utf-8")

    forbidden_patterns = [
        "sk-",
        "mongodb+srv://",
        "tokenfactory.esprit.tn",
    ]

    assert all(pattern not in text for pattern in forbidden_patterns)


def test_security_docs_do_not_contain_real_secret_patterns() -> None:
    docs = [
        Path("../docs/security/README.md"),
        Path("../docs/security/privacy_policy_notes.md"),
        Path("../docs/security/demo_safety_checklist.md"),
        Path("app/security/README.md"),
        Path("README.md"),
    ]
    forbidden_patterns = [
        "sk-",
        "mongodb+srv://",
        "tokenfactory.esprit.tn",
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert all(pattern not in text for pattern in forbidden_patterns)
