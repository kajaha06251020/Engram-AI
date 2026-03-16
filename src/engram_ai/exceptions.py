# src/engram_ai/exceptions.py

class EngramError(Exception):
    """Base exception for all Engram-AI errors."""

class StorageError(EngramError):
    """ChromaDB connection failure, corruption, etc."""

class LLMError(EngramError):
    """Claude API unreachable, rate limited, etc."""

class CrystallizationError(EngramError):
    """Not enough experiences, no patterns found, etc."""

class EvolutionError(EngramError):
    """Config file read-only, write failure, etc."""

class HookError(EngramError):
    """Hook stdin parse failure, pending queue error, etc."""
