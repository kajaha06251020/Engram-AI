import pytest
from engram_ai.project import ProjectManager


def _make_pm(tmp_path, mock_llm, **overrides):
    config = {"default_project": "default", **overrides}
    return ProjectManager(base_path=tmp_path, llm=mock_llm, config=config)


def test_get_forge_creates_project_dir(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    forge = pm.get_forge("myproject")
    assert (tmp_path / "myproject").is_dir()
    assert forge is not None


def test_get_forge_default_project(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    pm.get_forge()
    assert (tmp_path / "default").is_dir()


def test_get_forge_caches_instance(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    f1 = pm.get_forge("test")
    f2 = pm.get_forge("test")
    assert f1 is f2


def test_list_projects_empty(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    assert pm.list_projects() == []


def test_list_projects_after_create(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    pm.get_forge("alpha")
    pm.get_forge("beta")
    projects = pm.list_projects()
    assert set(projects) == {"alpha", "beta"}


def test_delete_project(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    pm.get_forge("to_delete")
    assert (tmp_path / "to_delete").is_dir()
    pm.delete_project("to_delete")
    assert not (tmp_path / "to_delete").is_dir()
    assert "to_delete" not in pm.list_projects()


def test_delete_default_raises(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    with pytest.raises(ValueError, match="default"):
        pm.delete_project("default")


def test_invalid_project_name_raises(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    with pytest.raises(ValueError):
        pm.get_forge("bad name!")


def test_get_all_forges(tmp_path, mock_llm):
    pm = _make_pm(tmp_path, mock_llm)
    pm.get_forge("a")
    pm.get_forge("b")
    all_forges = pm.get_all_forges()
    assert set(all_forges.keys()) == {"a", "b"}


def test_backward_compat_old_layout(tmp_path, mock_llm):
    """If base_path itself has chroma.sqlite3, treat it as the default project."""
    (tmp_path / "chroma.sqlite3").touch()
    pm = _make_pm(tmp_path, mock_llm)
    forge = pm.get_forge("default")
    assert forge is not None
    # The default subdir should NOT be created
    assert not (tmp_path / "default").is_dir()
