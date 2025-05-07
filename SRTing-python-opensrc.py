import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from whisper_timestamped import load_model, transcribe
from datetime import timedelta
from PIL import Image, ImageTk
import webbrowser
import traceback
import os
import sys
import threading

if sys.stderr is None:
    import os
    sys.stderr = open(os.devnull, "w")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class AppState:
    def __init__(self):
        self.show_ffmpeg_error = False


app_state = AppState()


def setup_whisper_assets():
    if getattr(sys, 'frozen', False):
        whisper_assets_path = resource_path(os.path.join("whisper", "assets"))

        os.makedirs(whisper_assets_path, exist_ok=True)

        if not os.path.exists(os.path.join(whisper_assets_path, "multilingual.tiktoken")):
            alt_path = resource_path("whisper/assets")
            if os.path.exists(os.path.join(alt_path, "multilingual.tiktoken")):
                whisper_assets_path = alt_path
    else:
        whisper_assets_path = os.path.abspath(os.path.join("whisper", "assets"))

    os.environ["WHISPER_ASSETS"] = whisper_assets_path

    print(f"Whisper assets path set to: {whisper_assets_path}")
    print(f"Path exists: {os.path.exists(whisper_assets_path)}")
    if os.path.exists(whisper_assets_path):
        print(f"Contents: {os.listdir(whisper_assets_path)}")

    tiktoken_file = os.path.join(whisper_assets_path, "multilingual.tiktoken")
    if not os.path.exists(tiktoken_file):
        print(f"WARNING: Critical file missing: {tiktoken_file}")

        for root, dirs, files in os.walk(
                os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()):
            if "multilingual.tiktoken" in files:
                found_path = os.path.join(root, "multilingual.tiktoken")
                print(f"Found tiktoken file at: {found_path}")

                import shutil
                os.makedirs(os.path.dirname(tiktoken_file), exist_ok=True)
                shutil.copy(found_path, tiktoken_file)
                print(f"Copied tiktoken file to: {tiktoken_file}")
                break


setup_whisper_assets()

ffmpeg_exe = resource_path(os.path.join("assets", "ffmpeg.exe"))
if os.path.exists(ffmpeg_exe):
    os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep + os.environ.get("PATH", "")
    print(f"Using ffmpeg from: {ffmpeg_exe}")
else:
    import subprocess

    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("Found ffmpeg in PATH")
    except:
        print(f"ffmpeg not found at: {ffmpeg_exe} or in PATH")
        app_state.show_ffmpeg_error = True


def debug_pyinstaller_environment():
    """Helper function to debug PyInstaller environment"""
    try:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.getcwd()

        with open(os.path.join(app_dir, "debug_info.txt"), "w", encoding="utf-8") as f:
            is_frozen = getattr(sys, 'frozen', False)
            f.write(f"Running from PyInstaller: {is_frozen}\n")

            if is_frozen:
                f.write(f"_MEIPASS: {sys._MEIPASS}\n")
                f.write(f"Executable: {sys.executable}\n")

            f.write(f"Current directory: {os.getcwd()}\n")

            whisper_assets = os.environ.get("WHISPER_ASSETS", "Not set")
            f.write(f"WHISPER_ASSETS: {whisper_assets}\n")
            f.write(f"WHISPER_ASSETS exists: {os.path.exists(whisper_assets)}\n")

            if os.path.exists(whisper_assets):
                f.write(f"WHISPER_ASSETS contents: {os.listdir(whisper_assets)}\n")

                tiktoken_path = os.path.join(whisper_assets, "multilingual.tiktoken")
                f.write(f"multilingual.tiktoken exists: {os.path.exists(tiktoken_path)}\n")

            f.write(f"PATH: {os.environ.get('PATH', 'Not set')}\n")

            ffmpeg_exe = resource_path(os.path.join("assets", "ffmpeg.exe"))
            f.write(f"ffmpeg_exe path: {ffmpeg_exe}\n")
            f.write(f"ffmpeg_exe exists: {os.path.exists(ffmpeg_exe)}\n")

            f.write(f"Python version: {sys.version}\n")
            f.write(f"Python executable: {sys.executable}\n")
            f.write(f"Python path: {sys.path}\n")

            try:
                import torch
                f.write(f"Torch available: Yes (version {torch.__version__})\n")
                f.write(f"Torch path: {os.path.dirname(torch.__file__)}\n")
            except Exception as e:
                f.write(f"Torch available: No (error: {str(e)})\n")

            try:
                import whisper_timestamped
                f.write(f"whisper_timestamped available: Yes\n")
                f.write(f"whisper_timestamped path: {os.path.dirname(whisper_timestamped.__file__)}\n")
            except Exception as e:
                f.write(f"whisper_timestamped available: No (error: {str(e)})\n")

    except Exception as e:
        with open("debug_error.txt", "w") as f:
            f.write(f"Error during debug: {str(e)}\n")
            traceback.print_exc(file=f)


