# image_utils.py
import os
from config import SUPPORTED_IMAGE_FORMATS, MAX_IMAGE_SIZE_MB


def validate_image_file(file_path):
    """验证图片文件是否可用"""
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return False, "文件不存在"

    # 检查文件扩展名
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in SUPPORTED_IMAGE_FORMATS:
        return False, f"不支持的文件格式: {file_ext}，支持格式: {', '.join(SUPPORTED_IMAGE_FORMATS)}"

    # 检查文件大小
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_IMAGE_SIZE_MB:
        return False, f"文件过大: {file_size_mb:.2f}MB，最大支持: {MAX_IMAGE_SIZE_MB}MB"

    return True, "文件验证通过"


def get_image_info(file_path):
    """获取图片信息"""
    try:
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        return {
            'size': file_size,
            'size_mb': file_size / (1024 * 1024),
            'extension': file_ext,
            'name': os.path.basename(file_path)
        }
    except Exception as e:
        return None