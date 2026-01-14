"""
History Storage - Save analysis history (key points only)
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class HistoryStorage:
    """Stores analysis history with key points only."""
    
    def __init__(self, db_path: str = "aether_history.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                input_preview TEXT,
                factors_count INTEGER,
                final_report TEXT,
                key_points TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, result: Dict) -> int:
        """Save analysis with key points extracted."""
        
        # Extract key points
        key_points = self._extract_key_points(result)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get input preview
        input_preview = ""
        if 'all_messages' in result:
            for msg in result['all_messages']:
                if msg.get('type') == 'FACTOR_LIST':
                    # Try to get original input from somewhere
                    input_preview = "Document analyzed"
                    break
        
        factors_count = len(result.get('factors', []))
        final_report = result.get('final_report', {}).get('report', '')
        
        cursor.execute("""
            INSERT INTO analyses (timestamp, input_preview, factors_count, final_report, key_points)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            input_preview[:200],
            factors_count,
            final_report[:5000],  # Limit size
            json.dumps(key_points)
        ))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return analysis_id
    
    def _extract_key_points(self, result: Dict) -> List[str]:
        """Extract key points from analysis result."""
        key_points = []
        
        # Extract factors
        factors = result.get('factors', [])
        for factor in factors:
            key_points.append(f"Factor: {factor.get('name', 'Unknown')}")
        
        # Extract final verdict if available
        final_report = result.get('final_report', {}).get('report', '')
        if final_report:
            # Try to extract verdict section
            if "Final Verdict" in final_report:
                verdict_section = final_report.split("Final Verdict")[-1][:200]
                key_points.append(f"Verdict: {verdict_section.strip()}")
        
        # Extract top recommendations
        if "Actionable Recommendations" in final_report:
            rec_section = final_report.split("Actionable Recommendations")[-1].split("\n\n")[0][:300]
            key_points.append(f"Recommendations: {rec_section.strip()}")
        
        return key_points[:10]  # Limit to 10 key points
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get analysis history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, input_preview, factors_count, key_points, created_at
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "timestamp": row[1],
                "input_preview": row[2],
                "factors_count": row[3],
                "key_points": json.loads(row[4]) if row[4] else [],
                "created_at": row[5]
            })
        
        return history
    
    def get_analysis(self, analysis_id: int) -> Optional[Dict]:
        """Get a specific analysis by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, input_preview, factors_count, final_report, key_points, created_at
            FROM analyses
            WHERE id = ?
        """, (analysis_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "timestamp": row[1],
            "input_preview": row[2],
            "factors_count": row[3],
            "final_report": row[4],
            "key_points": json.loads(row[5]) if row[5] else [],
            "created_at": row[6]
        }

