from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty, ListProperty


class CategoryCard(BoxLayout):
    """分类卡片组件"""
    category_id = NumericProperty(0)
    category_name = StringProperty("")
    parent_id = NumericProperty(0)
    subcategory_count = NumericProperty(0)
    question_count = NumericProperty(0)
    on_enter_callback = ObjectProperty(None)
    on_delete_callback = ObjectProperty(None)
    on_rename_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CategoryCard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = 140
        self.padding = [10, 10]
        self.spacing = 5
        self.background_normal = ''
        self.background_color = [0.95, 0.95, 0.95, 1]
        self.create_content()

    def create_content(self):
        self.clear_widgets()

        name_label = Label(text=self.category_name, font_size='16sp', color=(0.2, 0.2, 0.6, 1),
                           bold=True, size_hint_y=0.4, halign='left', valign='middle')
        name_label.bind(size=name_label.setter('text_size'))
        self.add_widget(name_label)

        stats_label = Label(text=f"子分类: {self.subcategory_count} | 题目: {self.question_count}",
                            font_size='12sp', color=(0.4, 0.4, 0.4, 1), size_hint_y=0.2,
                            halign='left', valign='middle')
        self.add_widget(stats_label)

        button_box = BoxLayout(orientation='horizontal', size_hint_y=0.4, spacing=5)

        enter_btn = Button(text="进入", font_size='12sp', background_color=(0.3, 0.6, 0.9, 1),
                           color=(1, 1, 1, 1))
        enter_btn.bind(on_press=self.on_enter)
        button_box.add_widget(enter_btn)

        rename_btn = Button(text="重命名", font_size='12sp', background_color=(0.9, 0.7, 0.3, 1),
                            color=(1, 1, 1, 1))
        rename_btn.bind(on_press=self.on_rename)
        button_box.add_widget(rename_btn)

        delete_btn = Button(text="删除", font_size='12sp', background_color=(0.9, 0.3, 0.3, 1),
                            color=(1, 1, 1, 1))
        delete_btn.bind(on_press=self.on_delete)
        button_box.add_widget(delete_btn)

        self.add_widget(button_box)

    def on_enter(self, instance):
        if self.on_enter_callback:
            self.on_enter_callback(self.category_id, self.category_name)

    def on_rename(self, instance):
        if self.on_rename_callback:
            self.on_rename_callback(self.category_id, self.category_name)

    def on_delete(self, instance):
        if self.on_delete_callback:
            self.on_delete_callback(self.category_id, self.category_name)


class QuestionCard(BoxLayout):
    """题目卡片组件"""
    question_id = NumericProperty(0)
    question_text = StringProperty("")
    question_preview = StringProperty("")
    answer_text = StringProperty("")
    difficulty = NumericProperty(3)
    question_type = StringProperty("简答题")
    on_view_callback = ObjectProperty(None)
    on_edit_callback = ObjectProperty(None)
    on_delete_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(QuestionCard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = 180
        self.padding = [10, 10]
        self.spacing = 5
        self.background_normal = ''
        self.background_color = [1, 1, 1, 1]
        self.create_content()

    def create_content(self):
        self.clear_widgets()

        header_box = BoxLayout(orientation='horizontal', size_hint_y=0.2)

        type_label = Label(text=f"[{self.question_type}]", font_size='12sp', color=(0.3, 0.5, 0.3, 1),
                           bold=True, size_hint_x=0.7)
        header_box.add_widget(type_label)

        diff_label = Label(text=f"难度: {self.difficulty}", font_size='11sp', color=(0.5, 0.5, 0.5, 1),
                           size_hint_x=0.3)
        header_box.add_widget(diff_label)
        self.add_widget(header_box)

        preview_label = Label(text=self.question_preview, font_size='13sp', color=(0, 0, 0, 1),
                              size_hint_y=0.5, halign='left', valign='top', text_size=(None, None))
        preview_label.bind(size=preview_label.setter('text_size'))
        self.add_widget(preview_label)

        button_box = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=5)

        view_btn = Button(text="查看", font_size='12sp', background_color=(0.4, 0.7, 0.4, 1),
                          color=(1, 1, 1, 1))
        view_btn.bind(on_press=self.on_view)
        button_box.add_widget(view_btn)

        edit_btn = Button(text="编辑", font_size='12sp', background_color=(0.3, 0.5, 0.8, 1),
                          color=(1, 1, 1, 1))
        edit_btn.bind(on_press=self.on_edit)
        button_box.add_widget(edit_btn)

        delete_btn = Button(text="删除", font_size='12sp', background_color=(0.9, 0.3, 0.3, 1),
                            color=(1, 1, 1, 1))
        delete_btn.bind(on_press=self.on_delete)
        button_box.add_widget(delete_btn)

        self.add_widget(button_box)

    def on_view(self, instance):
        if self.on_view_callback:
            self.on_view_callback(self.question_id)

    def on_edit(self, instance):
        if self.on_edit_callback:
            self.on_edit_callback(self.question_id)

    def on_delete(self, instance):
        if self.on_delete_callback:
            self.on_delete_callback(self.question_id)


