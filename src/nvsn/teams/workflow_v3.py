from ..teams.core import Team
from ..agents.super_intelligent import SuperIntelligentAgent
from ..agents.roles import AgentRole
from ..core.interfaces import LLMInterface, MemoryInterface, CommunicationInterface

def create_super_team(
    team_name: str,
    llm: LLMInterface,
    memory: MemoryInterface,
    communication: CommunicationInterface
) -> Team:
    """
    Factory function to create a SUPER INTELLIGENT team.
    """
    team = Team(name=team_name)

    # Planner - Uses SuperIntelligent logic
    planner = SuperIntelligentAgent(AgentRole.PLANNER, llm, memory, communication, team.id, name=f"{team_name}_OmniPlanner")

    # Engineer - Uses SuperIntelligent logic
    engineer = SuperIntelligentAgent(AgentRole.ENGINEER, llm, memory, communication, team.id, name=f"{team_name}_OmniEngineer")

    team.add_agent(planner)
    team.add_agent(engineer)

    return team
