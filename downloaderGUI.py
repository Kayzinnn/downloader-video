#!/usr/bin/env python3
"""
Interface gráfica para o downloader de vídeos do YouTube.

Instalação:
    pip install yt-dlp

Uso:
    python downloader_gui.py

Basta colar a URL do vídeo, escolher as opções e clicar em "Baixar".
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class DownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("520x360")
        self.resizable(False, False)
        self.configure(padx=20, pady=20)

        self.pasta_destino = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.apenas_audio = tk.BooleanVar(value=False)
        self.qualidade = tk.StringVar(value="Melhor disponível")

        self._montar_interface()

        if yt_dlp is None:
            messagebox.showwarning(
                "Dependência faltando",
                "A biblioteca 'yt-dlp' não está instalada.\n\nInstale com:\npip install yt-dlp",
            )

    def _montar_interface(self):
        # Título
        tk.Label(self, text="YouTube Downloader", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(self, text="Cole a URL do vídeo abaixo", fg="gray").pack(anchor="w", pady=(0, 15))

        # Campo de URL
        tk.Label(self, text="URL do vídeo:").pack(anchor="w")
        self.entry_url = tk.Entry(self, font=("Segoe UI", 11))
        self.entry_url.pack(fill="x", pady=(0, 15))
        self.entry_url.focus()

        # Pasta de destino
        tk.Label(self, text="Salvar em:").pack(anchor="w")
        frame_pasta = tk.Frame(self)
        frame_pasta.pack(fill="x", pady=(0, 15))
        tk.Entry(frame_pasta, textvariable=self.pasta_destino).pack(side="left", fill="x", expand=True)
        tk.Button(frame_pasta, text="Escolher...", command=self._escolher_pasta).pack(side="left", padx=(8, 0))

        # Opções: áudio e qualidade
        frame_opcoes = tk.Frame(self)
        frame_opcoes.pack(fill="x", pady=(0, 15))

        tk.Checkbutton(
            frame_opcoes, text="Baixar apenas áudio (MP3)", variable=self.apenas_audio,
            command=self._alternar_qualidade
        ).pack(side="left")

        tk.Label(frame_opcoes, text="   Qualidade:").pack(side="left")
        self.combo_qualidade = ttk.Combobox(
            frame_opcoes, textvariable=self.qualidade, state="readonly", width=18,
            values=["Melhor disponível", "1080p", "720p", "480p", "360p"],
        )
        self.combo_qualidade.pack(side="left")

        # Botão de baixar
        self.botao_baixar = tk.Button(
            self, text="Baixar", font=("Segoe UI", 11, "bold"),
            bg="#e62117", fg="white", height=2, command=self._iniciar_download
        )
        self.botao_baixar.pack(fill="x", pady=(5, 10))

        # Barra de progresso
        self.progresso = ttk.Progressbar(self, mode="determinate")
        self.progresso.pack(fill="x")

        # Status
        self.label_status = tk.Label(self, text="", fg="gray", anchor="w")
        self.label_status.pack(fill="x", pady=(8, 0))

    def _alternar_qualidade(self):
        self.combo_qualidade.configure(state="disabled" if self.apenas_audio.get() else "readonly")

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_destino.get())
        if pasta:
            self.pasta_destino.set(pasta)

    def _iniciar_download(self):
        if yt_dlp is None:
            messagebox.showerror("Erro", "A biblioteca 'yt-dlp' não está instalada.\nInstale com: pip install yt-dlp")
            return

        url = self.entry_url.get().strip()
        if not url:
            messagebox.showwarning("Atenção", "Cole a URL do vídeo antes de baixar.")
            return

        self.botao_baixar.configure(state="disabled", text="Baixando...")
        self.progresso["value"] = 0
        self.label_status.configure(text="Iniciando...")

        thread = threading.Thread(target=self._baixar, args=(url,), daemon=True)
        thread.start()

    def _baixar(self, url: str):
        pasta = self.pasta_destino.get()
        os.makedirs(pasta, exist_ok=True)

        qualidade_map = {"1080p": "1080", "720p": "720", "480p": "480", "360p": "360"}
        altura = qualidade_map.get(self.qualidade.get())

        if self.apenas_audio.get():
            formato = "bestaudio/best"
            postprocessors = [{
                "key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192",
            }]
        else:
            if altura:
                formato = f"bestvideo[height<={altura}]+bestaudio/best[height<={altura}]"
            else:
                formato = "bestvideo+bestaudio/best"
            postprocessors = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]

        opcoes = {
            "format": formato,
            "outtmpl": f"{pasta}/%(title)s.%(ext)s",
            "postprocessors": postprocessors,
            "noplaylist": True,
            "progress_hooks": [self._progresso_callback],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(opcoes) as ydl:
                info = ydl.extract_info(url, download=True)
                titulo = info.get("title", "arquivo")
            self.after(0, self._download_concluido, titulo)
        except Exception as e:
            self.after(0, self._download_erro, str(e))

    def _progresso_callback(self, d):
        if d["status"] == "downloading":
            percentual_str = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                percentual = float(percentual_str)
            except ValueError:
                percentual = 0
            velocidade = d.get("_speed_str", "").strip()
            self.after(0, self._atualizar_progresso, percentual, velocidade)
        elif d["status"] == "finished":
            self.after(0, self.label_status.configure, {"text": "Processando arquivo..."})

    def _atualizar_progresso(self, percentual, velocidade):
        self.progresso["value"] = percentual
        self.label_status.configure(text=f"Baixando... {percentual:.0f}% ({velocidade})")

    def _download_concluido(self, titulo):
        self.progresso["value"] = 100
        self.label_status.configure(text=f"✅ Concluído: {titulo}", fg="green")
        self.botao_baixar.configure(state="normal", text="Baixar")

    def _download_erro(self, mensagem):
        self.label_status.configure(text="❌ Erro no download", fg="red")
        self.botao_baixar.configure(state="normal", text="Baixar")
        messagebox.showerror("Erro ao baixar", mensagem)


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()