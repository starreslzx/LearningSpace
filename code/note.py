import json
import os
import json
import os


class QuestionNoteManager:
    """题目笔记管理器 - 按需加载单个笔记"""

    def __init__(self):
        self.notes_file = "question_notes.json"
        self.notes_cache = {}  # 缓存已加载的笔记
        self.all_notes_loaded = False  # 标记是否已加载所有笔记

    def _lazy_load_all_notes(self):
        """懒加载所有笔记到缓存（只在需要时调用）"""
        if self.all_notes_loaded:
            return

        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.notes_cache = json.load(f)
                self.all_notes_loaded = True
                print(f"已加载 {len(self.notes_cache)} 条笔记到缓存")
            else:
                # 文件不存在，创建空文件
                self._save_all_notes()
        except Exception as e:
            print(f"加载笔记文件失败: {e}")
            self.notes_cache = {}
            self.all_notes_loaded = True

    def _load_single_note(self, question_id):
        """按需加载单个题目的笔记"""
        question_id_str = str(question_id)

        # 如果已经在缓存中，直接返回
        if question_id_str in self.notes_cache:
            return self.notes_cache[question_id_str]

        try:
            # 尝试从文件读取单个笔记
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    all_notes = json.load(f)
                    note = all_notes.get(question_id_str, "")
                    # 放入缓存
                    self.notes_cache[question_id_str] = note
                    return note
        except Exception as e:
            print(f"读取笔记文件失败: {e}")

        return ""

    def _save_all_notes(self):
        """保存所有笔记到文件"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存笔记失败: {e}")

    def get_note(self, question_id):
        """获取题目笔记 - 按需加载"""
        question_id_str = str(question_id)

        # 先检查缓存
        if question_id_str in self.notes_cache:
            return self.notes_cache[question_id_str]

        # 按需加载
        return self._load_single_note(question_id)

    def save_note(self, question_id, note_content):
        """保存题目笔记"""
        try:
            question_id_str = str(question_id)
            self.notes_cache[question_id_str] = note_content.strip()
            self._save_all_notes()
            return True
        except Exception as e:
            print(f"保存笔记失败: {e}")
            return False

    def delete_note(self, question_id):
        """删除题目笔记"""
        try:
            question_id_str = str(question_id)
            if question_id_str in self.notes_cache:
                del self.notes_cache[question_id_str]
                self._save_all_notes()
                print(f"删除了题目 {question_id} 的笔记")
                return True
            else:
                # 如果不在缓存中，先加载所有笔记
                self._lazy_load_all_notes()
                if question_id_str in self.notes_cache:
                    del self.notes_cache[question_id_str]
                    self._save_all_notes()
                    return True
        except Exception as e:
            print(f"删除笔记失败: {e}")
        return False

    def has_note(self, question_id):
        """检查题目是否有笔记"""
        question_id_str = str(question_id)

        # 先检查缓存
        if question_id_str in self.notes_cache:
            return bool(self.notes_cache[question_id_str].strip())

        # 按需加载并检查
        note = self._load_single_note(question_id)
        return bool(note.strip())

    def get_notes_count(self):
        """获取笔记总数 - 需要时加载所有笔记"""
        if not self.all_notes_loaded:
            self._lazy_load_all_notes()
        return len(self.notes_cache)

    def get_question_with_notes(self, question_ids):
        """获取有笔记的题目ID列表 - 需要时加载所有笔记"""
        if not self.all_notes_loaded:
            self._lazy_load_all_notes()

        result = []
        for qid in question_ids:
            if str(qid) in self.notes_cache:
                result.append(qid)
        return result
