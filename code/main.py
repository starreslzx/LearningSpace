import os
from pathlib import Path
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.app import App
import time
import pytesseract
from todo_manager import TodoManager
from focus_mode import FocusMode
from ai_assistant import AIAssistant
from components import TaskDetailPopup
from question_bank import QuestionBankV2
from question_workshop import QuestionWorkshopScreen
from popup import *
from kivy.graphics import Color, Rectangle

# 配置字体路径
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
FONT_PATH = str(PROJECT_ROOT / 'fonts' / 'simhei.ttf')
FONT_DIR = str(PROJECT_ROOT / 'fonts')
TESSERACT_PATH = str(PROJECT_ROOT / 'tesseract.exe')

os.environ['KIVY_TEXT'] = FONT_DIR
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

Config.set('kivy', 'default_font', ['SimHei', FONT_PATH])
Config.set('graphics', 'default_font', ['SimHei', FONT_PATH])

try:
    LabelBase.register(name='Roboto', fn_regular=FONT_PATH)
except Exception as e:
    print(f"字体注册失败: {e}")

Builder.load_file('learning_space.kv')


def create_progress_updater(popup):
    """创建进度更新函数"""
    def update_progress(progress_percent, message):
        if popup and hasattr(popup, 'update_progress_with_percentage'):
            Clock.schedule_once(lambda dt: popup.update_progress_with_percentage(progress_percent, message), 0)
        elif popup and hasattr(popup, 'update_progress'):
            Clock.schedule_once(lambda dt: popup.update_progress(message), 0)
    return update_progress


def init_application():
    """初始化应用程序"""
    try:
        question_bank = QuestionBankV2()
        stats = question_bank.get_statistics()
        question_bank.close()
    except Exception as e:
        print(f"初始化失败: {e}")


class AutoWrapLabel(Label):
    """自动换行标签"""
    def __init__(self, **kwargs):
        super(AutoWrapLabel, self).__init__(**kwargs)
        self.size_hint_y = None
        self.bind(width=self.update_text_size, texture_size=self.update_height)

    def update_text_size(self, instance, width):
        if width > 0:
            self.text_size = (width * 0.95, None)
            self.texture_update()

    def update_height(self, instance, size):
        if size[1] > 0:
            self.height = size[1] + 20


