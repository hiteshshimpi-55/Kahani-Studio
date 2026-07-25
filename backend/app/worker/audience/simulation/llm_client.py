"""LLM client stubs for optional persona / patch / rewrite enhancement.

Deterministic simulation in ``simulator.py`` is the v1 path; these methods
are placeholders for a later LLM-backed layer.
"""

from __future__ import annotations


class LLMClient:
    async def simulate_persona(self, *args, **kwargs):
        raise NotImplementedError

    async def generate_patches(self, *args, **kwargs):
        raise NotImplementedError

    async def rewrite(self, *args, **kwargs):
        raise NotImplementedError
