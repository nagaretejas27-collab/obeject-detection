"""
database.py
-----------
Database management module for the Real-Time Object Detection Platform.
Handles MySQL connections, table initialization, detection event logging,
and log retrieval using mysql-connector-python and python-dotenv.
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "vision_platform")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


class DatabaseManager:
    """Manages all MySQL interactions for logging detection events."""

    def __init__(
        self,
        host: str = DB_HOST,
        user: str = DB_USER,
        password: str = DB_PASSWORD,
        database: str = DB_NAME,
        port: int = DB_PORT,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.is_connected = False
        self.fallback_logs: List[Dict] = []  # In-memory buffer if DB is offline

    def get_connection(self, include_db: bool = True):
        """Creates and returns a MySQL database connection."""
        config = {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "port": self.port,
        }
        if include_db:
            config["database"] = self.database
        return mysql.connector.connect(**config)

    def test_connection(self) -> Tuple[bool, str]:
        """Tests connection to the MySQL server and verifies database presence."""
        try:
            conn = self.get_connection(include_db=False)
            if conn.is_connected():
                cursor = conn.cursor()
                cursor.execute(f"SHOW DATABASES LIKE '{self.database}'")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                if result:
                    self.is_connected = True
                    return True, f"Connected to MySQL on {self.host}:{self.port} (Database '{self.database}' found)."
                else:
                    self.is_connected = True
                    return True, f"Connected to MySQL on {self.host}:{self.port} (Database '{self.database}' will be auto-created on init)."
            return False, "Could not establish connection."
        except Error as err:
            self.is_connected = False
            return False, f"MySQL Connection Error: {str(err)}"

    def init_db(self) -> Tuple[bool, str]:
        """Initializes database and detection_logs table if they don't already exist."""
        try:
            # 1. Connect without database to create database if missing
            conn = self.get_connection(include_db=False)
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            cursor.close()
            conn.close()

            # 2. Connect with database to create table
            conn = self.get_connection(include_db=True)
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS `detection_logs` (
                `log_id` INT AUTO_INCREMENT PRIMARY KEY,
                `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `object_class` VARCHAR(100) NOT NULL,
                `confidence` FLOAT NOT NULL,
                `bbox_x` INT NOT NULL,
                `bbox_y` INT NOT NULL,
                `bbox_w` INT NOT NULL,
                `bbox_h` INT NOT NULL,
                INDEX `idx_timestamp` (`timestamp`),
                INDEX `idx_object_class` (`object_class`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            conn.close()
            self.is_connected = True
            return True, f"Database `{self.database}` and table `detection_logs` initialized successfully."
        except Error as err:
            self.is_connected = False
            return False, f"Failed to initialize database: {str(err)}"

    def log_detection(
        self,
        object_class: str,
        confidence: float,
        bbox_x: int,
        bbox_y: int,
        bbox_w: int,
        bbox_h: int,
    ) -> bool:
        """
        Inserts a single detection event into MySQL table.
        Falls back to in-memory buffer if DB is temporarily unreachable.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = self.get_connection(include_db=True)
            cursor = conn.cursor()
            query = """
            INSERT INTO `detection_logs` 
            (`timestamp`, `object_class`, `confidence`, `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (timestamp, object_class, float(confidence), int(bbox_x), int(bbox_y), int(bbox_w), int(bbox_h))
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            self.is_connected = True
            return True
        except Error as err:
            self.is_connected = False
            # Save to fallback memory list for smooth UI operation
            self.fallback_logs.append({
                "log_id": len(self.fallback_logs) + 1,
                "timestamp": timestamp,
                "object_class": object_class,
                "confidence": round(float(confidence), 3),
                "bbox_x": int(bbox_x),
                "bbox_y": int(bbox_y),
                "bbox_w": int(bbox_w),
                "bbox_h": int(bbox_h),
                "status": "Offline Buffer",
            })
            return False

    def log_detections_batch(self, detections: List[Dict]) -> int:
        """
        Inserts multiple detection events in a single batch.
        Each detection item should have keys: object_class, confidence, bbox_x, bbox_y, bbox_w, bbox_h.
        """
        if not detections:
            return 0

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = self.get_connection(include_db=True)
            cursor = conn.cursor()
            query = """
            INSERT INTO `detection_logs` 
            (`timestamp`, `object_class`, `confidence`, `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            rows = [
                (
                    timestamp,
                    d["object_class"],
                    float(d["confidence"]),
                    int(d["bbox_x"]),
                    int(d["bbox_y"]),
                    int(d["bbox_w"]),
                    int(d["bbox_h"]),
                )
                for d in detections
            ]
            cursor.executemany(query, rows)
            conn.commit()
            inserted_count = cursor.rowcount
            cursor.close()
            conn.close()
            self.is_connected = True
            return inserted_count
        except Error:
            self.is_connected = False
            for d in detections:
                self.log_detection(
                    d["object_class"],
                    d["confidence"],
                    d["bbox_x"],
                    d["bbox_y"],
                    d["bbox_w"],
                    d["bbox_h"],
                )
            return len(detections)

    def get_recent_logs(self, limit: int = 15) -> pd.DataFrame:
        """
        Retrieves the latest detection events from MySQL as a pandas DataFrame.
        If offline, returns in-memory fallback logs.
        """
        try:
            conn = self.get_connection(include_db=True)
            query = f"""
            SELECT `log_id`, `timestamp`, `object_class`, `confidence`, `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`
            FROM `detection_logs`
            ORDER BY `log_id` DESC
            LIMIT {int(limit)}
            """
            df = pd.read_sql(query, conn)
            conn.close()
            self.is_connected = True
            if not df.empty:
                df["confidence"] = df["confidence"].apply(lambda x: f"{x:.2%}")
            return df
        except Exception:
            self.is_connected = False
            if self.fallback_logs:
                df = pd.DataFrame(self.fallback_logs[-limit:][::-1])
                return df
            return pd.DataFrame(columns=[
                "log_id", "timestamp", "object_class", "confidence",
                "bbox_x", "bbox_y", "bbox_w", "bbox_h"
            ])

    def get_statistics(self) -> Dict:
        """Retrieves count metrics for dashboard KPI display."""
        stats = {
            "total_detections": 0,
            "unique_classes": 0,
            "top_class": "N/A",
            "connected": False,
        }
        try:
            conn = self.get_connection(include_db=True)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS total FROM `detection_logs`")
            row = cursor.fetchone()
            stats["total_detections"] = row["total"] if row else 0

            cursor.execute(
                "SELECT `object_class`, COUNT(*) as cnt FROM `detection_logs` GROUP BY `object_class` ORDER BY cnt DESC LIMIT 1"
            )
            top_row = cursor.fetchone()
            if top_row:
                stats["top_class"] = f"{top_row['object_class']} ({top_row['cnt']})"

            cursor.execute("SELECT COUNT(DISTINCT `object_class`) AS unique_cnt FROM `detection_logs`")
            unique_row = cursor.fetchone()
            if unique_row:
                stats["unique_classes"] = unique_row["unique_cnt"]

            cursor.close()
            conn.close()
            stats["connected"] = True
            self.is_connected = True
            return stats
        except Exception:
            stats["connected"] = False
            stats["total_detections"] = len(self.fallback_logs)
            if self.fallback_logs:
                classes = [x["object_class"] for x in self.fallback_logs]
                stats["unique_classes"] = len(set(classes))
                if classes:
                    stats["top_class"] = max(set(classes), key=classes.count)
            return stats


# Global DatabaseManager singleton for application convenience
db_manager = DatabaseManager()