class PathBreadcrumb(BoxLayout):
    """路径面包屑导航组件"""
    path_items = ListProperty([])
    navigate_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PathBreadcrumb, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 40
        self.spacing = 2
        self.padding = [5, 5]
        self.bind(path_items=self.update_breadcrumb)

    def update_breadcrumb(self, instance, value):
        self.clear_widgets()
        for i, item in enumerate(self.path_items):
            if i > 0:
                sep_label = Label(text=">", font_size='14sp', color=(0.6, 0.6, 0.6, 1),
                                  size_hint_x=None, width=20)
                self.add_widget(sep_label)

            path_btn = Button(text=item['name'], font_size='14sp', background_color=(0.95, 0.95, 0.95, 1),
                              color=(0.3, 0.5, 0.8, 1) if i < len(self.path_items) - 1 else (0.2, 0.2, 0.2, 1),
                              size_hint_x=None, width=min(len(item['name']) * 10 + 20, 150),
                              background_normal='', background_down='')

            if i < len(self.path_items) - 1:
                path_btn.bind(on_press=lambda btn, item_id=item['id']: self.on_item_click(item_id))
            else:
                path_btn.disabled = True

            self.add_widget(path_btn)

    def on_item_click(self, item_id):
        if self.navigate_callback:
            self.navigate_callback(item_id)


class AutoHeightLabel(Label):
    """自适应高度的标签"""

    def __init__(self, **kwargs):
        super(AutoHeightLabel, self).__init__(**kwargs)
        self.size_hint_y = None
        self.text_size = (self.width, None)
        self.bind(text=self.update_height, width=self.update_height, texture_size=self.update_height)

    def update_height(self, *args):
        self.text_size = (self.width, None)
        if self.texture_size:
            self.height = self.texture_size[1] + 20
        else:
            self.height = 30


class UploadPopup(Popup):
    """上传文件弹窗"""

    def __init__(self, upload_callback=None, **kwargs):
        super(UploadPopup, self).__init__(**kwargs)
        self.upload_callback = upload_callback
        self.title = "上传题目材料"
        self.size_hint = (0.8, 0.7)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text="选择上传方式", size_hint_y=0.1, font_size='18sp'))

        button_layout = BoxLayout(orientation='vertical', size_hint_y=0.7, spacing=10)

        file_btn = Button(text="上传文本文件", size_hint_y=0.2, background_color=(0.3, 0.6, 0.9, 1))
        file_btn.bind(on_press=self.upload_file)
        button_layout.add_widget(file_btn)

        image_btn = Button(text="上传图片", size_hint_y=0.2, background_color=(0.9, 0.7, 0.3, 1))
        image_btn.bind(on_press=self.upload_image)
        button_layout.add_widget(image_btn)

        pdf_btn = Button(text="上传PDF文件", size_hint_y=0.2, background_color=(0.9, 0.5, 0.3, 1))
        pdf_btn.bind(on_press=self.upload_pdf)
        button_layout.add_widget(pdf_btn)

        document_btn = Button(text="上传Office文档", size_hint_y=0.2, background_color=(0.6, 0.5, 0.8, 1))
        document_btn.bind(on_press=self.upload_document)
        button_layout.add_widget(document_btn)

        layout.add_widget(button_layout)

        notice_label = Label(
            text="支持格式:\n文本: .txt, .md\n图片: .png, .jpg, .jpeg, .bmp, .gif, .webp\nPDF: .pdf\n文档: .doc, .docx, .ppt, .pptx, .xls, .xlsx",
            size_hint_y=0.1, font_size='12sp', color=(0.4, 0.4, 0.4, 1))
        layout.add_widget(notice_label)

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


