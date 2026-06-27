from dataclasses import dataclass, field


@dataclass
class KnownPlayerProfile:
    username: str
    uuid: str | None = None
    star_count: int | None = None
    notes: str = ""


@dataclass
class TeamState:
    team_bed_alive: bool
    players_alive: int
    average_star_count: int | None = None
    # average_estimated_skill_level should be based on stars but also how fast they break beds and get finals
    average_estimated_skill_level: int = 5
    known_players: list[KnownPlayerProfile] = field(default_factory=list)


@dataclass
class ActiveUserState:
    bed_alive: bool = True
    health: int = 20
    blocks: int = 0
    has_pickaxe: bool = False
    has_axe: bool = False
    has_shears: bool = False
    fireballs: int = 0
    golden_apples: int = 0
    armor_type: str = "leather"
    sword_type: str = "wood"

    @property
    def has_tools(self) -> bool:
        return self.has_pickaxe or self.has_axe or self.has_shears


@dataclass
class ResourceCountState:
    iron: int = 0
    gold: int = 0
    diamonds: int = 0
    emeralds: int = 0


@dataclass
class PassiveEnemyInfo:
    near_team_island: bool = False
    enemies_visible: int = 0


@dataclass
class ActiveGameState:
    time_elapsed_seconds: int
    game_phase: str
    map_name: str
    map_rush_type: str
    first_rush_iron_cost: int

    active_user: ActiveUserState
    resources: ResourceCountState
    enemy: PassiveEnemyInfo
    teams: dict[str, TeamState]
    target_team: str

    @property
    def target_enemy_team(self) -> TeamState:
        return self.teams[self.target_team]


def make_placeholder_state() -> ActiveGameState:
    return ActiveGameState(
        time_elapsed_seconds=92,
        game_phase="early_game",
        map_name="Lighthouse",
        map_rush_type="siderush",
        first_rush_iron_cost=8,
        active_user=ActiveUserState(
            bed_alive=True,
            health=20,
            blocks=48,
            has_pickaxe=False,
            has_axe=False,
            has_shears=True,
            fireballs=0,
            golden_apples=1,
            armor_type="leather",
            sword_type="stone",
        ),
        resources=ResourceCountState(
            iron=12,
            gold=4,
            diamonds=2,
            emeralds=0,
        ),
        enemy=PassiveEnemyInfo(
            near_team_island=False,
            enemies_visible=2,
        ),
        teams={
            "red": TeamState(
                team_bed_alive=True,
                players_alive=2,
                average_star_count=75,
                average_estimated_skill_level=5,
                known_players=[
                    KnownPlayerProfile(
                        username="RedPlayer1",
                        star_count=80,
                        notes="Placeholder red player.",
                    ),
                    KnownPlayerProfile(
                        username="RedPlayer2",
                        star_count=70,
                        notes="Placeholder red player.",
                    ),
                ],
            ),
            "blue": TeamState(
                team_bed_alive=True,
                players_alive=2,
                average_star_count=185,
                average_estimated_skill_level=8,
                known_players=[
                    KnownPlayerProfile(
                        username="BluePlayer1",
                        star_count=250,
                        notes="Aggressive rusher.",
                    ),
                    KnownPlayerProfile(
                        username="BluePlayer2",
                        star_count=120,
                        notes="Usually plays safer.",
                    ),
                ],
            ),
            "green": TeamState(
                team_bed_alive=False,
                players_alive=0,
                average_star_count=40,
                average_estimated_skill_level=4,
                known_players=[],
            ),
            "yellow": TeamState(
                team_bed_alive=True,
                players_alive=2,
                average_star_count=110,
                average_estimated_skill_level=6,
                known_players=[
                    KnownPlayerProfile(
                        username="YellowPlayer1",
                        star_count=100,
                        notes="Placeholder yellow player.",
                    ),
                    KnownPlayerProfile(
                        username="YellowPlayer2",
                        star_count=120,
                        notes="Placeholder yellow player.",
                    ),
                ],
            ),
        },
        target_team="blue",
    )


if __name__ == "__main__":
    state = make_placeholder_state()
    print(state)
    print(state.target_enemy_team)
