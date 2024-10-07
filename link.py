from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# Configura o caminho do ImageMagick (se necessário)
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})  # Ajuste o caminho conforme seu sistema

# Carrega o vídeo original
video = VideoFileClip("./play.mp4")


# Define o tempo para exibir o link nos últimos 5 segundos do vídeo
duracao_link = 5  # Duração em segundos
inicio_link = video.duration - duracao_link  # Quando o texto deve aparecer

# Cria um clipe de texto com o "link"
texto = TextClip("Clique aqui: https://example.com", fontsize=20, color='black')

# Define a duração do clipe de texto (5 segundos)
texto = texto.set_duration(duracao_link)

# Posiciona o texto na parte inferior do vídeo
texto = texto.set_pos(('center', 'bottom'))

# Sobrepõe o texto no vídeo nos últimos 5 segundos
video_com_texto = CompositeVideoClip([video, texto.set_start(inicio_link)])

# Salva o vídeo final
video_com_texto.write_videofile("output_video.mp4", codec="libx264")
