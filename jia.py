import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import win32gui
import win32api
import win32con
from pynput import mouse, keyboard

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class FullSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("林嘉原-同步器")
        self.root.geometry("520x400")
        self.root.attributes('-topmost', True)

        self.master_hwnd = None
        self.is_running = False
        self.is_paused = False
        self.listener_thread = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.left_button_down = False
        self.slave_vars = {}
        
        self.action_delay = tk.DoubleVar(value=0.001)
        self.sync_mouse_var = tk.BooleanVar(value=True)
        self.sync_keyboard_var = tk.BooleanVar(value=True)

        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, fill='x', padx=10)
        self.status_label = tk.Label(control_frame, text="狀態：尚未設定主控", font=("Microsoft JhengHei UI", 12), fg="orange")
        self.status_label.pack()
        options_frame = tk.Frame(control_frame)
        options_frame.pack(pady=5)
        tk.Checkbutton(options_frame, text="同步滑鼠", variable=self.sync_mouse_var, font=("Microsoft JhengHei UI", 10)).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(options_frame, text="同步鍵盤", variable=self.sync_keyboard_var, font=("Microsoft JhengHei UI", 10)).pack(side=tk.LEFT, padx=10)
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=5)
        self.set_master_button = tk.Button(btn_frame, text="1. 指定主控", command=self.prepare_to_set_master, font=("Microsoft JhengHei UI", 10))
        self.set_master_button.pack(side=tk.LEFT, padx=5)
        self.start_button = tk.Button(btn_frame, text="開始同步", command=self.start_sync, state=tk.DISABLED, font=("Microsoft JhengHei UI", 10))
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = tk.Button(btn_frame, text="結束同步", command=self.stop_sync, state=tk.DISABLED, font=("Microsoft JhengHei UI", 10))
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = tk.Button(btn_frame, text="暫停", command=self.toggle_pause, state=tk.DISABLED, font=("Microsoft JhengHei UI", 10))
        self.pause_button.pack(side=tk.LEFT, padx=5)
        delay_frame = tk.Frame(control_frame)
        delay_frame.pack(pady=5)
        tk.Label(delay_frame, text="動作延遲 (秒):", font=("Microsoft JhengHei UI", 10)).pack(side=tk.LEFT)
        tk.Entry(delay_frame, textvariable=self.action_delay, width=10).pack(side=tk.LEFT, padx=5)
        self.info_label = tk.Label(root, text="提示：按 F12 暫停/繼續，按 ESC 停止同步。", font=("Microsoft JhengHei UI", 9), fg="grey")
        self.info_label.pack(side=tk.BOTTOM, pady=5)
        list_frame = tk.LabelFrame(root, text=" 被控視窗列表 ", font=("Microsoft JhengHei UI", 10), padx=5, pady=5)
        list_frame.pack(pady=5, fill="both", expand=True, padx=10)
        self.scrollable_list = ScrollableFrame(list_frame)
        self.scrollable_list.pack(fill="both", expand=True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_status(self, text, color):
        self.status_label.config(text=f"狀態：{text}", fg=color)

    def prepare_to_set_master(self):
        self.update_status("請點擊任何視窗以將其設為主控...", "blue")
        temp_listener = mouse.Listener(on_click=self.on_master_select)
        temp_listener.start()

    def on_master_select(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            self.master_hwnd = win32gui.WindowFromPoint((x, y))
            if self.master_hwnd != 0:
                self.update_slave_list_ui()
                master_title = win32gui.GetWindowText(self.master_hwnd)
                self.update_status(f"主控已設定: {master_title[:20]}...", "#006400")
                self.start_button.config(state=tk.NORMAL)
                return False

    def update_slave_list_ui(self):
        self.clear_slave_list_ui()
        try:
            target_class_name = win32gui.GetClassName(self.master_hwnd)
            def callback(hwnd, extra):
                if (hwnd != self.master_hwnd and win32gui.IsWindowVisible(hwnd) and
                    win32gui.GetClassName(hwnd) == target_class_name):
                    var = tk.BooleanVar(value=True)
                    self.slave_vars[hwnd] = var
                    title = win32gui.GetWindowText(hwnd)
                    if not title: title = f"[無標題視窗, 句柄:{hwnd}]"
                    cb = tk.Checkbutton(self.scrollable_list.scrollable_frame, text=title, variable=var, anchor='w')
                    cb.pack(fill='x', padx=5)
            win32gui.EnumWindows(callback, None)
        except Exception: pass

    def clear_slave_list_ui(self):
        for widget in self.scrollable_list.scrollable_frame.winfo_children():
            widget.destroy()
        self.slave_vars.clear()
        
    def start_sync(self):
        if not self.master_hwnd: messagebox.showwarning("警告", "請先指定一個主控視窗"); return
        if self.is_running: return
        self.is_running = True
        self.update_status("同步中... (按F12或按鈕暫停)", "green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.NORMAL)
        self.set_master_button.config(state=tk.DISABLED)
        self.listener_thread = threading.Thread(target=self.run_listeners, daemon=True)
        self.listener_thread.start()

    def stop_sync(self):
        if not self.is_running: return
        self.is_running = False
        self.is_paused = False
        if self.mouse_listener: self.mouse_listener.stop()
        if self.keyboard_listener: self.keyboard_listener.stop()
        self.master_hwnd = None
        self.clear_slave_list_ui()
        self.update_status("已停止，請重新指定主控", "orange")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED, text="暫停")
        self.set_master_button.config(state=tk.NORMAL)

    def toggle_pause(self):
        if not self.is_running: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.update_status("同步暫停中... (按F12或按鈕繼續)", "blue"); self.pause_button.config(text="繼續")
        else:
            self.update_status("同步中... (按F12或按鈕暫停)", "green"); self.pause_button.config(text="暫停")
    
    def broadcast_message(self, message_type, *args):
        for hwnd, is_active_var in self.slave_vars.items():
            if is_active_var.get():
                try:
                    if message_type == "mouse_click": message, wParam, lParam = args; win32gui.PostMessage(hwnd, message, wParam, lParam)
                    elif message_type == "mouse_move": wParam, lParam = args; win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, wParam, lParam)
                    elif message_type == "key_event": message, vk_code = args; win32api.PostMessage(hwnd, message, vk_code, 0)
                    if message_type != "mouse_move": time.sleep(self.action_delay.get())
                except Exception: pass

    def on_click(self, x, y, button, pressed):
        if not self.is_running or self.is_paused or not self.sync_mouse_var.get(): return
        if button == mouse.Button.left:
            self.left_button_down = pressed
            if win32gui.WindowFromPoint((x,y)) == self.master_hwnd:
                client_coords = win32gui.ScreenToClient(self.master_hwnd, (x, y)); lParam = win32api.MAKELONG(client_coords[0], client_coords[1])
                message = win32con.WM_LBUTTONDOWN if pressed else win32con.WM_LBUTTONUP; wParam = win32con.MK_LBUTTON if pressed else 0
                self.broadcast_message("mouse_click", message, wParam, lParam)

    def on_move(self, x, y):
        if not self.is_running or self.is_paused or not self.sync_mouse_var.get() or not self.left_button_down: return
        if win32gui.WindowFromPoint((x,y)) == self.master_hwnd:
            client_coords = win32gui.ScreenToClient(self.master_hwnd, (x, y)); lParam = win32api.MAKELONG(client_coords[0], client_coords[1])
            wParam = win32con.MK_LBUTTON; self.broadcast_message("mouse_move", wParam, lParam)

    def on_press(self, key):
        if key == keyboard.Key.esc: self.root.after(0, self.stop_sync); return False
        if key == keyboard.Key.f12: self.root.after(0, self.toggle_pause); return
        if not self.is_running or self.is_paused or not self.sync_keyboard_var.get(): return
        if self.master_hwnd and win32gui.GetForegroundWindow() == self.master_hwnd:
            vk_code = self._get_vk_code(key)
            if vk_code: self.broadcast_message("key_event", win32con.WM_KEYDOWN, vk_code)

    def on_release(self, key):
        if not self.is_running or self.is_paused or not self.sync_keyboard_var.get(): return
        if self.master_hwnd and win32gui.GetForegroundWindow() == self.master_hwnd:
            vk_code = self._get_vk_code(key)
            if vk_code: self.broadcast_message("key_event", win32con.WM_KEYUP, vk_code)

    def run_listeners(self):
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener.start(); self.keyboard_listener.start()
        self.mouse_listener.join(); self.keyboard_listener.join()

    def on_closing(self):
        if self.is_running: self.stop_sync()
        self.root.destroy()

    def _get_vk_code(self, key):
        if hasattr(key, 'vk'): return key.vk
        elif hasattr(key, 'value'): return key.value.vk
        return None

if __name__ == "__main__":
    root = tk.Tk()
    app = FullSyncApp(root)
    root.mainloop()