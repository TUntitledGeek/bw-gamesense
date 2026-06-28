# BWGS algorithm engine, only scores plays, bedwars play list is in actions.py

from dataclasses import dataclass, field
from typing import Any

from conditions import rule_matches_state


@dataclass
class ScoreRule:
    path: str
    comparison: str
    value: Any
    score_change: int
    reasoning: str = ""


@dataclass
class BedwarsPlay:
    name: str
    base_score: int = 0
    rules: list[ScoreRule] = field(default_factory=list)


@dataclass
class ScoredBedwarsPlay:
    play_name: str
    final_score: int
    score_reasoning: list[str] = field(default_factory=list)


class BWScoringMachine:
    def __init__(self, plays: list[BedwarsPlay]):
        self.plays = plays

    def score_the_play(self, game_state: Any, play: BedwarsPlay) -> ScoredBedwarsPlay:
        current_score = play.base_score
        score_reasoning = []

        for rule in play.rules:
            if rule_matches_state(game_state, rule):
                current_score += rule.score_change

                if rule.reasoning:
                    note = f"{rule.score_change:+} | {rule.reasoning}"
                    score_reasoning.append(note)

        return ScoredBedwarsPlay(
            play_name=play.name,
            final_score=current_score,
            score_reasoning=score_reasoning,
        )

    def rank_all_plays(self, game_state: Any) -> list[ScoredBedwarsPlay]:
        play_results = []

        for play in self.plays:
            play_result = self.score_the_play(
                game_state=game_state,
                play=play,
            )

            play_results.append(play_result)

        play_results.sort(key=lambda play_result: play_result.final_score, reverse=True)

        return play_results

    def identify_optimal_play(self, game_state: Any) -> ScoredBedwarsPlay:
        ranked_plays = self.rank_all_plays(game_state)

        if not ranked_plays:
            raise ValueError(
                "BWGS is unable to score anything as no Bedwars plays were provided"
            )

        return ranked_plays[0]
