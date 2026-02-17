from typing import Dict, List, Optional
from ..core.interfaces import TeamInterface
from ..core.types import TeamState

class TeamRegistry:
    """
    Manages the lifecycle and retrieval of teams in the system.
    """
    def __init__(self):
        self._teams: Dict[str, TeamInterface] = {}

    def register(self, team: TeamInterface):
        if team.id in self._teams:
            raise ValueError(f"Team {team.id} already registered.")
        self._teams[team.id] = team

    def get_team(self, team_id: str) -> Optional[TeamInterface]:
        return self._teams.get(team_id)

    def get_all_teams(self) -> List[TeamInterface]:
        return list(self._teams.values())

    def remove_team(self, team_id: str):
        if team_id in self._teams:
            del self._teams[team_id]
