import sqlite3
from components import DraggableTaskItem


class TodoManager:
    """待办事项管理器"""

    def __init__(self):
        self.conn = sqlite3.connect('learning_space.db', check_same_thread=False)
        self.create_table()
        self.refresh_tasks = None

    def create_table(self):
        """创建任务表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                description TEXT DEFAULT '',
                completed BOOLEAN NOT NULL DEFAULT 0,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def clear_all_tasks(self):
        """清空所有任务"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks')
        self.conn.commit()
        if self.refresh_tasks:
            self.refresh_tasks()

    def clear_completed_tasks(self):
        """清除已完成的任务"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE completed = 1')
        self.conn.commit()
        if self.refresh_tasks:
            self.refresh_tasks()

    def add_task(self, task_text, description="", priority=0):
        """添加任务"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(priority) FROM tasks')
        result = cursor.fetchone()
        max_priority = result[0] if result[0] is not None else 0
        new_priority = max_priority + 1

        cursor.execute('INSERT INTO tasks (text, description, priority) VALUES (?, ?, ?)',
                       (task_text, description, new_priority))
        self.conn.commit()
        task_id = cursor.lastrowid

        if self.refresh_tasks:
            self.refresh_tasks()

        return task_id

    def update_task(self, task_id, task_text, description=""):
        """更新任务"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE tasks SET text = ?, description = ? WHERE id = ?',
                       (task_text, description, task_id))
        self.conn.commit()

        if self.refresh_tasks:
            self.refresh_tasks()

    def complete_task(self, task_id):
        """完成任务"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (task_id,))
        self.conn.commit()

        if self.refresh_tasks:
            self.refresh_tasks()

    def delete_task(self, task_id):
        """删除任务"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()

        if self.refresh_tasks:
            self.refresh_tasks()

    def load_tasks(self):
        """加载任务"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, text, description, completed, priority FROM tasks WHERE completed = 0 ORDER BY priority DESC, id DESC')
        task_data = cursor.fetchall()

        tasks = []
        for row in task_data:
            task_id, text, description, completed, priority = row
            task_item = DraggableTaskItem()
            task_item.setup(
                task_id=task_id,
                text=text,
                description=description,
                completed=bool(completed),
                todo_manager=self,
                refresh_callback=self.refresh_tasks
            )
            tasks.append(task_item)

        return tasks

    def move_task_up(self, task_id):
        """将任务上移"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT priority FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        if result:
            current_priority = result[0] if result[0] is not None else 0
            new_priority = current_priority + 1
            cursor.execute('UPDATE tasks SET priority = ? WHERE id = ?', (new_priority, task_id))
            self.conn.commit()
            if self.refresh_tasks:
                self.refresh_tasks()

    def move_task_down(self, task_id):
        """将任务下移"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT priority FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        if result:
            current_priority = result[0] if result[0] is not None else 0
            new_priority = max(0, current_priority - 1)
            cursor.execute('UPDATE tasks SET priority = ? WHERE id = ?', (new_priority, task_id))
            self.conn.commit()
            if self.refresh_tasks:
                self.refresh_tasks()