from .core import Team
from ..agents.roles import PlannerAgent, EngineerAgent, CriticAgent
from ..core.interfaces import LLMInterface, MemoryInterface, CommunicationInterface

def create_software_team(
    team_name: str,
    llm: LLMInterface,
    memory: MemoryInterface,
    communication: CommunicationInterface
) -> Team:
    """
    Factory function to create a standard software development team.
    Contains: Planner, Engineer, Critic.
    """
    team = Team(name=team_name)

    planner = PlannerAgent(llm, memory, communication, team.id, name=f"{team_name}_Planner")
    engineer = EngineerAgent(llm, memory, communication, team.id, name=f"{team_name}_Engineer")
    critic = CriticAgent(llm, memory, communication, team.id, name=f"{team_name}_Critic")

    team.add_agent(planner)
    team.add_agent(engineer)
    team.add_agent(critic)

    return team
