"""Tests for optional extras distribution behavior."""
import sys
import pytest


class TestClaudeLLMImportGuard:
    def test_raises_import_error_when_anthropic_missing(self, monkeypatch):
        """ClaudeLLM raises ImportError with install hint when anthropic not installed."""
        import importlib
        import engram_ai.llm.claude as claude_mod
        monkeypatch.setitem(sys.modules, "anthropic", None)
        importlib.reload(claude_mod)
        try:
            with pytest.raises(ImportError, match="pip install engram-ai\\[claude\\]"):
                claude_mod.ClaudeLLM()
        finally:
            # Restore the module to its real state
            importlib.reload(claude_mod)

    def test_works_when_anthropic_available(self):
        """ClaudeLLM instantiates normally when anthropic is installed."""
        try:
            from engram_ai.llm.claude import ClaudeLLM
            llm = ClaudeLLM(api_key="sk-test")
            assert llm is not None
        except ImportError:
            pytest.skip("anthropic not installed")


class TestMCPImportGuard:
    def test_raises_import_error_when_mcp_missing(self, monkeypatch):
        """create_mcp_server raises ImportError with install hint when mcp not installed."""
        import importlib
        import engram_ai.mcp as mcp_mod
        monkeypatch.setitem(sys.modules, "mcp", None)
        monkeypatch.setitem(sys.modules, "mcp.server", None)
        monkeypatch.setitem(sys.modules, "mcp.server.stdio", None)
        monkeypatch.setitem(sys.modules, "mcp.types", None)
        importlib.reload(mcp_mod)
        try:
            with pytest.raises(ImportError, match="pip install engram-ai\\[mcp\\]"):
                mcp_mod.create_mcp_server(None)
        finally:
            importlib.reload(mcp_mod)


class TestDashboardImportGuard:
    def test_server_raises_import_error_when_fastapi_missing(self, monkeypatch):
        """Dashboard server raises ImportError with install hint when fastapi missing."""
        import importlib
        import engram_ai.dashboard.server as server_mod
        monkeypatch.setitem(sys.modules, "fastapi", None)
        monkeypatch.setitem(sys.modules, "fastapi.staticfiles", None)
        monkeypatch.setitem(sys.modules, "fastapi.responses", None)
        monkeypatch.setitem(sys.modules, "starlette", None)
        monkeypatch.setitem(sys.modules, "starlette.middleware", None)
        monkeypatch.setitem(sys.modules, "starlette.middleware.cors", None)
        importlib.reload(server_mod)
        try:
            with pytest.raises(ImportError, match="pip install engram-ai\\[dashboard\\]"):
                server_mod.create_app(None)
        finally:
            importlib.reload(server_mod)

    def test_api_raises_import_error_when_fastapi_missing(self, monkeypatch):
        """Dashboard API raises ImportError with install hint when fastapi missing."""
        import importlib
        import engram_ai.dashboard.api as api_mod
        monkeypatch.setitem(sys.modules, "fastapi", None)
        monkeypatch.setitem(sys.modules, "starlette", None)
        monkeypatch.setitem(sys.modules, "starlette.requests", None)
        importlib.reload(api_mod)
        try:
            with pytest.raises(ImportError, match="pip install engram-ai\\[dashboard\\]"):
                api_mod.create_router(None)
        finally:
            importlib.reload(api_mod)


class TestForgeWithoutAnthropic:
    def test_forge_raises_helpful_error_when_no_llm_and_no_anthropic(self, monkeypatch, tmp_path):
        """Forge() with no llm and no anthropic raises ImportError with install hint."""
        import importlib
        import engram_ai.llm.claude as claude_mod
        import engram_ai.forge as forge_mod
        monkeypatch.setitem(sys.modules, "anthropic", None)
        importlib.reload(claude_mod)
        importlib.reload(forge_mod)
        try:
            with pytest.raises(ImportError, match="pip install engram-ai\\[claude\\]"):
                forge_mod.Forge(storage_path=str(tmp_path))
        finally:
            importlib.reload(claude_mod)
            importlib.reload(forge_mod)

    def test_forge_works_with_explicit_llm(self, tmp_path):
        """Forge(llm=mock) works without anthropic."""
        from tests.conftest import MockLLM
        from engram_ai.forge import Forge
        forge = Forge(llm=MockLLM(), storage_path=str(tmp_path))
        assert forge is not None

    def test_forge_succeeds_when_anthropic_installed_but_no_key(self, tmp_path):
        """Forge() with anthropic installed but no API key succeeds at construction."""
        import importlib
        try:
            import anthropic  # noqa: F401
        except ImportError:
            pytest.skip("anthropic not installed")
        # Reload to undo any monkeypatching from earlier tests in this session
        import engram_ai.llm.claude as claude_mod
        import engram_ai.forge as forge_mod
        importlib.reload(claude_mod)
        importlib.reload(forge_mod)
        forge = forge_mod.Forge(storage_path=str(tmp_path))
        assert forge is not None

    def test_recall_is_private(self, tmp_path):
        """recall() is renamed to _recall() and not publicly accessible."""
        from tests.conftest import MockLLM
        from engram_ai.forge import Forge
        forge = Forge(llm=MockLLM(), storage_path=str(tmp_path))
        assert hasattr(forge, "_recall")
        assert not hasattr(forge, "recall")

    def test_check_skill_effectiveness_is_private(self, tmp_path):
        """check_skill_effectiveness() renamed to _check_skill_effectiveness()."""
        from tests.conftest import MockLLM
        from engram_ai.forge import Forge
        forge = Forge(llm=MockLLM(), storage_path=str(tmp_path))
        assert hasattr(forge, "_check_skill_effectiveness")
        assert not hasattr(forge, "check_skill_effectiveness")


class TestPublicAPI:
    def test_query_result_importable(self):
        from engram_ai import QueryResult
        assert QueryResult is not None

    def test_all_exports_present(self):
        import engram_ai
        for name in ["Forge", "Experience", "Skill", "ProjectManager", "QueryResult"]:
            assert hasattr(engram_ai, name), f"Missing export: {name}"

    def test_base_storage_importable_from_submodule(self):
        from engram_ai.storage import BaseStorage
        assert BaseStorage is not None

    def test_base_llm_importable_from_submodule(self):
        from engram_ai.llm import BaseLLM
        assert BaseLLM is not None