debug_pyinstaller_environment()

SUPPORTED_FORMATS = [".mp3", ".mp4", ".avi", ".wav", ".mov"]

LANGUAGES = {
    "Auto (Detect automatically)": None,
    "Polish": "pl",
    "English": "en",
    "Spanish": "es",
    "German": "de",
    "French": "fr",
    "Turkish": "tr",
    "Arabic": "ar",
    "Ukrainian": "uk",
    "Thai": "th",
    "Persian (Farsi)": "fa",
    "Indonesian": "id",
    "Vietnamese": "vi",
    "Hebrew": "he"
}

MODEL_OPTIONS = {
    "tiny - very fast, low quality": "tiny",
    "base - fast, medium quality": "base",
    "small - slower, good quality": "small",
    "medium - slowest, very good quality": "medium"
}

UI_LANGUAGES = {
    "Polski": {
        "title": "SRTify",
        "select_file": "Wybierz plik audio/wideo:",
        "select_output": "Folder docelowy (opcjonalnie):",
        "select_lang": "Wybierz język nagrania:",
        "select_model": "Wybierz model transkrypcji:",
        "select_grouping": "Liczba słów na linię napisów:",
        "generate": "GENERUJ NAPISY",
        "error": "Błąd",
        "error_choose": "Wybierz plik, język i model.",
        "done": "Gotowe",
        "saved_as": "Napisy zapisane jako:",
        "error_log": "Coś poszło nie tak. Sprawdź error_log.txt"
    },
    "English": {
        "title": "SRTify",
        "select_file": "Select audio/video file:",
        "select_output": "Output folder (optional):",
        "select_lang": "Select spoken language:",
        "select_model": "Select transcription model:",
        "select_grouping": "Words per subtitle line:",
        "generate": "GENERATE SUBTITLES",
        "error": "Error",
        "error_choose": "Select file, language and model.",
        "done": "Done",
        "saved_as": "Subtitles saved as:",
        "error_log": "Something went wrong. Check error_log.txt"
    }
}

current_ui_lang = UI_LANGUAGES["English"]

try:
    root = tk.Tk()

    if app_state.show_ffmpeg_error:
        messagebox.showerror("FFmpeg Missing",
                             "ffmpeg was not found. This application requires ffmpeg to work properly.")

    icon_path = resource_path(os.path.join("assets", "sygnetlogostrlogo1.png"))
    if os.path.exists(icon_path):
        try:
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            root.iconphoto(False, icon_photo)
        except Exception as e:
            print(f"Error setting application icon: {str(e)}")
    root.title(current_ui_lang["title"])
    root.geometry("560x620")
    root.configure(bg="#121212")
except Exception as e:
    print(f"Error initializing Tkinter: {str(e)}")
    with open("tkinter_error.txt", "w") as f:
        f.write(f"Error initializing Tkinter: {str(e)}\n")
        traceback.print_exc(file=f)
    sys.exit(1)

selected_file = tk.StringVar()
output_folder = tk.StringVar()
words_per_line = tk.IntVar(value=1)

