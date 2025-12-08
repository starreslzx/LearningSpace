
from note import QuestionNoteManager
import time
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation


class ProcessingPopup(Popup):
    """处理中弹窗 - 显示AI解析进度和取消按钮 - 修复版本"""

    def __init__(self, cancel_callback=None, file_type=None, **kwargs):
        super(ProcessingPopup, self).__init__(**kwargs)
        self.cancel_callback = cancel_callback
        self.file_type = file_type or "文件"
        self.title = f"正在处理{self.file_type}"
        self.size_hint = (0.8, 0.6)
        self.auto_dismiss = False

        # 动画控制
        self.animation_event = None
        self.dot_count = 0

        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # 处理图标和标题
        icon_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        icon_label = Label(
            text="⏳",
            font_size='48sp',
            color=(0.3, 0.5, 0.8, 1)
        )
        icon_layout.add_widget(icon_label)
        layout.add_widget(icon_layout)

        # 处理信息
        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)

        title_label = Label(
            text=f"正在使用AI分析{self.file_type}",
            font_size='18sp',
            color=(0.2, 0.2, 0.2, 1)
        )
        info_layout.add_widget(title_label)

        self.progress_label = Label(
            text="AI正在提取题目内容，请耐心等待...",
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        info_layout.add_widget(self.progress_label)

        # 进度条（新增）
        progress_bar_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=0.2,
            spacing=5
        )

        self.progress_bar_bg = BoxLayout(
            size_hint=(1, 0.3),
            pos_hint={'center_x': 0.5},
            padding=[2, 2, 2, 2]
        )

        with self.progress_bar_bg.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            self.bg_rect = Rectangle(
                pos=self.progress_bar_bg.pos,
                size=self.progress_bar_bg.size
            )

        self.progress_bar_fg = BoxLayout(
            size_hint=(0, 1),  # 宽度从0开始
            pos_hint={'left': 0, 'center_y': 0.5}
        )

        with self.progress_bar_fg.canvas.before:
            Color(0.3, 0.6, 0.9, 1)
            self.fg_rect = Rectangle(
                pos=self.progress_bar_fg.pos,
                size=self.progress_bar_fg.size
            )

        self.progress_bar_bg.bind(
            pos=self.update_progress_rect,
            size=self.update_progress_rect
        )

        self.progress_bar_fg.bind(
            pos=self.update_progress_rect,
            size=self.update_progress_rect
        )

        progress_bar_layout.add_widget(Label(
            text="处理进度:",
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=0.5
        ))
        progress_bar_layout.add_widget(self.progress_bar_bg)

        info_layout.add_widget(progress_bar_layout)

        # 进度动画
        self.dot_animation_label = Label(
            text=".",
            font_size='14sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        info_layout.add_widget(self.dot_animation_label)

        layout.add_widget(info_layout)

        # 取消按钮
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)

        cancel_btn = Button(
            text="取消处理",
            font_size='16sp',
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        cancel_btn.bind(on_press=self.on_cancel)

        button_layout.add_widget(cancel_btn)
        layout.add_widget(button_layout)

        self.content = layout

        # 启动点动画和进度条动画
        self.start_animations()

    def start_animations(self):
        """启动所有动画"""
        self.dot_count = 0
        # 点动画
        self.animation_event = Clock.schedule_interval(self.animate_dots, 0.5)
        # 进度条脉动动画
        Clock.schedule_interval(self.pulse_progress_bar, 0.8)

    def update_progress_rect(self, instance, value):
        """更新进度条矩形位置"""
        if hasattr(self, 'bg_rect') and hasattr(instance, 'rect'):
            if instance == self.progress_bar_bg:
                self.bg_rect.pos = instance.pos
                self.bg_rect.size = instance.size
            elif instance == self.progress_bar_fg:
                self.fg_rect.pos = instance.pos
                self.fg_rect.size = instance.size

    def animate_dots(self, dt):
        """动画效果：点动"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * (self.dot_count + 1)
        self.dot_animation_label.text = dots

    def pulse_progress_bar(self, dt):
        """进度条脉动效果"""
        if hasattr(self, 'progress_bar_fg'):
            # 脉动动画：宽度从10%到30%之间变化
            import math
            pulse_value = 0.1 + 0.2 * (math.sin(time.time() * 2) + 1) / 2
            self.progress_bar_fg.size_hint_x = pulse_value
            # 更新颜色（轻微变化）
            with self.progress_bar_fg.canvas.before:
                Color(0.3, 0.6, 0.9, 0.7 + 0.3 * (math.sin(time.time() * 1.5) + 1) / 2)

    def on_cancel(self, instance):
        """取消按钮点击事件"""
        print("取消按钮被点击")
        # 停止所有动画
        self.stop_animations()

        if self.cancel_callback:
            print("调用取消回调函数")
            self.cancel_callback()

        self.dismiss()

    def stop_animations(self):
        """停止所有动画"""
        if self.animation_event:
            self.animation_event.cancel()
            self.animation_event = None

    def update_progress(self, message):
        """更新进度信息 - 修复版本"""
        print(f"更新进度: {message}")
        self.progress_label.text = message
        # 轻微调整进度条宽度以显示活动
        if hasattr(self, 'progress_bar_fg'):
            import random
            new_width = 0.15 + random.random() * 0.1
            self.progress_bar_fg.size_hint_x = new_width

    def update_progress_with_percentage(self, percentage, message):
        """更新带百分比的进度"""
        self.progress_label.text = f"{message} ({percentage:.1f}%)"
        # 更新进度条
        if hasattr(self, 'progress_bar_fg'):
            self.progress_bar_fg.size_hint_x = percentage / 100.0

    def on_dismiss(self):
        """弹窗关闭时清理资源"""
        print("弹窗关闭，清理资源")
        self.stop_animations()

class MultiQuestionPreviewPopup(Popup):
    """多题目预览弹窗 - 增加取消支持"""

    def __init__(self, questions_data, save_callback=None, cancel_callback=None, **kwargs):
        super(MultiQuestionPreviewPopup, self).__init__(**kwargs)
        self.questions_data = questions_data
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback  # 新增：取消回调
        self.selected_questions = [True] * len(questions_data)
        self.title = f"题目预览 ({len(questions_data)} 道题目)"
        self.size_hint = (0.95, 0.95)
        self.auto_dismiss = False

        self.create_ui()

    def create_ui(self):
        # 创建主布局
        main_layout = BoxLayout(orientation='vertical', padding=1, spacing=10)

        # 标题和统计
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08)
        header_layout.add_widget(Label(
            text=f"共提取到 {len(self.questions_data)} 道题目",
            font_size='16sp'
        ))

        select_all_btn = Button(
            text='全选/取消全选',
            size_hint_x=0.4,
            background_color=(0.3, 0.6, 0.9, 1)
        )
        select_all_btn.bind(on_press=self.select_all)

        header_layout.add_widget(select_all_btn)
        main_layout.add_widget(header_layout)

        # 题目列表
        scroll = ScrollView(size_hint_y=0.8)
        self.questions_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10
        )
        self.questions_container.bind(minimum_height=self.questions_container.setter('height'))

        for i, question_data in enumerate(self.questions_data):
            question_item = self.create_question_item(question_data, i)
            self.questions_container.add_widget(question_item)

        scroll.add_widget(self.questions_container)
        main_layout.add_widget(scroll)

        # 按钮区域
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)

        cancel_btn = Button(
            text='取消',
            background_color=(0.7, 0.7, 0.7, 1)
        )
        cancel_btn.bind(on_press=self.on_cancel)  # 修改：使用新的取消方法

        save_btn = Button(
            text=f'保存选中题目',
            background_color=(0.3, 0.6, 0.9, 1)
        )
        save_btn.bind(on_press=self.save_selected_questions)

        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(save_btn)
        main_layout.add_widget(button_layout)

        self.content = main_layout
        cancel_btn.bind(on_press=self.on_cancel)

    def on_cancel(self, instance):
        """处理取消按钮点击"""
        self.dismiss()
        if self.cancel_callback:
            self.cancel_callback()

    # ... 其他方法保持不变 ...
    def create_question_item(self, question_data, index):
        """创建题目项 - 自适应宽度，根据边界自动换行"""
        # 获取题目文本
        question_text = question_data.get('question', '')

        # 固定高度，让文本在固定区域内滚动
        item_height = 150  # 固定高度，内容超出时滚动

        item = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=item_height,
            spacing=5,
            padding=10
        )

        # 设置背景
        with item.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            item.rect = Rectangle(pos=item.pos, size=item.size)
        item.bind(pos=self.update_item_rect, size=self.update_item_rect)

        # 选择框和标题
        header = BoxLayout(orientation='horizontal', size_hint_y=0.25)

        checkbox = CheckBox(
            size_hint_x=0.1,
            active=True
        )
        checkbox.bind(active=lambda instance, value: self.on_checkbox_change(index, value))

        title_text = f"题目 {index + 1} - [{question_data.get('type', '简答题')}] {question_data.get('category', '默认')}"
        title = Label(
            text=title_text,
            size_hint_x=0.9,
            color=(0.2, 0.2, 0.2, 1),
            font_size='14sp',
            bold=True,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )

        header.add_widget(checkbox)
        header.add_widget(title)
        item.add_widget(header)

        # 题目内容 - 使用text_size实现自动换行
        question_content = BoxLayout(orientation='vertical', size_hint_y=0.65)

        # 创建滚动视图以确保长题目可滚动
        scroll_view = ScrollView(
            size_hint_y=1,
            bar_width=6,
            bar_color=(0.7, 0.7, 0.7, 0.5),
            do_scroll_x=False
        )

        # 修复：不使用BoundedScrollLabel，直接使用Label加ScrollView
        question_label = Label(
            text=question_text,
            text_size=(None, None),  # 不限制宽度，使用组件的实际宽度
            halign='left',
            valign='top',
            size_hint_y=None,
            font_size='14sp',
            color=(0.1, 0.1, 0.1, 1),
            line_height=1.2,
            padding=[5, 5]
        )

        def update_question_label_height(label, size):
            if label.texture_size[1] > 0:
                label.height = min(label.texture_size[1] + 20, 300)

        def update_text_width(self, dt=None):
            """更新文本宽度以适应容器"""
            try:
                if not hasattr(self, 'question_scroll') or not self.question_scroll:
                    return

                # 获取可用宽度
                if hasattr(self.question_scroll, 'width'):
                    scroll_width = self.question_scroll.width
                    if scroll_width > 0:
                        available_width = scroll_width * 0.95

                        # 更新题目文本宽度
                        if hasattr(self, 'question_label') and self.question_label:
                            if hasattr(self.question_label, 'text_size'):
                                self.question_label.text_size = (available_width, None)
                                if hasattr(self.question_label, 'texture_update'):
                                    self.question_label.texture_update()

                        # 更新答案文本宽度
                        if hasattr(self, 'answer_label') and self.answer_label:
                            if hasattr(self.answer_label, 'text_size'):
                                self.answer_label.text_size = (available_width, None)
                                if hasattr(self.answer_label, 'texture_update'):
                                    self.answer_label.texture_update()
            except Exception as e:
                print(f"更新文本宽度时出错: {e}")

        # 绑定事件
        question_label.bind(
            texture_size=update_question_label_height,
            width=lambda instance, value: update_text_width(instance, value)
        )

        # 初始设置文本宽度
        Clock.schedule_once(lambda dt: update_text_width(question_label, scroll_view.width), 0.1)

        # 包装标签以便滚动
        content_wrapper = BoxLayout(orientation='vertical', size_hint_y=None)
        content_wrapper.bind(minimum_height=content_wrapper.setter('height'))
        content_wrapper.add_widget(question_label)

        scroll_view.add_widget(content_wrapper)
        question_content.add_widget(scroll_view)
        item.add_widget(question_content)

        # 难度信息
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        footer.add_widget(Label(
            text=f"难度: {question_data.get('difficulty', 3)}",
            color=(0.5, 0.5, 0.5, 1),
            font_size='12sp'
        ))
        item.add_widget(footer)

        return item

    def update_item_rect(self, instance, value):
        """更新项矩形位置"""
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def on_checkbox_change(self, index, value):
        """复选框状态改变"""
        self.selected_questions[index] = value

    def select_all(self, instance):
        """全选/取消全选"""
        all_selected = all(self.selected_questions)
        new_state = not all_selected

        # 更新所有复选框状态
        for i in range(len(self.selected_questions)):
            self.selected_questions[i] = new_state

        # 刷新UI
        self.questions_container.clear_widgets()
        for i, question_data in enumerate(self.questions_data):
            question_item = self.create_question_item(question_data, i)
            self.questions_container.add_widget(question_item)

    def save_selected_questions(self, instance):
        """保存选中的题目"""
        selected_data = []
        for i, selected in enumerate(self.selected_questions):
            if selected:
                selected_data.append(self.questions_data[i])

        if not selected_data:
            self.show_error("请至少选择一个题目")
            return

        self.dismiss()
        if self.save_callback:
            self.save_callback(selected_data)

    def show_error(self, message):
        """显示错误消息"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        ok_btn = Button(text='确定', size_hint_y=0.3)
        popup = Popup(title='提示', content=content, size_hint=(0.6, 0.3))
        ok_btn.bind(on_press=popup.dismiss)
        content.add_widget(ok_btn)
        popup.open()


class EnhancedUploadPopup(Popup):
    """增强版上传文件弹窗 - 支持更多文件类型"""

    def __init__(self, upload_callback=None, **kwargs):
        super(EnhancedUploadPopup, self).__init__(**kwargs)
        self.upload_callback = upload_callback
        self.title = "上传题目材料"
        self.size_hint = (0.8, 0.7)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        title_label = Label(
            text="选择上传方式",
            size_hint_y=0.1,
            font_size='18sp'
        )
        layout.add_widget(title_label)

        button_layout = BoxLayout(orientation='vertical', size_hint_y=0.7, spacing=10)

        file_btn = Button(
            text="上传文本文件",
            size_hint_y=0.2,
            background_color=(0.3, 0.6, 0.9, 1)
        )
        file_btn.bind(on_press=self.upload_file)

        image_btn = Button(
            text="上传图片",
            size_hint_y=0.2,
            background_color=(0.9, 0.7, 0.3, 1)
        )
        image_btn.bind(on_press=self.upload_image)

        pdf_btn = Button(
            text="上传PDF文件",
            size_hint_y=0.2,
            background_color=(0.9, 0.5, 0.3, 1)
        )
        pdf_btn.bind(on_press=self.upload_pdf)

        document_btn = Button(
            text="上传Office文档",
            size_hint_y=0.2,
            background_color=(0.6, 0.5, 0.8, 1)
        )
        document_btn.bind(on_press=self.upload_document)

        button_layout.add_widget(file_btn)
        button_layout.add_widget(image_btn)
        button_layout.add_widget(pdf_btn)
        button_layout.add_widget(document_btn)
        layout.add_widget(button_layout)


        cancel_btn = Button(
            text="取消",
            size_hint_y=0.1,
            background_color=(0.7, 0.7, 0.7, 1)
        )
        cancel_btn.bind(on_press=self.dismiss)
        layout.add_widget(cancel_btn)

        self.content = layout

    def upload_file(self, instance):
        self.dismiss()
        if self.upload_callback:
            self.upload_callback('file')

    def upload_image(self, instance):
        self.dismiss()
        if self.upload_callback:
            self.upload_callback('image')

    def upload_pdf(self, instance):
        self.dismiss()
        if self.upload_callback:
            self.upload_callback('pdf')

    def upload_document(self, instance):
        self.dismiss()
        if self.upload_callback:
            self.upload_callback('document')


class EnhancedFileChooserPopup(Popup):
    """增强版文件选择弹窗"""

    def __init__(self, file_type='file', upload_callback=None, **kwargs):
        super(EnhancedFileChooserPopup, self).__init__(**kwargs)
        self.file_type = file_type
        self.upload_callback = upload_callback

        if file_type == 'image':
            self.title = "选择图片"
            self.filters = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.webp']
        elif file_type == 'pdf':
            self.title = "选择PDF文件"
            self.filters = ['*.pdf']
        elif file_type == 'document':
            self.title = "选择Office文档"
            self.filters = ['*.doc', '*.docx', '*.ppt', '*.pptx', '*.xls', '*.xlsx']
        else:
            self.title = "选择文本文件"
            self.filters = ['*.txt', '*.md', '*.pdf']

        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        notice_text = {
            'image': "选择图片文件",
            'pdf': "选择PDF文件",
            'document': "选择Office文档",
            'file': "选择文本文件"
        }.get(self.file_type, "选择文件")

        notice_label = Label(
            text=notice_text,
            size_hint_y=0.1,
            font_size='14sp'
        )
        layout.add_widget(notice_label)

        self.file_chooser = FileChooserListView(
            filters=self.filters,
            size_hint_y=0.7
        )
        layout.add_widget(self.file_chooser)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)

        cancel_btn = Button(text="取消")
        cancel_btn.bind(on_press=self.dismiss)

        select_btn = Button(text="选择")
        select_btn.bind(on_press=self.select_file)

        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(select_btn)
        layout.add_widget(button_layout)

        self.content = layout

    def select_file(self, instance):
        if self.file_chooser.selection:
            file_path = self.file_chooser.selection[0]
            self.dismiss()
            if self.upload_callback:
                self.upload_callback(file_path, self.file_type)


