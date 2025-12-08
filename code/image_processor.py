import os
import cv2
import pytesseract
import base64

class ImageProcessor:
    def __init__(self):
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']

    def preprocess_image(self, image_path):
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("无法读取图片文件")

            height, width = img.shape[:2]
            if height > 1024 or width > 1024:
                scale = min(1024 / height, 1024 / width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height))

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            denoised = cv2.medianBlur(gray, 3)

            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            return binary

        except Exception as e:
            print(f"图片预处理失败: {e}")
            return None

    def extract_text_with_tesseract(self, image_path):
        try:
            processed_img = self.preprocess_image(image_path)
            if processed_img is None:
                return "图片处理失败，无法提取文字"

            custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'

            text = pytesseract.image_to_string(processed_img, config=custom_config)

            cleaned_text = self.clean_extracted_text(text)

            return cleaned_text

        except Exception as e:
            print(f"OCR文字提取失败: {e}")
            return f"文字提取失败: {str(e)}"

    def clean_extracted_text(self, text):
        if not text:
            return "未识别到文字内容"

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        cleaned_text = '\n'.join(cleaned_lines)

        if len(cleaned_text) < 10:
            return "识别到的文字内容较少，请确保图片清晰且包含足够的文字"

        return cleaned_text

    def is_image_file(self, file_path):
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in self.supported_formats

    def convert_image_to_base64(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"图片转base64失败: {e}")
            return None

image_processor = ImageProcessor()