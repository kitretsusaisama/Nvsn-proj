import random
import copy
import structlog
from typing import List, Dict
from ..agents.autonomous import AutonomousAgent

logger = structlog.get_logger()

class AgentGenome:
    def __init__(self, system_prompt: str, tools: List[str], parameters: Dict[str, float]):
        self.system_prompt = system_prompt
        self.tools = tools
        self.parameters = parameters # e.g. temperature, aggression
        self.fitness = 0.0

class EvolutionaryEngine:
    """
    Manages the evolution of Agent configurations.
    """
    def __init__(self, population_size=10):
        self.population: List[AgentGenome] = []
        self.generation = 0
        self.logger = logger.bind(component="EvolutionaryEngine")
        self._init_population(population_size)

    def _init_population(self, size):
        for i in range(size):
            self.population.append(AgentGenome(
                system_prompt=f"You are Agent_{i}. Focus on efficiency.",
                tools=["python_interpreter", "web_search"],
                parameters={"temperature": 0.7, "risk_tolerance": random.random()}
            ))

    def evaluate_fitness(self):
        # In real system: Run tasks and measure success rate.
        # Simulation: Random fitness
        for genome in self.population:
            genome.fitness = random.random()

        self.population.sort(key=lambda x: x.fitness, reverse=True)
        best = self.population[0]
        self.logger.info("Generation Best", gen=self.generation, fitness=f"{best.fitness:.4f}")

    def evolve(self):
        self.generation += 1
        new_pop = self.population[:2] # Elitism: Keep top 2

        while len(new_pop) < len(self.population):
            parent1 = random.choice(self.population[:5])
            parent2 = random.choice(self.population[:5])
            child = self._crossover(parent1, parent2)
            self._mutate(child)
            new_pop.append(child)

        self.population = new_pop
        self.logger.info("Evolution Step Complete", gen=self.generation)

    def _crossover(self, p1: AgentGenome, p2: AgentGenome) -> AgentGenome:
        # Mix prompts and params
        prompt = p1.system_prompt if random.random() > 0.5 else p2.system_prompt
        params = {k: (v + p2.parameters[k])/2 for k, v in p1.parameters.items()}
        return AgentGenome(prompt, p1.tools, params)

    def _mutate(self, genome: AgentGenome):
        if random.random() < 0.1:
            genome.parameters["temperature"] = min(1.0, max(0.0, genome.parameters["temperature"] + random.uniform(-0.1, 0.1)))
            genome.system_prompt += " MUTATED."
