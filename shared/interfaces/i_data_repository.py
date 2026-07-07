"""
Data Repository Interface
=========================

Abstract interface for data persistence.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class IDataRepository(ABC, Generic[T]):
    """
    Abstract interface for data persistence.
    
    Defines the contract for saving, loading, and querying data.
    Generic type T represents the entity type.
    """
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """
        Save an entity.
        
        Args:
            entity: The entity to save
        """
        ...
    
    @abstractmethod
    def save_many(self, entities: List[T]) -> None:
        """
        Save multiple entities.
        
        Args:
            entities: List of entities to save
        """
        ...
    
    @abstractmethod
    def load(self, entity_id: str) -> Optional[T]:
        """
        Load an entity by ID.
        
        Args:
            entity_id: ID of the entity to load
            
        Returns:
            Entity if found, None otherwise
        """
        ...
    
    @abstractmethod
    def load_all(self) -> List[T]:
        """
        Load all entities.
        
        Returns:
            List of all entities
        """
        ...
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    @abstractmethod
    def query(self, **kwargs) -> List[T]:
        """
        Query entities by criteria.
        
        Args:
            **kwargs: Query criteria
            
        Returns:
            List of matching entities
        """
        ...
    
    @abstractmethod
    def count(self) -> int:
        """
        Count all entities.
        
        Returns:
            Total number of entities
        """
        ...
