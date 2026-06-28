import json
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path

try:
    from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
except ImportError:
    print("PySide6 is not installed.")
    print("Run this first:")
    print("python -m pip install PySide6")
    raise SystemExit(1)


PLAYS_LIST_FILE = Path(__file__).with_name("plays_list.json")

COMPARISON_OPTIONS = [
    "equal_to",
    "not_equal_to",
    "less_than",
    "less_than_or_equal_to",
    "greater_than",
    "greater_than_or_equal_to",
    "contains",
    "is_inside",
]

COMPARISON_OPTIONS_BY_TYPE = {
    "boolean": ["equal_to", "not_equal_to"],
    "number": [
        "equal_to",
        "not_equal_to",
        "less_than",
        "less_than_or_equal_to",
        "greater_than",
        "greater_than_or_equal_to",
    ],
    "text": ["equal_to", "not_equal_to", "contains", "is_inside"],
    "collection": ["contains", "is_inside"],
    "dictionary": ["contains"],
    "object": ["equal_to", "not_equal_to"],
    "unknown": COMPARISON_OPTIONS,
}

VALUE_OPTIONS_BY_TYPE = {
    "boolean": ["true", "false"],
}

PATH_NAME_REPLACEMENTS = {
    "active_user": "Your",
    "resources": "Resources",
    "enemy": "Enemy",
    "target_enemy_team": "Target",
    "team_bed_alive": "Bed Alive",
    "bed_alive": "Bed Alive",
    "players_alive": "Players Alive",
    "average_star_count": "Average Stars",
    "average_estimated_skill_level": "Estimated Skill",
    "near_team_island": "Near Your Island",
    "enemies_visible": "Enemies Visible",
    "has_tools": "Has Tools",
    "has_pickaxe": "Has Pickaxe",
    "has_axe": "Has Axe",
    "has_shears": "Has Shears",
    "first_rush_iron_cost": "First Rush Iron Cost",
    "game_phase": "Game Phase",
    "map_name": "Map",
    "map_rush_type": "Rush Type",
}

COMPARISON_TRANSLATIONS = {
    "equal_to": "=",
    "not_equal_to": "!=",
    "less_than": "<",
    "less_than_or_equal_to": "<=",
    "greater_than": ">",
    "greater_than_or_equal_to": ">=",
    "contains": "contains",
    "is_inside": "is in",
}

FALLBACK_PATH_TYPES = {
    "game_phase": "text",
    "map_name": "text",
    "map_rush_type": "text",
    "first_rush_iron_cost": "number",
    "active_user.bed_alive": "boolean",
    "active_user.health": "number",
    "active_user.blocks": "number",
    "active_user.has_tools": "boolean",
    "active_user.has_pickaxe": "boolean",
    "active_user.has_axe": "boolean",
    "active_user.has_shears": "boolean",
    "active_user.fireballs": "number",
    "active_user.golden_apples": "number",
    "active_user.armor_type": "text",
    "active_user.sword_type": "text",
    "resources.iron": "number",
    "resources.gold": "number",
    "resources.diamonds": "number",
    "resources.emeralds": "number",
    "enemy.near_team_island": "boolean",
    "enemy.enemies_visible": "number",
    "target_enemy_team.team_bed_alive": "boolean",
    "target_enemy_team.players_alive": "number",
    "target_enemy_team.average_star_count": "number",
    "target_enemy_team.average_estimated_skill_level": "number",
}


def load_plays_data():
    if not PLAYS_LIST_FILE.exists():
        return {"plays": []}

    try:
        with open(PLAYS_LIST_FILE, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)
    except json.JSONDecodeError:
        return {"plays": []}

    if not isinstance(loaded_data, dict):
        return {"plays": []}

    if "plays" not in loaded_data or not isinstance(loaded_data["plays"], list):
        loaded_data["plays"] = []

    for play in loaded_data["plays"]:
        if not isinstance(play, dict):
            continue

        play.setdefault("name", "unnamed_play")
        play.setdefault("base_score", 0)

        if "rules" not in play or not isinstance(play["rules"], list):
            play["rules"] = []

        for rule in play["rules"]:
            if not isinstance(rule, dict):
                continue

            rule.setdefault("path", "")
            rule.setdefault("comparison", "")
            rule.setdefault("value", "")
            rule.setdefault("score_change", "")
            rule.setdefault("reasoning", "")

    return loaded_data


def save_plays_data(plays_data):
    with open(PLAYS_LIST_FILE, "w", encoding="utf-8") as file:
        json.dump(plays_data, file, indent=2)


def parse_rule_value(value_text):
    value_text = str(value_text).strip()

    if value_text == "":
        return ""

    if value_text.lower() == "true":
        return True

    if value_text.lower() == "false":
        return False

    if value_text.lower() == "none":
        return None

    try:
        return json.loads(value_text)
    except json.JSONDecodeError:
        return value_text


def value_to_text(value):
    if isinstance(value, str):
        return value

    return json.dumps(value)


