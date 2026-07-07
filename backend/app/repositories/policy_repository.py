import json
from dataclasses import asdict
from typing import List, Optional

from shared.interfaces.i_data_repository import IDataRepository
from shared.schemas.policy import Policy, PolicyWeights
from shared.types.aliases import PolicyId
from shared.types.enums import PolicyCategory

from backend.app.database.connection import get_connection


class PolicyRepository(IDataRepository[Policy]):
    async def save(self, entity: Policy) -> None:
        conn = await get_connection()
        weights_json = json.dumps(asdict(entity.weights))
        await conn.execute(
            """INSERT OR REPLACE INTO policies
               (policy_id, name, description, category, weights, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                str(entity.id),
                entity.name,
                entity.description,
                entity.category.value,
                weights_json,
                1 if entity.is_active else 0,
            ),
        )
        await conn.commit()

    async def save_many(self, entities: List[Policy]) -> None:
        conn = await get_connection()
        for entity in entities:
            weights_json = json.dumps(asdict(entity.weights))
            await conn.execute(
                """INSERT OR REPLACE INTO policies
                   (policy_id, name, description, category, weights, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (
                    str(entity.id),
                    entity.name,
                    entity.description,
                    entity.category.value,
                    weights_json,
                    1 if entity.is_active else 0,
                ),
            )
        await conn.commit()

    async def load(self, entity_id: str) -> Optional[Policy]:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT * FROM policies WHERE policy_id = ? AND is_active = 1",
            (entity_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_policy(row)

    async def load_all(self) -> List[Policy]:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT * FROM policies WHERE is_active = 1 ORDER BY created_at DESC",
        )
        rows = await cursor.fetchall()
        return [self._row_to_policy(row) for row in rows]

    async def delete(self, entity_id: str) -> bool:
        conn = await get_connection()
        cursor = await conn.execute(
            "UPDATE policies SET is_active = 0 WHERE policy_id = ?",
            (entity_id,),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def query(self, **kwargs) -> List[Policy]:
        conn = await get_connection()
        conditions = []
        params = []
        for key, value in kwargs.items():
            if key == "category":
                conditions.append("category = ?")
                params.append(value.value if hasattr(value, "value") else str(value))
            elif key == "is_active":
                conditions.append("is_active = ?")
                params.append(1 if value else 0)
        where = " AND ".join(conditions) if conditions else "1=1"
        cursor = await conn.execute(
            f"SELECT * FROM policies WHERE {where} ORDER BY created_at DESC",
            params,
        )
        rows = await cursor.fetchall()
        return [self._row_to_policy(row) for row in rows]

    async def count(self) -> int:
        conn = await get_connection()
        cursor = await conn.execute("SELECT COUNT(*) FROM policies WHERE is_active = 1")
        row = await cursor.fetchone()
        return row[0] if row else 0

    def _row_to_policy(self, row) -> Policy:
        weights_dict = json.loads(row["weights"]) if isinstance(row["weights"], str) else {}
        return Policy(
            id=PolicyId(row["policy_id"]),
            name=row["name"],
            description=row["description"] or "",
            category=PolicyCategory(int(row["category"])),
            weights=PolicyWeights(**{k: float(v) for k, v in weights_dict.items()}),
            is_active=bool(row["is_active"]),
            enactment_tick=0,
        )
