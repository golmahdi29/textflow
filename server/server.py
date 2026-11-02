import os
import socket
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
from pathlib import Path
from datetime import datetime
import ctypes

import customtkinter as ctk
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SERVER_HOST = os.getenv("SERVER_HOST", "192.168.246.128")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

FONT_PATH = os.getenv("FONT_PATH", "assets/fonts/Vazir.ttf")
FONT_FAMILY = os.getenv("FONT_FAMILY", "Vazir")

FONT_FILE = Path(FONT_PATH)
if not FONT_FILE.is_absolute():
    FONT_FILE = BASE_DIR / FONT_FILE

FONT = "Tahoma"
PRIVATE_FONT_LOADED = False


def load_private_font():
    """Load the configured font privately on Windows before Tkinter starts."""
    global FONT, PRIVATE_FONT_LOADED

    if not FONT_FILE.is_file():
        print(f"Font file not found: {FONT_FILE}")
        return

    if os.name == "nt":
        try:
            gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
            add_font = gdi32.AddFontResourceExW
            add_font.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
            add_font.restype = ctypes.c_int

            # FR_PRIVATE = 0x10: make the font available to this process.
            result = add_font(str(FONT_FILE), 0x10, None)
            if result > 0:
                PRIVATE_FONT_LOADED = True
                FONT = FONT_FAMILY
                print(f"Private font loaded: {FONT_FILE}")
            else:
                print(f"Windows could not load the font: {FONT_FILE}")
        except Exception as exc:
            print(f"Could not register font: {exc}")
    else:
        print("Private font loading is implemented for Windows only.")


load_private_font()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#0B1120"
PANEL = "#111B2E"
CARD = "#17243A"
ACCENT = "#4F8CFF"
GREEN = "#22C993"
RED = "#FF647C"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"