def get_value_type_name(value):
    if isinstance(value, bool):
        return "boolean"

    if isinstance(value, (int, float)):
        return "number"

    if isinstance(value, str):
        return "text"

    if isinstance(value, (list, tuple, set)):
        return "collection"

    if isinstance(value, dict):
        return "dictionary"

    if is_dataclass(value):
        return "object"

    return "unknown"


def humanize_path(path):
    if not path:
        return "Empty Path"

    readable_parts = []

    for path_part in path.split("."):
        if path_part in PATH_NAME_REPLACEMENTS:
            readable_parts.append(PATH_NAME_REPLACEMENTS[path_part])
        else:
            readable_parts.append(path_part.replace("_", " ").title())

    return " ".join(readable_parts)


def humanize_comparison(comparison):
    return COMPARISON_TRANSLATIONS.get(comparison, comparison)


def make_rule_english(rule):
    path = rule.get("path", "")
    comparison = rule.get("comparison", "")
    value = value_to_text(rule.get("value", ""))

    if not path and not comparison and value == "":
        return "Empty Rule"

    readable_path = humanize_path(path)
    readable_comparison = humanize_comparison(comparison)

    if comparison == "":
        readable_comparison = "?"

    if value == "":
        value = "?"

    return f"{readable_path} {readable_comparison} {value}"


def collect_paths_from_object(
    selected_object,
    current_path="",
    path_options=None,
    path_type_map=None,
    depth=0,
):
    if path_options is None:
        path_options = set()

    if path_type_map is None:
        path_type_map = {}

    if depth > 6:
        return path_options, path_type_map

    if selected_object is None:
        return path_options, path_type_map

    if is_dataclass(selected_object):
        for field_info in fields(selected_object):
            field_name = field_info.name

            if current_path:
                full_path = f"{current_path}.{field_name}"
            else:
                full_path = field_name

            try:
                field_value = getattr(selected_object, field_name)
            except Exception:
                continue

            path_options.add(full_path)
            path_type_map[full_path] = get_value_type_name(field_value)

            collect_paths_from_object(
                selected_object=field_value,
                current_path=full_path,
                path_options=path_options,
                path_type_map=path_type_map,
                depth=depth + 1,
            )

        for property_name, class_value in vars(type(selected_object)).items():
            if not isinstance(class_value, property):
                continue

            if current_path:
                full_path = f"{current_path}.{property_name}"
            else:
                full_path = property_name

            try:
                property_value = getattr(selected_object, property_name)
            except Exception:
                continue

            path_options.add(full_path)
            path_type_map[full_path] = get_value_type_name(property_value)

            collect_paths_from_object(
                selected_object=property_value,
                current_path=full_path,
                path_options=path_options,
                path_type_map=path_type_map,
                depth=depth + 1,
            )

        return path_options, path_type_map

    if isinstance(selected_object, dict):
        for key, value in selected_object.items():
            key_text = str(key)

            if current_path:
                full_path = f"{current_path}.{key_text}"
            else:
                full_path = key_text

            path_options.add(full_path)
            path_type_map[full_path] = get_value_type_name(value)

            collect_paths_from_object(
                selected_object=value,
                current_path=full_path,
                path_options=path_options,
                path_type_map=path_type_map,
                depth=depth + 1,
            )

        return path_options, path_type_map

    return path_options, path_type_map


def load_path_options_from_placeholder_state():
    try:
        from placeholdergamestate import make_placeholder_state

        placeholder_state = make_placeholder_state()

        path_options, path_type_map = collect_paths_from_object(
            selected_object=placeholder_state,
        )

        return sorted(path_options), path_type_map

    except Exception:
        fallback_paths = sorted(FALLBACK_PATH_TYPES.keys())
        return fallback_paths, FALLBACK_PATH_TYPES.copy()


