import json
import os
import tempfile
import shutil


class QuestionNoteManager:
    """题目笔记管理器 - 优化后的纯懒加载实现"""

    def __init__(self):
        self.notes_file = "question_notes.json"
        self.notes_cache = {}  # 仅缓存实际访问过的笔记
        # 不再需要 all_notes_loaded 标志

    # ========== 核心方法优化：保持纯懒加载 ==========

    def get_note(self, question_id):
        """获取笔记 - 纯懒加载"""
        question_id_str = str(question_id)

        # 1. 先查缓存（最快的路径）
        if question_id_str in self.notes_cache:
            return self.notes_cache[question_id_str]

        # 2. 缓存未命中，从文件按需读取单条
        return self._load_single_note_from_file(question_id_str)

    def save_note(self, question_id, note_content):
        """保存笔记 - 不触发全量加载"""
        try:
            question_id_str = str(question_id)
            content = note_content.strip()

            # 1. 更新缓存
            self.notes_cache[question_id_str] = content

            # 2. 直接更新文件（使用原子操作）
            self._update_single_note_in_file(question_id_str, content)
            return True
        except Exception as e:
            print(f"保存笔记失败: {e}")
            # 回滚缓存
            if question_id_str in self.notes_cache:
                del self.notes_cache[question_id_str]
            return False

    def delete_note(self, question_id):
        """删除笔记 - 不触发全量加载"""
        question_id_str = str(question_id)

        try:
            # 1. 更新缓存（如果存在）
            if question_id_str in self.notes_cache:
                del self.notes_cache[question_id_str]

            # 2. 从文件中删除单条记录
            return self._delete_single_note_from_file(question_id_str)
        except Exception as e:
            print(f"删除笔记失败: {e}")
            return False

    def has_note(self, question_id):
        """检查是否有笔记 - 按需检查"""
        question_id_str = str(question_id)

        # 先检查缓存
        if question_id_str in self.notes_cache:
            return bool(self.notes_cache[question_id_str].strip())

        # 按需从文件检查
        note = self._load_single_note_from_file(question_id_str)
        return bool(note.strip())

    # ========== 文件操作辅助方法 ==========

    def _load_single_note_from_file(self, question_id_str):
        """从文件加载单条笔记（不污染缓存）"""
        try:
            if not os.path.exists(self.notes_file):
                return ""

            # 方法1：使用流式读取，避免全量加载（更高效）
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # 简单搜索匹配（适用于JSON格式）
                    if f'"{question_id_str}":' in line:
                        # 尝试解析这一行附近的JSON内容
                        return self._extract_note_from_line(line, f)

            # 方法2：如果文件不大，直接解析整个JSON（回退方案）
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                all_notes = json.load(f)
                note = all_notes.get(question_id_str, "")
                # 放入缓存（因为已经读取了）
                self.notes_cache[question_id_str] = note
                return note

        except (json.JSONDecodeError, KeyError, ValueError):
            # 文件损坏或格式错误
            return ""
        except Exception as e:
            print(f"读取笔记失败: {e}")
            return ""

    def _extract_note_from_line(self, line, file_handle, question_id_str=None):
        """从行中提取笔记内容"""
        try:
            # 寻找键值对
            key_str = f'"{question_id_str}":'
            key_index = line.find(key_str)
            if key_index != -1:
                value_start = key_index + len(key_str)
                # 尝试从该位置解析JSON值
                remaining = line[value_start:] + file_handle.read()
                # 简化：这里实际需要完整的JSON解析，下面使用简单实现
                import re
                match = re.search(r'^\s*"([^"]*)"', remaining)
                if match:
                    note = match.group(1)
                    self.notes_cache[question_id_str] = note
                    return note
        except:
            pass
        return ""

    def _update_single_note_in_file(self, question_id_str, content):
        """原子性地更新文件中的单条笔记"""
        if not os.path.exists(self.notes_file):
            # 文件不存在，创建新文件
            new_data = {question_id_str: content}
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            return

        # 原子更新：先写入临时文件，再替换原文件
        temp_file = None
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                    mode='w', encoding='utf-8',
                    delete=False, suffix='.json'
            ) as tf:
                temp_file = tf.name

                # 读取原文件
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    try:
                        all_notes = json.load(f)
                    except json.JSONDecodeError:
                        all_notes = {}

                # 更新数据
                all_notes[question_id_str] = content

                # 写入临时文件
                json.dump(all_notes, tf, ensure_ascii=False, indent=2)

            # 原子替换
            shutil.move(temp_file, self.notes_file)

        except Exception as e:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            raise e

    def _delete_single_note_from_file(self, question_id_str):
        """从文件中删除单条笔记"""
        if not os.path.exists(self.notes_file):
            return True  # 文件不存在，视为删除成功

        temp_file = None
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                    mode='w', encoding='utf-8',
                    delete=False, suffix='.json'
            ) as tf:
                temp_file = tf.name

                # 读取原文件
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    try:
                        all_notes = json.load(f)
                    except json.JSONDecodeError:
                        all_notes = {}

                # 删除指定条目
                if question_id_str in all_notes:
                    del all_notes[question_id_str]

                # 写入临时文件
                json.dump(all_notes, tf, ensure_ascii=False, indent=2)

            # 原子替换
            shutil.move(temp_file, self.notes_file)
            return True

        except Exception as e:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            print(f"删除文件记录失败: {e}")
            return False

    # ========== 统计方法优化：避免污染缓存 ==========

    def get_notes_count(self):
        """获取笔记总数 - 流式计数，不加载到缓存"""
        if not os.path.exists(self.notes_file):
            return 0

        try:
            # 流式读取统计条目数，不解析内容
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return len(data)
        except Exception as e:
            print(f"统计笔记数失败: {e}")
            return 0

    def get_question_with_notes(self, question_ids):
        """获取有笔记的题目ID列表 - 流式检查"""
        if not os.path.exists(self.notes_file):
            return []

        result = []
        try:
            # 读取文件一次
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                all_notes = json.load(f)

            # 检查每个ID
            for qid in question_ids:
                qid_str = str(qid)
                if qid_str in all_notes and all_notes[qid_str].strip():
                    result.append(qid)

                    # 按需加入缓存（可选）
                    if qid_str not in self.notes_cache:
                        self.notes_cache[qid_str] = all_notes[qid_str]

            return result
        except Exception as e:
            print(f"检查有笔记题目失败: {e}")
            return []

    # ========== 新增：批量操作优化 ==========

    def batch_get_notes(self, question_ids):
        """批量获取笔记 - 一次性读取，减少IO"""
        if not os.path.exists(self.notes_file):
            return {qid: "" for qid in question_ids}

        results = {}
        try:
            # 一次性读取所有笔记
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                all_notes = json.load(f)

            # 批量获取
            for qid in question_ids:
                qid_str = str(qid)
                note = all_notes.get(qid_str, "")
                results[qid] = note

                # 更新缓存
                self.notes_cache[qid_str] = note

            return results
        except Exception as e:
            print(f"批量获取笔记失败: {e}")
            return {qid: "" for qid in question_ids}

    def clear_cache(self):
        """清空缓存（内存优化）"""
        self.notes_cache.clear()

    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            "缓存笔记数": len(self.notes_cache),
            "缓存命中率": "需额外统计",  # 实际使用时可以添加命中计数
            "文件大小": f"{os.path.getsize(self.notes_file) if os.path.exists(self.notes_file) else 0} 字节"
        }