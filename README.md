[![SRTing Light](https://github.com/Eskimek/AI-message-by-discord-user/blob/main/assets/logo2lightmode.png#gh-light-mode-only)](https://github.com/Eskimek/AI-message-by-discord-user)
[![SRTing Dark](https://github.com/Eskimek/AI-message-by-discord-user/blob/main/assets/logo1.png#gh-dark-mode-only)](https://github.com/Eskimek/AI-message-by-discord-user)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-black?style=for-the-badge&logo=ffmpeg)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Whisper](https://img.shields.io/badge/Whisper-AI-lightgrey?style=for-the-badge&logo=openai)](https://github.com/openai/whisper)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange?style=for-the-badge)](https://wiki.python.org/moin/TkInter)

## 💡 About
**SRTing** is a local, offline subtitle generator using OpenAI Whisper with word-level timing.  
Built for use in **Premiere Pro**, but works anywhere `.srt` is accepted.

## What It Does
- Select audio/video file (MP3, MP4, WAV, etc.)
- Detect or set spoken language
- Choose subtitle model and word grouping
- Generate `.srt` subtitles in a few clicks
- Fully Premiere Pro compatible
- Local GUI (Tkinter) – no internet needed

## ⚙️ Requirements
- Python 3.10+
- `ffmpeg` (either in `assets/` or globally in PATH)
- `whisper_timestamped`, `torch`, `pillow`
- `multilingual.tiktoken` file (used by Whisper)
- `pyinstaller` (only if building `.exe`)

Install dependencies:
```bash
pip install whisper_timestamped torch pillow pyinstaller
```

## Running Without Building
If you're running the Python script directly:

```bash
python SRTing-python-open.py
```

You **must** have:

- `ffmpeg` accessible in PATH (`ffmpeg -version` should work),  
  **or** copy `ffmpeg.exe` into `assets/`
- `multilingual.tiktoken` file inside:  
  `whisper/assets/multilingual.tiktoken`

If the file is somewhere else, you can also set an env variable:

```bash
export WHISPER_ASSETS=/your/path/to/whisper/assets
```

## 📦 Building as .exe

To make a standalone `.exe` organize your files like this:

```
.
├── assets/
│   ├── ffmpeg.exe
│   ├── logosrtify1.png
│   ├── sygnetlogostrlogo1.png
│   └── dcblackicon.png
├── whisper/
│   └── assets/
│       └── multilingual.tiktoken
├── SRTing-python-open.py
```

Then build using this command:

```bash
pyinstaller --onefile --windowed --icon=assets/sygnetlogostrlogo1.png \
--add-data "assets/ffmpeg.exe;assets" \
--add-data "assets/logosrtify1.png;assets" \
--add-data "assets/sygnetlogostrlogo1.png;assets" \
--add-data "assets/dcblackicon.png;assets" \
--add-data "whisper;whisper" SRTing-python-open.py
```

> ⚠️ If `ffmpeg.exe` or `multilingual.tiktoken` are missing when building – your `.exe` will break.

## Premiere Pro Ready
The `.srt` output works straight in Premiere Pro. No formatting, encoding or re-saving needed. Just drag & drop.

## 📞 Contact
discord: **eskimek**