class TextFlowClient(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("تکست فلو | سامانه ارتباط شبکه")
        self.geometry("1050x720")
        self.minsize(850, 620)
        self.configure(fg_color=BG)

        self.client = None
        self.connected = False
        self.messages_sent = 0
        self.messages_received = 0
        self.send_lock = threading.Lock()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_header()
        self.create_dashboard()
        self.create_chat()
        self.create_footer()

        self.log("Click connect btn to start")
        if PRIVATE_FONT_LOADED:
            self.after(500, self.check_font_family)

    def check_font_family(self):
        try:
            available = list(tkfont.families(self))
            if FONT not in available:
                self.log(
                    f"نام فونت «{FONT}» در Tk پیدا نشد؛ "
                    "نام خانوادگی فونت را در فایل .env بررسی کنید."
                )
                print("Available font families:", available)
        except Exception as exc:
            print("Font check failed:", exc)

    def make_label(self, parent, text, size=14, color=TEXT, bold=False):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=(FONT, size, "bold" if bold else "normal"),
            text_color=color
        )

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=18)
        header.pack(fill="x", padx=22, pady=(22, 12))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=22, pady=16)

        self.make_label(right, "TextFlow", 27, ACCENT, True).pack(anchor="e")
        self.make_label(
            right,
            "سامانه ارسال و پردازش پیام با پروتکل TCP",
            12,
            MUTED
        ).pack(anchor="e", pady=(3, 0))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=22, pady=18)

        self.status_label = self.make_label(left, "● قطع ارتباط", 13, RED, True)
        self.status_label.pack(side="right", padx=8)

        self.connect_button = ctk.CTkButton(
            left,
            text="اتصال به سرور",
            width=125,
            height=36,
            corner_radius=10,
            font=(FONT, 12),
            command=self.connect_server
        )
        self.connect_button.pack(side="left", padx=5)

        self.about_button = ctk.CTkButton(
            left,
            text="درباره پروژه",
            width=105,
            height=36,
            corner_radius=10,
            fg_color=CARD,
            hover_color="#243653",
            font=(FONT, 12),
            command=self.show_about
        )
        self.about_button.pack(side="left", padx=5)

    def create_dashboard(self):
        dashboard = ctk.CTkFrame(self, fg_color="transparent")
        dashboard.pack(fill="x", padx=22, pady=5)

        cards = [
            ("پروتکل ارتباط", "TCP", ACCENT),
            ("پیام‌های ارسالی", "0", GREEN),
            ("پاسخ‌های دریافتی", "0", "#B794F6")
        ]
        self.stat_values = {}

        for title, value, color in cards:
            card = ctk.CTkFrame(dashboard, fg_color=CARD, corner_radius=15)
            card.pack(side="right", expand=True, fill="x", padx=6)

            self.make_label(card, title, 12, MUTED).pack(pady=(14, 5))
            value_label = self.make_label(card, value, 23, color, True)
            value_label.pack(pady=(0, 14))
            self.stat_values[title] = value_label

    def create_chat(self):
        container = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=18)
        container.pack(fill="both", expand=True, padx=22, pady=12)

        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.pack(fill="x", padx=20, pady=(16, 5))

        self.make_label(title_row, "محیط تبادل پیام", 17, TEXT, True).pack(side="right")
        self.make_label(
            title_row,
            f"{SERVER_HOST}:{SERVER_PORT}",
            11,
            MUTED
        ).pack(side="left")

        self.chat_box = ctk.CTkTextbox(
            container,
            corner_radius=12,
            fg_color="#0D1627",
            text_color=TEXT,
            font=(FONT, 13),
            wrap="word"
        )
        self.chat_box.pack(fill="both", expand=True, padx=18, pady=12)
        self.chat_box.configure(state="disabled")
        self.chat_box.tag_config("sent", foreground=ACCENT)
        self.chat_box.tag_config("received", foreground=GREEN)
        self.chat_box.tag_config("system", foreground=MUTED)

        input_area = ctk.CTkFrame(container, fg_color="transparent")
        input_area.pack(fill="x", padx=18, pady=(0, 18))

        self.message_entry = ctk.CTkEntry(
            input_area,
            placeholder_text="پیام خود را وارد کنید",
            height=45,
            corner_radius=12,
            font=(FONT, 13),
            justify="right"
        )
        self.message_entry.pack(
            side="right", fill="x", expand=True, padx=(0, 10)
        )
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = ctk.CTkButton(
            input_area,
            text="ارسال پیام  ←",
            width=145,
            height=45,
            corner_radius=12,
            font=(FONT, 13, "bold"),
            fg_color=ACCENT,
            hover_color="#3675E8",
            command=self.send_message,
            state="disabled"
        )
        self.send_button.pack(side="left")

    def create_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=25, pady=(0, 14))

        self.make_label(
            footer, "پروژه میان‌ترم مهندسی اینترنت", 11, MUTED
        ).pack(side="right")
        self.make_label(
            footer, "TCP • Client / Server", 11, MUTED
        ).pack(side="left")

    def log(self, message, tag="system"):
        if not hasattr(self, "chat_box"):
            return

        self.chat_box.configure(state="normal")
        time_text = datetime.now().strftime("%H:%M:%S")
        self.chat_box.insert("end", f"[{time_text}]  {message}\n\n", tag)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def connect_server(self):
        if self.connected:
            return
        self.connect_button.configure(state="disabled", text="در حال اتصال...")

        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        client = None
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((SERVER_HOST, SERVER_PORT))
            client.settimeout(None)

            self.client = client
            self.connected = True
            self.after(0, self._connected_ui)
        except OSError as error:
            if client:
                client.close()
            self.after(0, lambda err=str(error): self._connection_failed(err))

    def _connected_ui(self):
        self.status_label.configure(text="● متصل به سرور", text_color=GREEN)
        self.connect_button.configure(text="اتصال برقرار شد", state="disabled")
        self.send_button.configure(state="normal")
        self.log("اتصال TCP با موفقیت برقرار شد.")

    def _connection_failed(self, error):
        self.connected = False
        self.client = None
        self.status_label.configure(text="● قطع ارتباط", text_color=RED)
        self.connect_button.configure(text="تلاش مجدد", state="normal")
        self.log(f"خطا در اتصال به سرور: {error}")
        messagebox.showerror(
            "خطای اتصال",
            "اتصال به سرور برقرار نشد.\nمطمئن شوید سرور اجرا شده است."
        )

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return

        if not self.connected or not self.client:
            messagebox.showwarning("عدم اتصال", "ابتدا به سرور متصل شوید.")
            return

        if not self.send_lock.acquire(blocking=False):
            return

        self.send_button.configure(state="disabled")
        threading.Thread(
            target=self._send_worker,
            args=(message,),
            daemon=True
        ).start()

    def _send_worker(self, message):
        try:
            client = self.client
            if client is None:
                raise ConnectionError("اتصال به سرور برقرار نیست.")

            client.sendall((message + "\n").encode("utf-8"))

            response = bytearray()
            while not response.endswith(b"\n"):
                chunk = client.recv(4096)
                if not chunk:
                    raise ConnectionError("اتصال توسط سرور بسته شد.")
                response.extend(chunk)
                if len(response) > 1024 * 1024:
                    raise ValueError("پاسخ سرور بیش از حد بزرگ است.")

            result = response.decode("utf-8").rstrip("\r\n")
            self.messages_sent += 1
            self.messages_received += 1
            self.after(0, lambda msg=message, res=result: self._message_received(msg, res))
        except (OSError, ConnectionError, ValueError) as error:
            self.after(0, lambda err=str(error): self._communication_failed(err))
        finally:
            self.send_lock.release()

    def _message_received(self, message, result):
        self.log(f"پیام ارسالی شما: {message}", "sent")
        self.log(f"پاسخ سرور: {result}", "received")
        self.stat_values["پیام‌های ارسالی"].configure(text=str(self.messages_sent))
        self.stat_values["پاسخ‌های دریافتی"].configure(text=str(self.messages_received))
        self.message_entry.delete(0, "end")
        if self.connected:
            self.send_button.configure(state="normal")

    def _communication_failed(self, error):
        self.connected = False
        if self.client:
            try:
                self.client.close()
            except OSError:
                pass

        self.client = None
        self.status_label.configure(text="● قطع ارتباط", text_color=RED)
        self.connect_button.configure(text="اتصال مجدد", state="normal")
        self.send_button.configure(state="disabled")
        self.log(f"ارتباط قطع شد: {error}")

    def show_about(self):
        window = ctk.CTkToplevel(self)
        window.title("درباره پروژه")
        window.geometry("470x460")
        window.resizable(False, False)
        window.configure(fg_color=BG)
        window.transient(self)
        window.grab_set()

        self.make_label(window, "درباره پروژه", 25, ACCENT, True).pack(pady=(25, 5))
        self.make_label(window, "پروژه میان‌ترم", 14, MUTED).pack(pady=(0, 18))

        details = [
            ("عنوان پروژه", "سامانه تبدیل پیام با TCP"),
            ("نام درس", "مهندسی اینترنت"),
            ("استاد", "خانم زهرا ولدخانی"),
            ("زمان کلاس", "پنجشنبه، ساعت ۱۰:۱۰"),
            ("عضو اول", "مهدی گل خندانیان"),
            ("عضو دوم", "حنانه عباسی"),
        ]

        for title, value in details:
            card = ctk.CTkFrame(window, fg_color=CARD, corner_radius=10)
            card.pack(fill="x", padx=25, pady=4)
            self.make_label(card, title, 12, MUTED).pack(
                side="right", padx=12, pady=9
            )
            self.make_label(card, value, 12, TEXT, True).pack(
                side="left", padx=12, pady=9
            )

        ctk.CTkButton(
            window,
            text="بستن",
            width=120,
            command=window.destroy,
            font=(FONT, 12)
        ).pack(pady=18)

    def on_close(self):
        self.connected = False
        if self.client:
            try:
                self.client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.client.close()
            except OSError:
                pass
        self.destroy()


if __name__ == "__main__":
    app = TextFlowClient()
    app.mainloop()