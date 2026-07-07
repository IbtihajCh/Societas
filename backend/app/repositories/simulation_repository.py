import json
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from shared.schemas.simulation_state import SimulationState

from backend.app.database.connection import get_connection


class SimulationRepository:
    async def save_snapshot(self, tick: int, state: SimulationState) -> None:
        conn = await get_connection()
        state_json = json.dumps(asdict(state))
        await conn.execute(
            """INSERT OR REPLACE INTO state_snapshots
               (tick, state_json, created_at)
               VALUES (?, ?, datetime('now'))""",
            (tick, state_json),
        )
        await conn.commit()

    async def get_snapshots(self, tick_from: int, tick_to: int) -> List[Dict[str, Any]]:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT tick, state_json, created_at FROM state_snapshots WHERE tick >= ? AND tick <= ? ORDER BY tick ASC",
            (tick_from, tick_to),
        )
        rows = await cursor.fetchall()
        return [
            {
                "tick": row["tick"],
                "state": json.loads(row["state_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    async def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT tick, state_json, created_at FROM state_snapshots ORDER BY tick DESC LIMIT 1",
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "tick": row["tick"],
            "state": json.loads(row["state_json"]),
            "created_at": row["created_at"],
        }

    async def save_tick_record(self, tick: int, event_type: str, data: Dict[str, Any]) -> None:
        conn = await get_connection()
        data_json = json.dumps(data)
        await conn.execute(
            """INSERT INTO tick_history
               (tick, event_type, data_json, created_at)
               VALUES (?, ?, ?, datetime('now'))""",
            (tick, event_type, data_json),
        )
        await conn.commit()

    async def get_tick_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT id, tick, event_type, data_json, created_at FROM tick_history ORDER BY tick DESC, id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "tick": row["tick"],
                "event_type": row["event_type"],
                "data": json.loads(row["data_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
