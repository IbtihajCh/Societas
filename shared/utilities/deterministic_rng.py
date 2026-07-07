"""
Deterministic RNG Utility
=========================

Provides a seeded random number generator for deterministic simulation.
"""

import numpy as np
from typing import Optional


class DeterministicRNG:
    """
    Seeded random number generator for deterministic simulation.
    
    Wraps numpy's random Generator with a fixed seed to ensure
    reproducible simulation results across runs.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the RNG with an optional seed.
        
        Args:
            seed: Random seed for deterministic behavior.
                  If None, uses default seed (42).
        """
        self._seed = seed if seed is not None else 42
        self._rng = np.random.default_rng(self._seed)
    
    @property
    def seed(self) -> int:
        """Get the current seed value."""
        return self._seed
    
    def random(self) -> float:
        """
        Generate a random float in [0.0, 1.0).
        
        Returns:
            Random float
        """
        return float(self._rng.random())
    
    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """
        Generate a random float in [low, high).
        
        Args:
            low: Lower bound
            high: Upper bound
            
        Returns:
            Random float
        """
        return float(self._rng.uniform(low, high))
    
    def normal(self, mean: float = 0.0, std: float = 1.0) -> float:
        """
        Generate a random float from normal distribution.
        
        Args:
            mean: Mean of the distribution
            std: Standard deviation
            
        Returns:
            Random float
        """
        return float(self._rng.normal(mean, std))
    
    def choice(self, a: int, size: Optional[int] = None) -> int:
        """
        Randomly choose an integer from [0, a).
        
        Args:
            a: Upper bound (exclusive)
            size: Number of choices (None for single choice)
            
        Returns:
            Random integer or array of integers
        """
        result = self._rng.choice(a, size=size)
        if size is None:
            return int(result)
        return result
    
    def shuffle(self, x: list) -> None:
        """
        Shuffle a list in place.
        
        Args:
            x: List to shuffle
        """
        self._rng.shuffle(x)
    
    def reset(self, seed: Optional[int] = None) -> None:
        """
        Reset the RNG with a new seed.
        
        Args:
            seed: New seed value. If None, uses original seed.
        """
        self._seed = seed if seed is not None else self._seed
        self._rng = np.random.default_rng(self._seed)


# Global RNG instance
_global_rng: Optional[DeterministicRNG] = None


def get_rng(seed: Optional[int] = None) -> DeterministicRNG:
    """
    Get the global RNG instance.
    
    Args:
        seed: Optional seed to initialize/reset the RNG
        
    Returns:
        DeterministicRNG instance
    """
    global _global_rng
    if _global_rng is None or seed is not None:
        _global_rng = DeterministicRNG(seed)
    return _global_rng
