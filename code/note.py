import json
import os
import tempfile
import shutil


class QuestionNoteManager:
    """题目笔记管理器"""
    def __init__(self):
        self.notes_file = "question_notes.json"
        self.notes_cache = {}

    def get_note(self, question_id):
        """获取笔记"""
        question_id_str = str(question_id)
        if question_id_str in self.notes_cache:
            return self.notes_cache[question_id_str]
        return self._load_single_note_from_file(question_id_str)

    def save_note(self, question_id, note_content):
        """保存笔记"""
        try:
            question_id_str = str(question_id)
            content = note_content.strip()
            self.notes_cache[question_id_str] = content
            self._update_single_note_in_file(question_id_str, content)
            return True
        except Exception as e:
            print(f"保存笔记失败: {e}")
            return False

    def delete_note(self, question_id):
        """删除笔记"""
        question_id_str = str(question_id)
        try:
            if question_id_str in self.notes_cache:
                del self.notes_cache[question_id_str]
            return self._delete_single_note_from_file(question_id_str)
        except Exception as e:
            print(f"删除笔记失败: {e}")
            return False

    def has_note(self, question_id):
        """检查是否有笔记"""
        question_id_str = str(question_id)
        if question_id_str in self.notes_cache:
            return bool(self.notes_cache[question_id_str].strip())
        note = self._load_single_note_from_file(question_id_str)
        return bool(note.strip())

    def _load_single_note_from_file(self, question_id_str):
        """从文件加载单条笔记"""
        try:
            if not os.path.exists(self.notes_file):
                return ""
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                all_notes = json.load(f)
                note = all_notes.get(question_id_str, "")
                self.notes_cache[question_id_str] = note
                return note
        except (json.JSONDecodeError, KeyError, ValueError):
            return ""
        except Exception as e:
            print(f"读取笔记失败: {e}")
            return ""

    def _update_single_note_in_file(self, question_id_str, content):
        """原子性地更新文件中的单条笔记"""
        if not os.path.exists(self.notes_file):
            new_data = {question_id_str: content}
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            return

        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json') as tf:
                temp_file = tf.name
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    try:
                        all_notes = json.load(f)
                    except json.JSONDecodeError:
                        all_notes = {}
                all_notes[question_id_str] = content
                json.dump(all_notes, tf, ensure_ascii=False, indent=2)
            shutil.move(temp_file, self.notes_file)
        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            raise e

    def _delete_single_note_from_file(self, question_id_str):
        """从文件中删除单条笔记"""
        if not os.path.exists(self.notes_file):
            return True

        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json') as tf:
                temp_file = tf.name
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    try:
                        all_notes = json.load(f)
                    except json.JSONDecodeError:
                        all_notes = {}
                if question_id_str in all_notes:
                    del all_notes[question_id_str]
                json.dump(all_notes, tf, ensure_ascii=False, indent=2)
            shutil.move(temp_file, self.notes_file)
            return True
        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            print(f"删除文件记录失败: {e}")
            return False

    def get_notes_count(self):
        """获取笔记总数"""
        if not os.path.exists(self.notes_file):
            return 0
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return len(data)
        except Exception as e:
            print(f"统计笔记数失败: {e}")
            return 0

    def get_question_with_notes(self, question_ids):
        """获取有笔记的题目ID列表"""
        if not os.path.exists(self.notes_file):
            return []
        result = []
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                all_notes = json.load(f)
            for qid in question_ids:
                qid_str = str(qid)
                if qid_str in all_notes and all_notes[qid_str].strip():
                    result.append(qid)
                    if qid_str not in self.notes_cache:
                        self.notes_cache[qid_str] = all_notes[qid_str]
            return result
        except Exception as e:
            print(f"检查有笔记题目失败: {e}")
            return []

    def batch_get_notes(self, question_ids):
        """批量获取笔记"""
        if not os.path.exists(self.notes_file):
            return {qid: "" for qid in question_ids}
        results = {}
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                all_notes = json.load(f)
            for qid in question_ids:
                qid_str = str(qid)
                note = all_notes.get(qid_str, "")
                results[qid] = note
                self.notes_cache[qid_str] = note
            return results
        except Exception as e:
            print(f"批量获取笔记失败: {e}")
            return {qid: "" for qid in question_ids}

    def clear_cache(self):
        """清空缓存"""
        self.notes_cache.clear()

    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            "缓存笔记数": len(self.notes_cache),
            "文件大小": f"{os.path.getsize(self.notes_file) if os.path.exists(self.notes_file) else 0} 字节"
        }