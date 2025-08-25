import sqlite3
from config import DATABASE
from datetime import datetime

class DB_Manager:
    def __init__(self, db_name="planner.db"):
        self.db_name = db_name
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_tables(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    due_time TEXT,
                    priority TEXT CHECK(priority IN ('low','medium','high')) DEFAULT 'medium',
                    status TEXT CHECK(status IN ('active','done','expired')) DEFAULT 'active',
                    created_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()

    # Добавление пользователя
    def add_user(self, user_id: int, username: str = None):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
                (user_id, username, datetime.now().isoformat())
            )

    # Добавление задачи
    def add_task(self, user_id: int, title: str, description: str,
                 due_date: str, due_time: str, priority: str = "medium"):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tasks (user_id, title, description, due_date, due_time, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, description, due_date, due_time, priority, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    # Получение списка задач
    def list_tasks(self, user_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT task_id, title, due_date, due_time, status FROM tasks WHERE user_id=?",
                (user_id,)
            )
            return cursor.fetchall()

    # Отметка(-и) задач(-и) как выполненной(-ые)
    def mark_done(self, user_id, task_ids):
        with self.connect() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in task_ids)
            sql = f"UPDATE tasks SET status='done' WHERE user_id=? AND task_id IN ({placeholders})"
            cursor.execute(sql, (user_id, *task_ids))
            conn.commit()
            return cursor.rowcount

    # Удаление задач(-и)
    def delete_task(self, user_id, task_ids):
        with self.connect() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in task_ids)
            sql = f"DELETE FROM tasks WHERE user_id=? AND task_id IN ({placeholders})"
            cursor.execute(sql, (user_id, *task_ids))
            conn.commit()
            return cursor.rowcount

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)