class FileChooserPopup(Popup):
    """文件选择弹窗"""

    def __init__(self, file_type='file', upload_callback=None, **kwargs):
        super(FileChooserPopup, self).__init__(**kwargs)
        self.file_type = file_type
        self.upload_callback = upload_callback

        if file_type == 'image':
            self.title = "选择图片"
            self.filters = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.webp']
        elif file_type == 'pdf':
            self.title = "选择PDF文件"
            self.filters = ['*.pdf']
        elif file_type == 'document':
            self.title = "选择文档"
            self.filters = ['*.doc', '*.docx', '*.ppt', '*.pptx', '*.xls', '*.xlsx']
        else:
            self.title = "选择文件"
            self.filters = ['*.txt', '*.md', '*.pdf', '*.doc', '*.docx']

        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = False
        self.create_ui()


class QuestionPreviewPopup(Popup):
    """题目预览弹窗"""

    def __init__(self, question_data, save_callback=None, **kwargs):
        super(QuestionPreviewPopup, self).__init__(**kwargs)
        self.question_data = question_data
        self.save_callback = save_callback
        self.title = "题目预览"
        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = False
        self.create_ui()

    def create_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        type_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        type_layout.add_widget(Label(text="题目类型:", size_hint_x=0.3))
        self.type_input = TextInput(text=self.question_data.get('type', '选择题'),
                                    multiline=False, size_hint_x=0.7)
        type_layout.add_widget(self.type_input)
        layout.add_widget(type_layout)

        category_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        category_layout.add_widget(Label(text="题目分类:", size_hint_x=0.3))
        self.category_input = TextInput(text=self.question_data.get('category', '默认'),
                                        multiline=False, size_hint_x=0.7)
        category_layout.add_widget(self.category_input)
        layout.add_widget(category_layout)

        question_layout = BoxLayout(orientation='vertical', size_hint_y=0.4)
        question_layout.add_widget(Label(text="题目内容:", size_hint_y=0.2))
        self.question_input = TextInput(text=self.question_data.get('question', ''),
                                        multiline=True, size_hint_y=0.8)
        question_layout.add_widget(self.question_input)
        layout.add_widget(question_layout)

        answer_layout = BoxLayout(orientation='vertical', size_hint_y=0.3)
        answer_layout.add_widget(Label(text="参考答案:", size_hint_y=0.2))
        self.answer_input = TextInput(text=self.question_data.get('answer', ''),
                                      multiline=True, size_hint_y=0.8)
        answer_layout.add_widget(self.answer_input)
        layout.add_widget(answer_layout)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        cancel_btn = Button(text="取消")
        cancel_btn.bind(on_press=self.dismiss)
        save_btn = Button(text="保存题目")
        save_btn.bind(on_press=self.save_question)
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(save_btn)
        layout.add_widget(button_layout)

        self.content = layout

    def save_question(self, instance):
        updated_data = {
            'type': self.type_input.text,
            'category': self.category_input.text,
            'question': self.question_input.text,
            'answer': self.answer_input.text,
            'difficulty': self.question_data.get('difficulty', 3)
        }
        self.dismiss()
        if self.save_callback:
            self.save_callback(updated_data)


class TaskDetailPopup(Popup):
    """任务详情弹窗"""

    def __init__(self, todo_manager, task_text="", task_description="", task_id=None, refresh_callback=None, **kwargs):
        super(TaskDetailPopup, self).__init__(**kwargs)
        self.todo_manager = todo_manager
        self.task_id = task_id
        self.refresh_callback = refresh_callback
        self.title = "编辑任务" if task_id else "添加新任务"
        self.size_hint = (0.8, 0.6)
        self.auto_dismiss = False
        self.create_ui(task_text, task_description)

    def create_ui(self, task_text, task_description):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        name_layout = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        name_layout.add_widget(Label(text="任务名称:", size_hint_y=0.3))
        self.name_input = TextInput(text=task_text, multiline=False, size_hint_y=0.7)
        name_layout.add_widget(self.name_input)
        layout.add_widget(name_layout)

        desc_layout = BoxLayout(orientation='vertical', size_hint_y=0.5, spacing=5)
        desc_layout.add_widget(Label(text="任务描述:", size_hint_y=0.2))
        self.desc_input = TextInput(text=task_description, multiline=True, size_hint_y=0.8)
        desc_layout.add_widget(self.desc_input)
        layout.add_widget(desc_layout)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=10)
        cancel_btn = Button(text='取消')
        cancel_btn.bind(on_press=self.dismiss)
        save_btn = Button(text='保存')
        save_btn.bind(on_press=self.save_task)
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(save_btn)
        layout.add_widget(button_layout)

        self.content = layout

    def save_task(self, instance):
        name = self.name_input.text.strip()
        description = self.desc_input.text.strip()
        if not name:
            return

        if self.task_id:
            self.todo_manager.update_task(self.task_id, name, description)
        else:
            self.todo_manager.add_task(name, description)

        if self.refresh_callback:
            self.refresh_callback()
        self.dismiss()


