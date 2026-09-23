#!/usr/bin/env python3
"""
Downloader de vídeos do YouTube usando yt-dlp.

Instalação:
    pip install yt-dlp

Uso:
    python downloader.py <url>
    python downloader.py <url> --audio            # baixa só o áudio (mp3)
    python downloader.py <url> --pasta downloads   # define pasta de saída
    python downloader.py <url> --qualidade 720     # limita resolução (ex: 480, 720, 1080)
"""

import argparse
import sys

try:
    import yt_dlp
except ImportError:
    print("Erro: a biblioteca 'yt-dlp' não está instalada.")
    print("Instale com: pip install yt-dlp")
    sys.exit(1)


def baixar_video(url: str, pasta: str = "downloads", apenas_audio: bool = False, qualidade: str | None = None):
    """Baixa um vídeo (ou o áudio) do YouTube a partir da URL informada."""

    if apenas_audio:
        formato = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        if qualidade:
            formato = f"bestvideo[height<={qualidade}]+bestaudio/best[height<={qualidade}]"
        else:
            formato = "bestvideo+bestaudio/best"
        postprocessors = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]

    opcoes = {
        "format": formato,
        "outtmpl": f"{pasta}/%(title)s.%(ext)s",
        "postprocessors": postprocessors,
        "noplaylist": True,
        "progress_hooks": [_mostrar_progresso],
        "quiet": False,
    }

    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)
        titulo = info.get("title", "arquivo")
        print(f"\n✅ Download concluído: {titulo}")


def _mostrar_progresso(d):
    if d["status"] == "downloading":
        percentual = d.get("_percent_str", "").strip()
        velocidade = d.get("_speed_str", "").strip()
        print(f"\rBaixando... {percentual} ({velocidade})", end="", flush=True)
    elif d["status"] == "finished":
        print("\nProcessando arquivo...")


def main():
    parser = argparse.ArgumentParser(description="Baixa vídeos do YouTube com yt-dlp.")
    parser.add_argument("url", help="URL do vídeo do YouTube")
    parser.add_argument("--pasta", default="downloads", help="Pasta de destino (padrão: downloads)")
    parser.add_argument("--audio", action="store_true", help="Baixar apenas o áudio em MP3")
    parser.add_argument("--qualidade", default=None, help="Altura máxima do vídeo em pixels (ex: 480, 720, 1080)")

    args = parser.parse_args()

    try:
        baixar_video(args.url, pasta=args.pasta, apenas_audio=args.audio, qualidade=args.qualidade)
    except yt_dlp.utils.DownloadError as e:
        print(f"\n❌ Erro ao baixar: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()