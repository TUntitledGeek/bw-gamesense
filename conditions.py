from typing import Any


def grab_attribute_value_using_path(game_state: Any, path: str) -> Any:
    selected_object = game_state

    path_parts = path.split(".")

    for attribute_name in path_parts:
        if isinstance(selected_object, dict):
            selected_object = selected_object[attribute_name]
        else:
            selected_object = getattr(selected_object, attribute_name)

    return selected_object


def compare_values(actual_value: Any, comparison: str, expected_value: Any) -> bool:
    if comparison == "equal_to":
        return actual_value == expected_value

    if comparison == "not_equal_to":
        return actual_value != expected_value

    if comparison == "less_than":
        return actual_value < expected_value

    if comparison == "less_than_or_equal_to":
        return actual_value <= expected_value

    if comparison == "greater_than":
        return actual_value > expected_value

    if comparison == "greater_than_or_equal_to":
        return actual_value >= expected_value

    if comparison == "contains":
        return expected_value in actual_value

    if comparison == "is_inside":
        return actual_value in expected_value

    raise ValueError(f"Unknown comparison: {comparison}")


def rule_matches_state(game_state: Any, rule: Any) -> bool:
    actual_value = grab_attribute_value_using_path(
        game_state=game_state,
        path=rule.path,
    )

    return compare_values(
        actual_value=actual_value,
        comparison=rule.comparison,
        expected_value=rule.value,
    )


if __name__ == "__main__":
    from placeholdergamestate import make_placeholder_state

    game_state = make_placeholder_state()

    print("Path reader test:")
    print(grab_attribute_value_using_path(game_state, "active_user.blocks"))
    print(grab_attribute_value_using_path(game_state, "resources.iron"))
    print(grab_attribute_value_using_path(game_state, "enemy.enemies_visible"))
    print(
        grab_attribute_value_using_path(game_state, "target_enemy_team.team_bed_alive")
    )

    print("\nComparison test:")
    print(compare_values(48, "greater_than_or_equal_to", 32))
    print(compare_values(12, "less_than", 4))
    print(compare_values(True, "equal_to", True))