class BoundedScrollLabel(BoxLayout):
    """带边界的滚动标签"""
    text = StringProperty("")
    font_size = NumericProperty('14sp')

    def __init__(self, **kwargs):
        super(BoundedScrollLabel, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.build_ui()
        self.bind(text=self.on_text_change)

    def build_ui(self):
        self.scroll_view = ScrollView(bar_width=6, bar_color=(0.7, 0.7, 0.7, 0.5), do_scroll_x=False)
        self.label = AutoWrapLabel(text=self.text, halign='left', valign='top', size_hint_y=None,
                                   font_size=self.font_size, color=(0.1, 0.1, 0.1, 1), line_height=1.2, padding=[10, 10])
        content_wrapper = BoxLayout(orientation='vertical', size_hint_y=None)
        content_wrapper.bind(minimum_height=content_wrapper.setter('height'))
        content_wrapper.add_widget(self.label)
        self.scroll_view.add_widget(content_wrapper)
        self.add_widget(self.scroll_view)

    def on_text_change(self, instance, value):
        self.label.text = value

    def update_height(self, max_height=300):
        label_height = self.label.texture_size[1] if self.label.texture_size else 0
        self.height = min(label_height + 40, max_height)


class MainScreen(Screen):
    """主屏幕"""
    def show_quick_quiz(self):
        """显示快速闪卡"""
        try:
            question_bank = QuestionBankV2()
            popup = QuickQuizPopup(question_bank)
            popup.open()
        except Exception as e:
            print(f"打开快速闪卡时出错: {e}")


class TodoScreen(Screen):
    """待办事项屏幕"""
    def __init__(self, **kwargs):
        super(TodoScreen, self).__init__(**kwargs)
        self.todo_manager = TodoManager()
        self.todo_manager.refresh_tasks = self.refresh_task_list
        self._is_initialized = False

    def on_enter(self):
        """进入屏幕时初始化"""
        if not self._is_initialized:
            Clock.schedule_once(self._delayed_init, 0.2)

    def _delayed_init(self, dt):
        """延迟初始化"""
        self._is_initialized = True
        self.refresh_task_list()

    def show_add_task_popup(self):
        """显示添加任务弹窗"""
        try:
            popup = TaskDetailPopup(todo_manager=self.todo_manager, refresh_callback=self.refresh_task_list)
            popup.open()
        except Exception as e:
            print(f"打开任务弹窗时出错: {e}")

    def refresh_task_list(self, *args):
        """刷新任务列表"""
        try:
            if not hasattr(self, 'ids'):
                Clock.schedule_once(self.refresh_task_list, 0.1)
                return
            if 'task_list' not in self.ids:
                Clock.schedule_once(self.refresh_task_list, 0.1)
                return

            task_list = self.ids.task_list
            task_list.clear_widgets()
            tasks = self.todo_manager.load_tasks()

            for task in tasks:
                task_list.add_widget(task)

            if len(tasks) == 0:
                self.show_empty_state()
        except Exception as e:
            print(f"刷新任务列表时出错: {e}")

    def show_empty_state(self):
        """显示空状态"""
        task_list = self.ids.task_list
        empty_box = BoxLayout(orientation='vertical', size_hint_y=None, height=200, spacing=20, padding=40)
        empty_label = Label(text="暂无待办事项\n\n点击上方 [+] 按钮添加新任务", font_size='16sp',
                           color=(0.6, 0.6, 0.6, 1), halign='center', valign='middle')
        empty_label.bind(size=empty_label.setter('text_size'))
        empty_box.add_widget(empty_label)
        task_list.add_widget(empty_box)

    def clear_completed_tasks(self):
        """清空已完成任务"""
        try:
            self.todo_manager.clear_completed_tasks()
            Clock.schedule_once(lambda dt: self.refresh_task_list(), 0.1)
        except Exception as e:
            print(f"清空已完成任务时出错: {e}")

    def clear_all_tasks(self):
        """清空所有任务"""
        try:
            content = BoxLayout(orientation='vertical', spacing=10, padding=15)
            content.add_widget(Label(text="确认清空所有任务吗？", font_size='16sp', color=(0.8, 0.2, 0.2, 1),
                                   size_hint_y=0.4, halign='center'))
            content.add_widget(Label(text="此操作不可恢复！", font_size='14sp', color=(0.6, 0.6, 0.6, 1),
                                   size_hint_y=0.2, halign='center'))

            button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=0.4)
            cancel_btn = Button(text="取消", background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
            confirm_btn = Button(text="确认清空", background_color=(0.9, 0.2, 0.2, 1), color=(1, 1, 1, 1))

            def confirm_clear(instance):
                self.todo_manager.clear_all_tasks()
                popup.dismiss()
                Clock.schedule_once(lambda dt: self.refresh_task_list(), 0.1)
                self.show_message("成功", "已清空所有任务")

            cancel_btn.bind(on_press=lambda x: popup.dismiss())
            confirm_btn.bind(on_press=confirm_clear)

            button_box.add_widget(cancel_btn)
            button_box.add_widget(confirm_btn)
            content.add_widget(button_box)

            popup = Popup(title="清空确认", content=content, size_hint=(0.6, 0.3))
            popup.open()
        except Exception as e:
            print(f"清空所有任务时出错: {e}")

    def show_message(self, title, message):
        """显示消息弹窗"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message, font_size='14sp', halign='center'))
        ok_btn = Button(text='确定', size_hint_y=0.3, background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.3))
        ok_btn.bind(on_press=popup.dismiss)
        content.add_widget(ok_btn)
        popup.open()

    def start_quick_focus(self):
        """启动快速专注"""
        self.manager.current = 'focus'
        focus_screen = self.manager.get_screen('focus')
        focus_screen.start_focus_mode('25')


class FocusScreen(Screen):
    """专注模式屏幕"""
    def __init__(self, **kwargs):
        super(FocusScreen, self).__init__(**kwargs)
        self.focus_mode = FocusMode()
        self.timer_event = None
        self.current_duration = 25
        self.confirm_count = 0
        self.confirmation_messages = [
            "不再坚持一下吗？专注不易，放弃可惜",
            "真的要退出吗？专注的每一分钟都很宝贵",
            "最后确认：确定要放弃这次专注吗？"
        ]

    def go_back(self):
        """返回主屏幕"""
        try:
            if self.focus_mode and self.focus_mode.is_active:
                self.confirm_count = 1
                self.show_exit_confirmation()
            else:
                if self.manager:
                    self.manager.current = 'main'
        except Exception as e:
            print(f"Error in go_back: {e}")
            if self.manager:
                self.manager.current = 'main'

    def handle_confirm_exit(self, instance):
        """处理确认退出"""
        if self.confirm_count < 3:
            self.confirm_count += 1
            self.exit_popup.dismiss()
            Clock.schedule_once(lambda dt: self.show_exit_confirmation(), 0.1)
        else:
            self.confirm_exit(instance)

    def handle_cancel_exit(self, instance):
        """处理取消退出"""
        self.confirm_count = 0
        self.exit_popup.dismiss()

    def confirm_exit(self, instance):
        """确认退出专注模式"""
        self.stop_focus_mode()
        self.confirm_count = 0
        if hasattr(self, 'exit_popup') and self.exit_popup:
            self.exit_popup.dismiss()
        if self.manager:
            self.manager.current = 'main'

    def show_exit_confirmation(self):
        """显示退出确认对话框"""
        if self.confirm_count > 3:
            self.confirm_exit(None)
            return

        content = BoxLayout(orientation='vertical', spacing=5, padding=[10, 15, 10, 15])
        with content.canvas.before:
            Color(1, 1, 1, 1)
            content.rect = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda obj, pos: setattr(content.rect, 'pos', pos),
                    size=lambda obj, size: setattr(content.rect, 'size', size))

        progress_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, padding=[5, 5])
        progress_text = Label(text=f"退出确认 ({self.confirm_count}/3)", font_size='16sp',
                            color=(0.2, 0.2, 0.2, 1), bold=True, size_hint_x=0.5, halign='left', valign='middle')
        progress_text.bind(size=progress_text.setter('text_size'))
        progress_box.add_widget(progress_text)

        dots_box = BoxLayout(orientation='horizontal', size_hint_x=0.5, spacing=5)
        for i in range(3):
            if i + 1 < self.confirm_count:
                color = (0.8, 0.2, 0.2, 1)
                dot_text = "●"
            elif i + 1 == self.confirm_count:
                color = (0.3, 0.6, 0.9, 1)
                dot_text = "●"
            else:
                color = (0.7, 0.7, 0.7, 0.5)
                dot_text = "○"
            dot = Label(text=dot_text, font_size='18sp', color=color)
            dots_box.add_widget(dot)
        progress_box.add_widget(dots_box)
        content.add_widget(progress_box)

        message_container = BoxLayout(orientation='vertical', size_hint_y=0.6, padding=[10, 15], spacing=15)
        msg_index = self.confirm_count - 1
        if msg_index < 0:
            msg_index = 0
        elif msg_index >= len(self.confirmation_messages):
            msg_index = len(self.confirmation_messages) - 1

        if self.confirm_count == 1:
            icon_text = "?"
        elif self.confirm_count == 2:
            icon_text = "??"
        else:
            icon_text = "???"

        icon_label = Label(text=icon_text, font_size='40sp', size_hint_y=0.3, color=(0.3, 0.3, 0.3, 1))
        message_container.add_widget(icon_label)

        message = self.confirmation_messages[msg_index]
        message_label = Label(text=message, font_size='20sp', halign='center', valign='middle',
                            size_hint_y=0.7, line_height=1.3, color=(0.1, 0.1, 0.1, 1))
        message_label.bind(size=message_label.setter('text_size'),
                          texture_size=lambda lbl, size: setattr(lbl, 'height', max(80, size[1] + 20)))
        message_container.add_widget(message_label)
        content.add_widget(message_container)

        if self.confirm_count == 3:
            warning_container = BoxLayout(orientation='horizontal', size_hint_y=0.1, padding=[10, 0], spacing=5)
            warning_icon = Label(text="注意", font_size='14sp', color=(0.9, 0.6, 0.1, 1), size_hint_x=0.2)
            warning_text = Label(text="退出后专注进度将丢失", font_size='14sp', color=(0.9, 0.6, 0.1, 1),
                               bold=True, size_hint_x=0.8, halign='left', valign='middle')
            warning_text.bind(size=warning_text.setter('text_size'))
            warning_container.add_widget(warning_icon)
            warning_container.add_widget(warning_text)
            content.add_widget(warning_container)
        else:
            placeholder = BoxLayout(size_hint_y=0.1)
            content.add_widget(placeholder)

        button_container = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=15, padding=[0, 5])
        if self.confirm_count < 3:
            confirm_text = f"继续确认 ({self.confirm_count}/3)"
            confirm_bg_color = (0.3, 0.6, 0.9, 1)
        else:
            confirm_text = "确定退出"
            confirm_bg_color = (0.9, 0.3, 0.3, 1)

        confirm_btn = Button(text=confirm_text, background_color=confirm_bg_color, color=(1, 1, 1, 1),
                           bold=True, font_size='16sp')
        confirm_btn.bind(on_press=self.handle_confirm_exit)
        cancel_btn = Button(text="取消退出", background_color=(0.2, 0.7, 0.3, 1), color=(1, 1, 1, 1),
                          bold=True, font_size='16sp')
        cancel_btn.bind(on_press=self.handle_cancel_exit)
        button_container.add_widget(confirm_btn)
        button_container.add_widget(cancel_btn)
        content.add_widget(button_container)

        self.exit_popup = Popup(title="退出专注确认", title_size='18sp', title_color=(0.2, 0.2, 0.2, 1),
                              content=content, size_hint=(0.85, 0.7), separator_color=(0.7, 0.7, 0.7, 1),
                              background='', auto_dismiss=False)
        with self.exit_popup.canvas.before:
            Color(1, 1, 1, 1)
            self.exit_popup.bg_rect = Rectangle(pos=self.exit_popup.pos, size=self.exit_popup.size)
        self.exit_popup.bind(pos=lambda obj, pos: setattr(self.exit_popup.bg_rect, 'pos', pos),
                           size=lambda obj, size: setattr(self.exit_popup.bg_rect, 'size', size))
        self.exit_popup.open()

    def on_enter(self):
        """进入屏幕时更新UI"""
        self.update_ui_state()
        self.update_duration_button()

    def update_duration_button(self):
        """更新时长按钮"""
        if hasattr(self, 'ids') and 'duration_button' in self.ids:
            self.ids.duration_button.text = f"{self.current_duration}分钟"

    def show_duration_settings(self):
        """显示时长设置"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=15)
        with content.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            content.rect = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda obj, pos: setattr(content.rect, 'pos', pos),
                    size=lambda obj, size: setattr(content.rect, 'size', size))

        content.add_widget(Label(text="选择专注时长", font_size='20sp', color=(0.1, 0.1, 0.1, 1),
                               size_hint_y=0.15, halign='center', bold=True))

        scroll_view = ScrollView(size_hint_y=0.6, bar_width=8, bar_color=(0.3, 0.3, 0.3, 0.8),
                               do_scroll_x=False, bar_inactive_color=(0.6, 0.6, 0.6, 0.5))
        duration_grid = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=[10, 0, 10, 0])
        duration_grid.bind(minimum_height=duration_grid.setter('height'))

        durations = [5, 10, 15, 20, 25, 30, 45, 60, 90, 120]
        for minutes in durations:
            is_selected = minutes == self.current_duration
            duration_btn = Button(text=f"{minutes} 分钟", size_hint_y=None, height=55, font_size='17sp',
                                background_color=(0.3, 0.6, 0.9, 1) if is_selected else (0.85, 0.85, 0.85, 1),
                                background_normal='', color=(1, 1, 1, 1) if is_selected else (0.2, 0.2, 0.2, 1),
                                border=(2, 2, 2, 2) if is_selected else (1, 1, 1, 1))
            duration_btn.bind(on_press=lambda btn, m=minutes: self.select_duration(m))
            duration_grid.add_widget(duration_btn)

        scroll_view.add_widget(duration_grid)
        content.add_widget(scroll_view)

        custom_box = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10, padding=[0, 5, 0, 5])
        custom_label = Label(text="自定义:", font_size='17sp', size_hint_x=0.3, color=(0.2, 0.2, 0.2, 1),
                           halign='right', valign='middle')
        self.custom_input = TextInput(hint_text="输入分钟数", multiline=False, font_size='16sp', size_hint_x=0.4,
                                    input_filter='int', padding=[10, 10], background_color=(1, 1, 1, 1),
                                    foreground_color=(0.2, 0.2, 0.2, 1), hint_text_color=(0.6, 0.6, 0.6, 1),
                                    cursor_color=(0.3, 0.6, 0.9, 1))
        custom_btn = Button(text="设置", font_size='16sp', size_hint_x=0.3, background_color=(0.25, 0.7, 0.35, 1),
                          background_normal='', color=(1, 1, 1, 1), bold=True)
        custom_btn.bind(on_press=self.set_custom_duration)
        custom_box.add_widget(custom_label)
        custom_box.add_widget(self.custom_input)
        custom_box.add_widget(custom_btn)
        content.add_widget(custom_box)

        button_box = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=15, padding=[0, 10, 0, 0])
        cancel_btn = Button(text="取消", font_size='16sp', background_color=(0.7, 0.7, 0.7, 1),
                          background_normal='', color=(0.2, 0.2, 0.2, 1), bold=True)
        cancel_btn.bind(on_press=lambda x: self.duration_popup.dismiss())
        button_box.add_widget(cancel_btn)
        content.add_widget(button_box)

        self.duration_popup = Popup(title="专注时长设置", title_size='18sp', title_color=(0.1, 0.1, 0.1, 1),
                                  content=content, size_hint=(0.85, 0.75), separator_color=(0.7, 0.7, 0.7, 1),
                                  background='', auto_dismiss=False)
        with self.duration_popup.canvas.before:
            Color(0.98, 0.98, 0.98, 1)
            self.duration_popup.rect = Rectangle(pos=self.duration_popup.pos, size=self.duration_popup.size)
        self.duration_popup.bind(pos=lambda obj, pos: setattr(self.duration_popup.rect, 'pos', pos),
                               size=lambda obj, size: setattr(self.duration_popup.rect, 'size', size))
        self.custom_input.text = ""
        self.duration_popup.open()
        Clock.schedule_once(lambda dt: setattr(self.custom_input, 'focus', True), 0.1)

    def select_duration(self, minutes):
        """选择时长"""
        self.current_duration = minutes
        self.update_duration_button()
        self.duration_popup.dismiss()
        if not self.focus_mode.is_active:
            self.focus_mode.set_duration(minutes)
        if hasattr(self, 'ids') and 'start_button' in self.ids:
            self.ids.start_button.text = f"开始{minutes}分钟专注"
        self.show_quick_message(f"已设置为 {minutes} 分钟")

    def set_custom_duration(self, instance):
        """设置自定义时长"""
        try:
            custom_text = self.custom_input.text.strip()
            if custom_text:
                minutes = int(custom_text)
                if 1 <= minutes <= 240:
                    self.current_duration = minutes
                    self.update_duration_button()
                    self.duration_popup.dismiss()
                    if not self.focus_mode.is_active:
                        self.focus_mode.set_duration(minutes)
                    if hasattr(self, 'ids') and 'start_button' in self.ids:
                        self.ids.start_button.text = f"开始{minutes}分钟专注"
                    self.show_quick_message(f"已设置为 {minutes} 分钟")
                else:
                    self.show_quick_message("请输入1-240之间的数字")
            else:
                self.show_quick_message("请输入分钟数")
        except ValueError:
            self.show_quick_message("请输入有效数字")

    def show_quick_message(self, message, duration=1.5):
        """显示快速消息"""
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        content.add_widget(Label(text=message, font_size='14sp', halign='center'))
        popup = Popup(title="提示", content=content, size_hint=(0.6, 0.2), auto_dismiss=True)
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), duration)

    def start_focus_mode(self, duration=None):
        """启动专注模式"""
        try:
            if self.focus_mode.is_active:
                return
            if duration is not None:
                duration_minutes = int(duration)
                self.current_duration = duration_minutes
                self.update_duration_button()
            else:
                duration_minutes = self.current_duration

            if duration_minutes > 0:
                self.focus_mode.set_duration(duration_minutes)
                self.focus_mode.start(duration_minutes)
                self.update_ui_state()
                if self.timer_event:
                    self.timer_event.cancel()
                self.timer_event = Clock.schedule_interval(self.update_timer, 1)
                self.show_quick_message(f"开始 {duration_minutes} 分钟专注", 1)
        except ValueError:
            self.start_focus_mode(self.current_duration)
        except Exception as e:
            print(f"开始专注模式时出错: {e}")

    def stop_focus_mode(self):
        """停止专注模式"""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self.focus_mode.stop()
        self.update_ui_state()

    def update_timer(self, dt=None):
        """更新计时器"""
        if self.focus_mode.is_active:
            remaining = self.focus_mode.get_remaining_time()
            if remaining <= 0:
                if self.timer_event:
                    self.timer_event.cancel()
                    self.timer_event = None
                self.focus_mode.stop()
                self.update_ui_state()
                self.show_completion_message()
            else:
                self.ids.timer_display.text = self.format_time(remaining)

    def update_ui_state(self):
        """更新UI状态"""
        if self.focus_mode.is_active:
            self.ids.start_button.disabled = True
            self.ids.start_button.text = "专注中..."
            self.ids.duration_button.disabled = True
            remaining = self.focus_mode.get_remaining_time()
            self.ids.timer_display.text = self.format_time(remaining)
        else:
            self.ids.start_button.disabled = False
            self.ids.start_button.text = f"开始{self.current_duration}分钟专注"
            self.ids.duration_button.disabled = False
            self.ids.timer_display.text = '开始专注'

    def format_time(self, seconds):
        """格式化时间显示"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def show_quick_quiz(self):
        """显示快速闪卡"""
        try:
            self.manager.current = 'workshop'
            workshop_screen = self.manager.get_screen('workshop')
            workshop_screen.from_focus_mode = True
        except Exception as e:
            print(f"跳转到题目作坊时出错: {e}")
            try:
                question_bank = QuestionBankV2()
                popup = QuickQuizPopup(question_bank)
                popup.open()
            except Exception as e2:
                print(f"打开快速闪卡弹窗也失败: {e2}")

    def show_completion_message(self):
        """显示完成消息"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        message = Label(text='专注完成！\n恭喜你坚持到了最后！', font_size='18sp')
        content.add_widget(message)
        ok_btn = Button(text='确定', size_hint_y=0.3, background_color=(0.2, 0.6, 0.2, 1))
        ok_btn.bind(on_press=lambda x: self.completion_popup.dismiss())
        content.add_widget(ok_btn)
        self.completion_popup = Popup(title='专注完成', content=content, size_hint=(0.7, 0.4), auto_dismiss=False)
        self.completion_popup.open()

    def confirm_duration(self, instance):
        """确认时长"""
        self.duration_popup.dismiss()
        if not self.focus_mode.is_active:
            self.focus_mode.set_duration(self.current_duration)
        self.show_quick_message(f"专注时长已设置为 {self.current_duration} 分钟")

    def update_duration_display(self):
        """更新时长显示"""
        self.ids.duration_display.text = f"{self.current_duration} 分钟"