try:
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame", background="#121212")
    style.configure("TLabel", background="#121212", foreground="#D1C4E9", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
    style.configure("TCombobox", fieldbackground="#2c2c38", background="#2c2c38", foreground="white",
                    font=("Segoe UI", 11))
    style.map("TCombobox", fieldbackground=[("readonly", "#2c2c38")], foreground=[("readonly", "white")])

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
except Exception as e:
    print(f"Error setting up Tkinter style: {str(e)}")
    messagebox.showerror("Error", f"Error setting up UI: {str(e)}")

try:
    logo_path = resource_path(os.path.join("assets", "logosrtify1.png"))
    if os.path.exists(logo_path):
        logo_image = Image.open(logo_path).resize((180, 45), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(frame, image=logo_photo, bg="#121212")
        logo_label.image = logo_photo
        logo_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
    else:
        print(f"Logo not found at: {logo_path}")
except Exception as e:
    print(f"Error loading logo: {str(e)}")


def format_timestamp(seconds):
    try:
        millis = int((seconds - int(seconds)) * 1000)
        return f"{int(seconds // 3600):02}:{int((seconds % 3600) // 60):02}:{int(seconds % 60):02},{millis:03d}"
    except Exception as e:
        print(f"Error formatting timestamp: {str(e)}")
        return "00:00:00,000"


def transcribe_word_by_word(video_path, output_srt, lang, model_type, group_size):
    try:
        print(f"Loading model: {model_type}")
        model = load_model(model_type)

        print(f"Starting transcription of: {video_path}")
        result = transcribe(model, video_path, language=lang)
        print("Transcription complete, processing segments")

        index = 1
        grouped = []
        buffer = []

        for segment in result["segments"]:
            for word in segment["words"]:
                if word.get("start") is None or word.get("end") is None:
                    continue
                buffer.append(word)
                if len(buffer) == group_size:
                    grouped.append(buffer)
                    buffer = []
        if buffer:
            grouped.append(buffer)

        print(f"Writing SRT to: {output_srt}")
        with open(output_srt, "w", encoding="utf-8") as srt_file:
            for group in grouped:
                start = format_timestamp(group[0]["start"])
                end = format_timestamp(group[-1]["end"])
                text = " ".join([w["text"].strip() for w in group])
                srt_file.write(f"{index}\n{start} --> {end}\n{text}\n\n")
                index += 1

        print(f"SRT file created with {index - 1} subtitle entries")
        return output_srt
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        traceback.print_exc()
        raise


def browse_file():
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Multimedia files", "*.mp4 *.mp3 *.avi *.wav *.mov")])
        if file_path:
            selected_file.set(file_path)
    except Exception as e:
        print(f"Error browsing file: {str(e)}")
        messagebox.showerror("Error", f"Error selecting file: {str(e)}")


def choose_output_folder():
    try:
        folder_path = filedialog.askdirectory()
        if folder_path:
            output_folder.set(folder_path)
    except Exception as e:
        print(f"Error choosing output folder: {str(e)}")
        messagebox.showerror("Error", f"Error selecting folder: {str(e)}")


def change_language(event):
    try:
        global current_ui_lang
        lang = lang_ui_combobox.get()
        current_ui_lang = UI_LANGUAGES[lang]
        update_ui_texts()
    except Exception as e:
        print(f"Error changing language: {str(e)}")


def update_ui_texts():
    try:
        root.title(current_ui_lang["title"])
        file_label.config(text=current_ui_lang["select_file"])
        output_label.config(text=current_ui_lang["select_output"])
        lang_label.config(text=current_ui_lang["select_lang"])
        model_label.config(text=current_ui_lang["select_model"])
        group_label.config(text=current_ui_lang["select_grouping"])
        generate_button.config(text=current_ui_lang["generate"])
    except Exception as e:
        print(f"Error updating UI texts: {str(e)}")


def run_transcription():
    def task():
        try:
            file_path = selected_file.get()
            if not file_path:
                messagebox.showerror(current_ui_lang["error"], current_ui_lang["error_choose"])
                root.after(0, progress.stop)
                return

            if not any(file_path.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                messagebox.showerror("Error", "Unsupported file format.")
                root.after(0, progress.stop)
                return

            output_dir = output_folder.get()
            lang_display = lang_combobox.get()
            model_display = model_combobox.get()
            group_size = max(1, words_per_line.get())

            if not lang_display in LANGUAGES or model_display not in MODEL_OPTIONS:
                messagebox.showerror(current_ui_lang["error"], current_ui_lang["error_choose"])
                root.after(0, progress.stop)
                return

            lang = LANGUAGES.get(lang_display, None)
            model_type = MODEL_OPTIONS[model_display]
            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            output_srt = os.path.join(output_dir if output_dir else os.path.dirname(file_path),
                                      base_filename + "_subtitles.srt")

            print(f"Starting transcription with model: {model_type}, language: {lang}, group size: {group_size}")
            try:
                transcribe_word_by_word(file_path, output_srt, lang, model_type, group_size)
                root.after(0, lambda: messagebox.showinfo(current_ui_lang["done"],
                                                          f"{current_ui_lang['saved_as']}\n{output_srt}"))
            except Exception as e:
                error_log_path = os.path.join(os.path.dirname(file_path), "error_log.txt")
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Error: {str(e)}\n")
                    traceback.print_exc(file=f)
                root.after(0, lambda: messagebox.showerror(
                    current_ui_lang["error"],
                    f"{current_ui_lang['error_log']}\nError log saved at: {error_log_path}"
                ))
        except Exception as e:
            print(f"Error in transcription thread: {str(e)}")
            traceback.print_exc()
            root.after(0, lambda: messagebox.showerror("Error", f"Unexpected error: {str(e)}"))
        finally:
            root.after(0, progress.stop)

    progress.start()
    threading.Thread(target=task, daemon=True).start()


try:
    lang_ui_combobox = ttk.Combobox(frame, values=list(UI_LANGUAGES.keys()), state="readonly")
    lang_ui_combobox.set("English")
    lang_ui_combobox.grid(row=1, column=0, columnspan=3, sticky="e", pady=(0, 10))
    lang_ui_combobox.bind("<<ComboboxSelected>>", change_language)

    file_label = ttk.Label(frame)
    file_label.grid(row=2, column=0, sticky="w")
    file_entry = tk.Entry(frame, textvariable=selected_file, font=("Consolas", 10), bg="#1e1e1e", fg="white",
                          relief="flat")
    file_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 10))
    file_button = tk.Button(frame, text="...", command=browse_file, font=("Segoe UI", 10), bg="#7E57C2", fg="white",
                            relief="flat")
    file_button.grid(row=3, column=2, sticky="ew")

    output_label = ttk.Label(frame)
    output_label.grid(row=4, column=0, sticky="w", pady=(15, 5))
    output_entry = tk.Entry(frame, textvariable=output_folder, font=("Consolas", 10), bg="#1e1e1e", fg="white",
                            relief="flat")
    output_entry.grid(row=5, column=0, columnspan=2, sticky="ew", padx=(0, 10))
    output_button = tk.Button(frame, text="...", command=choose_output_folder, font=("Segoe UI", 10), bg="#7E57C2",
                              fg="white", relief="flat")
    output_button.grid(row=5, column=2, sticky="ew")

    lang_label = ttk.Label(frame)
    lang_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(20, 5))
    lang_combobox = ttk.Combobox(frame, values=list(LANGUAGES.keys()), state="readonly")
    lang_combobox.set("English")
    lang_combobox.grid(row=7, column=0, columnspan=3, sticky="ew")

    model_label = ttk.Label(frame)
    model_label.grid(row=8, column=0, columnspan=3, sticky="w", pady=(15, 5))
    model_combobox = ttk.Combobox(frame, values=list(MODEL_OPTIONS.keys()), state="readonly")
    model_combobox.set("base - fast, medium quality")
    model_combobox.grid(row=9, column=0, columnspan=3, sticky="ew")

    group_label = ttk.Label(frame)
    group_label.grid(row=10, column=0, columnspan=2, sticky="w", pady=(15, 5))
    group_spinbox = tk.Spinbox(frame, from_=1, to=10, textvariable=words_per_line, width=5)
    group_spinbox.grid(row=10, column=2, sticky="ew")


    def on_enter(e):
        generate_button.config(bg="#6A1B9A")


    def on_leave(e):
        generate_button.config(bg="#7E57C2")


    generate_button = tk.Button(
        frame,
        text=current_ui_lang["generate"],
        command=run_transcription,
        font=("Segoe UI", 12, "bold"),
        bg="#7E57C2",
        fg="white",
        relief="flat"
    )
    generate_button.grid(row=11, column=0, columnspan=3, sticky="ew", pady=(20, 10))
    generate_button.bind("<Enter>", on_enter)
    generate_button.bind("<Leave>", on_leave)

    progress = ttk.Progressbar(frame, mode='indeterminate')
    progress.grid(row=12, column=0, columnspan=3, sticky='ew', pady=(0, 10))

    dc_icon_path = resource_path(os.path.join("assets", "dcblackicon.png"))
    if os.path.exists(dc_icon_path):
        def open_discord():
            webbrowser.open("https://discord.com/users/eskimek")


        try:
            dc_img = Image.open(dc_icon_path).resize((24, 24), Image.LANCZOS)
            dc_photo = ImageTk.PhotoImage(dc_img)
            dc_btn = tk.Button(frame, image=dc_photo, text=" discord: eskimek", compound="left", command=open_discord,
                               font=("Segoe UI", 10), bg="#121212", fg="white", activebackground="#1e1e1e",
                               bd=0, relief="flat", cursor="hand2")
            dc_btn.image = dc_photo
            dc_btn.grid(row=13, column=0, columnspan=3, pady=(10, 0))
        except Exception as e:
            print(f"Error loading Discord icon: {str(e)}")
            dc_btn = tk.Button(frame, text="discord: eskimek", command=open_discord,
                               font=("Segoe UI", 10), bg="#121212", fg="white",
                               bd=0, relief="flat", cursor="hand2")
            dc_btn.grid(row=13, column=0, columnspan=3, pady=(10, 0))

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)

    update_ui_texts()
except Exception as e:
    print(f"Error setting up UI components: {str(e)}")
    with open("ui_error.txt", "w") as f:
        f.write(f"Error setting up UI: {str(e)}\n")
        traceback.print_exc(file=f)
    messagebox.showerror("Error", f"Failed to initialize UI: {str(e)}")

try:
    root.mainloop()
except Exception as e:
    print(f"Error in main loop: {str(e)}")
    with open("mainloop_error.txt", "w") as f:
        f.write(f"Error in mainloop: {str(e)}\n")
        traceback.print_exc(file=f)