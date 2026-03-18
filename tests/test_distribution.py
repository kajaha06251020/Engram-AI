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
