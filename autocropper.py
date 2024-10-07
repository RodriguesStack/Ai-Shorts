import cv2
import yt_dlp
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from moviepy.video.tools.subtitles import SubtitlesClip
from textwrap import wrap
import face_recognition
from youtube_transcript_api import YouTubeTranscriptApi

# Função para baixar o vídeo do YouTube
def download_video(url, filename):
    ydl_opts = {
        'format': 'best',
        'outtmpl': filename,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Função para detectar rostos no vídeo
def detect_faces(video_file):
    cap = cv2.VideoCapture(video_file)
    face_locations = []

    while len(face_locations) < 5:  # Limitar a detecção para 5 quadros únicos
        ret, frame = cap.read()
        if ret:
            rgb_frame = frame[:, :, ::-1]  # Convertendo BGR para RGB
            faces_in_frame = face_recognition.face_locations(rgb_frame)
            if faces_in_frame:
                face_locations = faces_in_frame
        else:
            break
    cap.release()

    return face_locations

# Função para recortar o vídeo com base nos rostos detectados
def crop_video(faces, input_file, output_file):
    if faces:
        cap = cv2.VideoCapture(input_file)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_video = cv2.VideoWriter(output_file, fourcc, 30.0, (frame_width, frame_height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            for top, right, bottom, left in faces:
                cropped_frame = frame[top:bottom, left:right]
                # Ajustar para manter a mesma resolução
                resized_frame = cv2.resize(cropped_frame, (frame_width, frame_height))
                output_video.write(resized_frame)

        cap.release()
        output_video.release()
        print("Vídeo recortado com sucesso.")
    else:
        print("Nenhum rosto detectado no vídeo.")

# Função para obter a transcrição do vídeo
def get_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return transcript

# Função para gerar legendas com estilo personalizado
def generator(txt, video_size, fontsize, border_thickness, border_color):
    wrapped_txt = "\n".join(wrap(txt, width=40)).upper()
    img = Image.new("RGBA", (video_size[0], int(video_size[1] * 0.2)), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font_path = "fonts/Montserrat-Black.ttf"  # Certifique-se de que o caminho da fonte está correto
    font = ImageFont.truetype(font_path, fontsize)
    left, top, right, bottom = d.multiline_textbbox((0, 0), wrapped_txt, font=font)
    text_width, text_height = right - left, bottom - top
    x = (img.width - text_width) // 2
    y = (img.height - text_height) // 2

    # Desenhar a borda ao redor do texto
    for i in range(-border_thickness, border_thickness + 1):
        for j in range(-border_thickness, border_thickness + 1):
            d.multiline_text((x + i, y + j), wrapped_txt, font=font, fill=border_color, align="center")
    d.multiline_text((x, y), wrapped_txt, font=font, fill="yellow", align="center")
    return ImageClip(np.array(img))

# Função para adicionar legendas ao vídeo
def add_subtitles_to_video(input_video, transcript, output_file):
    video = VideoFileClip(input_video)
    fontsize = int(video.h * 0.05)  # Ajustar o tamanho da fonte com base na altura do vídeo
    border_thickness = 8
    border_color = "black"

    subtitle_clips = []
    for entry in transcript:
        text = entry['text']
        start_time = entry['start']
        duration = entry['duration']
        subtitle_clip = (generator(text, video.size, fontsize, border_thickness, border_color)
                         .set_start(start_time)
                         .set_duration(duration)
                         .set_pos(("center", "bottom")))
        subtitle_clips.append(subtitle_clip)

    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_file, fps=video.fps, codec="libx264", audio_codec="aac")

# Função para dividir o vídeo em partes de 10 minutos
def split_video(input_file, part_duration=600):
    video = VideoFileClip(input_file)
    duration = int(video.duration)
    parts = []

    for start in range(0, duration, part_duration):
        end = min(start + part_duration, duration)
        part = video.subclip(start, end)
        parts.append(part)

    return parts

# Função para adicionar efeitos a cada parte do vídeo
def add_effects_to_parts(video_parts):
    effects = [lambda clip: clip.fx(vfx.colorx, 1.5),  # Aumentar a saturação
               lambda clip: clip.fx(vfx.lum_contrast, 0, 150),  # Aumentar contraste
               lambda clip: clip.fx(vfx.fadein, 1),  # Efeito de fade-in
               lambda clip: clip.fx(vfx.fadeout, 1)]  # Efeito de fade-out

    for i, part in enumerate(video_parts):
        if i < len(effects):
            video_parts[i] = effects[i](part)

    return video_parts

# Código principal
if __name__ == "__main__":
    video_url = 'https://www.youtube.com/watch?v=NHaczOsMQ20'
    output_filename = 'video_baixado.mp4'
    download_video(video_url, output_filename)

    faces = detect_faces(output_filename)
    cropped_video = 'video_recortado.mp4'
    crop_video(faces, output_filename, cropped_video)

    video_id = 'NHaczOsMQ20'  # Ajuste para o ID correto do vídeo
    transcript = get_transcript(video_id)

    # Dividir o vídeo em partes de 10 minutos
    video_parts = split_video(cropped_video, part_duration=600)
    video_parts_with_effects = add_effects_to_parts(video_parts)

    # Adicionar legendas a cada parte e salvar os vídeos
    for i, part in enumerate(video_parts_with_effects):
        output_file = f'video_parte_{i + 1}.mp4'
        part.write_videofile(output_file, fps=part.fps, codec="libx264", audio_codec="aac")
        add_subtitles_to_video(output_file, transcript, output_file)

    print("Todos os vídeos foram processados e salvos.")
