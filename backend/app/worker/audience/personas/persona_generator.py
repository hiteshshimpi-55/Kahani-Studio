"""Generate synthetic listener personas from PRD §6.9 dimensions.

MVP dimensions:
  - Age band: 16-20, 21-24, 25-34, 35-44
  - Gender: male, female, non_binary
  - City tier: tier_1, tier_2, tier_3
  - Intent: romance_escape, thriller_binge, true_story_curiosity, commute_passtime, share_with_friends
  - Language comfort: hindi, hinglish, english

Full cross-product would be 4×3×3×5×3 = 540 personas.
We sample a representative cohort of 24–48 personas weighted by genre relevance.
"""

from __future__ import annotations

import hashlib
import itertools
import random
from typing import Sequence

from app.worker.audience.personas.models import Persona

# ---------------------------------------------------------------------------
# Dimension values
# ---------------------------------------------------------------------------

AGE_BANDS = ["16-20", "21-24", "25-34", "35-44"]
GENDERS = ["male", "female", "non_binary"]
CITY_TIERS = ["tier_1", "tier_2", "tier_3"]
INTENTS = [
    "romance_escape",
    "thriller_binge",
    "true_story_curiosity",
    "commute_passtime",
    "share_with_friends",
]
LANGUAGE_COMFORTS = ["hindi", "hinglish", "english"]

# Genre → intent weight multipliers (higher = more likely to be sampled)
GENRE_INTENT_WEIGHTS: dict[str, dict[str, float]] = {
    "romance": {"romance_escape": 3.0, "commute_passtime": 1.5, "share_with_friends": 2.0},
    "thriller": {"thriller_binge": 3.0, "commute_passtime": 1.5, "true_story_curiosity": 1.5},
    "drama": {"romance_escape": 1.5, "true_story_curiosity": 2.0, "commute_passtime": 2.0},
    "biopic": {"true_story_curiosity": 3.0, "commute_passtime": 1.5},
    "horror": {"thriller_binge": 2.5, "share_with_friends": 2.0},
    "comedy": {"commute_passtime": 2.5, "share_with_friends": 2.5},
}

# Language → city tier affinities
LANGUAGE_CITY_WEIGHTS: dict[str, dict[str, float]] = {
    "hindi": {"tier_2": 1.5, "tier_3": 2.0, "tier_1": 1.0},
    "english": {"tier_1": 2.5, "tier_2": 1.0, "tier_3": 0.5},
    "hinglish": {"tier_1": 2.0, "tier_2": 1.5, "tier_3": 1.0},
}

# Behavioral priors by age band
AGE_ATTENTION_PRIORS: dict[str, dict[str, float]] = {
    "16-20": {"attention_span_sec": 90.0, "skip_threshold": 0.25, "share_propensity": 0.25},
    "21-24": {"attention_span_sec": 110.0, "skip_threshold": 0.28, "share_propensity": 0.20},
    "25-34": {"attention_span_sec": 130.0, "skip_threshold": 0.35, "share_propensity": 0.12},
    "35-44": {"attention_span_sec": 150.0, "skip_threshold": 0.40, "share_propensity": 0.08},
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def _persona_id(age: str, gender: str, city: str, intent: str, lang: str) -> str:
    """Deterministic persona ID from dimensions."""
    raw = f"{age}|{gender}|{city}|{intent}|{lang}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _weight_for(
    genre: str,
    language: str,
    age: str,
    gender: str,  # noqa: ARG001
    city: str,
    intent: str,
    lang_comfort: str,
) -> float:
    """Compute sampling weight for a persona combination."""
    w = 1.0

    # Genre × intent
    genre_weights = GENRE_INTENT_WEIGHTS.get(genre.lower(), {})
    w *= genre_weights.get(intent, 1.0)

    # Language × city tier
    lang_weights = LANGUAGE_CITY_WEIGHTS.get(language.lower(), {})
    w *= lang_weights.get(city, 1.0)

    # Language comfort match bonus
    if lang_comfort == language.lower():
        w *= 1.5
    elif lang_comfort == "hinglish" and language.lower() == "hindi":
        w *= 1.2

    # Age diversity nudge (avoid all being 25-34)
    if age in ("16-20", "35-44"):
        w *= 1.1

    return w


def generate_personas(
    genre: str = "thriller",
    language: str = "hindi",
    target_count: int = 24,
    seed: int | None = None,
) -> list[Persona]:
    """Generate a representative cohort of synthetic listener personas.

    Samples from the full cross-product weighted by genre + language affinity.
    Guarantees at least `target_count` personas (default 24, matching PRD requirement).
    """
    rng = random.Random(seed)

    # Build full candidate pool with weights
    candidates: list[tuple[float, tuple[str, str, str, str, str]]] = []
    for combo in itertools.product(AGE_BANDS, GENDERS, CITY_TIERS, INTENTS, LANGUAGE_COMFORTS):
        age, gender, city, intent, lang_comfort = combo
        w = _weight_for(genre, language, age, gender, city, intent, lang_comfort)
        candidates.append((w, combo))

    # Weighted sampling without replacement
    sampled: list[tuple[str, str, str, str, str]] = []
    pool = list(candidates)

    while len(sampled) < target_count and pool:
        weights = [w for w, _ in pool]
        chosen_idx = rng.choices(range(len(pool)), weights=weights, k=1)[0]
        _, combo = pool.pop(chosen_idx)
        sampled.append(combo)

    # Build Persona objects
    personas: list[Persona] = []
    for age, gender, city, intent, lang_comfort in sampled:
        priors = AGE_ATTENTION_PRIORS.get(age, AGE_ATTENTION_PRIORS["25-34"])
        personas.append(
            Persona(
                id=_persona_id(age, gender, city, intent, lang_comfort),
                age_band=age,
                gender=gender,
                city_tier=city,
                intent=intent,
                language_comfort=lang_comfort,
                attention_span_sec=priors["attention_span_sec"],
                skip_threshold=priors["skip_threshold"],
                share_propensity=priors["share_propensity"],
            )
        )

    return personas


def get_all_personas() -> Sequence[Persona]:
    """Return the default 24-persona cohort (useful for testing)."""
    return generate_personas()
