import re
from datetime import datetime
from pathlib import Path

from engram_ai.exceptions import EvolutionError


def write_delimited_section(
    path: Path, content: str, start_delim: str, end_delim: str, title: str,
) -> None:
    """Replace or append an HTML-comment-delimited section in a Markdown file."""
    now = datetime.now().isoformat(timespec="seconds")
    section = (
        f"{start_delim}\n"
        f"## {title}\n"
        f"<!-- Auto-generated. Last evolved: {now} -->\n"
        f"{content.rstrip()}\n"
        f"{end_delim}"
    )
    _write_section(path, section, start_delim, end_delim)


def write_comment_delimited_section(
    path: Path, content: str, start_delim: str, end_delim: str, title: str,
) -> None:
    """Replace or append a #-comment-delimited section in a plain text file."""
    now = datetime.now().isoformat(timespec="seconds")
    section = (
        f"{start_delim}\n"
        f"# {title}\n"
        f"# Auto-generated. Last evolved: {now}\n"
        f"{content.rstrip()}\n"
        f"{end_delim}"
    )
    _write_section(path, section, start_delim, end_delim)


def _write_section(path: Path, section: str, start_delim: str, end_delim: str) -> None:
    path = Path(path)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if start_delim in existing and end_delim in existing:
            pattern = re.compile(re.escape(start_delim) + r".*?" + re.escape(end_delim), re.DOTALL)
            content = pattern.sub(section, existing)
        else:
            content = existing.rstrip() + "\n\n" + section + "\n"
    else:
        content = section + "\n"
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise EvolutionError(f"Failed to write to {path}: {e}") from e
