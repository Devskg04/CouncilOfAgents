"""
State Manager - Free SQLite-based State Persistence
Replaces Redis with file-based state management
"""

import aiosqlite
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class StateManager:
    """
    Free, zero-cost state management using SQLite
    - File-based persistence
    - ACID transactions
    - Session isolation
    - Zero infrastructure cost
    """
    
    def __init__(self, db_path: str = "data/state.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database schema"""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Factors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factors (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                validation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agent outputs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                factor_id INTEGER,
                output_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Debate status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debate_status (
                session_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_phase TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                problem_statement TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_factors_session ON factors(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outputs_session ON agent_outputs(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_outputs_factor ON agent_outputs(factor_id)")
        
        conn.commit()
        conn.close()
    
    # ===== Session Management =====
    
    async def create_session(self, session_id: str, problem_statement: str) -> str:
        """Create a new analysis session"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO sessions (session_id, problem_statement, status, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, problem_statement, "active", json.dumps({}))
            )
            await db.commit()
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "session_id": row[0],
                        "problem_statement": row[1],
                        "status": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                        "created_at": row[4],
                        "completed_at": row[5]
                    }
        return None
    
    async def update_session_status(self, session_id: str, status: str):
        """Update session status"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE sessions SET status = ?, completed_at = ? WHERE session_id = ?",
                (status, datetime.utcnow().isoformat() if status == "completed" else None, session_id)
            )
            await db.commit()
    
    # ===== Factor Management =====
    
    async def store_factor(
        self,
        session_id: str,
        factor_id: int,
        name: str,
        description: str,
        validation: Optional[Dict[str, Any]] = None
    ):
        """Store a factor"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO factors (id, session_id, name, description, validation)
                VALUES (?, ?, ?, ?, ?)
                """,
                (factor_id, session_id, name, description, json.dumps(validation) if validation else None)
            )
            await db.commit()
    
    async def get_factors(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all factors for a session"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM factors WHERE session_id = ? ORDER BY id",
                (session_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "session_id": row[1],
                        "name": row[2],
                        "description": row[3],
                        "validation": json.loads(row[4]) if row[4] else None,
                        "created_at": row[5]
                    }
                    for row in rows
                ]
    
    async def get_factor(self, session_id: str, factor_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific factor"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM factors WHERE session_id = ? AND id = ?",
                (session_id, factor_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "session_id": row[1],
                        "name": row[2],
                        "description": row[3],
                        "validation": json.loads(row[4]) if row[4] else None,
                        "created_at": row[5]
                    }
        return None
    
    # ===== Agent Output Management =====
    
    async def store_agent_output(
        self,
        session_id: str,
        agent_name: str,
        output_type: str,
        content: Dict[str, Any],
        factor_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store agent output"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO agent_outputs (session_id, agent_name, factor_id, output_type, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    agent_name,
                    factor_id,
                    output_type,
                    json.dumps(content),
                    json.dumps(metadata) if metadata else None
                )
            )
            await db.commit()
    
    async def get_agent_outputs(
        self,
        session_id: str,
        agent_name: Optional[str] = None,
        factor_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get agent outputs with optional filtering"""
        query = "SELECT * FROM agent_outputs WHERE session_id = ?"
        params = [session_id]
        
        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)
        
        if factor_id is not None:
            query += " AND factor_id = ?"
            params.append(factor_id)
        
        query += " ORDER BY created_at"
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": row[0],
                        "session_id": row[1],
                        "agent_name": row[2],
                        "factor_id": row[3],
                        "output_type": row[4],
                        "content": json.loads(row[5]),
                        "metadata": json.loads(row[6]) if row[6] else None,
                        "created_at": row[7]
                    }
                    for row in rows
                ]
    
    # ===== Debate Status Management =====
    
    async def update_debate_status(
        self,
        session_id: str,
        status: str,
        current_phase: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update debate status"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO debate_status (session_id, status, current_phase, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    status,
                    current_phase,
                    json.dumps(metadata) if metadata else None,
                    datetime.utcnow().isoformat()
                )
            )
            await db.commit()
    
    async def get_debate_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get debate status"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM debate_status WHERE session_id = ?",
                (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "session_id": row[0],
                        "status": row[1],
                        "current_phase": row[2],
                        "metadata": json.loads(row[3]) if row[3] else None,
                        "created_at": row[4],
                        "updated_at": row[5]
                    }
        return None


# Global singleton instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create the global state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
