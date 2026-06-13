from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings


class PromptNotFoundError(FileNotFoundError):
    """Raised when a named prompt template is missing."""


class PromptRenderError(ValueError):
    """Raised when a prompt template cannot be rendered."""


@dataclass(frozen=True)
class RenderedPrompt:
    name: str
    version: str
    content: str


class _StrictFormatDict(dict[str, object]):
    def __missing__(self, key: str) -> object:
        raise PromptRenderError(f"Missing prompt variable: {key}") from None


class PromptRegistry:
    def __init__(self, template_dir: Path, version: str) -> None:
        self.template_dir = template_dir
        self.version = version

    def load_template(self, name: str) -> str:
        path = self.template_dir / f"{name}.md"
        if not path.exists():
            raise PromptNotFoundError(f"Prompt template '{name}' was not found.")
        return path.read_text(encoding="utf-8")

    def render(self, name: str, variables: dict[str, object] | None = None) -> RenderedPrompt:
        template = self.load_template(name)
        try:
            rendered = template.format_map(_StrictFormatDict(variables or {}))
        except PromptRenderError:
            raise
        except Exception as exc:
            raise PromptRenderError(f"Could not render prompt '{name}'.") from exc

        return RenderedPrompt(
            name=name,
            version=self.version,
            content=f"Prompt-Version: {self.version}\nPrompt-Name: {name}\n\n{rendered}",
        )


def get_prompt_registry(settings: Settings | None = None) -> PromptRegistry:
    active_settings = settings or get_settings()
    template_dir = Path(__file__).parent / "templates"
    return PromptRegistry(template_dir=template_dir, version=active_settings.llm_prompt_version)