class EditorBackend(QObject):
    playsChanged = Signal()
    pathsChanged = Signal()
    statusChanged = Signal()
    selectionChanged = Signal()

    def __init__(self):
        super().__init__()

        self.plays_data = load_plays_data()
        self.path_options, self.path_type_map = (
            load_path_options_from_placeholder_state()
        )

        self.selected_play_index = -1
        self.selected_rule_index = -1
        self._status = f"Editing {PLAYS_LIST_FILE.name}"

    def get_plays(self):
        return self.plays_data.get("plays", [])

    def get_path_options(self):
        return self.path_options

    def get_status(self):
        return self._status

    def get_selected_play_index(self):
        return self.selected_play_index

    def get_selected_rule_index(self):
        return self.selected_rule_index

    def get_selection_mode(self):
        if self.selected_rule_index >= 0:
            return "rule"

        if self.selected_play_index >= 0:
            return "play"

        return "none"

    def get_selected_play_name(self):
        play = self.get_selected_play()

        if play is None:
            return ""

        return str(play.get("name", ""))

    def get_selected_play_base_score(self):
        play = self.get_selected_play()

        if play is None:
            return ""

        return str(play.get("base_score", ""))

    def get_selected_rule_path(self):
        rule = self.get_selected_rule()

        if rule is None:
            return ""

        return str(rule.get("path", ""))

    def get_selected_rule_comparison(self):
        rule = self.get_selected_rule()

        if rule is None:
            return ""

        return str(rule.get("comparison", ""))

    def get_selected_rule_value(self):
        rule = self.get_selected_rule()

        if rule is None:
            return ""

        return value_to_text(rule.get("value", ""))

    def get_selected_rule_score_change(self):
        rule = self.get_selected_rule()

        if rule is None:
            return ""

        return str(rule.get("score_change", ""))

    def get_selected_rule_reasoning(self):
        rule = self.get_selected_rule()

        if rule is None:
            return ""

        return str(rule.get("reasoning", ""))

    def get_selected_rule_title(self):
        rule = self.get_selected_rule()

        if rule is None:
            return "No Rule Selected"

        return make_rule_english(rule)

    def get_selected_path_type(self):
        path = self.get_selected_rule_path()
        return self.get_path_type_name(path)

    def get_selected_comparison_options(self):
        return self.get_comparison_options_for_path(self.get_selected_rule_path())

    def get_selected_value_options(self):
        return self.get_value_options_for_path(self.get_selected_rule_path())

    def get_selected_value_index(self):
        value_text = self.get_selected_rule_value().lower()
        options = self.get_selected_value_options()

        try:
            return options.index(value_text)
        except ValueError:
            return -1

    plays = Property("QVariantList", get_plays, notify=playsChanged)
    pathOptions = Property("QStringList", get_path_options, notify=pathsChanged)
    status = Property(str, get_status, notify=statusChanged)

    selectedPlayIndex = Property(int, get_selected_play_index, notify=selectionChanged)
    selectedRuleIndex = Property(int, get_selected_rule_index, notify=selectionChanged)
    selectionMode = Property(str, get_selection_mode, notify=selectionChanged)

    selectedPlayName = Property(str, get_selected_play_name, notify=selectionChanged)
    selectedPlayBaseScore = Property(
        str,
        get_selected_play_base_score,
        notify=selectionChanged,
    )

    selectedRulePath = Property(str, get_selected_rule_path, notify=selectionChanged)
    selectedRuleComparison = Property(
        str,
        get_selected_rule_comparison,
        notify=selectionChanged,
    )
    selectedRuleValue = Property(str, get_selected_rule_value, notify=selectionChanged)
    selectedRuleScoreChange = Property(
        str,
        get_selected_rule_score_change,
        notify=selectionChanged,
    )
    selectedRuleReasoning = Property(
        str,
        get_selected_rule_reasoning,
        notify=selectionChanged,
    )
    selectedRuleTitle = Property(str, get_selected_rule_title, notify=selectionChanged)
    selectedPathType = Property(str, get_selected_path_type, notify=selectionChanged)
    selectedComparisonOptions = Property(
        "QStringList",
        get_selected_comparison_options,
        notify=selectionChanged,
    )
    selectedValueOptions = Property(
        "QStringList",
        get_selected_value_options,
        notify=selectionChanged,
    )
    selectedValueIndex = Property(
        int, get_selected_value_index, notify=selectionChanged
    )

    def set_status(self, message):
        self._status = message
        self.statusChanged.emit()

    def save_and_refresh(self, message):
        save_plays_data(self.plays_data)
        self.set_status(message)
        self.playsChanged.emit()
        self.selectionChanged.emit()

    def valid_play_index(self, play_index):
        return 0 <= play_index < len(self.plays_data.get("plays", []))

    def valid_rule_index(self, play_index, rule_index):
        if not self.valid_play_index(play_index):
            return False

        rules = self.plays_data["plays"][play_index].get("rules", [])
        return 0 <= rule_index < len(rules)

    def get_selected_play(self):
        if not self.valid_play_index(self.selected_play_index):
            return None

        return self.plays_data["plays"][self.selected_play_index]

    def get_selected_rule(self):
        if not self.valid_rule_index(
            self.selected_play_index, self.selected_rule_index
        ):
            return None

        return self.plays_data["plays"][self.selected_play_index]["rules"][
            self.selected_rule_index
        ]

    def get_path_type_name(self, path):
        if not path:
            return "unknown"

        return self.path_type_map.get(path, "unknown")

    def get_comparison_options_for_path(self, path):
        path_type = self.get_path_type_name(path)
        return COMPARISON_OPTIONS_BY_TYPE.get(path_type, COMPARISON_OPTIONS)

    def get_value_options_for_path(self, path):
        path_type = self.get_path_type_name(path)
        return VALUE_OPTIONS_BY_TYPE.get(path_type, [])

    def clean_rule_if_needed(self, play_index, rule_index):
        if not self.valid_rule_index(play_index, rule_index):
            return

        rule = self.plays_data["plays"][play_index]["rules"][rule_index]

        path = rule.get("path", "")
        path_type = self.get_path_type_name(path)

        allowed_comparisons = self.get_comparison_options_for_path(path)
        current_comparison = rule.get("comparison", "")

        if current_comparison and current_comparison not in allowed_comparisons:
            rule["comparison"] = ""

        if path_type == "boolean":
            current_value = value_to_text(rule.get("value", "")).lower()

            if current_value not in ["", "true", "false"]:
                rule["value"] = ""

    @Slot(int)
    def selectPlay(self, play_index):
        if not self.valid_play_index(play_index):
            return

        self.selected_play_index = play_index
        self.selected_rule_index = -1
        self.selectionChanged.emit()

    @Slot(int, int)
    def selectRule(self, play_index, rule_index):
        if not self.valid_rule_index(play_index, rule_index):
            return

        self.selected_play_index = play_index
        self.selected_rule_index = rule_index
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self):
        self.selected_play_index = -1
        self.selected_rule_index = -1
        self.selectionChanged.emit()

    @Slot(result=int)
    def addPlay(self):
        new_play_number = len(self.plays_data["plays"]) + 1

        new_play = {
            "name": f"new_play_{new_play_number}",
            "base_score": 0,
            "rules": [],
        }

        self.plays_data["plays"].append(new_play)

        self.selected_play_index = len(self.plays_data["plays"]) - 1
        self.selected_rule_index = -1

        self.save_and_refresh("Added new play.")
        return self.selected_play_index

    @Slot(int, result=int)
    def addRule(self, play_index):
        if not self.valid_play_index(play_index):
            self.set_status("Select a valid play before adding a rule.")
            return -1

        new_rule = {
            "path": "",
            "comparison": "",
            "value": "",
            "score_change": "",
            "reasoning": "",
        }

        self.plays_data["plays"][play_index]["rules"].append(new_rule)

        self.selected_play_index = play_index
        self.selected_rule_index = (
            len(self.plays_data["plays"][play_index]["rules"]) - 1
        )

        self.save_and_refresh("Added empty rule.")
        return self.selected_rule_index

    @Slot()
    def addRuleToSelectedPlay(self):
        if not self.valid_play_index(self.selected_play_index):
            self.set_status("Select a play before adding a rule.")
            return

        self.addRule(self.selected_play_index)

    @Slot()
    def deleteSelected(self):
        if self.selected_rule_index >= 0:
            self.deleteRule(self.selected_play_index, self.selected_rule_index)
            return

        if self.selected_play_index >= 0:
            self.deletePlay(self.selected_play_index)

    @Slot(int)
    def deletePlay(self, play_index):
        if not self.valid_play_index(play_index):
            return

        play_name = self.plays_data["plays"][play_index].get("name", "unnamed")
        del self.plays_data["plays"][play_index]

        if not self.plays_data["plays"]:
            self.selected_play_index = -1
            self.selected_rule_index = -1
        else:
            self.selected_play_index = min(
                play_index, len(self.plays_data["plays"]) - 1
            )
            self.selected_rule_index = -1

        self.save_and_refresh(f"Deleted play: {play_name}")

    @Slot(int, int)
    def deleteRule(self, play_index, rule_index):
        if not self.valid_rule_index(play_index, rule_index):
            return

        del self.plays_data["plays"][play_index]["rules"][rule_index]

        self.selected_play_index = play_index
        self.selected_rule_index = -1

        self.save_and_refresh("Deleted rule.")

    @Slot(str, str)
    def updateSelectedPlayField(self, field_name, new_value):
        self.updatePlayField(self.selected_play_index, field_name, new_value)

    @Slot(str, str)
    def updateSelectedRuleField(self, field_name, new_value):
        self.updateRuleField(
            self.selected_play_index,
            self.selected_rule_index,
            field_name,
            new_value,
        )

    @Slot(int, str, str)
    def updatePlayField(self, play_index, field_name, new_value):
        if not self.valid_play_index(play_index):
            return

        play = self.plays_data["plays"][play_index]
        new_value = str(new_value).strip()

        if field_name == "name":
            play["name"] = new_value

        elif field_name == "base_score":
            if new_value in ["", "-"]:
                play["base_score"] = ""
            else:
                try:
                    play["base_score"] = int(new_value)
                except ValueError:
                    self.set_status("Base score must be a number.")
                    return

        self.save_and_refresh("Updated play.")

    @Slot(int, int, str, str)
    def updateRuleField(self, play_index, rule_index, field_name, new_value):
        if not self.valid_rule_index(play_index, rule_index):
            return

        rule = self.plays_data["plays"][play_index]["rules"][rule_index]
        new_value = str(new_value).strip()

        if field_name == "path":
            rule["path"] = new_value
            self.clean_rule_if_needed(play_index, rule_index)

        elif field_name == "comparison":
            allowed_comparisons = self.get_comparison_options_for_path(
                rule.get("path", "")
            )

            if new_value and new_value not in allowed_comparisons:
                self.set_status("That comparison does not match this path type.")
                return

            rule["comparison"] = new_value

        elif field_name == "value":
            rule["value"] = parse_rule_value(new_value)
            self.clean_rule_if_needed(play_index, rule_index)

        elif field_name == "score_change":
            if new_value in ["", "-"]:
                rule["score_change"] = ""
            else:
                try:
                    rule["score_change"] = int(new_value)
                except ValueError:
                    self.set_status("Score change must be a number.")
                    return

        elif field_name == "reasoning":
            rule["reasoning"] = new_value

        self.save_and_refresh("Updated rule.")

    @Slot()
    def saveNow(self):
        save_plays_data(self.plays_data)
        self.set_status(f"Saved to {PLAYS_LIST_FILE.name}")
        self.playsChanged.emit()
        self.selectionChanged.emit()

    @Slot()
    def reloadPaths(self):
        self.path_options, self.path_type_map = (
            load_path_options_from_placeholder_state()
        )
        self.pathsChanged.emit()
        self.playsChanged.emit()
        self.selectionChanged.emit()
        self.set_status(f"Reloaded {len(self.path_options)} path options.")

    @Slot(str, result=int)
    def pathIndex(self, path):
        try:
            return self.path_options.index(path)
        except ValueError:
            return -1

    @Slot(str, str, result=int)
    def comparisonIndex(self, path, comparison):
        options = self.get_comparison_options_for_path(path)

        try:
            return options.index(comparison)
        except ValueError:
            return -1

    @Slot(int, result=str)
    def playTitle(self, play_index):
        if not self.valid_play_index(play_index):
            return "Play"

        play = self.plays_data["plays"][play_index]
        play_name = str(play.get("name", "")).strip()

        if not play_name:
            play_name = "unnamed"

        return f"Play {play_index + 1} ({play_name})"

    @Slot(int, int, result=str)
    def ruleTitle(self, play_index, rule_index):
        if not self.valid_rule_index(play_index, rule_index):
            return "Rule"

        rule = self.plays_data["plays"][play_index]["rules"][rule_index]
        return make_rule_english(rule)

    @Slot(int, int, result=str)
    def ruleScoreText(self, play_index, rule_index):
        if not self.valid_rule_index(play_index, rule_index):
            return ""

        rule = self.plays_data["plays"][play_index]["rules"][rule_index]
        score_change = rule.get("score_change", "")

        if score_change == "":
            return "score ?"

        try:
            score_number = int(score_change)
        except (TypeError, ValueError):
            return "score ?"

        return f"{score_number:+}"

    @Slot(int, int, result=str)
    def rulePathType(self, play_index, rule_index):
        if not self.valid_rule_index(play_index, rule_index):
            return "unknown"

        rule = self.plays_data["plays"][play_index]["rules"][rule_index]
        return self.get_path_type_name(rule.get("path", ""))


