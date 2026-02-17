from ..teams.core import Team
from ..agents.cognitive import CognitiveAgent
from ..agents.roles import AgentRole
from ..core.interfaces import LLMInterface, MemoryInterface, CommunicationInterface

def create_cognitive_team(
    team_name: str,
    llm: LLMInterface,
    memory: MemoryInterface,
    communication: CommunicationInterface
) -> Team:
    """
    Factory function to create an advanced team of cognitive agents.
    """
    team = Team(name=team_name)

    # Planner - Uses Cognitive/ReAct logic
    planner = CognitiveAgent(AgentRole.PLANNER, llm, memory, communication, team.id, name=f"{team_name}_Planner")

    # Engineer - Uses Cognitive/ReAct logic
    engineer = CognitiveAgent(AgentRole.ENGINEER, llm, memory, communication, team.id, name=f"{team_name}_Engineer")

    # Critic - Uses Cognitive/ReAct logic
    critic = CognitiveAgent(AgentRole.CRITIC, llm, memory, communication, team.id, name=f"{team_name}_Critic")

    team.add_agent(planner)
    team.add_agent(engineer)
    team.add_agent(critic)

    return team