class AIChatScreen(Screen):
    """AI聊天屏幕"""
    def __init__(self, **kwargs):
        super(AIChatScreen, self).__init__(**kwargs)
        self.ai_assistant = AIAssistant()
        self.chat_history = []
        self.source_type = None
        self.source_data = None
        self.original_question = None
        self.create_ui()

    def set_question_with_source(self, question_text, source_type, source_data=None):
        """设置问题来源"""
        self.original_question = question_text
        self.source_type = source_type
        self.source_data = source_data
        self.input_field.text = f"关于这道题：{question_text}\n\n请帮我解释一下："
        Clock.schedule_once(lambda dt: setattr(self.input_field, 'focus', True), 0.1)
        app = App.get_running_app()
        if app:
            app.quick_quiz_popup = source_data

    def go_back(self, instance):
        """返回"""
        app = App.get_running_app()
        if self.source_type == 'quick_quiz' and hasattr(app, 'quick_quiz_popup'):
            self.return_to_quick_quiz()
        else:
            self.manager.current = 'main'

    def return_to_quick_quiz(self):
        """返回快速闪卡"""
        app = App.get_running_app()
        if not app:
            self.manager.current = 'main'
            return
        self.manager.current = 'workshop'
        Clock.schedule_once(self._reopen_quick_quiz_popup, 0.1)

    def _reopen_quick_quiz_popup(self, dt):
        """重新打开快速闪卡弹窗"""
        try:
            app = App.get_running_app()
            if not app:
                return
            if hasattr(app, 'quick_quiz_popup') and app.quick_quiz_popup:
                popup = app.quick_quiz_popup
                if hasattr(popup, 'restore_state_from_ai_chat'):
                    popup.restore_state_from_ai_chat()
                popup.open()
                del app.quick_quiz_popup
            else:
                workshop_screen = self.manager.get_screen('workshop')
                if hasattr(workshop_screen, 'questions_cache') and workshop_screen.questions_cache:
                    workshop_screen.open_quick_quiz_popup()
                else:
                    self.show_message("提示", "无法恢复原题目")
        except Exception as e:
            print(f"重新打开快速闪卡失败: {e}")

    def show_message(self, title, message):
        """显示消息"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message, font_size='14sp', halign='center'))
        ok_btn = Button(text='确定', size_hint_y=0.3, background_color=(0.7, 0.7, 0.7, 1), color=(1, 1, 1, 1))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        ok_btn.bind(on_press=popup.dismiss)
        content.add_widget(ok_btn)
        popup.open()

    def create_ui(self):
        """创建UI"""
        layout = FloatLayout()
        title_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), pos_hint={'top': 1}, padding=[15, 5, 15, 5])
        with title_bar.canvas.before:
            Color(0.2, 0.4, 0.7, 1)
            title_bar.rect = Rectangle(pos=title_bar.pos, size=title_bar.size)
        title_bar.bind(pos=self.update_rect, size=self.update_rect)
        title_label = Label(text="AI学习助手", font_size='20sp', color=(1, 1, 1, 1), bold=True, size_hint_x=0.8)
        back_btn = Button(text='返回', font_size='16sp', background_color=(0.8, 0.8, 0.8, 0.8),
                        color=(0.2, 0.2, 0.2, 1), size_hint_x=0.2)
        back_btn.bind(on_press=self.go_back)
        title_bar.add_widget(title_label)
        title_bar.add_widget(back_btn)
        layout.add_widget(title_bar)

        self.chat_scroll = ScrollView(size_hint=(1, 0.75), pos_hint={'top': 0.92}, bar_width=8,
                                    bar_color=(0.7, 0.7, 0.7, 0.8), do_scroll_x=False)
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=[10, 10, 10, 10])
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.chat_scroll.add_widget(self.chat_layout)
        layout.add_widget(self.chat_scroll)

        input_container = BoxLayout(orientation='vertical', size_hint=(1, 0.17), pos_hint={'bottom': 1},
                                  spacing=5, padding=[10, 5, 10, 5])
        input_row = BoxLayout(orientation='horizontal', size_hint_y=0.7, spacing=10)
        self.input_field = TextInput(hint_text="请输入您的问题...", multiline=True, size_hint_x=0.7,
                                   font_size='16sp', background_color=(1, 1, 1, 1))
        send_btn = Button(text="发送", font_size='16sp', background_color=(0.3, 0.6, 0.9, 1),
                        color=(1, 1, 1, 1), size_hint_x=0.3)
        send_btn.bind(on_press=self.send_message)
        input_row.add_widget(self.input_field)
        input_row.add_widget(send_btn)
        input_container.add_widget(input_row)

        bottom_buttons = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)
        clear_btn = Button(text="清除历史", font_size='14sp', background_color=(0.8, 0.4, 0.4, 1),
                         color=(1, 1, 1, 1))
        clear_btn.bind(on_press=self.clear_chat)
        placeholder = BoxLayout(size_hint_x=0.5)
        bottom_buttons.add_widget(clear_btn)
        bottom_buttons.add_widget(placeholder)
        input_container.add_widget(bottom_buttons)
        layout.add_widget(input_container)
        self.add_widget(layout)

    def update_rect(self, instance, value):
        """更新矩形位置"""
        if hasattr(instance, 'rect'):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

    def set_question_in_input(self, question_text):
        """在输入框中设置问题"""
        self.input_field.text = f"关于这道题：{question_text}\n\n请帮我解释一下："
        Clock.schedule_once(lambda dt: setattr(self.input_field, 'focus', True), 0.1)

    def add_message(self, sender, message):
        """添加消息"""
        bubble = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=[10, 10, 10, 10])
        if sender == "user":
            bubble_color = (0.9, 0.95, 1, 1)
            align = 'right'
        else:
            bubble_color = (0.95, 0.98, 0.95, 1)
            align = 'left'

        with bubble.canvas.before:
            Color(*bubble_color)
            bubble.rect = Rectangle(pos=bubble.pos, size=bubble.size)
        bubble.bind(pos=lambda obj, pos: setattr(bubble.rect, 'pos', pos),
                   size=lambda obj, size: setattr(bubble.rect, 'size', size))

        sender_label = Label(text="你" if sender == "user" else "AI助手", font_size='12sp',
                           color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=20, halign=align,
                           text_size=(self.width * 0.7, None))
        message_label = Label(text=message, text_size=(self.width * 0.7, None), halign='left', valign='top',
                            size_hint_y=None, font_size='16sp', color=(0.2, 0.2, 0.2, 1), line_height=1.3)

        def update_message_height(label, size):
            label.height = max(30, size[1] + 10)
        message_label.bind(texture_size=update_message_height)

        def update_bubble_height():
            bubble_height = sender_label.height + message_label.height + 30
            bubble.height = max(70, bubble_height)
        message_label.bind(texture_size=lambda x, y: update_bubble_height())

        bubble.add_widget(sender_label)
        bubble.add_widget(message_label)
        update_bubble_height()
        self.chat_layout.add_widget(bubble)
        self.chat_history.append({'sender': sender, 'message': message, 'timestamp': time.time()})
        Clock.schedule_once(self.scroll_to_bottom, 0.1)

    def scroll_to_bottom(self, dt=None):
        """滚动到底部"""
        self.chat_scroll.scroll_y = 0

    def send_message(self, instance):
        """发送消息"""
        message = self.input_field.text.strip()
        if not message:
            return
        self.add_message("user", message)
        self.input_field.text = ""

        thinking_bubble = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=[10, 10, 10, 10])
        with thinking_bubble.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            thinking_bubble.rect = Rectangle(pos=thinking_bubble.pos, size=thinking_bubble.size)
        thinking_bubble.bind(pos=lambda obj, pos: setattr(thinking_bubble.rect, 'pos', pos),
                           size=lambda obj, size: setattr(thinking_bubble.rect, 'size', size))
        thinking_label = Label(text="AI正在思考...", font_size='14sp', color=(0.5, 0.5, 0.5, 1),
                             italic=True, halign='left')
        thinking_bubble.add_widget(thinking_label)
        thinking_bubble.height = 50
        self.thinking_bubble = thinking_bubble
        self.chat_layout.add_widget(thinking_bubble)
        Clock.schedule_once(self.scroll_to_bottom, 0.1)

        current_context = ""
        if self.chat_history and len(self.chat_history) > 0:
            for msg in reversed(self.chat_history):
                if msg['sender'] == 'user' and '关于这道题：' in msg['message']:
                    parts = msg['message'].split('关于这道题：')
                    if len(parts) > 1:
                        current_context = parts[1].split('\n')[0]
                        break

        Clock.schedule_once(lambda dt: self.get_ai_response_improved(message, current_context), 0.5)

    def get_ai_response_improved(self, user_message, question_context):
        """获取AI响应"""
        try:
            if hasattr(self, 'thinking_bubble') and self.thinking_bubble in self.chat_layout.children:
                self.chat_layout.remove_widget(self.thinking_bubble)

            if question_context:
                full_prompt = f"""
