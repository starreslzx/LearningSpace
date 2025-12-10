import os
import re
import json
import time
from typing import List, Dict, Any
import tempfile
import hashlib
from threading import Lock, Event
from openai import OpenAI
from datetime import datetime
import logging

# 图片处理相关导入
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

# 从config.py导入API密钥
try:
    from config import API_KEY
except ImportError:
    print("警告: 未找到config.py文件或API_KEY配置")
    API_KEY = None

# 关闭PDF解析库的调试日志
logging.getLogger('pdfplumber').setLevel(logging.WARNING)
logging.getLogger('PyPDF2').setLevel(logging.WARNING)
logging.getLogger('pdfminer').setLevel(logging.WARNING)


class AIAssistant:
    """
    AI助手类 - 负责与大型语言模型交互，提取和处理题目
    基于ModelScope API实现，支持文本/PDF/图片题目提取
    """

    def __init__(self, api_keys: List[str] = None, base_url: str = None,
                 model: str = "Qwen/Qwen2.5-Coder-32B-Instruct",
                 questions_dir: str = "questions_library",
                 stream: bool = True):
        """
        初始化AI助手

        Args:
            api_keys: API密钥列表，支持多个密钥轮换使用（保持接口不变，但内部简化为只使用第一个）
            base_url: API基础URL
            model: 使用的模型名称
            questions_dir: 题目库目录
            stream: 是否使用流式输出
        """
        # 处理API密钥 - 保持接口兼容性
        if api_keys is None:
            # 首先尝试从config.py导入的API_KEY
            if API_KEY:
                api_keys = [API_KEY]
            else:
                # 然后尝试环境变量
                env_keys = os.getenv('MODELSCOPE_API_KEY', '')
                if env_keys:
                    api_keys = [key.strip() for key in env_keys.split(',') if key.strip()]
                else:
                    api_keys = []

        if not api_keys:
            raise ValueError(
                "错误: 未找到API密钥。请确保：\n"
                "1. 在config.py中设置API_KEY变量\n"
                "2. 或设置MODELSCOPE_API_KEY环境变量\n"
                "3. 或直接传入api_keys参数"
            )

        # 保持原有的api_keys属性，但内部只使用第一个
        self.api_keys = api_keys
        self.base_url = base_url or "https://api-inference.modelscope.cn/v1/"
        self.model = model
        self.questions_dir = questions_dir
        self.stream = stream

        # 创建题目库目录
        os.makedirs(self.questions_dir, exist_ok=True)
        print(f"题目库目录: {os.path.abspath(self.questions_dir)}")
        print(f"流式输出: {'启用' if self.stream else '禁用'}")
        print(f"使用模型: {self.model}")

        # 创建OpenAI客户端（只使用第一个API密钥）
        self.client = OpenAI(
            api_key=self.api_keys[0],
            base_url=self.base_url
        )

        # API调用管理 - 简化为简单的间隔控制
        self.last_api_call_time = 0
        self.min_call_interval = 2.0  # API调用最小间隔
        self.api_call_lock = Lock()

        # 客户端使用统计（保持原有接口）
        self.client_stats = {0: {'success': 0, 'failures': 0, 'last_used': 0}}
        self.current_client_index = 0

        # 缓存已处理的文件，避免重复处理
        self.file_cache = {}

        # 新增：取消标志
        self.cancel_event = Event()
        self.is_cancelled = False

        print(f"AI助手初始化完成，已加载 {len(self.api_keys)} 个API密钥（使用第一个）")
        print(f"API调用间隔: {self.min_call_interval}秒")

    # ==================== 新增：取消控制方法 ====================

    def cancel_processing(self):
        """取消当前处理"""
        print("收到取消请求，正在停止处理...")
        self.cancel_event.set()
        self.is_cancelled = True

    def reset_cancel(self):
        """重置取消标志"""
        self.cancel_event.clear()
        self.is_cancelled = False

    def check_cancelled(self):
        """检查是否已取消"""
        if self.is_cancelled or self.cancel_event.is_set():
            raise Exception("处理已被用户取消")
        return False

    # ==================== 保持原有接口的方法 ====================

    def process_file_and_save_questions(self, file_path: str, file_type: str,
                                        target_dir: str = None,
                                        max_chunk_size: int = 800,
                                        progress_callback=None) -> Dict[str, Any]:
        """
        处理文件并保存题目到指定目录（支持文本/PDF/图片）
        """
        if target_dir is None:
            target_dir = self.questions_dir

        os.makedirs(target_dir, exist_ok=True)

        questions = self.process_large_file_and_extract_questions(
            file_path, file_type, max_chunk_size, progress_callback
        )

        result = self.save_questions_to_directory(questions, target_dir, os.path.basename(file_path))

        return result

    def save_questions_to_directory(self, questions: List[Dict[str, Any]],
                                    target_dir: str, source_filename: str) -> Dict[str, Any]:
        """
        保存题目到目录
        """
        if not questions:
            return {
                "success": False,
                "message": "没有题目可保存",
                "saved_count": 0,
                "target_dir": target_dir
            }

        try:
            source_name = os.path.splitext(source_filename)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            question_subdir = os.path.join(target_dir, f"{source_name}_{timestamp}")
            os.makedirs(question_subdir, exist_ok=True)

            saved_files = []
            for i, question in enumerate(questions):
                question_type = question.get('type', 'unknown').replace('/', '_')
                category = question.get('category', 'unknown').replace('/', '_')
                filename = f"Q{i + 1:03d}_{question_type}_{category}.json"
                filepath = os.path.join(question_subdir, filename)

                question_with_meta = question.copy()
                question_with_meta['_metadata'] = {
                    'source_file': source_filename,
                    'extraction_time': datetime.now().isoformat(),
                    'question_id': f"Q{i + 1:03d}",
                    'file_path': filepath
                }

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(question_with_meta, f, ensure_ascii=False, indent=2)

                saved_files.append(filepath)

            summary_file = os.path.join(question_subdir, "questions_summary.json")
            summary = {
                "source_file": source_filename,
                "extraction_time": datetime.now().isoformat(),
                "total_questions": len(questions),
                "questions_summary": [
                    {
                        "question_id": f"Q{i + 1:03d}",
                        "type": q.get('type', 'unknown'),
                        "category": q.get('category', 'unknown'),
                        "difficulty": q.get('difficulty', 3),
                        "file": os.path.basename(saved_files[i])
                    }
                    for i, q in enumerate(questions)
                ]
            }

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            self.update_questions_library_index(target_dir)

            return {
                "success": True,
                "message": f"成功保存 {len(questions)} 道题目",
                "saved_count": len(questions),
                "target_dir": question_subdir,
                "summary_file": summary_file,
                "question_files": saved_files
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"保存题目失败: {str(e)}",
                "saved_count": 0,
                "target_dir": target_dir
            }

    def update_questions_library_index(self, library_dir: str):
        """
        更新题目库索引
        """
        try:
            index_file = os.path.join(library_dir, "library_index.json")
            index_data = {
                "last_updated": datetime.now().isoformat(),
                "total_collections": 0,
                "collections": []
            }

            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)

            collections = []
            for item in os.listdir(library_dir):
                item_path = os.path.join(library_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    summary_file = os.path.join(item_path, "questions_summary.json")
                    if os.path.exists(summary_file):
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary = json.load(f)
                            collections.append({
                                "name": item,
                                "path": item_path,
                                "source_file": summary.get("source_file", "unknown"),
                                "extraction_time": summary.get("extraction_time", ""),
                                "question_count": summary.get("total_questions", 0)
                            })

            index_data["collections"] = collections
            index_data["total_collections"] = len(collections)
            index_data["last_updated"] = datetime.now().isoformat()

            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

            print(f"题目库索引已更新，共有 {len(collections)} 个题目集合")

        except Exception as e:
            print(f"更新题目库索引失败: {e}")

    def process_large_file_and_extract_questions(self, file_path: str, file_type: str,
                                                 max_chunk_size: int = 800,
                                                 progress_callback=None) -> List[Dict[str, Any]]:
        """
        处理大文件并提取所有题目（支持文本/PDF/图片）
        """
        try:
            # 重置取消标志
            self.reset_cancel()

            file_hash = self.get_file_hash(file_path)
            if file_hash in self.file_cache:
                print("使用缓存的处理结果")
                return self.file_cache[file_hash]

            print(f"开始处理文件: {file_path}")

            # 1. 读取文件内容 - 检查取消
            self.check_cancelled()
            content = self.extract_text_from_file(file_path, file_type)
            print(f"原始内容长度: {len(content)} 字符")
            if not content or len(content.strip()) == 0:
                print("文件内容为空")
                return []

            # 2. 预处理内容 - 检查取消
            self.check_cancelled()
            processed_content = self.preprocess_content(content)
            if not processed_content:
                print("内容预处理后为空")
                return []

            print(f"预处理后内容长度: {len(processed_content)} 字符")

            # 3. 分割内容 - 检查取消
            self.check_cancelled()
            chunks = self.split_content_into_chunks(processed_content, max_chunk_size)
            print(f"将内容分割成 {len(chunks)} 个块")

            if progress_callback:
                progress_callback(0, f"文件已分割成 {len(chunks)} 个块")

            # 4. 处理每个块 - 每个块都检查取消
            all_questions = []
            for i, chunk in enumerate(chunks):
                # 检查是否已取消
                try:
                    self.check_cancelled()
                except Exception as e:
                    print(f"处理被取消: {e}")
                    return all_questions  # 返回已处理的题目

                if progress_callback:
                    progress_callback((i + 1) / len(chunks) * 100, f"正在处理第 {i + 1}/{len(chunks)} 个块...")

                print(f"处理第 {i + 1}/{len(chunks)} 个块 (长度: {len(chunk)} 字符)...")
                chunk_questions = self.extract_questions_from_chunk(chunk, i + 1)
                all_questions.extend(chunk_questions)

                # 添加延迟避免API限制 - 检查取消
                if i < len(chunks) - 1:
                    time.sleep(1)

            # 5. 后处理和过滤 - 检查取消
            self.check_cancelled()
            filtered_questions = self.post_process_questions(all_questions)
            print(f"提取到 {len(all_questions)} 道题目，过滤后剩余 {len(filtered_questions)} 道")

            self.file_cache[file_hash] = filtered_questions
            return filtered_questions

        except Exception as e:
            if "处理已被用户取消" in str(e):
                print("用户取消了文件处理")
                return []
            else:
                print(f"处理文件失败: {e}")
                import traceback
                traceback.print_exc()
                return []

    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        从文件中提取文本内容（扩展支持图片）
        """
        try:
            if file_type == 'file' or file_type == 'text':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            elif file_type == 'pdf':
                return self.extract_text_from_pdf(file_path)
            elif file_type == 'image':
                return self.extract_text_from_image(file_path)
            else:
                print(f"暂不支持的文件类型: {file_type}")
                return ""
        except Exception as e:
            print(f"提取文件文本失败: {e}")
            return ""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        从PDF提取文本
        """
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            print("请安装pdfplumber: pip install pdfplumber")
            return ""
        except Exception as e:
            print(f"PDF文本提取失败: {e}")
            return ""

    def extract_text_from_image(self, image_path: str, lang: str = 'chi_sim+eng') -> str:
        """
        从图片提取文本（OCR），支持中文+英文混合识别
        """
        try:
            img = Image.open(image_path)
            img = self.preprocess_image_for_ocr(img)
            text = pytesseract.image_to_string(img, lang=lang)
            text = text.replace('\x0c', '').strip()
            print(f"图片OCR识别完成，提取文本长度: {len(text)} 字符")
            return text
        except ImportError:
            print("请安装pytesseract和Pillow: pip install pytesseract pillow")
            print("并安装Tesseract OCR引擎:")
            print("  - Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("  - macOS: brew install tesseract tesseract-lang")
            print("  - Linux: sudo apt-get install tesseract-ocr tesseract-ocr-chinese-simplified")
            return ""
        except Exception as e:
            print(f"图片OCR识别失败: {e}")
            return ""

    def preprocess_image_for_ocr(self, img: Image.Image) -> Image.Image:
        """
        图片预处理，提高OCR识别准确率
        """
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter())
        threshold = 128
        img = img.point(lambda x: 255 if x > threshold else 0)
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        return img

    def preprocess_content(self, content: str) -> str:
        """
        内容预处理
        """
        if not content:
            return ""

        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[^\w\u4e00-\u9fff\s\.,\?\!，。？！：；""''\(\)\[\]\-\+\*/=<>]', '', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)

        return content.strip()

    def split_content_into_chunks(self, content: str, max_chunk_size: int) -> List[str]:
        """
        智能分割内容为更小的块
        """
        if len(content) <= max_chunk_size:
            return [content]

        print(f"内容长度: {len(content)} 字符，最大块大小: {max_chunk_size} 字符")

        chunks_fixed = self._split_fixed_length(content, max_chunk_size)
        print(f"按固定长度分割成 {len(chunks_fixed)} 个块")
        return chunks_fixed


    def _split_fixed_length(self, content: str, max_chunk_size: int) -> List[str]:
        """固定长度分割，但尽量在合理位置分割"""
        chunks = []
        start = 0

        while start < len(content):
            end = start + max_chunk_size

            if end >= len(content):
                chunks.append(content[start:])
                break

            for split_point in range(end, start, -1):
                if split_point >= len(content):
                    continue

                char = content[split_point]
                prev_char = content[split_point - 1] if split_point > 0 else ''

                if prev_char in '。！？.!?':
                    end = split_point
                    break
                elif char == '\n' and split_point - start > max_chunk_size * 0.8:
                    end = split_point
                    break
                elif char in '，,;；:' and split_point - start > max_chunk_size * 0.8:
                    end = split_point
                    break
                elif char in ' \t' and split_point - start > max_chunk_size * 0.9:
                    end = split_point
                    break

            chunks.append(content[start:end])
            start = end

        return chunks

    def extract_questions_from_chunk(self, chunk: str, chunk_number: int) -> List[Dict[str, Any]]:
        """
        从内容块中提取题目
        """
        if chunk is None:
            print(f"第{chunk_number}块: chunk为None，跳过处理")
            return []

        chunk = str(chunk).strip()
        if not chunk or len(chunk) < 10:
            print(f"第{chunk_number}块: 内容太短或为空，跳过处理")
            return []

        prompt = self.build_extraction_prompt(chunk, chunk_number)

        if prompt is None:
            print(f"第{chunk_number}块: 提示词生成失败")
            return []

        print(f"\n=== 第{chunk_number}块提取提示 (长度: {len(chunk)} 字符) ===")
        print(f"提示词长度: {len(prompt)} 字符")

        try:
            # 检查是否已取消
            self.check_cancelled()

            if self.stream:
                print(f"\n--- 第{chunk_number}块AI响应 ---")
                response = self.call_ai_api_stream(prompt)
                print(f"\n--- 第{chunk_number}块处理完成 ---")
            else:
                response = self.call_ai_api(prompt)
                print(f"第{chunk_number}块AI返回结果长度: {len(response)} 字符")

            questions = self.parse_ai_response(response, chunk_number)
            print(f"第{chunk_number}块提取到 {len(questions)} 道题目")
            return questions

        except Exception as e:
            if "处理已被用户取消" in str(e):
                raise e  # 重新抛出取消异常
            print(f"第{chunk_number}块提取题目失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def build_extraction_prompt(self, chunk: str, chunk_number: int) -> str:
        """
        构建题目提取提示词
        """
        chunk_str = str(chunk) if chunk is not None else ""
        max_chunk_length = 2000
        if len(chunk_str) > max_chunk_length:
            chunk_str = chunk_str[:max_chunk_length] + "... [内容已截断]"

        return f"""
你是一个专业的题目提取助手。请从以下文本中分解成若干所有完整的题目：

提取要求：
1. 只提取完整的题目，对于不完整的片段可以根据你的知识完善题目、选项和解答,但是不能返回残缺的题目
2. 返回有效的JSON数组格式
3. 每个题目包含以下字段：
   - type: 题目类型（选择题、填空题、简答题、计算题等）
   - category: 题目分类（数学、编程、物理、语文等）
   - question: 完整的题目内容
   - answer: 参考答案或解题思路
   - difficulty: 难度等级（1-100）

4. 如果题目有选项，请包含在question字段中，如果题目本身有答案，要从question中删除，放入answer,并且在questin被挖掉的地方用下划线替代，
5. 如果文本中没有题目，返回空数组[]
6. 由于要用于app呈现，对于一个问题除题目与选项、选项与选项之间必须有换行符，其余必须均删除，请你做出相应修改
7. 如果是可以背记的知识点，可以放入question,answer填略
文本内容（第{chunk_number}部分）
"{chunk_str}"

请严格按以下JSON格式返回，不要有其他文字：

[
  {{
    "type": "题目类型",
    "category": "分类名称", 
    "question": "完整题目",
    "answer": "答案",
    "notes": "笔记",
    "difficulty": 难度
  }}
]
"""

    def call_ai_api(self, prompt: str, max_retries: int = 3) -> str:
        """
        调用AI API（非流式）- 简化版本
        """
        for attempt in range(max_retries):
            try:
                # 检查是否已取消
                self.check_cancelled()

                # 确保间隔时间
                with self.api_call_lock:
                    current_time = time.time()
                    time_since_last_call = current_time - self.last_api_call_time

                    if time_since_last_call < self.min_call_interval:
                        wait_time = self.min_call_interval - time_since_last_call
                        print(f"API调用频率控制，等待 {wait_time:.2f} 秒...")
                        time.sleep(wait_time)

                    print(f"调用API (尝试 {attempt + 1}/{max_retries})...")

                    # 调用API（非流式）
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一个专业的题目提取助手，请严格按照要求的JSON格式返回结果。"
                            },
                            {
                                "role": "user",
                                "content": prompt if prompt else ""
                            }
                        ],
                        temperature=0.1,
                        max_tokens=4000,
                        stream=False
                    )

                    # 更新最后调用时间和统计
                    self.last_api_call_time = time.time()
                    self.client_stats[self.current_client_index]['last_used'] = time.time()
                    self.client_stats[self.current_client_index]['success'] += 1

                content = response.choices[0].message.content

                if content:
                    return content
                else:
                    raise Exception("API返回内容为空")

            except Exception as e:
                print(f"API请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                self.client_stats[self.current_client_index]['failures'] += 1
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

        raise Exception("所有API请求尝试失败")

    def call_ai_api_stream(self, prompt: str, max_retries: int = 3) -> str:
        """
        调用AI API（流式）- 简化版本
        """
        for attempt in range(max_retries):
            try:
                # 检查是否已取消
                self.check_cancelled()

                # 确保间隔时间
                with self.api_call_lock:
                    current_time = time.time()
                    time_since_last_call = current_time - self.last_api_call_time

                    if time_since_last_call < self.min_call_interval:
                        wait_time = self.min_call_interval - time_since_last_call
                        print(f"API调用频率控制，等待 {wait_time:.2f} 秒...")
                        time.sleep(wait_time)

                    print(f"调用API (流式, 尝试 {attempt + 1}/{max_retries})...")

                    # 调用API（流式）
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "你是一个专业的题目提取助手，请严格按照要求的JSON格式返回结果。"
                            },
                            {
                                "role": "user",
                                "content": prompt if prompt else ""
                            }
                        ],
                        stream=True,
                        temperature=0.1,
                        max_tokens=4000
                    )

                    # 更新最后调用时间和统计
                    self.last_api_call_time = time.time()
                    self.client_stats[self.current_client_index]['last_used'] = time.time()

                # 收集流式响应
                full_response = ""
                for chunk in response:
                    # 检查是否已取消（在每个chunk之间）
                    self.check_cancelled()

                    if chunk.choices[0].delta.content is not None:
                        content_chunk = chunk.choices[0].delta.content
                        print(content_chunk, end='', flush=True)
                        full_response += content_chunk

                print()

                if full_response:
                    self.client_stats[self.current_client_index]['success'] += 1
                    return full_response
                else:
                    raise Exception("API返回内容为空")

            except Exception as e:
                print(f"API流式请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                self.client_stats[self.current_client_index]['failures'] += 1
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

        raise Exception("所有API流式请求尝试失败")

    def parse_ai_response(self, response: str, chunk_number: int) -> List[Dict[str, Any]]:
        """
        解析AI响应
        """
        try:
            cleaned_response = self.clean_ai_response(response)

            if not cleaned_response or cleaned_response.strip() == "":
                print(f"第{chunk_number}块: AI返回内容为空")
                return []

            try:
                questions = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                print(f"第{chunk_number}块: JSON解析失败，尝试修复...")
                questions = self.try_fix_json(response)

                if questions is None:
                    print(f"第{chunk_number}块: 无法修复JSON，返回空列表")
                    return []

            if not isinstance(questions, list):
                print(f"第{chunk_number}块: AI返回格式错误，期望列表，得到 {type(questions)}")
                return []

            return questions

        except Exception as e:
            print(f"第{chunk_number}块: 解析响应失败: {e}")
            print(f"原始响应: {response[:500]}...")
            return []

    def try_fix_json(self, response: str):
        """
        尝试修复JSON格式
        """
        try:
            start = response.find('[')
            end = response.rfind(']')

            if start != -1 and end != -1 and end > start:
                json_str = response[start:end + 1]
                return json.loads(json_str)

            patterns = [
                r'```json\s*(\[.*?\])\s*```',
                r'```\s*(\[.*?\])\s*```',
                r'JSON:\s*(\[.*?\])',
                r'输出:\s*(\[.*?\])',
            ]

            for pattern in patterns:
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        continue

        except Exception as e:
            print(f"修复JSON失败: {e}")

        return None

    def clean_ai_response(self, response: str) -> str:
        """
        清理AI响应，提取JSON部分
        """
        if not response:
            return ""

        response = response.strip()

        try:
            json.loads(response)
            return response
        except:
            pass

        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            extracted = json_match.group()
            extracted = re.sub(r'^[^{[]*', '', extracted)
            extracted = re.sub(r'[^}\]]*$', '', extracted)
            return extracted

        return ""

    def post_process_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        后处理题目列表
        """
        if not questions:
            return []

        filtered_questions = [q for q in questions if self.is_complete_question(q)]
        print(f"完整性过滤: {len(questions)} -> {len(filtered_questions)}")

        unique_questions = self.deduplicate_questions(filtered_questions)
        print(f"去重过滤: {len(filtered_questions)} -> {len(unique_questions)}")

        for question in unique_questions:
            if 'difficulty' in question:
                try:
                    difficulty = int(question['difficulty'])
                    question['difficulty'] = max(1, min(5, difficulty))
                except:
                    question['difficulty'] = 3

        return unique_questions

    def is_complete_question(self, question: Dict[str, Any]) -> bool:
        """
        检查题目是否完整
        """
        required_fields = ['type', 'category', 'question', 'answer']

        for field in required_fields:
            if field not in question or not question[field] or not str(question[field]).strip():
                return False

        question_text = str(question['question']).strip()
        if len(question_text) < 5:
            return False

        answer_text = str(question['answer']).strip()
        if len(answer_text) < 1:
            return False

        return True

    def deduplicate_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        题目去重
        """
        unique_questions = []
        seen_fingerprints = set()

        for question in questions:
            fingerprint = self.create_question_fingerprint(question['question'])

            if fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                unique_questions.append(question)

        return unique_questions

    def create_question_fingerprint(self, question_text: str) -> str:
        """
        创建题目的指纹用于去重
        """
        text = question_text.lower().strip()
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        text_hash = hashlib.md5(text[:100].encode()).hexdigest()
        return text_hash

    def get_file_hash(self, file_path: str) -> str:
        """
        获取文件哈希值用于缓存
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except:
            try:
                mtime = os.path.getmtime(file_path)
                return hashlib.md5(f"{file_path}_{mtime}".encode()).hexdigest()
            except:
                return hashlib.md5(file_path.encode()).hexdigest()

    def print_library_status(self):
        """打印题目库状态"""
        index_file = os.path.join(self.questions_dir, "library_index.json")
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            print(f"\n题目库状态:")
            print(f"最后更新: {index_data.get('last_updated', '未知')}")
            print(f"题目集合数量: {index_data.get('total_collections', 0)}")

            total_questions = sum(coll.get('question_count', 0) for coll in index_data.get('collections', []))
            print(f"总题目数量: {total_questions}")

            print("\n题目集合列表:")
            for coll in index_data.get('collections', []):
                print(f"  - {coll.get('name', '未知')}: {coll.get('question_count', 0)} 道题目")
        else:
            print("题目库索引文件不存在")

    # ==================== 兼容接口方法 ====================

    def extract_multiple_questions_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """从图片中提取多个题目"""
        return self.process_large_file_and_extract_questions(image_path, 'image', max_chunk_size=800)

    def extract_multiple_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取多个题目"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(text)
            temp_path = f.name

        try:
            return self.process_large_file_and_extract_questions(temp_path, 'file', max_chunk_size=800)
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def extract_multiple_questions_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """从PDF中提取多个题目"""
        return self.process_large_file_and_extract_questions(pdf_path, 'pdf', max_chunk_size=800)

    def extract_multiple_questions_from_document(self, document_path: str) -> List[Dict[str, Any]]:
        """从Office文档中提取多个题目（目前仅支持文本提取）"""
        # 暂时只支持文本提取，可以通过扩展支持Office文档
        return self.process_large_file_and_extract_questions(document_path, 'file', max_chunk_size=800)

    def chat_with_question(self, question, user_query):
        """
        基于题目进行AI对话
        Args:
            question: 原始题目内容
            user_query: 用户询问的问题
        Returns:
            str: AI的回答
        """
        try:
            prompt = f"""你是一个学习助手，请根据以下题目帮助解答用户的问题。

题目内容：
{question}

用户的问题：
{user_query}

请根据题目内容，提供详细的解答和解释。如果用户的问题与题目无关，也请尽量提供有帮助的回答。

你的回答："""

            response = self.call_ai_api(prompt)

            if not response:
                return f"我已收到您的问题：'{user_query}'，但我暂时无法提供详细的解答。请检查网络连接或稍后再试。"

            return response.strip()

        except Exception as e:
            print(f"AI对话失败: {e}")
            return f"抱歉，处理您的请求时出现错误：{str(e)}"

    def call_api(self, prompt: str) -> str:
        """
        简单的API调用方法（兼容原有接口）
        """
        return self.call_ai_api(prompt)
