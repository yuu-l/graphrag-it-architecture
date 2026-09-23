"""scripts/gen_docs.py 的单元测试（LLM 用假实现，不依赖真实 API key）。"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import scripts.gen_docs as gen_docs
from app.graph.schema import ComponentCategory


def test_components_cover_23_across_10_categories() -> None:
    assert len(gen_docs.COMPONENTS) == 23
    categories = {spec.category for spec in gen_docs.COMPONENTS}
    assert categories == set(ComponentCategory)


def test_build_prompt_contains_four_sections_and_name() -> None:
    spec = gen_docs.COMPONENTS[0]
    prompt = gen_docs.build_prompt(spec)
    assert spec.name in prompt
    for section in ("## 特性", "## 适用场景", "## 部署形态", "## 局限"):
        assert section in prompt


def test_is_placeholder_api_key() -> None:
    assert gen_docs.is_placeholder_api_key("sk-xxxx")
    assert gen_docs.is_placeholder_api_key("")
    assert not gen_docs.is_placeholder_api_key("sk-real-key-123")


async def test_generate_component_doc_calls_llm() -> None:
    class FakeLLM:
        async def ainvoke(self, prompt: str):
            self.prompt = prompt
            return SimpleNamespace(content="## 特性\n测试正文")

    fake = FakeLLM()
    spec = gen_docs.ComponentSpec("Redis", ComponentCategory.CACHE, "https://redis.io/")
    content = await gen_docs.generate_component_doc(fake, spec)
    assert content == "## 特性\n测试正文"
    assert "Redis" in fake.prompt


def test_write_doc_writes_markdown(tmp_path) -> None:
    spec = gen_docs.ComponentSpec("MySQL", ComponentCategory.DATABASE, "https://dev.mysql.com/")
    path = gen_docs.write_doc(spec, "# 正文", tmp_path)
    assert path.name == "MySQL.md"
    assert path.read_text(encoding="utf-8") == "# 正文"


def test_write_doc_handles_name_with_space(tmp_path) -> None:
    spec = gen_docs.ComponentSpec("Apache HTTP Server", ComponentCategory.WEB_SERVER, "https://httpd.apache.org/")
    path = gen_docs.write_doc(spec, "# x", tmp_path)
    assert path.name == "Apache HTTP Server.md"
    assert path.exists()


async def test_generate_component_doc_rejects_empty_content() -> None:
    class EmptyLLM:
        async def ainvoke(self, prompt: str):
            return SimpleNamespace(content="")

    spec = gen_docs.ComponentSpec("Redis", ComponentCategory.CACHE, "https://redis.io/")
    with pytest.raises(RuntimeError):
        await gen_docs.generate_component_doc(EmptyLLM(), spec)


def test_build_llm_fails_on_placeholder_key(monkeypatch) -> None:
    monkeypatch.setattr(gen_docs.settings, "llm_api_key", "sk-xxxx")
    with pytest.raises(RuntimeError):
        gen_docs._build_llm()
