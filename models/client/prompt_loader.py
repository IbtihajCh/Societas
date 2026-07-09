import re
from pathlib import Path
from typing import Optional

import yaml
import jinja2


class PromptLoadError(Exception):
    pass


class PromptLoader:
    _CACHE: dict[str, tuple[dict, jinja2.Template]] = {}

    def __init__(self, prompts_dir: Optional[Path] = None):
        base = Path(__file__).resolve().parent.parent.parent
        self._prompts_dir = prompts_dir or (base / "prompts")

    def load(self, prompt_name: str, variables: Optional[dict] = None) -> tuple[str, dict]:
        cache_key = str(prompt_name)
        if cache_key in self._CACHE:
            frontmatter, template = self._CACHE[cache_key]
        else:
            path = self._prompts_dir / prompt_name
            if not path.exists():
                path = path.with_suffix(".md")
            if not path.exists():
                raise PromptLoadError(f"prompt not found: {prompt_name}")

            raw = path.read_text(encoding="utf-8")

            fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", raw, re.DOTALL)
            if not fm_match:
                raise PromptLoadError(f"missing YAML frontmatter in {path.name}")

            frontmatter = yaml.safe_load(fm_match.group(1))
            body = fm_match.group(2)
            template = jinja2.Template(body)
            self._CACHE[cache_key] = (frontmatter, template)

        rendered = template.render(**(variables or {}))
        return rendered, frontmatter
