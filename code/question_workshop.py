from kivy.app import App
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, Rectangle
import threading
import traceback
import os

try:
    from ai_assistant import AIAssistant
except ImportError:
    AIAssistant = None

try:
    from question_bank import QuestionBankV2
except ImportError:
    QuestionBankV2 = None

from popup import QuickQuizPopup
from note import QuestionNoteManager


class ProcessingPopup(Popup):
    """处理中弹窗"""
    def __init__(self, cancel_callback=None, file_type=None, **kwargs):
        super(ProcessingPopup, self).__init__(**kwargs)
        self.cancel_callback = cancel_callback
        self.file_type = file_type or "文件"
        self.title = f"正在处理{self.file_type}"
        self.size_hint = (0.8, 0.6)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        icon_label = Label(text="⏳", font_size='48sp', color=(0.3, 0.5, 0.8, 1))
        layout.add_widget(icon_label)

        info_layout = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        title_label = Label(text=f"正在使用AI分析{self.file_type}", font_size='18sp', color=(0.2, 0.2, 0.2, 1))
        info_layout.add_widget(title_label)

        self.progress_label = Label(text="AI正在提取题目内容，请耐心等待...", font_size='14sp', color=(0.5, 0.5, 0.5, 1))
        info_layout.add_widget(self.progress_label)
        layout.add_widget(info_layout)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)
        cancel_btn = Button(text="取消处理", font_size='16sp', background_color=(0.8, 0.3, 0.3, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_press=self.on_cancel)
        button_layout.add_widget(cancel_btn)
        layout.add_widget(button_layout)

        self.content = layout

    def on_cancel(self, instance):
        if self.cancel_callback:
            self.cancel_callback()
        self.dismiss()

    def update_progress(self, message):
        self.progress_label.text = message

    def update_progress_with_percentage(self, percentage, message):
        self.progress_label.text = f"{message} ({percentage:.1f}%)"


class MultiQuestionPreviewPopup(Popup):
    """多题目预览弹窗"""
    def __init__(self, questions_data, save_callback=None, cancel_callback=None, **kwargs):
        super(MultiQuestionPreviewPopup, self).__init__(**kwargs)
        self.questions_data = questions_data
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback
        self.selected_questions = [True] * len(questions_data)
        self.title = f"题目预览 ({len(questions_data)} 道题目)"
        self.size_hint = (0.95, 0.95)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=1, spacing=10)
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=0.08)
        header_layout.add_widget(Label(text=f"共提取到 {len(self.questions_data)} 道题目", font_size='16sp'))

        select_all_btn = Button(text='全选/取消全选', size_hint_x=0.4, background_color=(0.3, 0.6, 0.9, 1))
        select_all_btn.bind(on_press=self.select_all)
        header_layout.add_widget(select_all_btn)
        main_layout.add_widget(header_layout)

        scroll = ScrollView(size_hint_y=0.8)
        self.questions_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.questions_container.bind(minimum_height=self.questions_container.setter('height'))

        for i, question_data in enumerate(self.questions_data):
            question_item = self.create_question_item(question_data, i)
            self.questions_container.add_widget(question_item)

        scroll.add_widget(self.questions_container)
        main_layout.add_widget(scroll)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)
        cancel_btn = Button(text='取消', background_color=(0.7, 0.7, 0.7, 1))
        cancel_btn.bind(on_press=self.on_cancel)
        save_btn = Button(text=f'保存选中题目', background_color=(0.3, 0.6, 0.9, 1))
        save_btn.bind(on_press=self.save_selected_questions)
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(save_btn)
        main_layout.add_widget(button_layout)

        self.content = main_layout

    def create_question_item(self, question_data, index):
        item = BoxLayout(orientation='vertical', size_hint_y=None, height=150, spacing=5, padding=10)
        with item.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            item.rect = Rectangle(pos=item.pos, size=item.size)
        item.bind(pos=self.update_item_rect, size=self.update_item_rect)

        header = BoxLayout(orientation='horizontal', size_hint_y=0.25)
        checkbox = CheckBox(size_hint_x=0.1, active=True)
        checkbox.bind(active=lambda instance, value: self.on_checkbox_change(index, value))

        title_text = f"题目 {index + 1} - [{question_data.get('type', '简答题')}] {question_data.get('category', '默认')}"
        title = Label(text=title_text, size_hint_x=0.9, color=(0.2, 0.2, 0.2, 1), font_size='14sp', bold=True,
                     text_size=(None, None), halign='left', valign='middle')
        header.add_widget(checkbox)
        header.add_widget(title)
        item.add_widget(header)

        question_content = BoxLayout(orientation='vertical', size_hint_y=0.65)
        scroll_view = ScrollView(size_hint_y=1, bar_width=6, bar_color=(0.7, 0.7, 0.7, 0.5), do_scroll_x=False)

        question_label = Label(text=question_data.get('question', ''), text_size=(None, None), halign='left',
                             valign='top', size_hint_y=None, font_size='14sp', color=(0.1, 0.1, 0.1, 1),
                             line_height=1.2, padding=[5, 5])

        def update_question_label_height(label, size):
            if label.texture_size[1] > 0:
                label.height = min(label.texture_size[1] + 20, 300)

        def update_text_width(label, width):
            if width > 0:
                label.text_size = (width - 10, None)
                label.texture_update()

        question_label.bind(texture_size=update_question_label_height,
                          width=lambda instance, value: update_text_width(instance, value))
        Clock.schedule_once(lambda dt: update_text_width(question_label, scroll_view.width), 0.1)

        content_wrapper = BoxLayout(orientation='vertical', size_hint_y=None)
        content_wrapper.bind(minimum_height=content_wrapper.setter('height'))
        content_wrapper.add_widget(question_label)
        scroll_view.add_widget(content_wrapper)
        question_content.add_widget(scroll_view)
        item.add_widget(question_content)

        footer = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        footer.add_widget(Label(text=f"难度: {question_data.get('difficulty', 3)}", color=(0.5, 0.5, 0.5, 1), font_size='12sp'))
        item.add_widget(footer)
        return item

    def update_item_rect(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def on_checkbox_change(self, index, value):
        self.selected_questions[index] = value

    def select_all(self, instance):
        all_selected = all(self.selected_questions)
        new_state = not all_selected
        for i in range(len(self.selected_questions)):
            self.selected_questions[i] = new_state
        self.questions_container.clear_widgets()
        for i, question_data in enumerate(self.questions_data):
            question_item = self.create_question_item(question_data, i)
            self.questions_container.add_widget(question_item)

    def save_selected_questions(self, instance):
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

    def on_cancel(self, instance):
        self.dismiss()
        if self.cancel_callback:
            self.cancel_callback()

    def show_error(self, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        ok_btn = Button(text='确定', size_hint_y=0.3)
        popup = Popup(title='提示', content=content, size_hint=(0.6, 0.3))
        ok_btn.bind(on_press=popup.dismiss)
        content.add_widget(ok_btn)
        popup.open()


class EnhancedUploadPopup(Popup):
    """增强版上传文件弹窗"""
    def __init__(self, upload_callback=None, **kwargs):
        super(EnhancedUploadPopup, self).__init__(**kwargs)
        self.upload_callback = upload_callback
        self.title = "上传题目材料"
        self.size_hint = (0.8, 0.7)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        title_label = Label(text="选择上传方式", size_hint_y=0.1, font_size='18sp')
        layout.add_widget(title_label)

        button_layout = BoxLayout(orientation='vertical', size_hint_y=0.7, spacing=10)
        file_btn = Button(text="上传文本文件", size_hint_y=0.2, background_color=(0.3, 0.6, 0.9, 1))
        file_btn.bind(on_press=self.upload_file)
        image_btn = Button(text="上传图片", size_hint_y=0.2, background_color=(0.9, 0.7, 0.3, 1))
        image_btn.bind(on_press=self.upload_image)
        pdf_btn = Button(text="上传PDF文件", size_hint_y=0.2, background_color=(0.9, 0.5, 0.3, 1))
        pdf_btn.bind(on_press=self.upload_pdf)
        document_btn = Button(text="上传Office文档", size_hint_y=0.2, background_color=(0.6, 0.5, 0.8, 1))
        document_btn.bind(on_press=self.upload_document)

        button_layout.add_widget(file_btn)
        button_layout.add_widget(image_btn)
        button_layout.add_widget(pdf_btn)
        button_layout.add_widget(document_btn)
        layout.add_widget(button_layout)

        cancel_btn = Button(text="取消", size_hint_y=0.1, background_color=(0.7, 0.7, 0.7, 1))
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

        notice_label = Label(text=notice_text, size_hint_y=0.1, font_size='14sp')
        layout.add_widget(notice_label)

        self.file_chooser = FileChooserListView(filters=self.filters, size_hint_y=0.7)
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


class QuestionWorkshopScreen(Screen):
    """题目作坊主屏幕"""
    def __init__(self, **kwargs):
        super(QuestionWorkshopScreen, self).__init__(**kwargs)
        self.question_bank = None
        self.ai_assistant = None
        self.current_category_id = 0
        self.category_history = []
        self.processing_popup = None
        self._processing_cancelled = False
        self.from_focus_mode = False
        self.note_manager = QuestionNoteManager()
        Clock.schedule_once(self.init_components, 0.1)

    def init_components(self, dt=None):
        """初始化组件"""
        try:
            app = App.get_running_app()
            if app and hasattr(app, 'get_question_bank'):
                self.question_bank = app.get_question_bank()
            else:
                self.question_bank = QuestionBankV2()

            if self.ai_assistant is None:
                self.ai_assistant = AIAssistant()

            self.load_content()
        except Exception as e:
            print(f"初始化组件失败: {e}")

    def on_enter(self):
        """当进入屏幕时调用"""
        if self.question_bank is None:
            Clock.schedule_once(self.init_components, 0.1)
        else:
            Clock.schedule_once(self.load_content, 0.1)

    def load_content(self, dt=None):
        """加载当前分类的内容"""
        try:
            if not hasattr(self, 'ids') or 'content_container' not in self.ids:
                Clock.schedule_once(self.load_content, 0.1)
                return

            if self.question_bank is None:
                self.question_bank = QuestionBankV2()

            self.ids.content_container.clear_widgets()
            self.questions_cache = []
            self.update_path_breadcrumb()

            categories = self.question_bank.get_categories_by_parent(self.current_category_id)
            if categories:
                for cat in categories:
                    self.add_category_card(cat)

            if self.current_category_id != 0:
                questions = self.question_bank.get_questions_by_category(self.current_category_id)
                self.questions_cache = questions
                if questions:
                    for question in questions:
                        self.add_question_card(question)

            if not categories and (self.current_category_id == 0 or not questions):
                self.show_empty_state()

            if hasattr(self, 'ids') and 'back_button' in self.ids:
                self.ids.back_button.disabled = (self.current_category_id == 0)
        except Exception as e:
            print(f"加载内容时发生错误: {e}")

    def show_empty_state(self):
        """显示空状态"""
        empty_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=300, spacing=20, padding=40)
        with empty_box.canvas.before:
            Color(0.98, 0.98, 0.98, 1)
            empty_box.rect = Rectangle(pos=empty_box.pos, size=empty_box.size)

        empty_box.bind(pos=lambda obj, pos: setattr(empty_box.rect, 'pos', pos),
                      size=lambda obj, size: setattr(empty_box.rect, 'size', size))

        icon_label = Label(text="📂", font_size='48sp', color=(0.7, 0.7, 0.7, 1), size_hint_y=0.3)
        empty_box.add_widget(icon_label)

        if self.current_category_id == 0:
            empty_text = "这里是根目录\n\n您可以创建新的分类来组织您的题目"
        else:
            current_name = self.get_category_name(self.current_category_id)
            empty_text = f"「{current_name}」目录为空\n\n您可以添加题目或子分类"

        empty_label = Label(text=empty_text, font_size='16sp', color=(0.6, 0.6, 0.6, 1),
                           halign='center', valign='middle', size_hint_y=0.4)
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_box.add_widget(empty_label)

        quick_actions = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=20, padding=[20, 0])
        add_category_btn = Button(text="新建分类", font_size='14sp', background_color=(0.3, 0.6, 0.9, 1),
                                color=(1, 1, 1, 1))
        add_category_btn.bind(on_press=lambda x: self.show_add_category_popup())
        quick_actions.add_widget(add_category_btn)

        if self.current_category_id != 0:
            add_question_btn = Button(text="添加题目", font_size='14sp', background_color=(0.4, 0.7, 0.4, 1),
                                    color=(1, 1, 1, 1))
            add_question_btn.bind(on_press=lambda x: self.show_upload_popup())
            quick_actions.add_widget(add_question_btn)

        empty_box.add_widget(quick_actions)
        self.ids.content_container.add_widget(empty_box)

    def get_category_name(self, category_id):
        """获取分类名称"""
        if category_id == 0:
            return "根目录"

        if self.question_bank and hasattr(self.question_bank, 'get_category_info'):
            try:
                category_info = self.question_bank.get_category_info(category_id)
                if category_info and 'name' in category_info:
                    return category_info['name']
            except Exception as e:
                print(f"获取分类名称失败: {e}")

        return "未知分类"

    def update_path_breadcrumb(self):
        """更新路径面包屑导航"""
        try:
            if self.current_category_id == 0:
                path_items = [{'id': 0, 'name': '根目录'}]
            else:
                if self.question_bank and hasattr(self.question_bank, 'get_category_path_info'):
                    path_info = self.question_bank.get_category_path_info(self.current_category_id)
                    path_items = path_info if path_info else [{'id': 0, 'name': '根目录'}]
                else:
                    path_items = [{'id': 0, 'name': '根目录'}]

            if hasattr(self, 'ids') and 'path_breadcrumb' in self.ids:
                breadcrumb = self.ids.path_breadcrumb
                breadcrumb.clear_widgets()

                for i, item in enumerate(path_items):
                    btn = Button(text=item['name'], size_hint_x=None, width=100, font_size='12sp',
                               background_color=(1, 1, 1, 1), color=(0.2, 0.2, 0.2, 1),
                               bold=i == len(path_items) - 1, background_normal='', border=(0, 0, 0, 0))
                    btn.bind(on_press=lambda x, cat_id=item['id']: self.navigate_to_category(cat_id))
                    breadcrumb.add_widget(btn)

                    if i < len(path_items) - 1:
                        sep = Label(text=">", size_hint_x=None, width=20, color=(0.5, 0.5, 0.5, 1))
                        breadcrumb.add_widget(sep)
        except Exception as e:
            print(f"更新路径面包屑失败: {e}")

    def view_question_detail(self, question_id):
        """查看题目详情"""
        try:
            current_index = -1
            for i, q in enumerate(self.questions_cache):
                if q['id'] == question_id:
                    current_index = i
                    break

            if current_index == -1:
                self.show_message("提示", "题目不存在")
                return

            self.open_quick_quiz_popup(current_index)
        except Exception as e:
            print(f"打开QuickQuizPopup失败: {e}")

    def open_quick_quiz_popup(self, start_index=0):
        """打开QuickQuizPopup显示题目"""
        try:
            if not self.questions_cache:
                self.show_message("提示", "当前分类没有题目")
                return

            popup = QuickQuizPopup(question_bank=self.question_bank, questions=self.questions_cache,
                                 current_index=start_index)
            popup.open()
        except Exception as e:
            print(f"创建QuickQuizPopup失败: {e}")

    def add_category_card(self, category_data):
        """添加分类卡片到界面"""
        simple_card = BoxLayout(orientation='vertical', size_hint=(1, None), height=120, padding=10, spacing=5)
        with simple_card.canvas.before:
            Color(1, 1, 1, 1)
            simple_card.rect = Rectangle(pos=simple_card.pos, size=simple_card.size)

        simple_card.bind(pos=lambda obj, pos: setattr(simple_card.rect, 'pos', pos),
                        size=lambda obj, size: setattr(simple_card.rect, 'size', size))

        name_label = Label(text=category_data['name'], font_size='16sp', color=(0.2, 0.2, 0.2, 1),
                         bold=True, size_hint_y=0.4)
        simple_card.add_widget(name_label)

        stats_label = Label(text=f"子分类: {category_data['subcategory_count']} | 题目: {category_data['question_count']}",
                          font_size='12sp', color=(0.5, 0.5, 0.5, 1), size_hint_y=0.2)
        simple_card.add_widget(stats_label)

        button_box = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=5)
        enter_btn = Button(text="进入", font_size='12sp', background_color=(0.3, 0.6, 0.9, 1), color=(1, 1, 1, 1))
        enter_btn.bind(on_press=lambda x, cat_id=category_data['id'], cat_name=category_data['name']:
                      self.enter_category(cat_id, cat_name))
        button_box.add_widget(enter_btn)

        rename_btn = Button(text="重命名", font_size='12sp', background_color=(0.9, 0.7, 0.3, 1), color=(1, 1, 1, 1))
        rename_btn.bind(on_press=lambda x, cat_id=category_data['id'], cat_name=category_data['name']:
                       self.rename_category(cat_id, cat_name))
        button_box.add_widget(rename_btn)

        delete_btn = Button(text="删除", font_size='12sp', background_color=(0.9, 0.3, 0.3, 1), color=(1, 1, 1, 1))
        delete_btn.bind(on_press=lambda x, cat_id=category_data['id'], cat_name=category_data['name']:
                       self.delete_category_confirm(cat_id, cat_name))
        button_box.add_widget(delete_btn)

        simple_card.add_widget(button_box)
        self.ids.content_container.add_widget(simple_card)

    def add_question_card(self, question_data):
        """添加题目卡片到界面"""
        simple_card = BoxLayout(orientation='vertical', size_hint=(1, None), height=120, padding=10, spacing=5)
        with simple_card.canvas.before:
            Color(1, 1, 1, 1)
            simple_card.rect = Rectangle(pos=simple_card.pos, size=simple_card.size)

        simple_card.bind(pos=lambda obj, pos: setattr(simple_card.rect, 'pos', pos),
                        size=lambda obj, size: setattr(simple_card.rect, 'size', size))

        question_text = question_data['question']
        preview = question_text[:80] + "..." if len(question_text) > 80 else question_text

        question_label = Label(text=preview, font_size='13sp', color=(0.3, 0.3, 0.3, 1),
                             size_hint_y=0.6, halign='left', valign='top')
        question_label.bind(size=question_label.setter('text_size'))
        simple_card.add_widget(question_label)

        button_box = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=5)
        view_btn = Button(text="查看", size_hint_x=0.33, font_size='12sp', background_color=(0.4, 0.7, 0.4, 1),
                        color=(1, 1, 1, 1))
        view_btn.bind(on_press=lambda x: self.view_question_detail(question_data['id']))
        button_box.add_widget(view_btn)

        edit_btn = Button(text="编辑", size_hint_x=0.33, font_size='12sp', background_color=(0.3, 0.5, 0.8, 1),
                        color=(1, 1, 1, 1))
        edit_btn.bind(on_press=lambda x: self.edit_question(question_data['id']))
        button_box.add_widget(edit_btn)

        delete_btn = Button(text="删除", size_hint_x=0.34, font_size='12sp', background_color=(0.9, 0.3, 0.3, 1),
                          color=(1, 1, 1, 1))
        delete_btn.bind(on_press=lambda x: self.delete_question_confirm(question_data['id']))
        button_box.add_widget(delete_btn)

        simple_card.add_widget(button_box)
        self.ids.content_container.add_widget(simple_card)

    def navigate_to_category(self, category_id):
        """导航到指定分类"""
        self.current_category_id = category_id
        Clock.schedule_once(self.load_content, 0.1)

    def navigate_back(self):
        """返回上一级分类"""
        try:
            if self.current_category_id == 0:
                self.go_back()
                return

            category_info = self.question_bank.get_category_info(self.current_category_id)
            if category_info:
                parent_id = category_info['parent_id'] if category_info['parent_id'] is not None else 0
                self.current_category_id = parent_id
                Clock.schedule_once(self.load_content, 0.1)
            else:
                self.current_category_id = 0
                self.category_history = []
                Clock.schedule_once(self.load_content, 0.1)
        except Exception as e:
            print(f"返回时出错: {e}")
            self.current_category_id = 0
            Clock.schedule_once(self.load_content, 0.1)

    def go_to_main_screen(self):
        """从底部按钮跳转到主界面"""
        if self.manager:
            if self.from_focus_mode:
                self.from_focus_mode = False
                self.manager.current = 'focus'
            else:
                self.manager.current = 'main'

    def show_add_menu(self):
        """显示添加菜单"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        content.add_widget(Label(text="添加内容", font_size='18sp', color=(0.2, 0.3, 0.6, 1),
                               size_hint_y=0.2, halign='center'))

        button_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.6)
        if self.current_category_id != 0:
            add_question_btn = Button(text="添加题目", font_size='16sp', size_hint_y=0.5,
                                    background_color=(0.3, 0.6, 0.9, 1), color=(1, 1, 1, 1))
            add_question_btn.bind(on_press=lambda x: self.show_upload_popup())
            button_box.add_widget(add_question_btn)

        add_category_btn = Button(text="添加子分类", font_size='16sp', size_hint_y=0.5,
                                background_color=(0.4, 0.7, 0.4, 1), color=(1, 1, 1, 1))
        add_category_btn.bind(on_press=lambda x: self.show_add_category_popup())
        button_box.add_widget(add_category_btn)
        content.add_widget(button_box)

        close_btn = Button(text="取消", size_hint_y=0.2, background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        close_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(close_btn)

        popup = Popup(title="", content=content, size_hint=(0.6, 0.5), auto_dismiss=True)
        popup.open()

    def show_add_category_popup(self):
        """显示添加分类弹窗"""
        current_name = "根目录" if self.current_category_id == 0 else self.get_category_name(self.current_category_id)
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        content.add_widget(Label(text=f"在「{current_name}」下新建分类", font_size='16sp',
                               color=(0.2, 0.3, 0.6, 1), size_hint_y=0.2, halign='center'))

        input_box = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.4)
        name_input = TextInput(multiline=False, font_size='16sp', size_hint_y=0.6,
                             hint_text="请输入分类名称", padding=[10, 10])
        input_box.add_widget(name_input)
        content.add_widget(input_box)

        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.3)
        cancel_btn = Button(text="取消", background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_press=lambda x: popup.dismiss())

        create_btn = Button(text="创建", background_color=(0.3, 0.6, 0.9, 1), color=(1, 1, 1, 1))

        def create_category(instance):
            category_name = name_input.text.strip()
            if not category_name:
                self.show_message("提示", "分类名称不能为空")
                return

            try:
                category_id = self.question_bank.create_category(
                    category_name, self.current_category_id if self.current_category_id != 0 else None)
                popup.dismiss()
                Clock.schedule_once(self.load_content, 0.1)
            except Exception as e:
                print(f"创建分类失败: {e}")

        create_btn.bind(on_press=create_category)
        button_box.add_widget(cancel_btn)
        button_box.add_widget(create_btn)
        content.add_widget(button_box)

        popup = Popup(title="", content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()
        Clock.schedule_once(lambda dt: setattr(name_input, 'focus', True), 0.1)

    def show_upload_popup(self):
        """显示上传文件弹窗"""
        if self.current_category_id == 0:
            self.show_message("提示", "请在具体分类下添加题目")
            return

        upload_popup = EnhancedUploadPopup(upload_callback=self.handle_upload_choice)
        upload_popup.open()

    def handle_upload_choice(self, upload_type):
        """处理上传选择"""
        file_type = upload_type
        file_chooser = EnhancedFileChooserPopup(file_type=file_type, upload_callback=self.process_selected_file)
        file_chooser.open()

    def process_selected_file(self, file_path, file_type):
        """处理选择的文件"""
        if not os.path.exists(file_path):
            self.show_message("错误", f"文件不存在: {file_path}")
            return

        self.processing_popup = ProcessingPopup(cancel_callback=self.cancel_processing, file_type=file_type)
        self.processing_popup.open()
        self._processing_cancelled = False

        def process_in_background():
            try:
                if self._processing_cancelled:
                    Clock.schedule_once(lambda dt: self.processing_popup.dismiss(), 0)
                    return

                if self.ai_assistant is None:
                    self.ai_assistant = AIAssistant()

                questions = []
                if file_type == 'image':
                    questions = self.ai_assistant.process_large_file_and_extract_questions(
                        file_path, 'image', max_chunk_size=800, progress_callback=None)
                elif file_type == 'pdf':
                    questions = self.ai_assistant.process_large_file_and_extract_questions(
                        file_path, 'pdf', max_chunk_size=800, progress_callback=None)
                else:
                    questions = self.ai_assistant.process_large_file_and_extract_questions(
                        file_path, 'file', max_chunk_size=800, progress_callback=None)

                Clock.schedule_once(lambda dt: self.show_questions_preview(questions), 0)
            except Exception as e:
                print(f"处理文件失败: {e}")
                Clock.schedule_once(lambda dt: self.processing_popup.dismiss(), 0)

        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()

    def cancel_processing(self):
        """取消处理"""
        self._processing_cancelled = True
        if self.ai_assistant:
            self.ai_assistant.cancel_processing()
        if self.processing_popup:
            self.processing_popup.dismiss()

    def show_questions_preview(self, questions):
        """显示题目预览"""
        if self.processing_popup:
            self.processing_popup.dismiss()

        if not questions:
            self.show_message("提示", "未从文件中提取到题目")
            return

        preview_popup = MultiQuestionPreviewPopup(questions_data=questions,
                                                save_callback=self.process_uploaded_questions,
                                                cancel_callback=None)
        preview_popup.open()

    def process_uploaded_questions(self, selected_questions):
        """处理上传的题目 - 保存到当前分类"""
        try:
            if self.current_category_id == 0:
                self.show_message("错误", "请先进入具体分类再添加题目")
                return

            saved_count = 0
            for question_data in selected_questions:
                try:
                    self.question_bank.add_question_to_category(self.current_category_id, question_data)
                    saved_count += 1
                except Exception as e:
                    print(f"保存单个题目失败: {e}")
                    continue

            Clock.schedule_once(self.load_content, 0.5)
        except Exception as e:
            print(f"保存题目失败: {e}")

    def rename_category(self, category_id, old_name):
        """重命名分类"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        content.add_widget(Label(text="重命名分类", font_size='16sp', color=(0.2, 0.3, 0.6, 1),
                               size_hint_y=0.2, halign='center'))

        input_box = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.4)
        name_input = TextInput(text=old_name, multiline=False, font_size='16sp', size_hint_y=0.6, padding=[10, 10])
        input_box.add_widget(name_input)
        content.add_widget(input_box)

        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.3)
        cancel_btn = Button(text="取消", background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_press=lambda x: popup.dismiss())

        save_btn = Button(text="保存", background_color=(0.3, 0.6, 0.9, 1), color=(1, 1, 1, 1))

        def save_rename(instance):
            new_name = name_input.text.strip()
            if not new_name:
                self.show_message("提示", "分类名称不能为空")
                return

            if new_name == old_name:
                popup.dismiss()
                return

            try:
                success = self.question_bank.update_category_name(category_id, new_name)
                if success:
                    popup.dismiss()
                    Clock.schedule_once(self.load_content, 0.1)
            except Exception as e:
                print(f"重命名分类失败: {e}")

        save_btn.bind(on_press=save_rename)
        button_box.add_widget(cancel_btn)
        button_box.add_widget(save_btn)
        content.add_widget(button_box)

        popup = Popup(title="", content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()

    def delete_category_confirm(self, category_id, category_name):
        """确认删除分类"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        content.add_widget(Label(text=f"确认删除分类「{category_name}」？", font_size='16sp',
                               color=(0.8, 0.2, 0.2, 1), size_hint_y=0.3, halign='center'))
        content.add_widget(Label(text="警告：不可恢复！", font_size='12sp', color=(0.6, 0.3, 0.3, 1),
                               size_hint_y=0.3, halign='center'))

        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
        cancel_btn = Button(text="取消", background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_press=lambda x: popup.dismiss())

        delete_btn = Button(text="确认删除", background_color=(0.9, 0.2, 0.2, 1), color=(1, 1, 1, 1))

        def delete_category(instance):
            try:
                self.question_bank.delete_category(category_id)
                popup.dismiss()
                Clock.schedule_once(self.load_content, 0.1)
            except Exception as e:
                print(f"删除分类失败: {e}")

        delete_btn.bind(on_press=delete_category)
        button_box.add_widget(cancel_btn)
        button_box.add_widget(delete_btn)
        content.add_widget(button_box)

        popup = Popup(title="删除确认", content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        popup.open()

    def edit_question(self, question_id):
        """编辑题目"""
        self.show_message("提示", "编辑功能开发中")

    def delete_question_confirm(self, question_id):
        """确认删除题目"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        content.add_widget(Label(text="确认删除题目？", font_size='16sp', color=(0.8, 0.2, 0.2, 1),
                               size_hint_y=0.4, halign='center'))
        content.add_widget(Label(text="删除后不可恢复", font_size='14sp', color=(0.6, 0.6, 0.6, 1),
                               size_hint_y=0.2, halign='center'))

        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
        cancel_btn = Button(text="取消", background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        cancel_btn.bind(on_press=lambda x: popup.dismiss())

        delete_btn = Button(text="确认删除", background_color=(0.9, 0.2, 0.2, 1), color=(1, 1, 1, 1))

        def delete_question(instance):
            try:
                cursor = self.question_bank.conn.cursor()
                cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
                self.question_bank.conn.commit()
                popup.dismiss()
                Clock.schedule_once(self.load_content, 0.1)
            except Exception as e:
                print(f"删除题目失败: {e}")

        delete_btn.bind(on_press=delete_question)
        button_box.add_widget(cancel_btn)
        button_box.add_widget(delete_btn)
        content.add_widget(button_box)

        popup = Popup(title="删除确认", content=content, size_hint=(0.6, 0.3), auto_dismiss=False)
        popup.open()

    def show_message(self, title, message):
        """显示消息弹窗"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message, font_size='14sp', halign='center'))
        ok_btn = Button(text='确定', size_hint_y=0.3, background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.3))
        ok_btn.bind(on_press=popup.dismiss)
        content.add_widget(ok_btn)
        popup.open()

    def enter_category(self, category_id, category_name):
        """进入分类"""
        if self.current_category_id != 0:
            self.category_history.append({
                'id': self.current_category_id,
                'name': self.get_category_name(self.current_category_id)
            })

        self.current_category_id = category_id
        Clock.schedule_once(self.load_content, 0.1)

    def go_back(self):
        """返回上一级屏幕"""
        if self.manager:
            if self.from_focus_mode:
                self.from_focus_mode = False
                self.manager.current = 'focus'
            else:
                self.manager.current = 'main'