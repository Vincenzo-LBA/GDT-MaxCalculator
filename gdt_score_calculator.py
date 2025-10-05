"""Game Dev Tycoon review score calculator.

This module implements an approximation of the review algorithm from
Greenheart Games' *Game Dev Tycoon*.  It is heavily inspired by community
documentation that describes the internal score (``g``) used to determine
review ratings.  The main entry points are :class:`ReviewAlgorithm`, which
contains the scoring logic, and :func:`simulate_best_game`, which explores a
grid of design/tech point combinations to find the best possible result.

The core formula is ``g = (m + m·q) · p · o · r · w · t`` where:

* ``m`` – Normalised sum of design and technology points.
* ``q`` – Quality factor produced from the design/tech ratio and optional
  research bonuses.
* ``p`` – Multiplier for platform/genre synergies.
* ``o`` – Multiplier for audience/theme synergies.
* ``r`` – Bug penalty that scales with the amount of unresolved bugs.
* ``w`` – Penalty for developing on multiple platforms simultaneously.
* ``t`` – Trend bonus applied when the game matches an ongoing trend.

After calculating ``g`` the algorithm compares it to a Target Game Score
to determine a provisional review rating.  The final rating is capped by an
``expertise limit`` that reflects team specialisation in the original game.

This script is not official and should be treated as an educational tool.
Feel free to tweak the defaults if you have more accurate data for your
version of the game.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain, combinations
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class GameParameters:
    """Container for parameters needed to compute the game score and rating."""

    design_points: float
    tech_points: float
    genre: str
    size: str
    platform_factor: float = 1.0
    audience_factor: float = 1.0
    bug_ratio: float = 0.0
    multi_platform_penalty: float = 1.0
    trend_factor: float = 1.0
    extra_quality: float = 0.0
    target_game_score: float = 100.0
    expertise_limit: float = 9.0


class ReviewAlgorithm:
    """Implements the review calculation used in *Game Dev Tycoon*.

    Use :meth:`calculate_game_score` to compute the internal game score (``g``)
    and :meth:`calculate_final_rating` to compute the provisional review
    rating.  The ideal design/tech ratios are approximate values gathered from
    community guides.  If you have more recent data you can adjust the ratios
    in :data:`IDEAL_DT_RATIOS` accordingly.
    """

    #: Ideal Design/Tech ratios by genre based on community documentation.
    IDEAL_DT_RATIOS: Dict[str, float] = {
        "Adventure": 0.4,
        "RPG": 0.6,
        "Strategy": 1.4,
        "Simulation": 1.6,
        "Action": 1.8,
        "Casual": 0.5,
    }

    #: Size multipliers used to normalise design/tech points by game size.
    SIZE_MULTIPLIERS: Dict[str, float] = {
        "Small": 1.0,
        "Medium": 1.2,
        "Large": 1.4,
        "AAA": 1.7,
    }

    def calculate_quality_factor(self, design: float, tech: float, genre: str) -> float:
        """Calculate the quality factor ``q`` based on the design/tech ratio.

        ``q`` rewards games whose design-to-tech ratio is close to the ideal
        ratio for the selected genre and penalises games that deviate too far
        from it.

        Returns
        -------
        float
            ``+0.1`` when the ratio is within 10 % of the ideal, ``-0.1`` when
            it differs by more than 30 %, or ``0`` otherwise.
        """

        ratio = float("inf") if tech <= 0 else design / tech
        ideal = self.IDEAL_DT_RATIOS.get(genre, 1.0)

        difference = float("inf") if ideal == 0 else abs(ratio - ideal) / ideal

        if difference < 0.1:
            return 0.1
        if difference > 0.3:
            return -0.1
        return 0.0

    def calculate_game_score(self, params: GameParameters) -> float:
        """Compute the internal game score ``g`` for the supplied parameters."""

        size_mult = self.SIZE_MULTIPLIERS.get(params.size, 1.0)
        if size_mult == 0:
            raise ValueError("Size multiplier must be non-zero.")

        total_points = params.design_points + params.tech_points
        m = total_points / (2.0 * size_mult)

        q_base = self.calculate_quality_factor(
            params.design_points, params.tech_points, params.genre
        )
        q = q_base + params.extra_quality

        p = params.platform_factor
        o = params.audience_factor

        bug_ratio = max(0.0, min(params.bug_ratio, 1.0))
        r = 1.0 - 0.8 * bug_ratio

        w = params.multi_platform_penalty
        t = params.trend_factor

        return (m + m * q) * p * o * r * w * t

    def calculate_final_rating(
        self, g: float, target_game_score: float, expertise_limit: float
    ) -> float:
        """Calculate the provisional review rating based on ``g``.

        The raw rating is ``10 * g / target_game_score`` and is clamped to the
        range [1, 10].  The expertise limit simulates the game's specialist cap
        and further scales the rating.  The result is finally capped at 10.
        """

        if target_game_score <= 0:
            raise ValueError("Target game score must be positive.")

        raw_rating = 10.0 * g / target_game_score
        clamped = max(1.0, min(raw_rating, 10.0))
        final_rating = clamped * (expertise_limit / 10.0)
        return min(final_rating, 10.0)


def _powerset(iterable: Iterable[str]) -> Iterable[Tuple[str, ...]]:
    """Return the powerset of the provided iterable as tuples."""

    items = list(iterable)
    return chain.from_iterable(combinations(items, r) for r in range(len(items) + 1))


def simulate_best_game(
    genre: str,
    size: str,
    platform_factor: float = 1.0,
    audience_factor: float = 1.0,
    bug_ratio: float = 0.0,
    trend_factor: float = 1.0,
    extra_quality: float = 0.0,
    design_range: Tuple[int, int] = (50, 300),
    tech_range: Tuple[int, int] = (50, 300),
    step: int = 5,
    target_game_score: float = 300.0,
    expertise_limit: float = 9.0,
    research_options: Optional[Dict[str, Tuple[int, int]]] = None,
) -> Tuple[float, GameParameters, float]:
    """Explore design/tech combinations to find the highest scoring game."""

    algorithm = ReviewAlgorithm()

    best_g = 0.0
    best_params: Optional[GameParameters] = None
    best_rating = 0.0

    research_combos: List[Tuple[str, ...]]
    if research_options:
        research_combos = [tuple(combo) for combo in _powerset(research_options)]
    else:
        research_combos = [tuple()]

    for design in range(design_range[0], design_range[1] + 1, step):
        for tech in range(tech_range[0], tech_range[1] + 1, step):
            for combo in research_combos:
                bonus_design = 0
                bonus_tech = 0

                if research_options:
                    for item in combo:
                        d_bonus, t_bonus = research_options[item]
                        bonus_design += d_bonus
                        bonus_tech += t_bonus

                params = GameParameters(
                    design_points=design + bonus_design,
                    tech_points=tech + bonus_tech,
                    genre=genre,
                    size=size,
                    platform_factor=platform_factor,
                    audience_factor=audience_factor,
                    bug_ratio=bug_ratio,
                    multi_platform_penalty=1.0,
                    trend_factor=trend_factor,
                    extra_quality=extra_quality,
                    target_game_score=target_game_score,
                    expertise_limit=expertise_limit,
                )

                g_score = algorithm.calculate_game_score(params)
                rating = algorithm.calculate_final_rating(
                    g_score, params.target_game_score, params.expertise_limit
                )

                if g_score > best_g:
                    best_g = g_score
                    best_params = params
                    best_rating = rating

    if best_params is None:
        raise RuntimeError("No valid game parameters found. Check input ranges.")

    return best_g, best_params, best_rating


def main() -> None:
    """Example usage when executing this module directly."""

    genre = "Strategy"
    size = "Small"
    platform_factor = 1.0
    audience_factor = 1.0
    bug_ratio = 0.0
    trend_factor = 1.0
    extra_quality = 0.0
    design_range = (50, 150)
    tech_range = (50, 150)
    step = 10
    target_game_score = 300.0
    expertise_limit = 9.0

    research_options = {
        "Savegame": (5, 5),
        "Linear Story": (8, 4),
        "2D Graphics v2": (10, 10),
        "Mono Sound": (3, 3),
    }

    best_g, best_params, best_rating = simulate_best_game(
        genre=genre,
        size=size,
        platform_factor=platform_factor,
        audience_factor=audience_factor,
        bug_ratio=bug_ratio,
        trend_factor=trend_factor,
        extra_quality=extra_quality,
        design_range=design_range,
        tech_range=tech_range,
        step=step,
        target_game_score=target_game_score,
        expertise_limit=expertise_limit,
        research_options=research_options,
    )

    print(f"Best g: {best_g:.2f}")
    print(f"Best rating: {best_rating:.2f}")
    print("Parameters for best game:")
    print(best_params)


if __name__ == "__main__":
    main()

