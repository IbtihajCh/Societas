"""
Agent Registry
==============

Registry for managing all agents in the simulation.
"""

from typing import Dict, List, Optional

from shared.types.aliases import AgentId
from shared.schemas.agent_state import AgentState

from simulation.agents.agent import Agent


class AgentRegistry:
    """
    Registry for managing all agents in the simulation.
    
    Provides lookup, iteration, and lifecycle management for agents.
    
    Attributes:
        _agents: Dictionary mapping agent IDs to Agent instances
    """
    
    def __init__(self):
        """Initialize an empty agent registry."""
        self._agents: Dict[AgentId, Agent] = {}
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register a new agent.
        
        Args:
            agent: The agent to register
        """
        self._agents[agent.get_id()] = agent
    
    def unregister_agent(self, agent_id: AgentId) -> None:
        """
        Unregister an agent.
        
        Args:
            agent_id: ID of the agent to unregister
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
    
    def get_agent(self, agent_id: AgentId) -> Optional[AgentState]:
        """
        Get an agent's state by ID.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            AgentState if found, None otherwise
        """
        agent = self._agents.get(agent_id)
        return agent.get_state() if agent else None
    
    def get_all_agents(self) -> List[AgentState]:
        """
        Get all active agents.
        
        Returns:
            List of all active AgentState objects
        """
        return [agent.get_state() for agent in self._agents.values() if agent.is_alive()]
    
    def get_agent_count(self) -> int:
        """
        Get the total number of registered agents.
        
        Returns:
            Number of agents
        """
        return len(self._agents)
    
    def clear(self) -> None:
        """Clear all agents from the registry."""
        self._agents.clear()
