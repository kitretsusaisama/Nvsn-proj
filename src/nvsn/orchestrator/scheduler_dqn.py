import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
import structlog
from collections import deque
from typing import List, Tuple
from ..core.types import Task, AgentState

logger = structlog.get_logger()

class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, output_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

class NeuralScheduler:
    """
    Deep Q-Network (DQN) Scheduler.
    Learns optimal agent assignment policies via Reinforcement Learning.
    """
    def __init__(self, num_agents: int = 5, state_dim: int = 4):
        self.num_agents = num_agents
        self.state_dim = state_dim
        self.memory = deque(maxlen=10000)
        self.batch_size = 32
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DQN(state_dim, num_agents).to(self.device)
        self.target_net = DQN(state_dim, num_agents).to(self.device)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.logger = logger.bind(component="NeuralScheduler")

    def _encode_state(self, task: Task, agents: List[AgentState]) -> np.ndarray:
        """
        Encodes system state into a vector.
        Features: [TaskDifficulty, AvgAgentLoad, SystemHealth, TimeOfDay]
        Simplified for MVP.
        """
        # Feature engineering simulation
        difficulty = 0.5 # Placeholder
        avg_load = sum([0.5 for _ in agents]) / len(agents) if agents else 0
        health = 1.0
        time_val = 0.5

        return np.array([difficulty, avg_load, health, time_val], dtype=np.float32)

    def select_action(self, state: np.ndarray, available_agents: List[str]) -> int:
        if random.random() < self.epsilon:
            return random.randint(0, self.num_agents - 1)

        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_t)
            # Mask unavailable agents? For now assume simplified fixed pool
            return q_values.argmax().item()

    def store_experience(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def optimize_model(self):
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        state_batch, action_batch, reward_batch, next_state_batch, done_batch = zip(*batch)

        state_batch = torch.FloatTensor(np.array(state_batch)).to(self.device)
        action_batch = torch.LongTensor(action_batch).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(reward_batch).to(self.device)
        next_state_batch = torch.FloatTensor(np.array(next_state_batch)).to(self.device)
        done_batch = torch.FloatTensor(done_batch).to(self.device)

        q_values = self.policy_net(state_batch).gather(1, action_batch)
        next_q_values = self.target_net(next_state_batch).max(1)[0].detach()
        expected_q_values = reward_batch + (self.gamma * next_q_values * (1 - done_batch))

        loss = nn.MSELoss()(q_values.squeeze(), expected_q_values)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return loss.item()

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())