QML_SOURCE = r"""
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

ApplicationWindow {
    id: appWindow

    width: 1240
    height: 780
    minimumWidth: 1040
    minimumHeight: 680

    visible: true
    title: "BWGS Play Editor"

    color: "#f4efe6"

    Material.theme: Material.Light
    Material.accent: "#b7791f"
    Material.primary: "#b7791f"

    readonly property color bgColor: "#f4efe6"
    readonly property color panelColor: "#fffaf2"
    readonly property color panelAltColor: "#fdf6ea"
    readonly property color cardColor: "#ffffff"
    readonly property color cardHover: "#f6ecd8"
    readonly property color ruleRowColor: "#faf3e7"
    readonly property color selectedColor: "#e7f5eb"
    readonly property color selectedRuleColor: "#d9f2e1"

    readonly property color borderColor: "#cdbfaa"
    readonly property color strongBorderColor: "#b9a98f"
    readonly property color softBorderColor: "#e0d4c2"

    readonly property color textColor: "#231f1a"
    readonly property color mutedText: "#74695b"

    readonly property color buttonAccentColor: "#b7791f"
    readonly property color buttonAccentHover: "#9a6419"
    readonly property color greenActionColor: "#168a43"
    readonly property color greenActionHover: "#e5f6eb"

    readonly property color dangerColor: "#c2410c"
    readonly property color warningColor: "#a16207"

    Rectangle {
        anchors.fill: parent
        color: bgColor
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                width: 40
                height: 40
                radius: 9
                color: buttonAccentColor

                Text {
                    anchors.centerIn: parent
                    text: "BW"
                    color: "white"
                    font.pixelSize: 14
                    font.bold: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Text {
                    text: "BWGS Play Editor"
                    color: textColor
                    font.pixelSize: 23
                    font.bold: true
                }

                Text {
                    text: "Compact rule editor for Bedwars GameSense scoring"
                    color: mutedText
                    font.pixelSize: 12
                }
            }

            Rectangle {
                radius: 8
                color: panelColor
                border.color: borderColor
                border.width: 1
                height: 30
                width: Math.min(390, statusText.implicitWidth + 22)

                Text {
                    id: statusText
                    anchors.centerIn: parent
                    text: backend.status
                    color: mutedText
                    font.pixelSize: 11
                    elide: Text.ElideRight
                    width: parent.width - 18
                }
            }

            Button {
                text: "Reload Paths"
                flat: true
                Material.foreground: mutedText
                onClicked: backend.reloadPaths()
            }

            Button {
                text: "Save"
                highlighted: true
                Material.accent: buttonAccentColor
                onClicked: backend.saveNow()
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            handle: Rectangle {
                implicitWidth: 8
                color: "transparent"

                Rectangle {
                    anchors.centerIn: parent
                    width: 1
                    height: parent.height
                    color: strongBorderColor
                }
            }

            Rectangle {
                id: listPanel

                SplitView.preferredWidth: 790
                SplitView.minimumWidth: 560
                SplitView.fillWidth: true

                radius: 10
                color: panelColor
                border.color: strongBorderColor
                border.width: 1
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 9

                    RowLayout {
                        Layout.fillWidth: true

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0

                            Text {
                                text: "Existing Plays"
                                color: textColor
                                font.pixelSize: 18
                                font.bold: true
                            }

                            Text {
                                text: "Select a play or rule, then edit it in the right inspector."
                                color: mutedText
                                font.pixelSize: 11
                            }
                        }

                        Button {
                            text: "+ Add Play"
                            highlighted: true
                            Material.accent: buttonAccentColor
                            onClicked: backend.addPlay()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: softBorderColor
                    }

                    ScrollView {
                        id: playsScroll

                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        clip: true
                        ScrollBar.vertical.policy: ScrollBar.AsNeeded
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        Column {
                            id: playsColumn

                            width: playsScroll.availableWidth
                            spacing: 8

                            Repeater {
                                model: backend.plays

                                delegate: PlayNode {
                                    width: playsColumn.width
                                    playIndex: index
                                    playData: modelData
                                }
                            }

                            Rectangle {
                                width: playsColumn.width
                                height: 46
                                radius: 8
                                color: addPlayMouse.containsMouse ? greenActionHover : panelAltColor
                                border.color: addPlayMouse.containsMouse ? greenActionColor : softBorderColor
                                border.width: 1

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 7

                                    Text {
                                        text: "+"
                                        color: greenActionColor
                                        font.pixelSize: 20
                                        font.bold: true
                                        anchors.verticalCenter: parent.verticalCenter
                                    }

                                    Text {
                                        text: "Add Play"
                                        color: greenActionColor
                                        font.pixelSize: 13
                                        font.bold: true
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }

                                MouseArea {
                                    id: addPlayMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: backend.addPlay()
                                }
                            }

                            Item {
                                width: 1
                                height: 6
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: inspectorPanel

                SplitView.preferredWidth: 390
                SplitView.minimumWidth: 350
                SplitView.maximumWidth: 500

                radius: 10
                color: panelAltColor
                border.color: strongBorderColor
                border.width: 1
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0

                            Text {
                                text: "Inspector"
                                color: textColor
                                font.pixelSize: 18
                                font.bold: true
                            }

                            Text {
                                text: backend.selectionMode === "rule"
                                    ? "Editing selected rule"
                                    : backend.selectionMode === "play"
                                        ? "Editing selected play"
                                        : "Nothing selected"
                                color: mutedText
                                font.pixelSize: 11
                            }
                        }

                        Button {
                            visible: backend.selectionMode !== "none"
                            text: "Delete"
                            flat: true
                            Material.foreground: dangerColor
                            onClicked: backend.deleteSelected()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: borderColor
                    }

                    Loader {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        sourceComponent: backend.selectionMode === "rule"
                            ? ruleInspector
                            : backend.selectionMode === "play"
                                ? playInspector
                                : emptyInspector
                    }
                }
            }
        }
    }

    component InspectorLabel: Text {
        color: mutedText
        font.pixelSize: 10
        font.bold: true
    }

    component InspectorField: ColumnLayout {
        property string labelText: ""

        spacing: 4

        InspectorLabel {
            text: labelText
        }
    }

    component InfoPill: Rectangle {
        property string pillText: ""
        property color pillColor: "#fffaf2"
        property color pillTextColor: mutedText

        radius: 7
        color: pillColor
        border.color: borderColor
        border.width: 1
        height: 24
        width: pillLabel.implicitWidth + 18

        Text {
            id: pillLabel
            anchors.centerIn: parent
            text: pillText
            color: pillTextColor
            font.pixelSize: 10
            font.bold: true
        }
    }

    component EmptyCard: Rectangle {
        Layout.fillWidth: true
        radius: 9
        color: cardColor
        border.color: borderColor
        border.width: 1
    }

    component PlayNode: Rectangle {
        id: playNode

        property int playIndex: -1
        property var playData: ({})
        property bool expanded: true
        property bool selected: backend.selectionMode === "play"
            && backend.selectedPlayIndex === playIndex

        radius: 9
        color: selected ? selectedColor : playMouse.containsMouse ? cardHover : cardColor
        border.color: selected ? greenActionColor : borderColor
        border.width: selected ? 2 : 1

        height: nodeContent.implicitHeight + 18

        MouseArea {
            id: playMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: backend.selectPlay(playNode.playIndex)
        }

        ColumnLayout {
            id: nodeContent

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 9
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                spacing: 7

                Button {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 28
                    text: playNode.expanded ? "▾" : "▸"
                    flat: true
                    Material.foreground: mutedText
                    onClicked: playNode.expanded = !playNode.expanded
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0

                    Text {
                        text: backend.playTitle(playNode.playIndex)
                        color: textColor
                        font.pixelSize: 14
                        font.bold: true
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }

                    Text {
                        text: (playData.rules ? playData.rules.length : 0) + " rules"
                        color: mutedText
                        font.pixelSize: 10
                    }
                }

                InfoPill {
                    pillText: "base " + (playData.base_score === undefined ? 0 : playData.base_score)
                    pillColor: "#fff7e8"
                }

                Button {
                    text: "+ Rule"
                    flat: true
                    Material.foreground: buttonAccentColor
                    onClicked: backend.addRule(playNode.playIndex)
                }
            }

            Column {
                visible: playNode.expanded
                Layout.fillWidth: true
                spacing: 5

                Repeater {
                    model: playData.rules ? playData.rules.length : 0

                    delegate: RuleNode {
                        width: parent.width
                        playIndex: playNode.playIndex
                        ruleIndex: index
                        ruleData: playData.rules[index]
                    }
                }

                Rectangle {
                    width: parent.width
                    height: 34
                    radius: 8
                    color: addRuleMouse.containsMouse ? greenActionHover : panelAltColor
                    border.color: addRuleMouse.containsMouse ? greenActionColor : softBorderColor
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "+ Add Rule"
                        color: greenActionColor
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        id: addRuleMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.addRule(playNode.playIndex)
                    }
                }
            }
        }
    }

    component RuleNode: Rectangle {
        id: ruleNode

        property int playIndex: -1
        property int ruleIndex: -1
        property var ruleData: ({})
        property bool selected: backend.selectionMode === "rule"
            && backend.selectedPlayIndex === playIndex
            && backend.selectedRuleIndex === ruleIndex

        radius: 8
        color: selected ? selectedRuleColor : ruleMouse.containsMouse ? "#f6ecd8" : ruleRowColor
        border.color: selected ? greenActionColor : softBorderColor
        border.width: selected ? 2 : 1

        height: 44

        MouseArea {
            id: ruleMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: backend.selectRule(ruleNode.playIndex, ruleNode.ruleIndex)
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 8
            spacing: 8

            Rectangle {
                width: 24
                height: 24
                radius: 6
                color: selected ? greenActionColor : "#fffaf2"
                border.color: selected ? greenActionColor : borderColor
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: ruleNode.ruleIndex + 1
                    color: selected ? "white" : mutedText
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                Text {
                    text: backend.ruleTitle(ruleNode.playIndex, ruleNode.ruleIndex)
                    color: textColor
                    font.pixelSize: 12
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }

                Text {
                    text: ruleData.reasoning || "No reasoning yet"
                    color: mutedText
                    font.pixelSize: 10
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }

            InfoPill {
                pillText: backend.rulePathType(ruleNode.playIndex, ruleNode.ruleIndex)
                pillColor: "#fffaf2"
            }

            InfoPill {
                pillText: backend.ruleScoreText(ruleNode.playIndex, ruleNode.ruleIndex)
                pillColor: "#fff7e8"
                pillTextColor: warningColor
            }
        }
    }

    Component {
        id: emptyInspector

        ColumnLayout {
            spacing: 10

            EmptyCard {
                implicitHeight: 165

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Text {
                        text: "Select something to edit"
                        color: textColor
                        font.pixelSize: 16
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "Choose a play or rule from the left panel. The compact editor will appear here."
                        color: mutedText
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }

                    Button {
                        text: "+ Add Play"
                        highlighted: true
                        Material.accent: buttonAccentColor
                        onClicked: backend.addPlay()
                    }
                }
            }
        }
    }

    Component {
        id: playInspector

        ColumnLayout {
            spacing: 10

            EmptyCard {
                implicitHeight: playInspectorContent.implicitHeight + 24

                ColumnLayout {
                    id: playInspectorContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 10

                    Text {
                        text: "Selected Play"
                        color: textColor
                        font.pixelSize: 16
                        font.bold: true
                    }

                    InspectorField {
                        labelText: "NAME"
                        Layout.fillWidth: true

                        TextField {
                            Layout.fillWidth: true
                            text: backend.selectedPlayName
                            placeholderText: "first_rush"
                            selectByMouse: true

                            onEditingFinished: {
                                backend.updateSelectedPlayField("name", text)
                            }
                        }
                    }

                    InspectorField {
                        labelText: "BASE SCORE"
                        Layout.fillWidth: true

                        TextField {
                            Layout.fillWidth: true
                            text: backend.selectedPlayBaseScore
                            placeholderText: "0"
                            selectByMouse: true

                            onEditingFinished: {
                                backend.updateSelectedPlayField("base_score", text)
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Button {
                            text: "+ Add Rule"
                            highlighted: true
                            Material.accent: buttonAccentColor
                            onClicked: backend.addRuleToSelectedPlay()
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        Button {
                            text: "Delete Play"
                            flat: true
                            Material.foreground: dangerColor
                            onClicked: backend.deleteSelected()
                        }
                    }
                }
            }
        }
    }

    Component {
        id: ruleInspector

        ColumnLayout {
            spacing: 10

            EmptyCard {
                implicitHeight: ruleInspectorContent.implicitHeight + 24

                ColumnLayout {
                    id: ruleInspectorContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 10

                    Text {
                        text: "Selected Rule"
                        color: textColor
                        font.pixelSize: 16
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: backend.selectedRuleTitle
                        color: mutedText
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        InfoPill {
                            pillText: "type: " + backend.selectedPathType
                            pillTextColor: greenActionColor
                            pillColor: "#f0f8ef"
                        }

                        InfoPill {
                            pillText: backend.selectedRuleScoreChange === ""
                                ? "score ?"
                                : "score " + backend.selectedRuleScoreChange
                            pillTextColor: warningColor
                            pillColor: "#fff7e8"
                        }

                        Item {
                            Layout.fillWidth: true
                        }
                    }

                    InspectorField {
                        labelText: "PATH"
                        Layout.fillWidth: true

                        ComboBox {
                            Layout.fillWidth: true
                            editable: true
                            model: backend.pathOptions
                            currentIndex: backend.pathIndex(backend.selectedRulePath)

                            onActivated: {
                                backend.updateSelectedRuleField("path", currentText)
                            }

                            onAccepted: {
                                backend.updateSelectedRuleField("path", editText)
                            }
                        }
                    }

                    InspectorField {
                        labelText: "COMPARISON"
                        Layout.fillWidth: true

                        ComboBox {
                            Layout.fillWidth: true
                            model: backend.selectedComparisonOptions
                            currentIndex: backend.comparisonIndex(
                                backend.selectedRulePath,
                                backend.selectedRuleComparison
                            )

                            onActivated: {
                                backend.updateSelectedRuleField("comparison", currentText)
                            }
                        }
                    }

                    InspectorField {
                        labelText: "VALUE"
                        Layout.fillWidth: true

                        Loader {
                            Layout.fillWidth: true
                            sourceComponent: backend.selectedPathType === "boolean"
                                ? booleanValueEditor
                                : textValueEditor
                        }

                        Component {
                            id: booleanValueEditor

                            ComboBox {
                                width: parent ? parent.width : 320
                                model: backend.selectedValueOptions
                                currentIndex: backend.selectedValueIndex

                                onActivated: {
                                    backend.updateSelectedRuleField("value", currentText)
                                }
                            }
                        }

                        Component {
                            id: textValueEditor

                            TextField {
                                width: parent ? parent.width : 320
                                text: backend.selectedRuleValue
                                placeholderText: "32, early_game, leather, etc."
                                selectByMouse: true

                                onEditingFinished: {
                                    backend.updateSelectedRuleField("value", text)
                                }
                            }
                        }
                    }

                    InspectorField {
                        labelText: "SCORE CHANGE"
                        Layout.fillWidth: true

                        TextField {
                            Layout.fillWidth: true
                            text: backend.selectedRuleScoreChange
                            placeholderText: "25"
                            selectByMouse: true

                            onEditingFinished: {
                                backend.updateSelectedRuleField("score_change", text)
                            }
                        }
                    }

                    InspectorField {
                        labelText: "REASONING"
                        Layout.fillWidth: true

                        TextArea {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 76
                            text: backend.selectedRuleReasoning
                            placeholderText: "Enough blocks for a basic rush."
                            wrapMode: TextArea.Wrap
                            selectByMouse: true

                            onEditingFinished: {
                                backend.updateSelectedRuleField("reasoning", text)
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true

                        Button {
                            text: "Delete Rule"
                            flat: true
                            Material.foreground: dangerColor
                            onClicked: backend.deleteSelected()
                        }

                        Item {
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
"""


def main():
    try:
        QQuickStyle.setStyle("Material")
    except Exception:
        pass

    app = QGuiApplication(sys.argv)

    backend = EditorBackend()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.loadData(QML_SOURCE.encode("utf-8"), QUrl("qrc:/main.qml"))

    if not engine.rootObjects():
        print("Failed to load the QML interface.")
        raise SystemExit(1)

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