class CategoryItem(BoxLayout):
    """分类项"""
    category_name = StringProperty("")
    question_count = NumericProperty(0)
    is_expanded = BooleanProperty(False)

    def __init__(self, category_name, question_count, toggle_callback=None, **kwargs):
        super(CategoryItem, self).__init__(**kwargs)
        self.category_name = category_name
        self.question_count = question_count
        self.toggle_callback = toggle_callback

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.toggle_callback:
            self.toggle_callback(self.category_name, self.is_expanded)


class DraggableTaskItem(BoxLayout):
    """可拖拽的任务项"""
    task_text = StringProperty("")
    task_description = StringProperty("")
    is_completed = BooleanProperty(False)
    task_id = NumericProperty(0)

    def __init__(self, **kwargs):
        super(DraggableTaskItem, self).__init__(**kwargs)

    def setup(self, task_id, text, description, completed, todo_manager, refresh_callback):
        self.task_id = task_id
        self.task_text = text
        self.task_description = description
        self.is_completed = completed
        self.todo_manager = todo_manager
        self.refresh_callback = refresh_callback

    def on_checkbox_active(self, checkbox, value):
        self.is_completed = value
        if value and self.todo_manager:
            self.todo_manager.complete_task(self.task_id)
            if self.refresh_callback:
                Clock.schedule_once(lambda dt: self.refresh_callback(), 0.1)

    def delete_task(self, instance=None):
        if self.todo_manager:
            self.todo_manager.delete_task(self.task_id)
            if self.refresh_callback:
                Clock.schedule_once(lambda dt: self.refresh_callback(), 0.1)

    def edit_task(self, instance=None):
        popup = TaskDetailPopup(todo_manager=self.todo_manager, task_text=self.task_text,
                                task_description=self.task_description, task_id=self.task_id,
                                refresh_callback=self.refresh_callback)
        popup.open()

    def move_up(self):
        if self.todo_manager:
            self.todo_manager.move_task_up(self.task_id)
            if self.refresh_callback:
                Clock.schedule_once(lambda dt: self.refresh_callback(), 0.1)

    def move_down(self):
        if self.todo_manager:
            self.todo_manager.move_task_down(self.task_id)
            if self.refresh_callback:
                Clock.schedule_once(lambda dt: self.refresh_callback(), 0.1)


class QuickQuestionCard(BoxLayout):
    """快速闪卡组件"""
    question_text = StringProperty("")
    answer_text = StringProperty("")
    category = StringProperty("")
    difficulty = NumericProperty(1)
    show_answer = BooleanProperty(False)

    def __init__(self, question_data, **kwargs):
        super(QuickQuestionCard, self).__init__(**kwargs)
        self.question_text = question_data.get("question", "")
        self.answer_text = question_data.get("answer", "")
        self.category = question_data.get("category", "默认")
        self.difficulty = question_data.get("difficulty", 1)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        Clock.schedule_once(self.update_height, 0.1)

    def update_height(self, dt=None):
        question_lines = len(self.question_text) // 60 + 1
        answer_lines = len(self.answer_text) // 60 + 1
        base_height = 60
        text_height = (question_lines + answer_lines) * 30
        total_height = base_height + text_height
        total_height = max(100, min(500, total_height))
        self.height = total_height

    def toggle_answer(self):
        self.show_answer = not self.show_answer
        Clock.schedule_once(self.update_height, 0.1)


class ChatBubble(BoxLayout):
    """聊天气泡组件"""
    text = StringProperty("")
    is_user = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(ChatBubble, self).__init__(**kwargs)
        self.size_hint_y = None
        self.bind(text=self.update_height)

    def update_height(self, *args):
        lines = len(self.text) // 40 + 1
        self.height = max(60, lines * 25 + 20)

    @property
    def bubble_color(self):
        return (0.85, 0.85, 0.85, 1) if not self.is_user else (0.7, 0.9, 0.7, 1)