题目内容：
{question_context}

用户的具体问题：
{user_message}
请根据用户的具体问题回答，如果是无关问题请引导用户用户到题目上来，无法回答请表达你的抱歉，正常对话，不要用json格式
"""
                try:
                    if hasattr(self.ai_assistant, 'call_ai_api'):
                        response = self.ai_assistant.call_ai_api(full_prompt)
                    elif hasattr(self.ai_assistant, 'chat_with_question'):
                        response = self.ai_assistant.chat_with_question(question_context, user_message)
                    else:
                        import requests
                        import json
                        api_key = self.ai_assistant.api_keys[0] if self.ai_assistant.api_keys else ""
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        data = {
                            "model": "gpt-3.5-turbo",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "你是一个学习助手，请直接回答用户的问题，不要使用'我已收到您的问题'这样的开场白。"
                                },
                                {
                                    "role": "user",
                                    "content": full_prompt
                                }
                            ],
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                        response = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json=data
                        )
                        if response.status_code == 200:
                            result = response.json()
                            response = result['choices'][0]['message']['content']
                        else:
                            raise Exception(f"API请求失败: {response.status_code}")
                except Exception as api_error:
                    print(f"API调用失败: {api_error}")
                    response = f"关于您的问题：{user_message}\n\n基于题目内容：{question_context}\n\n我的解答是：由于这是一个示例，我建议您查阅相关资料或向老师请教以获得更详细的解答。"
            else:
                response = f"关于您的问题：{user_message}\n\n我建议您提供更多上下文信息，这样我能更好地为您解答。"

            self.add_message("ai", response)
        except Exception as e:
            print(f"获取AI回复时出错: {e}")
            self.add_message("ai", f"我尝试为您解答这个问题，但遇到了一些困难。\n\n请尝试重新表述您的问题，或者检查网络连接。")

    def clear_chat(self, instance):
        """清除聊天历史"""
        self.chat_layout.clear_widgets()
        self.chat_history = []
        self.input_field.text = ""

    def reopen_quick_quiz(self, dt):
        """重新打开快速闪卡"""
        try:
            app = App.get_running_app()
            if app and app.root:
                main_screen = app.root.get_screen('main')
                if hasattr(main_screen, 'show_quick_quiz'):
                    main_screen.show_quick_quiz()
        except Exception as e:
            print(f"重新打开快速闪卡失败: {e}")
            self.manager.current = 'main'


class LearningSpaceApp(App):
    """学习空间应用"""
    def build(self):
        """构建应用"""
        init_application()
        Window.size = (400, 600)
        self.global_question_bank = None
        sm = ScreenManager()

        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(TodoScreen(name='todo'))
        sm.add_widget(FocusScreen(name='focus'))
        sm.add_widget(QuestionWorkshopScreen(name='workshop'))
        sm.add_widget(AIChatScreen(name='ai_chat'))

        sm.current = 'main'
        return sm

    def on_start(self):
        """应用启动时调用"""
        pass

    def get_question_bank(self):
        """获取题库"""
        if self.global_question_bank is None:
            try:
                from question_bank import QuestionBankV2
                self.global_question_bank = QuestionBankV2()
            except Exception as e:
                print(f"创建全局数据库连接失败: {e}")
                return None
        return self.global_question_bank

    def on_stop(self):
        """应用停止时调用"""
        if hasattr(self, 'global_question_bank') and self.global_question_bank:
            try:
                self.global_question_bank.close()
            except Exception as e:
                print(f"关闭数据库连接失败: {e}")

    def on_pause(self):
        """应用暂停时调用"""
        return True

    def on_resume(self):
        """应用恢复时调用"""
        pass


if __name__ == '__main__':
    LearningSpaceApp().run()