class QuickQuizPopup(Popup):
    """快速闪卡弹窗 """

    def __init__(self, question_bank, questions=None, current_index=0, **kwargs):
        super(QuickQuizPopup, self).__init__(**kwargs)
        self.question_bank = question_bank
        self.title = ""
        self.size_hint = (0.97, 0.97)
        self.auto_dismiss = False

        # 初始化笔记管理器
        self.note_manager = QuestionNoteManager()

        # 如果外部传入了题目，使用这些题目，否则从数据库随机获取
        if questions is not None:
            self.current_questions = questions
            self.current_index = current_index
            self.use_external_questions = True
        else:
            self.current_questions = []
            self.current_index = 0
            self.use_external_questions = False

        self.showing_answer = False
        self.current_question_id = None

        # 保存状态以便从AI聊天返回
        self._saved_state = {
            'questions': self.current_questions.copy() if questions else [],
            'index': current_index,
            'external': self.use_external_questions
        }

        self.create_ui()

        # 加载题目
        if questions is not None and len(questions) > 0:
            self.show_current_question()
            self.update_button_states()
        else:
            self.load_random_questions()

    def create_ui(self):
        """创建界面 - 重新设计布局，确保不重叠"""
        # 使用FloatLayout作为主容器
        layout = FloatLayout()

        # ==================== 右上角关闭按钮
        self.close_btn = Button(
            text='x',
            font_size='22sp',
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={'right': 0.99, 'top': 0.99},
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            background_normal='',
            bold=True
        )
        self.close_btn.bind(on_press=self.dismiss)
        layout.add_widget(self.close_btn)

        # ==================== 顶部标题区域 ====================
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.06),  # 减少高度
            pos_hint={'top': 0.99, 'x': 0},
            padding=[10, 0]
        )
        self.question_num_label = Label(
            text="快速闪卡",
            font_size='18sp',  # 减小字体
            color=(0.3, 0.4, 0.7, 1),
            halign='center',
            valign='middle',
            bold=True
        )
        header.add_widget(self.question_num_label)
        layout.add_widget(header)

        # ==================== 题目区域 - 重新设计 ====================
        # 题目容器
        question_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.96, 0.68),  # 使用相对高度，占据68%
            pos_hint={'center_x': 0.5, 'top': 0.92},  # 顶部靠上
            padding=[1, 1, 1, 1]
        )

        # 题目区域的白色背景
        with question_container.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            question_container.rect = Rectangle(pos=question_container.pos, size=question_container.size)

        question_container.bind(
            pos=lambda obj, pos: setattr(question_container.rect, 'pos', pos),
            size=lambda obj, size: setattr(question_container.rect, 'size', size)
        )

        # 题目滚动区域 - 支持滑动条
        self.question_scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=10,  # 加宽滚动条
            bar_color=(0.7, 0.7, 0.7, 0.9),  # 更明显的滚动条
            do_scroll_x=False,
            scroll_type=['bars', 'content'],
            bar_inactive_color=(0.7, 0.7, 0.7, 0.5)
        )

        # 题目内容标签 - 让内容决定高度，通过滚动查看
        self.question_label = Label(
            text="加载题目中...",
            halign='left',
            valign='top',
            size_hint_y=None,
            font_size='18sp',
            color=(0.15, 0.15, 0.15, 1),
            line_height=1.3,
            padding=[15, 15]
        )

        def update_question_height(label, texture_size):
            """动态更新题目标签的高度"""
            if texture_size[1] > 0:
                # 设置标签高度为内容高度
                label.height = texture_size[1] + 30
                # 确保至少有最小高度
                if label.height < 200:
                    label.height = 200

        self.question_label.bind(
            texture_size=update_question_height,
            width=lambda label, width: setattr(label, 'text_size', (width - 30, None))
        )

        self.question_scroll.add_widget(self.question_label)
        question_container.add_widget(self.question_scroll)
        layout.add_widget(question_container)

        # ==================== 答案区域 ====================
        self.answer_area = BoxLayout(
            orientation='vertical',
            size_hint=(0.96, None),
            height=0,  # 初始高度为0
            pos_hint={'center_x': 0.5, 'y': 0.23},  # 调整位置
            spacing=5,
            padding=[15, 10, 15, 10],
            opacity=0
        )

        with self.answer_area.canvas.before:
            Color(0.95, 0.98, 0.95, 1)
            self.answer_area.rect = Rectangle(pos=self.answer_area.pos, size=self.answer_area.size)

        self.answer_area.bind(
            pos=lambda obj, pos: setattr(self.answer_area.rect, 'pos', pos),
            size=lambda obj, size: setattr(self.answer_area.rect, 'size', size)
        )

        # 答案滚动视图
        self.answer_scroll = ScrollView(
            size_hint_y=1,
            bar_width=8,
            bar_color=(0.7, 0.7, 0.7, 0.8),
            do_scroll_x=False,
            scroll_type=['bars', 'content']
        )

        # 答案内容标签
        self.answer_label = Label(
            text="",
            halign='left',
            valign='top',
            size_hint_y=None,
            font_size='16sp',
            color=(0.3, 0.3, 0.3, 1),
            line_height=1.3,
            padding=[10, 10]
        )

        def update_answer_height(label, texture_size):
            """动态更新答案标签的高度"""
            if texture_size[1] > 0:
                new_height = max(80, texture_size[1] + 20)
                label.height = min(new_height, 200)  # 限制最大高度

        self.answer_label.bind(
            texture_size=update_answer_height,
            width=lambda label, width: setattr(label, 'text_size', (width - 30, None))
        )

        self.answer_scroll.add_widget(self.answer_label)
        self.answer_area.add_widget(self.answer_scroll)
        layout.add_widget(self.answer_area)

        # ==================== 控制按钮区域 ====================
        # 按钮容器 - 更扁的布局
        controls_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.15),  # 减少高度到15%
            pos_hint={'bottom': 0.05, 'x': 0},  # 上移，留出空间
            spacing=2,  # 减少间距
            padding=[10, 2, 10, 2]  # 减少内边距
        )

        # 第一行：上一题、显示答案、下一题
        controls = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.45,
            spacing=5  # 减少间距
        )

        self.prev_btn = Button(
            text='上一题',
            font_size='14sp',  # 减小字体
            background_color=(0.4, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.3
        )
        self.prev_btn.bind(on_press=self.prev_question)

        self.toggle_btn = Button(
            text='显示答案',
            font_size='14sp',  # 减小字体
            background_color=(0.3, 0.7, 0.4, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.4
        )
        self.toggle_btn.bind(on_press=self.toggle_answer)

        self.next_btn = Button(
            text='下一题',
            font_size='14sp',  # 减小字体
            background_color=(0.4, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.3
        )
        self.next_btn.bind(on_press=self.next_question)

        controls.add_widget(self.prev_btn)
        controls.add_widget(self.toggle_btn)
        controls.add_widget(self.next_btn)

        # 第二行：笔记、AI助手、新题集
        functions = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.45,
            spacing=8,
            padding=[0, 2, 0, 0]
        )

        # 笔记按钮
        self.note_btn = Button(
            text='记笔记',
            font_size='14sp',  # 减小字体
            background_color=(0.8, 0.5, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.33,
            bold=True
        )
        self.note_btn.bind(on_press=self.edit_note)

        # AI助手按钮
        self.ai_btn = Button(
            text='AI助手',
            font_size='14sp',  # 减小字体
            background_color=(0.9, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.33,
            bold=True
        )
        self.ai_btn.bind(on_press=self.goto_ai_chat)

        # 新题集按钮
        new_set_btn = Button(
            text='新题集',
            font_size='14sp',  # 减小字体
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.33,
            bold=True
        )
        new_set_btn.bind(on_press=self.load_new_questions)

        functions.add_widget(self.note_btn)
        functions.add_widget(self.ai_btn)
        functions.add_widget(new_set_btn)

        controls_container.add_widget(controls)
        controls_container.add_widget(functions)
        layout.add_widget(controls_container)

        self.content = layout

    def show_current_question(self):
        """显示当前题目"""
        if not self.current_questions or self.current_index >= len(self.current_questions):
            self.show_empty_state()
            return

        current = self.current_questions[self.current_index]
        self.current_question_id = current.get('id')

        # 更新题目编号
        if self.use_external_questions:
            self.question_num_label.text = f"题目作坊 ({self.current_index + 1}/{len(self.current_questions)})"
        else:
            self.question_num_label.text = f"快速闪卡 ({self.current_index + 1}/{len(self.current_questions)})"

        # 获取题目和答案文本
        question_text = current.get('question', '')
        answer_text = current.get('answer', '')

        # 处理题目文本：如果开头没有换行符，添加一个
        if question_text and not question_text.startswith('\n'):
            question_text = '\n' + question_text

        # 不截断长文本，让滚动条工作
        # 设置题目文本
        self.question_label.text = question_text

        # 设置答案文本
        if answer_text and len(answer_text) > 1500:
            answer_text = answer_text[:1497] + "..."
        self.answer_label.text = answer_text

        # 切换题目时总是隐藏答案
        self.showing_answer = False
        self.toggle_btn.text = '显示答案'

        # 重置答案区域
        self.answer_area.height = 0
        self.answer_area.opacity = 0

        # 更新按钮状态
        self.update_button_states()

        # 重置滚动位置到顶部
        Clock.schedule_once(lambda dt: setattr(self.question_scroll, 'scroll_y', 1), 0.1)
        Clock.schedule_once(lambda dt: setattr(self.answer_scroll, 'scroll_y', 1), 0.1)

        # 确保文本宽度更新
        Clock.schedule_once(self.update_text_width, 0.2)

    def update_text_width(self, dt=None):
        """更新文本宽度以适应容器"""
        # 更新题目文本宽度
        if hasattr(self, 'question_label') and self.question_label:
            if hasattr(self.question_label, 'texture_size'):
                available_width = self.question_scroll.width - 30  # 减去内边距
                if available_width > 0:
                    self.question_label.text_size = (available_width, None)
                    self.question_label.texture_update()

        # 更新答案文本宽度
        if hasattr(self, 'answer_label') and self.answer_label:
            if hasattr(self.answer_label, 'texture_size'):
                available_width = self.answer_scroll.width - 30  # 减去内边距
                if available_width > 0:
                    self.answer_label.text_size = (available_width, None)
                    self.answer_label.texture_update()

    def toggle_answer(self, instance):
        """切换答案显示"""
        if not self.current_questions:
            return

        # 检查当前题目是否有答案
        current_question = self.current_questions[self.current_index]
        if not current_question.get('answer', '').strip():
            # 没有答案的题目
            self.show_message("提示", "本题暂无参考答案")
            return

        self.showing_answer = not self.showing_answer

        if self.showing_answer:
            self.toggle_btn.text = '隐藏答案'

            # 计算答案所需高度
            answer_text = current_question.get('answer', '')
            if answer_text:
                # 估算行数（每行约50字符）
                lines = len(answer_text) // 50 + 1
                answer_height = min(max(lines * 25, 100), 200)  # 限制最大高度
            else:
                answer_height = 80

            # 调整答案区域位置和高度
            self.answer_area.height = answer_height + 40  # 加上标题和边距

            # 答案区域展开动画
            anim = Animation(height=self.answer_area.height, opacity=1, duration=0.3)
            anim.start(self.answer_area)

            # 确保答案文本宽度更新
            Clock.schedule_once(self.update_text_width, 0.1)

            # 滚动到答案顶部
            Clock.schedule_once(lambda dt: setattr(self.answer_scroll, 'scroll_y', 1), 0.2)
        else:
            self.toggle_btn.text = '显示答案'
            # 答案区域收起动画
            anim = Animation(height=0, opacity=0, duration=0.3)
            anim.start(self.answer_area)

    def goto_ai_chat(self, instance):
        """跳转到AI对话界面"""
        if not self.current_questions:
            return

        current_question = self.current_questions[self.current_index]
        question_text = current_question.get('question', '')

        # 保存当前状态
        self.save_current_state()

        # 保存到全局变量
        app = App.get_running_app()
        if app:
            app.last_quick_quiz_popup = self
            print("保存QuickQuizPopup到app")

        # 关闭弹窗
        self.dismiss()

        # 打开AI聊天界面
        if app and app.root:
            app.root.current = 'ai_chat'

            # 获取AI聊天屏幕并传递题目
            ai_chat_screen = app.root.get_screen('ai_chat')

            # 设置题目和来源信息
            if hasattr(ai_chat_screen, 'set_question_with_source'):
                ai_chat_screen.set_question_with_source(
                    question_text,
                    'quick_quiz',
                    self  # 传递当前弹窗实例
                )
            elif hasattr(ai_chat_screen, 'set_question_in_input'):
                ai_chat_screen.set_question_in_input(question_text)



    def save_current_state(self):
        """保存当前状态"""
        if self.current_questions:
            self._saved_state = {
                'questions': self.current_questions.copy(),
                'index': self.current_index,
                'external': self.use_external_questions,
                'question_id': self.current_question_id,
                'showing_answer': self.showing_answer
            }
            print(f"保存状态: 第{self.current_index + 1}题, 共{len(self.current_questions)}题")

    def restore_state_from_ai_chat(self):
        """从AI聊天返回时恢复状态"""
        if hasattr(self, '_saved_state') and self._saved_state:
            print(f"从AI聊天恢复状态: 第{self._saved_state['index'] + 1}题")

            # 恢复状态
            self.current_questions = self._saved_state['questions']
            self.current_index = self._saved_state['index']
            self.use_external_questions = self._saved_state.get('external', False)
            self.current_question_id = self._saved_state.get('question_id')
            self.showing_answer = self._saved_state.get('showing_answer', False)

            # 重新显示题目
            self.show_current_question()
            self.update_button_states()

            # 如果之前显示答案，恢复答案区域
            if self.showing_answer:
                Clock.schedule_once(self.restore_answer_display, 0.5)

    def restore_answer_display(self, dt):
        """恢复答案显示"""
        if self.showing_answer and self.current_questions:
            current_question = self.current_questions[self.current_index]
            answer_text = current_question.get('answer', '')
            if answer_text:
                # 重新计算并显示答案
                lines = len(answer_text) // 50 + 1
                answer_height = min(max(lines * 25, 100), 250)

                self.answer_area.height = answer_height + 40
                self.answer_area.opacity = 1
                self.toggle_btn.text = '隐藏答案'


    def prev_question(self, instance):
        """上一题 - 自动隐藏答案"""
        if self.current_index > 0:
            # 自动隐藏答案
            self.hide_answer_before_navigate()
            self.current_index -= 1
            self.show_current_question()

    def next_question(self, instance):
        """下一题 - 自动隐藏答案"""
        if self.current_index < len(self.current_questions) - 1:
            # 自动隐藏答案
            self.hide_answer_before_navigate()
            self.current_index += 1
            self.show_current_question()

    def hide_answer_before_navigate(self):
        """在切换题目前隐藏答案"""
        if self.showing_answer:
            self.showing_answer = False
            self.toggle_btn.text = '显示答案'
            # 立即隐藏答案区域
            self.answer_area.height = 0
            self.answer_area.opacity = 0

    def setup_backgrounds(self):
        """为题目和答案区域设置背景"""
        # 题目区域背景
        with self.question_scroll.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.question_bg_rect = Rectangle(pos=self.question_scroll.pos, size=self.question_scroll.size)

        # 答案区域背景
        with self.answer_area.canvas.before:
            Color(0.95, 0.98, 0.95, 1)  # 浅绿色背景
            self.answer_bg_rect = Rectangle(pos=self.answer_area.pos, size=self.answer_area.size)

        # 绑定位置和大小变化
        self.question_scroll.bind(pos=self.update_bg_rect, size=self.update_bg_rect)
        self.answer_area.bind(pos=self.update_bg_rect, size=self.update_bg_rect)


    def update_bg_rect(self, instance, value):
        """更新背景矩形位置"""
        if instance == self.question_scroll and hasattr(self, 'question_bg_rect'):
            self.question_bg_rect.pos = instance.pos
            self.question_bg_rect.size = instance.size
        elif instance == self.answer_area and hasattr(self, 'answer_bg_rect'):
            self.answer_bg_rect.pos = instance.pos
            self.answer_bg_rect.size = instance.size

    def update_rect(self, instance, value):
        """更新矩形位置"""
        if hasattr(instance, 'rect'):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

    def load_random_questions(self, instance=None):
        """加载随机题目"""
        try:
            questions = self.question_bank.get_random_questions(10)
            if not questions:
                self.show_empty_state()
                return

            self.current_questions = questions
            self.current_index = 0
            self.show_current_question()

            # 确保文本宽度更新
            Clock.schedule_once(self.update_text_width, 0.2)
        except Exception as e:
            print(f"加载随机题目失败: {e}")
            self.show_empty_state()

    def load_new_questions(self, instance=None):
        """加载新题集 - 如果使用外部题目，则不改变题目列表"""
        if self.use_external_questions:
            # 如果使用外部题目，只是重置到第一题
            if self.current_questions:
                self.current_index = 0
                self.show_current_question()
            return

        # 否则从数据库加载随机题目
        self.load_random_questions()

    def show_empty_state(self):
        """显示空状态"""
        self.question_label.text = '\n题库中没有题目。\n请先在题目作坊中添加题目。'
        self.answer_label.text = ""
        self.question_num_label.text = "题目: 0/0"

        self.toggle_btn.disabled = True
        self.prev_btn.disabled = True
        self.next_btn.disabled = True
        self.ai_btn.disabled = True
        self.note_btn.disabled = True  # 禁用笔记按钮

    def show_message(self, title, message):
        """显示消息弹窗"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(
            text=message,
            font_size='14sp',
            halign='center'
        ))

        ok_btn = Button(
            text='确定',
            size_hint_y=0.3,
            background_color=(0.7, 0.7, 0.7, 1),
            color=(1, 1, 1, 1)
        )

        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.6, 0.4)
        )

        ok_btn.bind(on_press=popup.dismiss)
        content.add_widget(ok_btn)
        popup.open()

    def update_button_states(self):
        """更新按钮状态"""
        if not self.current_questions:
            self.prev_btn.disabled = True
            self.next_btn.disabled = True
            self.toggle_btn.disabled = True
            self.ai_btn.disabled = True
            self.note_btn.disabled = True
            return

        self.prev_btn.disabled = self.current_index == 0
        self.next_btn.disabled = self.current_index == len(self.current_questions) - 1

        # 只有有答案的题目才能显示答案
        current_question = self.current_questions[self.current_index]
        has_answer = current_question.get('answer', '').strip() != ''
        self.toggle_btn.disabled = not has_answer

        # 笔记按钮始终可用（只要有题目）
        self.note_btn.disabled = False

    def edit_note(self, instance):
        """编辑笔记 - 点击时才加载当前题目的笔记"""
        if not self.current_question_id:
            self.show_message("提示", "没有选中题目")
            return

            # 只在点击时才获取笔记
        current_note = self.note_manager.get_note(self.current_question_id)

        # 创建编辑弹窗
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)

        # 标题
        title_box = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        title_label = Label(
            text="笔记",
            font_size='18sp',
            color=(0.8, 0.5, 0.2, 1),
            size_hint_x=0.8
        )
        title_box.add_widget(title_label)

        # 清空笔记按钮（只在有笔记时显示）
        clear_btn = Button(
            text="清空",
            font_size='14sp',
            size_hint_x=0.2,
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )

        def clear_note(instance):
            if self.note_manager.delete_note(self.current_question_id):
                note_input.text = ""
                # 移除清空按钮
                if clear_btn in title_box.children:
                    title_box.remove_widget(clear_btn)
                self.show_message("提示", "笔记已清空")

        clear_btn.bind(on_press=clear_note)

        # 只有有笔记时才显示清空按钮
        if current_note and current_note.strip():
            title_box.add_widget(clear_btn)

        content.add_widget(title_box)

        note_input = TextInput(
            text=current_note if current_note else "",
            multiline=True,
            font_size='16sp',
            size_hint_y=0.5,
            hint_text="在这里输入您的笔记...",
            padding=[10, 10]
        )
        content.add_widget(note_input)

        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.1)

        cancel_btn = Button(
            text="取消",
            background_color=(0.7, 0.7, 0.7, 1),
            color=(1, 1, 1, 1)
        )
        cancel_btn.bind(on_press=lambda x: popup.dismiss())

        save_btn = Button(
            text="保存",
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1)
        )

        def save_note(instance):
            note_text = note_input.text.strip()
            if note_text:
                if self.note_manager.save_note(self.current_question_id, note_text):
                    popup.dismiss()
                    self.show_message("成功", "笔记已保存")
                    # 如果之前没有清空按钮，现在添加
                    if not (clear_btn in title_box.children):
                        title_box.add_widget(clear_btn)
                else:
                    self.show_message("错误", "保存笔记失败")
            else:
                # 如果文本框为空，则删除笔记
                if self.note_manager.delete_note(self.current_question_id):
                    popup.dismiss()
                    self.show_message("提示", "笔记已清空")
                    # 移除清空按钮
                    if clear_btn in title_box.children:
                        title_box.remove_widget(clear_btn)

        save_btn.bind(on_press=save_note)

        button_box.add_widget(cancel_btn)
        button_box.add_widget(save_btn)
        content.add_widget(button_box)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.9, 0.8),
            auto_dismiss=False
        )
        popup.open()

        # 自动聚焦到输入框
        Clock.schedule_once(lambda dt: setattr(note_input, 'focus', True), 0.1)