from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import NumericProperty, StringProperty, ObjectProperty


class CategoryCard(BoxLayout):
    """分类卡片组件"""
    category_id = NumericProperty(0)
    category_name = StringProperty("")
    parent_id = NumericProperty(0)
    subcategory_count = NumericProperty(0)
    question_count = NumericProperty(0)
    on_enter_callback = ObjectProperty(None)
    on_rename_callback = ObjectProperty(None)
    on_delete_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CategoryCard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = 120
        self.padding = [10, 10]
        self.spacing = 5

        # 设置背景色
        self.background_normal = ''
        self.background_color = [0.95, 0.95, 0.95, 1]

        self.create_content()

    def create_content(self):
        """创建卡片内容"""
        # 清除现有内容
        self.clear_widgets()

        # 分类名称
        name_label = Label(
            text=self.category_name,
            font_size='16sp',
            color=(0.2, 0.2, 0.6, 1),
            bold=True,
            size_hint_y=0.4,
            halign='left',
            valign='middle'
        )
        self.add_widget(name_label)

        # 统计信息
        stats_label = Label(
            text=f"子分类: {self.subcategory_count} | 题目: {self.question_count}",
            font_size='12sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.2,
            halign='left',
            valign='middle'
        )
        self.add_widget(stats_label)

        # 操作按钮
        button_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.4,
            spacing=5
        )

        # 进入按钮
        enter_btn = Button(
            text="进入",
            font_size='12sp',
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1)
        )
        enter_btn.bind(on_press=self.on_enter)
        button_box.add_widget(enter_btn)

        # 重命名按钮
        rename_btn = Button(
            text="重命名",
            font_size='12sp',
            background_color=(0.9, 0.7, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        rename_btn.bind(on_press=self.on_rename)
        button_box.add_widget(rename_btn)

        # 删除按钮
        delete_btn = Button(
            text="删除",
            font_size='12sp',
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        delete_btn.bind(on_press=self.on_delete)
        button_box.add_widget(delete_btn)

        self.add_widget(button_box)

    def on_enter(self, instance):
        """进入分类"""
        print(f"CategoryCard: 进入分类 {self.category_id}, {self.category_name}")
        if self.on_enter_callback:
            self.on_enter_callback(self.category_id, self.category_name)
        else:
            print("警告: on_enter_callback 未设置")

    def on_rename(self, instance):
        """重命名分类"""
        print(f"CategoryCard: 重命名分类 {self.category_id}, {self.category_name}")
        if self.on_rename_callback:
            self.on_rename_callback(self.category_id, self.category_name)
        else:
            print("警告: on_rename_callback 未设置")

    def on_delete(self, instance):
        """删除分类"""
        print(f"CategoryCard: 删除分类 {self.category_id}, {self.category_name}")
        if self.on_delete_callback:
            self.on_delete_callback(self.category_id, self.category_name)
        else:
            print("警告: on_delete_callback 未设置")