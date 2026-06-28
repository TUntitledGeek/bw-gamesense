import json
import tkinter as tk
from dataclasses import fields, is_dataclass
from pathlib import Path
from tkinter import messagebox, ttk

try:
    import ttkbootstrap as ttkbootstrap_theme

    USING_TTKBOOTSTRAP = True
except ImportError:
    ttkbootstrap_theme = None
    USING_TTKBOOTSTRAP = False


APP_THEME = "flatly"
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

    with open(PLAYS_LIST_FILE, "r", encoding="utf-8") as file:
        loaded_data = json.load(file)

    if "plays" not in loaded_data:
        loaded_data["plays"] = []

    return loaded_data


def save_plays_data(plays_data):
    with open(PLAYS_LIST_FILE, "w", encoding="utf-8") as file:
        json.dump(plays_data, file, indent=2)


def parse_rule_value(value_text):
    value_text = value_text.strip()

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


class BWGSActionEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("BWGS Play Editor")
        self.root.geometry("1280x780")
        self.root.minsize(1000, 650)

        self.plays_data = load_plays_data()
        self.path_options, self.path_type_map = (
            load_path_options_from_placeholder_state()
        )

        self.tree_item_info = {}
        self.play_tree_items = {}
        self.play_field_items = {}
        self.rule_tree_items = {}
        self.rule_field_items = {}

        self.selected_play_index = None
        self.selected_rule_index = None
        self.loading_form = False
        self.active_floating_editor = None

        self.play_name_var = tk.StringVar()
        self.play_base_score_var = tk.StringVar()

        self.rule_path_var = tk.StringVar()
        self.rule_comparison_var = tk.StringVar()
        self.rule_value_var = tk.StringVar()
        self.rule_score_change_var = tk.StringVar()
        self.rule_reasoning_var = tk.StringVar()

        self.setup_style()
        self.build_layout()
        self.connect_form_events()
        self.refresh_tree()

    def setup_style(self):
        style = ttk.Style()

        if not USING_TTKBOOTSTRAP:
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        style.configure("Treeview", rowheight=30, font=("TkDefaultFont", 10))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        style.configure("Title.TLabel", font=("TkDefaultFont", 17, "bold"))
        style.configure("Subtitle.TLabel", foreground="#6c757d")
        style.configure("Hint.TLabel", foreground="#6c757d")

    def build_layout(self):
        main_frame = ttk.Frame(self.root, padding=14)
        main_frame.pack(fill="both", expand=True)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        top_bar = ttk.Frame(main_frame)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        title_area = ttk.Frame(top_bar)
        title_area.pack(side="left")

        ttk.Label(title_area, text="BWGS Play Editor", style="Title.TLabel").pack(
            anchor="w"
        )

        ttk.Label(
            title_area,
            text="Edit Bedwars plays, score rules, paths, comparisons, and reasoning.",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        ttk.Button(top_bar, text="Save", command=self.save_now).pack(
            side="right",
            padx=(8, 0),
        )

        ttk.Button(top_bar, text="Reload Paths", command=self.reload_path_options).pack(
            side="right",
            padx=(8, 0),
        )

        ttk.Button(
            top_bar,
            text="Delete Selected",
            command=self.delete_selected_item,
        ).pack(side="right", padx=(8, 0))

        main_pane = ttk.PanedWindow(main_frame, orient="horizontal")
        main_pane.grid(row=1, column=0, sticky="nsew")

        tree_card = ttk.Frame(main_pane, padding=10)
        editor_card = ttk.Frame(main_pane, padding=10)

        main_pane.add(tree_card, weight=3)
        main_pane.add(editor_card, weight=1)

        self.build_tree_area(tree_card)
        self.build_side_editor(editor_card)

        self.status_var = tk.StringVar(value=f"Editing {PLAYS_LIST_FILE.name}")
        ttk.Label(main_frame, textvariable=self.status_var, style="Hint.TLabel").grid(
            row=2,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

    def build_tree_area(self, tree_frame):
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=1)

        section_header = ttk.Frame(tree_frame)
        section_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(
            section_header,
            text="Existing Plays",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(side="left")

        ttk.Label(
            section_header,
            text="Double-click values to edit inline",
            style="Hint.TLabel",
        ).pack(side="right")

        self.plays_tree = ttk.Treeview(
            tree_frame,
            columns=("field", "value"),
            show="tree headings",
            selectmode="browse",
        )

        self.plays_tree.heading("#0", text="Play / Rule")
        self.plays_tree.heading("field", text="Field")
        self.plays_tree.heading("value", text="Value")

        self.plays_tree.column("#0", width=390, minwidth=270)
        self.plays_tree.column("field", width=145, minwidth=110)
        self.plays_tree.column("value", width=470, minwidth=250)

        self.plays_tree.tag_configure("play", background="#eaf2ff")
        self.plays_tree.tag_configure("rule", background="#f8f9fa")
        self.plays_tree.tag_configure("add_button", foreground="#198754")
        self.plays_tree.tag_configure("field", foreground="#495057")

        y_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.plays_tree.yview,
        )

        x_scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="horizontal",
            command=self.plays_tree.xview,
        )

        self.plays_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )

        self.plays_tree.grid(row=1, column=0, sticky="nsew")
        y_scrollbar.grid(row=1, column=1, sticky="ns")
        x_scrollbar.grid(row=2, column=0, sticky="ew")

        self.plays_tree.bind("<<TreeviewSelect>>", self.on_tree_selection_changed)
        self.plays_tree.bind("<Double-1>", self.on_tree_double_click)
        self.plays_tree.bind("<Delete>", self.delete_selected_item)

        ttk.Label(
            tree_frame,
            text="Enter saves text edits. Escape cancels. Dropdown edits save after choosing an option.",
            style="Hint.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    def build_side_editor(self, editor_frame):
        editor_frame.columnconfigure(0, weight=1)

        ttk.Label(
            editor_frame,
            text="Inspector",
            font=("TkDefaultFont", 12, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        play_outer_box = ttk.LabelFrame(editor_frame, text="Selected Play")
        play_outer_box.grid(row=1, column=0, sticky="ew")

        play_box = ttk.Frame(play_outer_box, padding=10)
        play_box.pack(fill="x", expand=True)

        play_box.columnconfigure(1, weight=1)

        ttk.Label(play_box, text="Name").grid(row=0, column=0, sticky="w")
        self.play_name_entry = ttk.Entry(play_box, textvariable=self.play_name_var)
        self.play_name_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(play_box, text="Base").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.play_base_score_entry = ttk.Entry(
            play_box,
            textvariable=self.play_base_score_var,
            width=10,
        )
        self.play_base_score_entry.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(8, 0),
            pady=(8, 0),
        )

        ttk.Button(
            play_box,
            text="＋ Add Rule",
            command=self.add_rule_to_selected_play,
        ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(12, 0))

        rule_outer_box = ttk.LabelFrame(editor_frame, text="Rule Contents")
        rule_outer_box.grid(row=2, column=0, sticky="ew", pady=(12, 0))

        rule_box = ttk.Frame(rule_outer_box, padding=10)
        rule_box.pack(fill="x", expand=True)

        rule_box.columnconfigure(0, weight=1)

        ttk.Label(rule_box, text="Path").grid(row=0, column=0, sticky="w")
        self.rule_path_combo = ttk.Combobox(
            rule_box,
            textvariable=self.rule_path_var,
            values=self.path_options,
        )
        self.rule_path_combo.grid(row=1, column=0, sticky="ew")

        ttk.Label(rule_box, text="Comparison").grid(
            row=2,
            column=0,
            sticky="w",
            pady=(8, 0),
        )
        self.rule_comparison_combo = ttk.Combobox(
            rule_box,
            textvariable=self.rule_comparison_var,
            values=COMPARISON_OPTIONS,
            state="readonly",
        )
        self.rule_comparison_combo.grid(row=3, column=0, sticky="ew")

        ttk.Label(rule_box, text="Value").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.rule_value_combo = ttk.Combobox(
            rule_box,
            textvariable=self.rule_value_var,
            values=[],
        )
        self.rule_value_combo.grid(row=5, column=0, sticky="ew")

        ttk.Label(rule_box, text="Score change").grid(
            row=6,
            column=0,
            sticky="w",
            pady=(8, 0),
        )
        self.rule_score_entry = ttk.Entry(
            rule_box,
            textvariable=self.rule_score_change_var,
        )
        self.rule_score_entry.grid(row=7, column=0, sticky="ew")

        ttk.Label(rule_box, text="Reasoning").grid(
            row=8,
            column=0,
            sticky="w",
            pady=(8, 0),
        )
        self.rule_reasoning_entry = ttk.Entry(
            rule_box,
            textvariable=self.rule_reasoning_var,
        )
        self.rule_reasoning_entry.grid(row=9, column=0, sticky="ew")

        ttk.Label(
            editor_frame,
            text="Comparison and value options adjust based on the selected path type.",
            wraplength=310,
            style="Hint.TLabel",
        ).grid(row=3, column=0, sticky="ew", pady=(12, 0))

    def connect_form_events(self):
        self.play_name_var.trace_add("write", self.on_play_form_changed)
        self.play_base_score_var.trace_add("write", self.on_play_form_changed)

        self.rule_path_var.trace_add("write", self.on_rule_form_changed)
        self.rule_comparison_var.trace_add("write", self.on_rule_form_changed)
        self.rule_value_var.trace_add("write", self.on_rule_form_changed)
        self.rule_score_change_var.trace_add("write", self.on_rule_form_changed)
        self.rule_reasoning_var.trace_add("write", self.on_rule_form_changed)

        self.rule_path_combo.bind("<KeyRelease>", self.update_path_autocomplete)

    def get_path_type(self, path):
        if not path:
            return "unknown"

        return self.path_type_map.get(path, "unknown")

    def get_comparison_options_for_path(self, path):
        path_type = self.get_path_type(path)
        return COMPARISON_OPTIONS_BY_TYPE.get(path_type, COMPARISON_OPTIONS)

    def get_value_options_for_path(self, path):
        path_type = self.get_path_type(path)
        return VALUE_OPTIONS_BY_TYPE.get(path_type, [])

    def update_rule_widgets_for_path(self, clean_invalid_values):
        path = self.rule_path_var.get().strip()
        path_type = self.get_path_type(path)

        comparison_options = self.get_comparison_options_for_path(path)
        self.rule_comparison_combo["values"] = comparison_options

        value_options = self.get_value_options_for_path(path)
        self.rule_value_combo["values"] = value_options

        if path_type == "boolean":
            self.rule_value_combo.configure(state="readonly")
        else:
            if self.selected_rule_index is not None:
                self.rule_value_combo.configure(state="normal")

        if not clean_invalid_values:
            return

        self.loading_form = True

        current_comparison = self.rule_comparison_var.get().strip()

        if current_comparison and current_comparison not in comparison_options:
            self.rule_comparison_var.set("")

        if path_type == "boolean":
            current_value = self.rule_value_var.get().strip().lower()

            if current_value not in ["", "true", "false"]:
                self.rule_value_var.set("")

        self.loading_form = False

    def update_path_autocomplete(self, event=None):
        typed_text = self.rule_path_var.get().lower().strip()

        if not typed_text:
            self.rule_path_combo["values"] = self.path_options
            return

        matching_paths = [
            path for path in self.path_options if typed_text in path.lower()
        ]

        self.rule_path_combo["values"] = matching_paths[:100]

    def refresh_tree(self, selected_play_index=None, selected_rule_index=None):
        self.tree_item_info = {}
        self.play_tree_items = {}
        self.play_field_items = {}
        self.rule_tree_items = {}
        self.rule_field_items = {}

        for item in self.plays_tree.get_children():
            self.plays_tree.delete(item)

        item_to_select = None

        for play_index, play in enumerate(self.plays_data.get("plays", [])):
            play_item = self.plays_tree.insert(
                "",
                "end",
                text=self.make_play_tree_title(play_index, play),
                values=("play", f"base_score: {play.get('base_score', 0)}"),
                open=True,
                tags=("play",),
            )

            self.play_tree_items[play_index] = play_item
            self.tree_item_info[play_item] = {
                "type": "play",
                "play_index": play_index,
            }

            if selected_play_index == play_index and selected_rule_index is None:
                item_to_select = play_item

            name_item = self.plays_tree.insert(
                play_item,
                "end",
                text="Play Field",
                values=("name", play.get("name", "")),
                tags=("field",),
            )

            self.play_field_items[(play_index, "name")] = name_item
            self.tree_item_info[name_item] = {
                "type": "play_field",
                "play_index": play_index,
                "field": "name",
            }

            base_score_item = self.plays_tree.insert(
                play_item,
                "end",
                text="Play Field",
                values=("base_score", play.get("base_score", 0)),
                tags=("field",),
            )

            self.play_field_items[(play_index, "base_score")] = base_score_item
            self.tree_item_info[base_score_item] = {
                "type": "play_field",
                "play_index": play_index,
                "field": "base_score",
            }

            for rule_index, rule in enumerate(play.get("rules", [])):
                rule_item = self.plays_tree.insert(
                    play_item,
                    "end",
                    text=self.make_rule_tree_title(rule_index, rule),
                    values=("rule", rule.get("reasoning", "")),
                    open=False,
                    tags=("rule",),
                )

                self.rule_tree_items[(play_index, rule_index)] = rule_item
                self.tree_item_info[rule_item] = {
                    "type": "rule",
                    "play_index": play_index,
                    "rule_index": rule_index,
                }

                if (
                    selected_play_index == play_index
                    and selected_rule_index == rule_index
                ):
                    item_to_select = rule_item

                for field_name in [
                    "path",
                    "comparison",
                    "value",
                    "score_change",
                    "reasoning",
                ]:
                    field_item = self.plays_tree.insert(
                        rule_item,
                        "end",
                        text="Rule Field",
                        values=(field_name, value_to_text(rule.get(field_name, ""))),
                        tags=("field",),
                    )

                    self.rule_field_items[(play_index, rule_index, field_name)] = (
                        field_item
                    )
                    self.tree_item_info[field_item] = {
                        "type": "rule_field",
                        "play_index": play_index,
                        "rule_index": rule_index,
                        "field": field_name,
                    }

            add_rule_item = self.plays_tree.insert(
                play_item,
                "end",
                text="＋ Add Rule",
                values=("button", "Double-click to add an empty rule to this play"),
                tags=("add_button",),
            )

            self.tree_item_info[add_rule_item] = {
                "type": "add_rule_button",
                "play_index": play_index,
            }

        add_play_item = self.plays_tree.insert(
            "",
            "end",
            text="＋ Add Play",
            values=("button", "Double-click to add a new placeholder play"),
            tags=("add_button",),
        )

        self.tree_item_info[add_play_item] = {
            "type": "add_play_button",
        }

        if item_to_select is not None:
            self.plays_tree.selection_set(item_to_select)
            self.plays_tree.focus(item_to_select)
            self.plays_tree.see(item_to_select)

    def make_play_tree_title(self, play_index, play):
        play_name = play.get("name", "").strip()

        if not play_name:
            play_name = "unnamed"

        return f"Play {play_index + 1} ({play_name})"

    def make_rule_tree_title(self, rule_index, rule):
        return f"Rule {rule_index + 1} ({make_rule_english(rule)})"

    def on_tree_selection_changed(self, event=None):
        selected_item = self.get_selected_tree_item()

        if selected_item is None:
            self.selected_play_index = None
            self.selected_rule_index = None
            self.load_selected_data_into_form()
            return

        item_info = self.tree_item_info.get(selected_item)

        if item_info is None:
            return

        if item_info["type"] == "add_play_button":
            self.selected_play_index = None
            self.selected_rule_index = None
            self.load_selected_data_into_form()
            return

        self.selected_play_index = item_info.get("play_index")

        if item_info["type"] in ["rule", "rule_field"]:
            self.selected_rule_index = item_info.get("rule_index")
        else:
            self.selected_rule_index = None

        self.load_selected_data_into_form()

    def on_tree_double_click(self, event):
        selected_item = self.plays_tree.identify_row(event.y)
        selected_column = self.plays_tree.identify_column(event.x)

        if not selected_item:
            return

        item_info = self.tree_item_info.get(selected_item)

        if item_info is None:
            return

        if item_info["type"] == "add_play_button":
            self.add_play()
            return

        if item_info["type"] == "add_rule_button":
            self.add_blank_rule_to_play(item_info["play_index"])
            return

        if selected_column == "#2" and item_info["type"] in [
            "play_field",
            "rule_field",
        ]:
            self.start_floating_edit(selected_item, selected_column)
            return

        if item_info["type"] in ["play", "play_field"]:
            self.play_name_entry.focus_set()
            self.play_name_entry.select_range(0, tk.END)
            return

        if item_info["type"] in ["rule", "rule_field"]:
            self.rule_path_combo.focus_set()
            return

    def get_selected_tree_item(self):
        selected_items = self.plays_tree.selection()

        if not selected_items:
            return None

        return selected_items[0]

    def get_rule_path_for_tree_item(self, item_info):
        if item_info["type"] != "rule_field":
            return ""

        play_index = item_info["play_index"]
        rule_index = item_info["rule_index"]

        rule = self.plays_data["plays"][play_index]["rules"][rule_index]
        return rule.get("path", "")

    def start_floating_edit(self, selected_item, selected_column):
        if self.active_floating_editor is not None:
            self.active_floating_editor.destroy()
            self.active_floating_editor = None

        item_info = self.tree_item_info.get(selected_item)

        if item_info is None:
            return

        field_name = item_info.get("field")

        if field_name is None:
            return

        x, y, width, height = self.plays_tree.bbox(selected_item, selected_column)
        old_value = self.plays_tree.set(selected_item, "value")

        editor_is_dropdown = False

        if field_name == "comparison":
            path = self.get_rule_path_for_tree_item(item_info)
            comparison_options = self.get_comparison_options_for_path(path)

            editor = ttk.Combobox(
                self.plays_tree,
                values=comparison_options,
                state="readonly",
            )
            editor.set(old_value)
            editor_is_dropdown = True

        elif field_name == "path":
            editor = ttk.Combobox(
                self.plays_tree,
                values=self.path_options,
            )
            editor.set(old_value)
            self.attach_inline_path_autocomplete(editor)
            editor_is_dropdown = True

        elif field_name == "value":
            path = self.get_rule_path_for_tree_item(item_info)
            path_type = self.get_path_type(path)

            if path_type == "boolean":
                editor = ttk.Combobox(
                    self.plays_tree,
                    values=["true", "false"],
                    state="readonly",
                )

                if old_value.lower() in ["true", "false"]:
                    editor.set(old_value.lower())
                else:
                    editor.set("")

                editor_is_dropdown = True
            else:
                editor = ttk.Entry(self.plays_tree)
                editor.insert(0, old_value)

        else:
            editor = ttk.Entry(self.plays_tree)
            editor.insert(0, old_value)

        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()

        self.active_floating_editor = editor
        edit_finished = {"value": False}

        def finish_edit(event=None):
            if edit_finished["value"]:
                return

            edit_finished["value"] = True
            new_value_text = editor.get()
            editor.destroy()
            self.active_floating_editor = None

            self.apply_floating_edit(
                selected_item=selected_item,
                new_value_text=new_value_text,
            )

        def cancel_edit(event=None):
            if edit_finished["value"]:
                return

            edit_finished["value"] = True
            editor.destroy()
            self.active_floating_editor = None

        editor.bind("<Return>", finish_edit)
        editor.bind("<Escape>", cancel_edit)

        if editor_is_dropdown:
            editor.bind("<<ComboboxSelected>>", finish_edit)

            def open_dropdown():
                try:
                    editor.event_generate("<Button-1>")
                except tk.TclError:
                    pass

            self.root.after(100, open_dropdown)
        else:
            editor.bind("<FocusOut>", finish_edit)

    def attach_inline_path_autocomplete(self, combo_box):
        def update_options(event=None):
            typed_text = combo_box.get().lower().strip()

            if not typed_text:
                combo_box["values"] = self.path_options
                return

            matching_paths = [
                path for path in self.path_options if typed_text in path.lower()
            ]

            combo_box["values"] = matching_paths[:100]

        combo_box.bind("<KeyRelease>", update_options)

    def clean_rule_comparison_and_value_if_needed(self, play_index, rule_index):
        rule = self.plays_data["plays"][play_index]["rules"][rule_index]

        path = rule.get("path", "")
        path_type = self.get_path_type(path)

        current_comparison = rule.get("comparison", "")
        allowed_comparisons = self.get_comparison_options_for_path(path)

        if current_comparison and current_comparison not in allowed_comparisons:
            rule["comparison"] = ""

        if path_type == "boolean":
            current_value = value_to_text(rule.get("value", "")).lower()

            if current_value not in ["", "true", "false"]:
                rule["value"] = ""

    def apply_floating_edit(self, selected_item, new_value_text):
        item_info = self.tree_item_info.get(selected_item)

        if item_info is None:
            return

        item_type = item_info["type"]
        field_name = item_info.get("field")
        play_index = item_info.get("play_index")

        if item_type == "play_field":
            if field_name == "base_score":
                try:
                    new_value = int(new_value_text.strip())
                except ValueError:
                    messagebox.showerror(
                        "Invalid base score",
                        "Base score must be a number.",
                    )
                    return
            else:
                new_value = new_value_text.strip()

            self.plays_data["plays"][play_index][field_name] = new_value

            self.save_silently()
            self.refresh_tree(selected_play_index=play_index)
            self.load_selected_data_into_form()
            return

        if item_type == "rule_field":
            rule_index = item_info["rule_index"]

            if field_name == "score_change":
                try:
                    new_value = int(new_value_text.strip() or "0")
                except ValueError:
                    messagebox.showerror(
                        "Invalid score change",
                        "Score change must be a number.",
                    )
                    return

            elif field_name == "value":
                new_value = parse_rule_value(new_value_text)

            elif field_name == "comparison":
                rule = self.plays_data["plays"][play_index]["rules"][rule_index]
                path = rule.get("path", "")
                allowed_comparisons = self.get_comparison_options_for_path(path)

                if new_value_text and new_value_text not in allowed_comparisons:
                    messagebox.showerror(
                        "Invalid comparison",
                        "That comparison does not make sense for this path.",
                    )
                    return

                new_value = new_value_text.strip()

            else:
                new_value = new_value_text.strip()

            self.plays_data["plays"][play_index]["rules"][rule_index][field_name] = (
                new_value
            )

            if field_name == "path":
                self.clean_rule_comparison_and_value_if_needed(play_index, rule_index)

            self.save_silently()
            self.refresh_tree(
                selected_play_index=play_index,
                selected_rule_index=rule_index,
            )
            self.load_selected_data_into_form()

    def load_selected_data_into_form(self):
        self.loading_form = True

        if self.selected_play_index is None:
            self.play_name_var.set("")
            self.play_base_score_var.set("")
            self.set_play_fields_enabled(False)
        else:
            selected_play = self.plays_data["plays"][self.selected_play_index]

            self.set_play_fields_enabled(True)
            self.play_name_var.set(selected_play.get("name", ""))
            self.play_base_score_var.set(str(selected_play.get("base_score", 0)))

        if self.selected_rule_index is None:
            self.rule_path_var.set("")
            self.rule_comparison_var.set("")
            self.rule_value_var.set("")
            self.rule_score_change_var.set("")
            self.rule_reasoning_var.set("")
            self.set_rule_fields_enabled(False)
        else:
            selected_rule = self.plays_data["plays"][self.selected_play_index]["rules"][
                self.selected_rule_index
            ]

            self.set_rule_fields_enabled(True)

            self.rule_path_var.set(selected_rule.get("path", ""))
            self.update_rule_widgets_for_path(clean_invalid_values=False)

            self.rule_comparison_var.set(selected_rule.get("comparison", ""))
            self.rule_value_var.set(value_to_text(selected_rule.get("value", "")))
            self.rule_score_change_var.set(str(selected_rule.get("score_change", "")))
            self.rule_reasoning_var.set(selected_rule.get("reasoning", ""))

            self.update_rule_widgets_for_path(clean_invalid_values=True)

        self.loading_form = False

    def set_play_fields_enabled(self, enabled):
        state = "normal" if enabled else "disabled"

        self.play_name_entry.configure(state=state)
        self.play_base_score_entry.configure(state=state)

    def set_rule_fields_enabled(self, enabled):
        if enabled:
            self.rule_path_combo.configure(state="normal")
            self.rule_comparison_combo.configure(state="readonly")
            self.rule_value_combo.configure(state="normal")
            self.rule_score_entry.configure(state="normal")
            self.rule_reasoning_entry.configure(state="normal")
            self.update_rule_widgets_for_path(clean_invalid_values=False)
        else:
            self.rule_path_combo.configure(state="disabled")
            self.rule_comparison_combo.configure(state="disabled")
            self.rule_value_combo.configure(state="disabled")
            self.rule_score_entry.configure(state="disabled")
            self.rule_reasoning_entry.configure(state="disabled")

    def on_play_form_changed(self, *args):
        if self.loading_form:
            return

        if self.selected_play_index is None:
            return

        selected_play = self.plays_data["plays"][self.selected_play_index]

        selected_play["name"] = self.play_name_var.get()

        base_score_text = self.play_base_score_var.get().strip()

        if base_score_text not in ["", "-"]:
            try:
                selected_play["base_score"] = int(base_score_text)
            except ValueError:
                self.status_var.set("Base score must be a number.")
                return

        self.update_play_tree_display(self.selected_play_index)
        self.save_silently()

    def on_rule_form_changed(self, *args):
        if self.loading_form:
            return

        if self.selected_play_index is None or self.selected_rule_index is None:
            return

        self.update_rule_widgets_for_path(clean_invalid_values=True)

        selected_rule = self.plays_data["plays"][self.selected_play_index]["rules"][
            self.selected_rule_index
        ]

        selected_rule["path"] = self.rule_path_var.get()
        selected_rule["comparison"] = self.rule_comparison_var.get()
        selected_rule["value"] = parse_rule_value(self.rule_value_var.get())

        score_change_text = self.rule_score_change_var.get().strip()

        if score_change_text not in ["", "-"]:
            try:
                selected_rule["score_change"] = int(score_change_text)
            except ValueError:
                self.status_var.set("Score change must be a number.")
                return
        else:
            selected_rule["score_change"] = ""

        selected_rule["reasoning"] = self.rule_reasoning_var.get()

        self.clean_rule_comparison_and_value_if_needed(
            self.selected_play_index,
            self.selected_rule_index,
        )

        self.update_rule_tree_display(
            self.selected_play_index, self.selected_rule_index
        )
        self.save_silently()

    def update_play_tree_display(self, play_index):
        play = self.plays_data["plays"][play_index]

        play_item = self.play_tree_items.get(play_index)

        if play_item:
            self.plays_tree.item(
                play_item,
                text=self.make_play_tree_title(play_index, play),
                values=("play", f"base_score: {play.get('base_score', 0)}"),
            )

        name_item = self.play_field_items.get((play_index, "name"))

        if name_item:
            self.plays_tree.item(name_item, values=("name", play.get("name", "")))

        base_score_item = self.play_field_items.get((play_index, "base_score"))

        if base_score_item:
            self.plays_tree.item(
                base_score_item,
                values=("base_score", play.get("base_score", 0)),
            )

    def update_rule_tree_display(self, play_index, rule_index):
        rule = self.plays_data["plays"][play_index]["rules"][rule_index]

        rule_item = self.rule_tree_items.get((play_index, rule_index))

        if rule_item:
            self.plays_tree.item(
                rule_item,
                text=self.make_rule_tree_title(rule_index, rule),
                values=("rule", rule.get("reasoning", "")),
            )

        for field_name in ["path", "comparison", "value", "score_change", "reasoning"]:
            field_item = self.rule_field_items.get((play_index, rule_index, field_name))

            if field_item:
                self.plays_tree.item(
                    field_item,
                    values=(field_name, value_to_text(rule.get(field_name, ""))),
                )

    def add_play(self):
        new_play_number = len(self.plays_data["plays"]) + 1

        new_play = {
            "name": f"new_play_{new_play_number}",
            "base_score": 0,
            "rules": [],
        }

        self.plays_data["plays"].append(new_play)
        new_play_index = len(self.plays_data["plays"]) - 1

        self.save_silently()
        self.refresh_tree(selected_play_index=new_play_index)

        self.selected_play_index = new_play_index
        self.selected_rule_index = None
        self.load_selected_data_into_form()

        self.play_name_entry.focus_set()
        self.play_name_entry.select_range(0, tk.END)

    def add_rule_to_selected_play(self):
        if self.selected_play_index is None:
            messagebox.showwarning("No play selected", "Select a play first.")
            return

        self.add_blank_rule_to_play(self.selected_play_index)

    def add_blank_rule_to_play(self, play_index):
        new_rule = {
            "path": "",
            "comparison": "",
            "value": "",
            "score_change": "",
            "reasoning": "",
        }

        self.plays_data["plays"][play_index]["rules"].append(new_rule)

        new_rule_index = len(self.plays_data["plays"][play_index]["rules"]) - 1

        self.save_silently()
        self.refresh_tree(
            selected_play_index=play_index,
            selected_rule_index=new_rule_index,
        )

        self.selected_play_index = play_index
        self.selected_rule_index = new_rule_index
        self.load_selected_data_into_form()

        self.rule_path_combo.focus_set()

    def delete_selected_item(self, event=None):
        selected_item = self.get_selected_tree_item()

        if selected_item is None:
            messagebox.showwarning("Nothing selected", "Select a play or rule first.")
            return

        item_info = self.tree_item_info.get(selected_item)

        if item_info is None:
            return

        if item_info["type"] == "add_play_button":
            return

        if item_info["type"] == "add_rule_button":
            return

        if item_info["type"] in ["rule", "rule_field"]:
            self.delete_rule(
                play_index=item_info["play_index"],
                rule_index=item_info["rule_index"],
            )
            return

        if item_info["type"] in ["play", "play_field"]:
            self.delete_play(play_index=item_info["play_index"])
            return

    def delete_play(self, play_index):
        play_name = self.plays_data["plays"][play_index].get("name", "")

        confirmed = messagebox.askyesno(
            "Delete play",
            f"Delete the whole play '{play_name}'?",
        )

        if not confirmed:
            return

        del self.plays_data["plays"][play_index]

        self.selected_play_index = None
        self.selected_rule_index = None

        self.save_silently()
        self.refresh_tree()
        self.load_selected_data_into_form()

    def delete_rule(self, play_index, rule_index):
        confirmed = messagebox.askyesno(
            "Delete rule",
            f"Delete rule {rule_index + 1} from this play?",
        )

        if not confirmed:
            return

        del self.plays_data["plays"][play_index]["rules"][rule_index]

        self.selected_rule_index = None

        self.save_silently()
        self.refresh_tree(selected_play_index=play_index)
        self.load_selected_data_into_form()

    def reload_path_options(self):
        self.path_options, self.path_type_map = (
            load_path_options_from_placeholder_state()
        )
        self.rule_path_combo["values"] = self.path_options
        self.update_rule_widgets_for_path(clean_invalid_values=True)

        self.status_var.set(f"Reloaded {len(self.path_options)} path options.")

    def save_silently(self):
        save_plays_data(self.plays_data)
        self.status_var.set(f"Saved to {PLAYS_LIST_FILE.name}")

    def save_now(self):
        save_plays_data(self.plays_data)
        messagebox.showinfo("Saved", f"Saved to {PLAYS_LIST_FILE.name}.")


def make_root_window():
    if USING_TTKBOOTSTRAP:
        return ttkbootstrap_theme.Window(themename=APP_THEME)

    return tk.Tk()


if __name__ == "__main__":
    root = make_root_window()
    app = BWGSActionEditor(root)
    root.mainloop()
