def test_pending_path_inside_storage_dir(tmp_path, mock_llm):
    storage_dir = tmp_path / "project_a"
    from engram_ai import Forge
    forge = Forge(storage_path=str(storage_dir), llm=mock_llm)
    forge.record_pending(action="test", context="ctx")
    pending_file = storage_dir / "pending.jsonl"
    assert pending_file.exists(), f"pending.jsonl should be inside {storage_dir}"
    # Ensure it is NOT in the parent
    parent_pending = tmp_path / "pending.jsonl"
    assert not parent_pending.exists(), "pending.jsonl must not be in parent dir"
