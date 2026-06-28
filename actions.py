import json
from pathlib import Path

from algoengine import BedwarsPlay, ScoreRule

Plays_List_File = Path(__file__).with_name("plays_list.json")


def load_bedwars_plays():
    if not Plays_List_File.exists():
        return []

    with open(Plays_List_File, "r", encoding="utf-8") as file:
        saved_data = json.load(file)

    plays = []

    for play_data in saved_data.get("plays", []):
        rules = []

        for rule_data in play_data.get("rules", []):
            rules.append(
                ScoreRule(
                    path=rule_data["path"],
                    comparison=rule_data["comparison"],
                    value=rule_data["value"],
                    score_change=rule_data["score_change"],
                    reasoning=rule_data.get("reasoning", ""),
                )
            )

        plays.append(
            BedwarsPlay(
                name=play_data["name"],
                base_score=play_data.get("base_score", 0),
                rules=rules,
            )
        )

    return plays


BedwarsPlays = load_bedwars_plays()
