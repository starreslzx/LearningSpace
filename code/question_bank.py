import sqlite3


class QuestionBankV2:
    """题目库管理器 - 支持多级分类版本"""

    def __init__(self):
        self.db_path = 'learning_space.db'
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.init_database()

    def init_database(self):
        """初始化数据库，创建多级分类表和题目表，并确保根分类存在"""
        cursor = self.conn.cursor()

        # 创建多级分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER DEFAULT 0,
                path TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建支持多级分类的题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                type TEXT DEFAULT '简答题',
                question TEXT NOT NULL,
                answer TEXT,
                difficulty INTEGER DEFAULT 3,
                needs_review BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # 初始化根分类
        cursor.execute("SELECT id FROM categories WHERE parent_id = 0 AND name = '根目录'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO categories (name, parent_id, path) VALUES ('根目录', 0, '根目录')")

        self.conn.commit()
        print("数据库v2结构初始化完成")

    def create_category(self, name, parent_id=0):
        """创建新分类，自动生成分类路径"""
        cursor = self.conn.cursor()

        # 处理父分类信息，默认使用根目录
        if parent_id == 0:
            cursor.execute("SELECT id FROM categories WHERE name = '根目录'")
            parent_id = cursor.fetchone()[0]
            parent_path = '根目录'
        else:
            cursor.execute("SELECT name, path FROM categories WHERE id = ?", (parent_id,))
            result = cursor.fetchone()
            if result:
                parent_name, parent_path = result
            else:
                cursor.execute("SELECT id FROM categories WHERE name = '根目录'")
                parent_id = cursor.fetchone()[0]
                parent_path = '根目录'

        # 插入新分类
        path = f"{parent_path}/{name}"
        cursor.execute(
            "INSERT INTO categories (name, parent_id, path) VALUES (?, ?, ?)",
            (name, parent_id, path)
        )
        category_id = cursor.lastrowid

        self.conn.commit()
        print(f"创建分类成功: {name} (ID: {category_id}), 父分类: {parent_id}")
        return category_id

    def get_categories_by_parent(self, parent_id=0):
        """获取指定父分类下的所有子分类，包含子分类数和题目数统计"""
        cursor = self.conn.cursor()

        # 定位根目录ID
        if parent_id == 0:
            cursor.execute("SELECT id FROM categories WHERE name = '根目录'")
            parent_id = cursor.fetchone()[0]

        cursor.execute('''
            SELECT c.id, c.name, c.path, 
                   (SELECT COUNT(*) FROM categories WHERE parent_id = c.id) as subcategory_count,
                   (SELECT COUNT(*) FROM questions WHERE category_id = c.id) as question_count
            FROM categories c
            WHERE c.parent_id = ?
            ORDER BY c.name
        ''', (parent_id,))

        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'subcategory_count': row[3],
                'question_count': row[4],
                'total_count': row[3] + row[4]
            })

        return categories

    def get_category_info(self, category_id):
        """获取指定分类的详细信息，包含子分类数和题目数统计"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, name, parent_id, path, 
                   (SELECT COUNT(*) FROM categories WHERE parent_id = categories.id) as subcategory_count,
                   (SELECT COUNT(*) FROM questions WHERE category_id = categories.id) as question_count
            FROM categories
            WHERE id = ?
        ''', (category_id,))

        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'parent_id': result[2],
                'path': result[3],
                'subcategory_count': result[4],
                'question_count': result[5],
                'total_count': result[4] + result[5]
            }
        return None

    def get_category_path_info(self, category_id):
        """递归获取分类的路径信息（从根到当前分类）"""
        if category_id == 0:
            return [{'id': 0, 'name': '根目录', 'path': '根目录'}]

        cursor = self.conn.cursor()
        cursor.execute('''
            WITH RECURSIVE category_path AS (
                SELECT id, name, parent_id, name as path_name, 0 as level
                FROM categories 
                WHERE id = ?
                UNION ALL
                SELECT c.id, c.name, c.parent_id, c.name, cp.level + 1
                FROM categories c
                JOIN category_path cp ON c.id = cp.parent_id
            )
            SELECT * FROM category_path ORDER BY level DESC
        ''', (category_id,))

        path_info = []
        for row in cursor.fetchall():
            path_info.append({
                'id': row[0],
                'name': row[1],
                'parent_id': row[2]
            })

        # 兜底处理：路径为空时返回根目录
        if not path_info:
            cursor.execute("SELECT id, name FROM categories WHERE name = '根目录'")
            root = cursor.fetchone()
            if root:
                path_info.append({
                    'id': root[0],
                    'name': root[1],
                    'parent_id': 0
                })

        return path_info

    def get_questions_by_category(self, category_id):
        """获取指定分类下的所有题目，按创建时间倒序排列"""
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT id, type, question, answer, difficulty, needs_review, created_at
            FROM questions
            WHERE category_id = ?
            ORDER BY created_at DESC
        ''', (category_id,))

        questions = []
        for row in cursor.fetchall():
            questions.append({
                'id': row[0],
                'type': row[1],
                'question': row[2],
                'answer': row[3] or '',
                'difficulty': row[4],
                'needs_review': bool(row[5]),
                'created_at': row[6]
            })

        return questions

    def add_question_to_category(self, category_id, question_data):
        """添加题目到指定分类，question_data包含type/question/answer/difficulty/needs_review字段"""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO questions (category_id, type, question, answer, difficulty, needs_review)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            category_id,
            question_data.get('type', '简答题'),
            question_data.get('question', ''),
            question_data.get('answer', ''),
            question_data.get('difficulty', 3),
            question_data.get('needs_review', True)
        ))

        question_id = cursor.lastrowid
        self.conn.commit()
        print(f"添加题目成功，ID: {question_id}, 分类ID: {category_id}")
        return question_id

    def get_random_questions(self, limit=10, category_id=None):
        """获取随机题目，可指定分类和数量"""
        cursor = self.conn.cursor()

        if category_id:
            cursor.execute('''
                SELECT id, type, question, answer, difficulty, needs_review
                FROM questions 
                WHERE category_id = ? 
                ORDER BY RANDOM() 
                LIMIT ?
            ''', (category_id, limit))
        else:
            cursor.execute('''
                SELECT id, type, question, answer, difficulty, needs_review
                FROM questions 
                ORDER BY RANDOM() 
                LIMIT ?
            ''', (limit,))

        questions = []
        for row in cursor.fetchall():
            questions.append({
                'id': row[0],
                'type': row[1],
                'question': row[2],
                'answer': row[3] or '',
                'difficulty': row[4],
                'needs_review': bool(row[5])
            })
        return questions

    def delete_category(self, category_id):
        """递归删除分类及其所有子分类、关联题目"""
        cursor = self.conn.cursor()

        # 递归获取所有子分类ID
        def get_all_subcategories(parent_id):
            subcategories = [parent_id]
            cursor.execute("SELECT id FROM categories WHERE parent_id = ?", (parent_id,))
            for row in cursor.fetchall():
                subcategories.extend(get_all_subcategories(row[0]))
            return subcategories

        all_categories = get_all_subcategories(category_id)

        # 删除关联题目
        placeholders = ','.join(['?'] * len(all_categories))
        cursor.execute(f"DELETE FROM questions WHERE category_id IN ({placeholders})", all_categories)

        # 逆序删除分类（先删子分类，再删父分类）
        all_categories.reverse()
        cursor.executemany("DELETE FROM categories WHERE id = ?", [(cid,) for cid in all_categories])

        self.conn.commit()
        print(f"删除分类成功，共删除 {len(all_categories)} 个分类及其题目")

    def update_category_name(self, category_id, new_name):
        """更新分类名称，并同步更新子分类的路径"""
        cursor = self.conn.cursor()

        # 获取原分类信息
        cursor.execute("SELECT parent_id, path FROM categories WHERE id = ?", (category_id,))
        result = cursor.fetchone()
        if not result:
            return False

        parent_id, old_path = result

        # 获取父分类路径
        if parent_id == 0:
            parent_path = '根目录'
        else:
            cursor.execute("SELECT path FROM categories WHERE id = ?", (parent_id,))
            parent_path_result = cursor.fetchone()
            parent_path = parent_path_result[0] if parent_path_result else '根目录'

        # 更新当前分类名称和路径
        new_path = f"{parent_path}/{new_name}"
        cursor.execute(
            "UPDATE categories SET name = ?, path = ? WHERE id = ?",
            (new_name, new_path, category_id)
        )

        # 同步更新子分类路径
        cursor.execute("SELECT id, path FROM categories WHERE path LIKE ?", (f"{old_path}/%",))
        for row in cursor.fetchall():
            sub_id, sub_path = row
            new_sub_path = sub_path.replace(old_path, new_path, 1)
            cursor.execute("UPDATE categories SET path = ? WHERE id = ?", (new_sub_path, sub_id))

        self.conn.commit()
        print(f"更新分类名称成功: {old_path} -> {new_path}")
        return True

    def search_categories(self, keyword):
        """根据关键词搜索分类（匹配名称或路径）"""
        cursor = self.conn.cursor()
        search_term = f"%{keyword}%"

        cursor.execute('''
            SELECT id, name, path, parent_id
            FROM categories 
            WHERE name LIKE ? OR path LIKE ?
            ORDER BY path
        ''', (search_term, search_term))

        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'parent_id': row[3]
            })

        return categories

    def get_statistics(self):
        """获取题库统计信息：分类总数、题目总数、根分类数"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions")
        question_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 0")
        root_category_count = cursor.fetchone()[0]

        return {
            'category_count': category_count,
            'question_count': question_count,
            'root_category_count': root_category_count
        }

    def close(self):
        """关闭数据库连接"""
        self.conn.close()