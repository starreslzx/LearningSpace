import sqlite3
from components import DraggableTaskItem


class TodoManager:
    def __init__(self):
        self.conn = sqlite3.connect('learning_space.db', check_same_thread=False)
        self.create_table()
        self.refresh_tasks = None

    def create_table(self):
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
        print(f"已清空所有任务")
        if self.refresh_tasks:
            self.refresh_tasks()

    def clear_completed_tasks(self):
        """清除已完成的任务 - 保留未完成的任务"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE completed = 1')
        self.conn.commit()
        print(f"已清除 {cursor.rowcount} 个已完成任务")
        if self.refresh_tasks:
            self.refresh_tasks()

    def add_task(self, task_text, description="", priority=0):
        cursor = self.conn.cursor()
        # 获取当前最大优先级，新任务优先级为最大+1（放在最前面）
        cursor.execute('SELECT MAX(priority) FROM tasks')
        result = cursor.fetchone()
        max_priority = result[0] if result[0] is not None else 0
        new_priority = max_priority + 1

        cursor.execute(
            'INSERT INTO tasks (text, description, priority) VALUES (?, ?, ?)',
            (task_text, description, new_priority)
        )
        self.conn.commit()
        task_id = cursor.lastrowid
        print(f"添加任务: {task_text}, ID: {task_id}")
        return task_id

    def update_task(self, task_id, task_text, description=""):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE tasks SET text = ?, description = ? WHERE id = ?',
            (task_text, description, task_id)
        )
        self.conn.commit()
        print(f"更新任务 ID: {task_id}")

    def complete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE tasks SET completed = 1 WHERE id = ?',
            (task_id,)
        )
        self.conn.commit()
        print(f"完成任务 ID: {task_id}")

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()
        print(f"删除任务 ID: {task_id}")

    def load_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, text, description, completed, priority FROM tasks WHERE completed = 0 ORDER BY priority DESC, id DESC'
        )

        tasks = []
        task_data = cursor.fetchall()

        for row in task_data:
            task_id = row[0]
            text = row[1]
            description = row[2] if len(row) > 2 else ""
            completed = row[3] if len(row) > 3 else False
            priority = row[4] if len(row) > 4 else 0

            # 创建任务项并设置属性
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

        print(f"从数据库加载了 {len(tasks)} 个任务")
        return tasks

    def move_task_up(self, task_id):
        """将任务上移（增加优先级）"""
        cursor = self.conn.cursor()
        # 获取当前任务的优先级
        cursor.execute('SELECT priority FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        if result:
            current_priority = result[0] if result[0] is not None else 0
            # 增加优先级（数值越大越靠前）
            new_priority = current_priority + 1
            cursor.execute('UPDATE tasks SET priority = ? WHERE id = ?', (new_priority, task_id))
            self.conn.commit()
            if self.refresh_tasks:
                self.refresh_tasks()

    def move_task_down(self, task_id):
        """将任务下移（降低优先级）"""
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
