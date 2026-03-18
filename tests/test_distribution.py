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
