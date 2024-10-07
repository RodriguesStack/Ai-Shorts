from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import os
import yt_dlp
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import numpy as np
import requests
import time

app = Flask(__name__)
CORS(app)  # Habilitar CORS

# Diretório para armazenar os vídeos processados
VIDEO_DIR = os.path.join('static', 'videos')
os.makedirs(VIDEO_DIR, exist_ok=True)

# Função para baixar vídeo do YouTube usando yt-dlp
def download_video(url, output_path):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Baixa o melhor formato disponível
        'outtmpl': output_path,
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Função para gerar legendas automáticas com AssemblyAI
def generate_subtitles(audio_path):
    API_KEY = "181e4113234a4ebab72186d67ff11b22"  # Insira sua chave de API do AssemblyAI
    headers = {'authorization': API_KEY}

    # Upload do arquivo de áudio para AssemblyAI
    upload_url = 'https://api.assemblyai.com/v2/upload'
    with open(audio_path, 'rb') as f:
        response = requests.post(upload_url, headers=headers, files={'file': f})
    audio_url = response.json()['upload_url']

    # Solicitar transcrição
    transcript_url = 'https://api.assemblyai.com/v2/transcript'
    transcript_request = {'audio_url': audio_url}
    transcript_response = requests.post(transcript_url, headers=headers, json=transcript_request)
    transcript_id = transcript_response.json()['id']

    # Aguardar conclusão da transcrição
    while True:
        transcript_status = requests.get(f'{transcript_url}/{transcript_id}', headers=headers).json()
        if transcript_status['status'] == 'completed':
            return transcript_status['words']  # Retorna palavras com timestamps
        elif transcript_status['status'] == 'failed':
            raise Exception('Transcription failed')
        time.sleep(5)

# Função para adicionar legendas com diferentes estilos
def add_subtitles_with_style(video_path, subtitles, output_path, style='default'):
    video = VideoFileClip(video_path)

    def generator(txt):
        wrapped_txt = "\n".join(wrap(txt.upper(), width=20))
        img = Image.new("RGBA", (video.size[0], int(video.h * 0.2)), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        fontsize = int(video.h * 0.04)
        font = ImageFont.truetype("fonts/Montserrat-Black.ttf", fontsize)
        left, top, right, bottom = d.multiline_textbbox((0, 0), wrapped_txt, font=font)
        text_width, text_height = right - left, bottom - top
        x = (img.width - text_width) // 2
        y = (img.height - text_height) // 2
        border_thickness = 8
        border_color = "black"

        # Mudança de estilo nas bordas
        for i in range(-border_thickness, border_thickness + 1):
            for j in range(-border_thickness, border_thickness + 1):
                d.multiline_text((x + i, y + j), wrapped_txt, font=font, fill=border_color, align="center")

        # Diferentes estilos para o preenchimento
        if style == 'highlight':
            fill_color = "yellow"
        elif style == 'bold':
            fill_color = "red"
        else:
            fill_color = "white"

        d.multiline_text((x, y), wrapped_txt, font=font, fill=fill_color, align="center")
        img_np = np.array(img)
        return ImageClip(img_np)

    # Criar legendas como clips de texto
    subtitle_clips = [generator(word['text']).set_start(word['start'] / 1000).set_end(word['end'] / 1000) for word in subtitles]

    # Sobrepor legendas no vídeo
    final = CompositeVideoClip([video] + subtitle_clips)
    final.write_videofile(output_path, fps=24)

# Função para processar vídeo para TikTok
def process_youtube_video_for_tiktok(youtube_url, start_time=None, end_time=None):
    video_path = os.path.join(VIDEO_DIR, "downloaded_video.mp4")
    download_video(youtube_url, video_path)

    # Cortar vídeo
    cut_video_path = os.path.join(VIDEO_DIR, "cut_video.mp4")
    video = VideoFileClip(video_path).subclip(start_time, end_time)

    # Adaptar para o formato TikTok (9:16)
    tiktok_video = video.resize(height=1920).crop(x_center=video.w / 2, width=1080, height=1920)
    tiktok_video.write_videofile(cut_video_path)

    # Extrair áudio
    audio_path = os.path.join(VIDEO_DIR, "audio.mp3")
    video.audio.write_audiofile(audio_path)

    # Gerar legendas
    subtitles = generate_subtitles(audio_path)

    # Adicionar legendas coloridas e chamativas
    final_video_path = os.path.join(VIDEO_DIR, "final_tiktok_video.mp4")
    add_subtitles_with_style(cut_video_path, subtitles, final_video_path, style='highlight')

    return final_video_path

@app.route('/api/process_video', methods=['POST'])
def api_process_video():
    data = request.get_json()
    youtube_url = data.get('url')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    # Converter para inteiro, se fornecido
    start_time = int(start_time) if start_time else None
    end_time = int(end_time) if end_time else None

    try:
        video_path = process_youtube_video_for_tiktok(youtube_url, start_time, end_time)
        return jsonify({
            'message': 'Vídeo processado com sucesso',
            'video_path': f'http://localhost:8000/videos/{os.path.basename(video_path)}'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/videos/<filename>')
def get_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
