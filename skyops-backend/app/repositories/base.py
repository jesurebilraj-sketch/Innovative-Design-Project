"""Generic base repository for SQLAlchemy CRUD operations."""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository class providing standard database operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id_val: str) -> Optional[ModelType]:
        """Retrieve a single entity by its primary key ID."""
        return self.db.query(self.model).filter(self.model.id == id_val).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """List entities with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity and commit."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, id_val: str) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id_val)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False
