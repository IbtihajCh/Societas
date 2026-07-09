import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from models.client.prompt_loader import PromptLoader, PromptLoadError


class TestPromptLoader:
    def test_load_prompts_dir_not_found(self):
        loader = PromptLoader(prompts_dir=Path("/nonexistent"))
        with pytest.raises(PromptLoadError, match="prompt not found"):
            loader.load("nonexistent-prompt")

    def test_load_with_frontmatter_and_template(self):
        with TemporaryDirectory() as tmp:
            prompts_dir = Path(tmp)
            prompt_file = prompts_dir / "test-prompt.md"
            prompt_file.write_text(
                "---\ntemperature: 0.5\nmax_tokens: 100\n---\nHello {{ name }}!"
            )
            loader = PromptLoader(prompts_dir=prompts_dir)
            rendered, frontmatter = loader.load("test-prompt", {"name": "World"})

        assert rendered == "Hello World!"
        assert frontmatter["temperature"] == 0.5
        assert frontmatter["max_tokens"] == 100

    def test_load_without_extension(self):
        with TemporaryDirectory() as tmp:
            prompts_dir = Path(tmp)
            prompt_file = prompts_dir / "my-prompt.md"
            prompt_file.write_text("---\nkey: val\n---\nContent")
            loader = PromptLoader(prompts_dir=prompts_dir)
            rendered, frontmatter = loader.load("my-prompt")
        assert frontmatter["key"] == "val"
        assert rendered == "Content"

    def test_load_caches_frontmatter_and_template(self):
        with TemporaryDirectory() as tmp:
            prompts_dir = Path(tmp)
            prompt_file = prompts_dir / "cached.md"
            prompt_file.write_text("---\na: 1\n---\n{{ x }}")
            loader = PromptLoader(prompts_dir=prompts_dir)
            r1, f1 = loader.load("cached", {"x": "first"})
            r2, f2 = loader.load("cached", {"x": "second"})
        assert f1["a"] == 1
        assert f2["a"] == 1
        assert r1 == "first"
        assert r2 == "second"

    def test_missing_frontmatter_raises_error(self):
        with TemporaryDirectory() as tmp:
            prompts_dir = Path(tmp)
            prompt_file = prompts_dir / "bad.md"
            prompt_file.write_text("No frontmatter here")
            loader = PromptLoader(prompts_dir=prompts_dir)
            with pytest.raises(PromptLoadError, match="missing YAML frontmatter"):
                loader.load("bad")
