import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json
import os
import ctypes
from ctypes import windll
from PIL import Image, ImageDraw, ImageTk

class ModernTodoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Todo & DDL")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 窗口尺寸
        window_width = 380
        window_height = 600
        
        # 计算位置：右上角往中心偏移
        # 距离右边缘100px，距离顶部80px
        x_position = screen_width - window_width + 200
        y_position = 50
        
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.minsize(320, 450)
        
        # 设置DPI感知，提高清晰度
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except:
                pass
        
        # 设置窗口置顶和去除标题栏
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # iOS 风格配色
        self.bg_color = "#FFFFFF"
        self.secondary_bg = "#F2F2F7"
        self.accent_color = "#007AFF"
        self.accent_hover = "#0051D5"
        self.text_primary = "#000000"
        self.text_secondary = "#8E8E93"
        self.border_color = "#E5E5EA"
        self.success_color = "#34C759"
        self.warning_color = "#FF9500"
        self.danger_color = "#FF3B30"
        
        # 设置窗口样式
        self.root.configure(bg='#000001')  # 设置透明色键
        
        # 数据文件路径
        self.data_file = "todos.json"
        self.todos = self.load_todos()
        
        # 用于拖动和调整大小
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.resize_edge = None
        
        self.setup_ui()
        
        # 应用圆角效果（Windows 11）
        self.apply_rounded_corners()
        
        self.refresh_todo_list()
        
        
    def apply_rounded_corners(self):
        """应用Windows 11圆角效果"""
        try:
            hwnd = windll.user32.GetParent(self.root.winfo_id())
            
            # Windows 11的窗口圆角API
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int)
            )
        except:
            # 如果不是Windows 11或API调用失败，使用备选方案
            pass
            
    def setup_ui(self):
        # 主容器 - 圆角背景
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 顶部区域（包含标题和日期）- 可拖动
        header = tk.Frame(main_container, bg=self.bg_color, cursor="fleur")
        header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # 当前日期显示
        current_date = datetime.now()
        date_text = current_date.strftime("%m月%d日 %A")
        weekday_map = {
            'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
            'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'
        }
        for en, zh in weekday_map.items():
            date_text = date_text.replace(en, zh)
            
        date_label = tk.Label(header, text=date_text,
                             bg=self.bg_color, fg=self.text_secondary,
                             font=("PingFang SC", 11), cursor="fleur")
        date_label.pack(anchor=tk.W)
        
        # 标题
        title_frame = tk.Frame(header, bg=self.bg_color, cursor="fleur")
        title_frame.pack(fill=tk.X, pady=(5, 0))
        
        title_label = tk.Label(title_frame, text="Todo & DDL",
                              bg=self.bg_color, fg=self.text_primary,
                              font=("PingFang SC", 20, "bold"), cursor="fleur")
        title_label.pack(side=tk.LEFT)
        
        # 控制按钮容器
        controls = tk.Frame(title_frame, bg=self.bg_color)
        controls.pack(side=tk.RIGHT)
        
        # 最小化按钮
        minimize_btn = tk.Label(controls, text="─",
                               bg=self.bg_color, fg=self.text_secondary,
                               font=("Arial", 16), cursor="hand2")
        minimize_btn.pack(side=tk.LEFT, padx=5)
        minimize_btn.bind('<Button-1>', lambda e: self.minimize_window())
        minimize_btn.bind('<Enter>', lambda e: minimize_btn.config(fg=self.text_primary))
        minimize_btn.bind('<Leave>', lambda e: minimize_btn.config(fg=self.text_secondary))
        
        # 关闭按钮
        close_btn = tk.Label(controls, text="✕",
                            bg=self.bg_color, fg=self.text_secondary,
                            font=("Arial", 16), cursor="hand2")
        close_btn.pack(side=tk.LEFT, padx=5)
        close_btn.bind('<Button-1>', lambda e: self.root.quit())
        close_btn.bind('<Enter>', lambda e: close_btn.config(fg=self.danger_color))
        close_btn.bind('<Leave>', lambda e: close_btn.config(fg=self.text_secondary))
        
        # 绑定标题栏拖动
        header.bind('<Button-1>', self.start_drag)
        header.bind('<B1-Motion>', self.do_drag)
        date_label.bind('<Button-1>', self.start_drag)
        date_label.bind('<B1-Motion>', self.do_drag)
        title_label.bind('<Button-1>', self.start_drag)
        title_label.bind('<B1-Motion>', self.do_drag)
        title_frame.bind('<Button-1>', self.start_drag)
        title_frame.bind('<B1-Motion>', self.do_drag)
        
        # 统计信息
        self.stats_frame = tk.Frame(main_container, bg=self.secondary_bg, 
                                    highlightthickness=0)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=(10, 15))
        
        self.stats_label = tk.Label(self.stats_frame, text="",
                                    bg=self.secondary_bg, fg=self.text_secondary,
                                    font=("PingFang SC", 10), pady=8)
        self.stats_label.pack()
        
        # 输入区域（固定在底部）
        input_outer = tk.Frame(main_container, bg=self.secondary_bg)
        input_outer.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 内部padding容器
        input_container = tk.Frame(input_outer, bg=self.secondary_bg)
        input_container.pack(fill=tk.X, padx=20, pady=20)
        
        # 任务输入框
        task_frame = tk.Frame(input_container, bg="white", 
                             highlightbackground=self.border_color, 
                             highlightthickness=1)
        task_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.task_entry = tk.Entry(task_frame, font=("PingFang SC", 13),
                                   relief=tk.FLAT, bd=0, bg="white",
                                   fg=self.text_primary,
                                   insertbackground=self.accent_color)
        self.task_entry.pack(fill=tk.X, padx=15, pady=12)
        self.task_entry.insert(0, "")
        self.task_entry.bind('<FocusIn>', self.on_task_focus_in)
        self.task_entry.bind('<FocusOut>', self.on_task_focus_out)
        self.task_entry.bind('<Return>', lambda e: self.add_todo())
        self.task_entry.config(fg=self.text_secondary)
        
        # DDL选择器
        ddl_frame = tk.Frame(input_container, bg="white",
                            highlightbackground=self.border_color,
                            highlightthickness=1)
        ddl_frame.pack(fill=tk.X, pady=(0, 10))
        
        ddl_inner = tk.Frame(ddl_frame, bg="white")
        ddl_inner.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(ddl_inner, text="📅", bg="white",
                font=("Arial", 14)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.date_entry = tk.Entry(ddl_inner, font=("PingFang SC", 12),
                                   relief=tk.FLAT, bd=0, bg="white",
                                   width=12, fg=self.text_primary,
                                   insertbackground=self.accent_color)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(ddl_inner, text="🕐", bg="white",
                font=("Arial", 14)).pack(side=tk.LEFT, padx=(0, 8))
        
        self.time_entry = tk.Entry(ddl_inner, font=("PingFang SC", 12),
                                   relief=tk.FLAT, bd=0, bg="white",
                                   width=8, fg=self.text_primary,
                                   insertbackground=self.accent_color)
        self.time_entry.insert(0, "23:59")
        self.time_entry.pack(side=tk.LEFT)
        
        # 添加按钮
        self.add_button = tk.Frame(input_container, bg=self.accent_color,
                                   cursor="hand2")
        self.add_button.pack(fill=tk.X)
        
        add_label = tk.Label(self.add_button, text="添加", 
                            bg=self.accent_color, fg="white",
                            font=("PingFang SC", 14, "bold"),
                            cursor="hand2")
        add_label.pack(pady=12)
        
        self.add_button.bind('<Button-1>', lambda e: self.add_todo())
        add_label.bind('<Button-1>', lambda e: self.add_todo())
        self.add_button.bind('<Enter>', lambda e: self.on_add_button_hover(True))
        self.add_button.bind('<Leave>', lambda e: self.on_add_button_hover(False))
        add_label.bind('<Enter>', lambda e: self.on_add_button_hover(True))
        add_label.bind('<Leave>', lambda e: self.on_add_button_hover(False))
        
        # 待办列表容器（在输入区域上方，填充剩余空间）
        list_container = tk.Frame(main_container, bg=self.bg_color)
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # Canvas用于滚动
        self.canvas = tk.Canvas(list_container, bg=self.bg_color,
                               highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条容器
        scrollbar_container = tk.Frame(list_container, bg=self.bg_color, width=8)
        scrollbar_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 自定义滚动条
        self.scrollbar = tk.Canvas(scrollbar_container, bg=self.bg_color,
                                   width=4, highlightthickness=0)
        self.scrollbar.pack(fill=tk.Y, expand=True)
        
        # 滚动条指示器
        self.scroll_indicator = self.scrollbar.create_rectangle(
            0, 0, 4, 50, fill=self.border_color, outline=""
        )
        
        # 内部Frame
        self.todo_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.canvas_window = self.canvas.create_window((0, 0), 
                                                       window=self.todo_frame,
                                                       anchor=tk.NW)
        
        self.todo_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # 绑定鼠标滚轮事件到多个组件
        self.bind_mousewheel(self.canvas)
        self.bind_mousewheel(self.todo_frame)
        self.bind_mousewheel(list_container)
        
        # 绑定canvas滚动事件来更新滚动条
        self.canvas.bind('<Configure>', self.update_scrollbar)
        
        # 绑定窗口边缘调整大小
        self.root.bind('<Motion>', self.check_resize_cursor)
        self.root.bind('<Button-1>', self.start_resize)
        self.root.bind('<B1-Motion>', self.do_resize)
        self.root.bind('<ButtonRelease-1>', self.stop_resize)
        
    def check_resize_cursor(self, event):
        """检查鼠标位置并改变光标"""
        if hasattr(self, 'resizing') and self.resizing:
            return
            
        edge_size = 10
        x, y = event.x, event.y
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # 检测边缘位置
        on_right = width - edge_size <= x <= width
        on_bottom = height - edge_size <= y <= height
        on_left = 0 <= x <= edge_size
        on_top = 0 <= y <= edge_size
        
        if on_bottom and on_right:
            self.root.config(cursor="size_nw_se")
            self.resize_edge = "se"
        elif on_bottom and on_left:
            self.root.config(cursor="size_ne_sw")
            self.resize_edge = "sw"
        elif on_top and on_right:
            self.root.config(cursor="size_ne_sw")
            self.resize_edge = "ne"
        elif on_top and on_left:
            self.root.config(cursor="size_nw_se")
            self.resize_edge = "nw"
        elif on_right:
            self.root.config(cursor="size_we")
            self.resize_edge = "e"
        elif on_left:
            self.root.config(cursor="size_we")
            self.resize_edge = "w"
        elif on_bottom:
            self.root.config(cursor="size_ns")
            self.resize_edge = "s"
        elif on_top:
            self.root.config(cursor="size_ns")
            self.resize_edge = "n"
        else:
            self.root.config(cursor="")
            self.resize_edge = None
            
    def start_resize(self, event):
        """开始调整大小"""
        if self.resize_edge:
            self.resizing = True
            self.resize_start_x = event.x_root
            self.resize_start_y = event.y_root
            self.resize_start_width = self.root.winfo_width()
            self.resize_start_height = self.root.winfo_height()
            self.resize_start_window_x = self.root.winfo_x()
            self.resize_start_window_y = self.root.winfo_y()
        else:
            self.resizing = False
            
    def do_resize(self, event):
        """执行调整大小"""
        if not hasattr(self, 'resizing') or not self.resizing:
            return
            
        delta_x = event.x_root - self.resize_start_x
        delta_y = event.y_root - self.resize_start_y
        
        new_width = self.resize_start_width
        new_height = self.resize_start_height
        new_x = self.resize_start_window_x
        new_y = self.resize_start_window_y
        
        if 'e' in self.resize_edge:
            new_width = max(320, self.resize_start_width + delta_x)
        if 'w' in self.resize_edge:
            new_width = max(320, self.resize_start_width - delta_x)
            if new_width > 320:
                new_x = self.resize_start_window_x + delta_x
        if 's' in self.resize_edge:
            new_height = max(450, self.resize_start_height + delta_y)
        if 'n' in self.resize_edge:
            new_height = max(450, self.resize_start_height - delta_y)
            if new_height > 450:
                new_y = self.resize_start_window_y + delta_y
                
        self.root.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
        
    def stop_resize(self, event):
        """停止调整大小"""
        self.resizing = False
        self.resize_edge = None
        
    def bind_mousewheel(self, widget):
        """绑定鼠标滚轮事件"""
        widget.bind('<MouseWheel>', self.on_mousewheel)
        widget.bind('<Enter>', self.bind_mousewheel_to_frame)
        widget.bind('<Leave>', self.unbind_mousewheel_from_frame)
        
    def bind_mousewheel_to_frame(self, event):
        """鼠标进入时绑定滚轮"""
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)
        
    def unbind_mousewheel_from_frame(self, event):
        """鼠标离开时解绑滚轮"""
        self.canvas.unbind_all('<MouseWheel>')
        
    def on_mousewheel(self, event):
        """处理鼠标滚轮滚动"""
        # 检查是否有内容需要滚动
        if self.canvas.bbox("all"):
            # 平滑滚动
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            self.update_scrollbar()
        
    def update_scrollbar(self, event=None):
        """更新自定义滚动条位置和大小"""
        # 获取canvas的滚动区域
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
            
        canvas_height = self.canvas.winfo_height()
        content_height = bbox[3] - bbox[1]
        
        if content_height <= canvas_height:
            # 内容不足一屏，隐藏滚动条
            self.scrollbar.coords(self.scroll_indicator, 0, 0, 0, 0)
            return
        
        # 计算滚动条的高度和位置
        scrollbar_height = self.scrollbar.winfo_height()
        indicator_height = max(30, (canvas_height / content_height) * scrollbar_height)
        
        # 获取当前滚动位置
        scroll_pos = self.canvas.yview()[0]
        indicator_y = scroll_pos * scrollbar_height
        
        # 更新滚动条指示器
        self.scrollbar.coords(
            self.scroll_indicator,
            0, indicator_y,
            4, indicator_y + indicator_height
        )
        
    def on_add_button_hover(self, is_hover):
        if is_hover:
            self.add_button.config(bg=self.accent_hover)
            for child in self.add_button.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=self.accent_hover)
        else:
            self.add_button.config(bg=self.accent_color)
            for child in self.add_button.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(bg=self.accent_color)
        
    def on_task_focus_in(self, event):
        if self.task_entry.get() == "":
            self.task_entry.delete(0, tk.END)
            self.task_entry.config(fg=self.text_primary)
            
    def on_task_focus_out(self, event):
        if not self.task_entry.get():
            self.task_entry.insert(0, "")
            self.task_entry.config(fg=self.text_secondary)
            
    def on_frame_configure(self, event):
        """当内容frame大小改变时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.update_scrollbar()
        
    def on_canvas_configure(self, event):
        """当canvas大小改变时调整内容宽度"""
        # 关键：更新canvas_window的宽度以匹配canvas
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        self.update_scrollbar()
        
    def start_drag(self, event):
        if not hasattr(self, 'resizing') or not self.resizing:
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        
    def do_drag(self, event):
        if not hasattr(self, 'resizing') or not self.resizing:
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")
        
    def minimize_window(self):
        self.root.iconify()
        
    def add_todo(self):
        task = self.task_entry.get().strip()
        if not task or task == "":
            return
            
        date = self.date_entry.get().strip()
        time = self.time_entry.get().strip()
        
        todo = {
            "task": task,
            "ddl": f"{date} {time}",
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        
        self.todos.append(todo)
        self.save_todos()
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, "")
        self.task_entry.config(fg=self.text_secondary)
        self.refresh_todo_list()
        
    def toggle_complete(self, index):
        self.todos[index]["completed"] = not self.todos[index]["completed"]
        self.save_todos()
        self.refresh_todo_list()
        
    def delete_todo(self, index):
        del self.todos[index]
        self.save_todos()
        self.refresh_todo_list()
        
    def update_stats(self):
        total = len(self.todos)
        completed = sum(1 for todo in self.todos if todo["completed"])
        pending = total - completed
        
        if total == 0:
            stats_text = "暂无待办事项"
        else:
            stats_text = f"共 {total} 项  ·  已完成 {completed} 项  ·  待完成 {pending} 项"
            
        self.stats_label.config(text=stats_text)
        
    def refresh_todo_list(self):
        # 清空现有列表
        for widget in self.todo_frame.winfo_children():
            widget.destroy()
            
        # 更新统计
        self.update_stats()
        
        # 分离未完成和已完成的任务
        pending_todos = []
        completed_todos = []
        
        for idx, todo in enumerate(self.todos):
            if todo["completed"]:
                completed_todos.append((idx, todo))
            else:
                pending_todos.append((idx, todo))
        
        # 对未完成任务按DDL排序
        pending_todos.sort(key=lambda x: x[1]["ddl"])
        
        # 对已完成任务按完成时间排序（如果有的话，否则按DDL）
        completed_todos.sort(key=lambda x: x[1].get("completed_at", x[1]["ddl"]))
        
        # 先显示未完成的任务
        for original_idx, todo in pending_todos:
            card = self.create_todo_item(original_idx, todo)
            self.bind_mousewheel(card)
        
        # 再显示已完成的任务
        for original_idx, todo in completed_todos:
            card = self.create_todo_item(original_idx, todo)
            self.bind_mousewheel(card)
            
        # 刷新后更新滚动条
        self.root.after(100, self.update_scrollbar)
            
    def create_todo_item(self, index, todo):
        # 卡片容器 - 填充整个宽度
        card = tk.Frame(self.todo_frame, bg="white",
                       highlightbackground=self.border_color,
                       highlightthickness=1)
        card.pack(fill=tk.X, expand=True, pady=(0, 8))
        
        # 内容容器
        content = tk.Frame(card, bg="white")
        content.pack(fill=tk.X, expand=True, padx=15, pady=12)
        
        # 左侧：复选框和内容
        left_frame = tk.Frame(content, bg="white")
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 顶部：复选框和任务
        top_frame = tk.Frame(left_frame, bg="white")
        top_frame.pack(fill=tk.X, anchor=tk.W)
        
        # 自定义圆形复选框
        check_size = 22
        check_canvas = tk.Canvas(top_frame, width=check_size, height=check_size,
                                bg="white", highlightthickness=0, cursor="hand2")
        check_canvas.pack(side=tk.LEFT, padx=(0, 10))
        
        if todo["completed"]:
            # 已完成：实心圆
            check_canvas.create_oval(2, 2, check_size-2, check_size-2,
                                    fill=self.success_color, outline=self.success_color, width=2)
            check_canvas.create_text(check_size//2, check_size//2, text="✓",
                                    fill="white", font=("Arial", 12, "bold"))
        else:
            # 未完成：空心圆
            check_canvas.create_oval(2, 2, check_size-2, check_size-2,
                                    outline=self.border_color, width=2)
        
        check_canvas.bind('<Button-1>', lambda e: self.toggle_complete(index))
        
        # 任务文字容器 - 使其填充可用宽度
        task_container = tk.Frame(top_frame, bg="white")
        task_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 任务文字
        if todo["completed"]:
            task_label = tk.Label(task_container, text=todo["task"],
                                 bg="white", fg=self.text_secondary,
                                 font=("PingFang SC", 14, "overstrike"),
                                 anchor=tk.W, justify=tk.LEFT)
        else:
            task_label = tk.Label(task_container, text=todo["task"],
                                 bg="white", fg=self.text_primary,
                                 font=("PingFang SC", 14),
                                 anchor=tk.W, justify=tk.LEFT)
        task_label.pack(fill=tk.X, expand=True)
        
        # DDL信息
        try:
            ddl_dt = datetime.strptime(todo["ddl"], "%Y-%m-%d %H:%M")
            time_diff = ddl_dt - datetime.now()
            
            if time_diff.days < 0:
                icon = "⚠️"
                ddl_color = self.danger_color
                ddl_text = f"{icon} {todo['ddl']} 已过期"
            elif time_diff.days == 0:
                icon = "🔥"
                ddl_color = self.warning_color
                ddl_text = f"{icon} 今天 {ddl_dt.strftime('%H:%M')}"
            elif time_diff.days <= 3:
                icon = "⏰"
                ddl_color = self.warning_color
                ddl_text = f"{icon} {time_diff.days}天后 {ddl_dt.strftime('%H:%M')}"
            else:
                icon = "📅"
                ddl_color = self.text_secondary
                ddl_text = f"{icon} {todo['ddl']}"
                
        except:
            icon = "📅"
            ddl_color = self.text_secondary
            ddl_text = f"{icon} {todo['ddl']}"
            
        ddl_label = tk.Label(left_frame, text=ddl_text,
                            bg="white", fg=ddl_color,
                            font=("PingFang SC", 11), anchor=tk.W)
        ddl_label.pack(fill=tk.X, pady=(5, 0), padx=(32, 0))
        
        # 右侧：删除按钮
        delete_canvas = tk.Canvas(content, width=30, height=30,
                                 bg="white", highlightthickness=0, cursor="hand2")
        delete_canvas.pack(side=tk.RIGHT, padx=(5, 0))
        
        delete_canvas.create_text(15, 15, text="🗑️", font=("Arial", 16))
        delete_canvas.bind('<Button-1>', lambda e: self.delete_todo(index))
        
        # 为卡片内的所有子组件绑定滚轮事件
        self.bind_mousewheel(content)
        self.bind_mousewheel(left_frame)
        self.bind_mousewheel(top_frame)
        
        return card
        
    def load_todos(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def save_todos(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.todos, f, ensure_ascii=False, indent=2)
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ModernTodoApp()
    app.run()