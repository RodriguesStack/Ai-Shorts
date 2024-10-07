from flask import Flask, render_template, request, send_from_directory, redirect, url_for
import os
import yt_dlp
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import numpy as np
import assemblyai as aai

app = Flask(__name__)

# Directory to store processed videos
VIDEO_DIR = os.path.join('static', 'videos')
os.makedirs(VIDEO_DIR, exist_ok=True)

# Function to download video from YouTube using yt_dlp
def download_video(url, output_path):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Simplificado para garantir o download do melhor formato
        'outtmpl': output_path,
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Function to format time for SRT
def format_time(milliseconds):
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# Function to process the video
def process_video(url):
    video_path = os.path.join(VIDEO_DIR, "movie-out.mp4")
    
    # Download the video
    download_video(url, video_path)

    # Load video and extract audio
    video = VideoFileClip(video_path)

    # Check if the video has audio
    if video.audio is None:
        raise Exception("The video does not contain audio.")

    audio_path = os.path.join(VIDEO_DIR, "audio.mp3")

    try:
        # Attempt to save audio as MP3 (default codec)
        video.audio.write_audiofile(audio_path, codec="mp3")
    except Exception as e:
        print(f"Error writing audio file: {e}")
        raise

    # Transcription using AssemblyAI
    aai.settings.api_key = "181e4113234a4ebab72186d67ff11b22"  # Replace with your API key
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(language_code=aai.LanguageCode.pt)
    transcript = transcriber.transcribe(audio_path, config)

    # Generate SRT file
    transcript_path = os.path.join(VIDEO_DIR, "transcript.srt")
    with open(transcript_path, "w", encoding="utf-8") as file:
        srt_string = ""
        subtitle_count = 1
        buffer = []
        previous_end_time = 0

        for word in transcript.words:
            text = word.text
            start_time = previous_end_time
            end_time = word.end
            buffer.append(text)

            if len(buffer) == 5:  # Modify as needed for subtitle duration
                srt_string += f"{subtitle_count}\n"
                srt_string += f"{format_time(start_time)} --> {format_time(end_time)}\n"
                srt_string += " ".join(buffer) + "\n\n"
                subtitle_count += 1
                buffer = []
                previous_end_time = end_time

        if buffer:
            srt_string += f"{subtitle_count}\n"
            srt_string += f"{format_time(previous_end_time)} --> {format_time(end_time)}\n"
            srt_string += " ".join(buffer) + "\n\n"

        file.write(srt_string)

    # Create subtitles
    def generator(txt):
        wrapped_txt = "\n".join(wrap(txt, width=20)).upper()
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

        for i in range(-border_thickness, border_thickness + 1):
            for j in range(-border_thickness, border_thickness + 1):
                d.multiline_text((x + i, y + j), wrapped_txt, font=font, fill=border_color, align="center")

        d.multiline_text((x, y), wrapped_txt, font=font, fill="yellow", align="center")
        img_np = np.array(img)
        return ImageClip(img_np)

    # Generate final video with subtitles
    subtitles = SubtitlesClip(transcript_path, generator)
    subtitles = subtitles.set_pos(("center", "bottom")).margin(bottom=int(video.h * 0.12), opacity=0)
    
    # Combine video and subtitles
    final_video = CompositeVideoClip([video, subtitles])
    final_video.audio = video.audio

    # Write video with subtitles and audio
    final_video.write_videofile(
        video_path,
        fps=video.fps,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",  # Adjust as necessary
        preset="medium"    # Adjust to "fast" or "slow" as desired
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        process_video(url)
        return redirect(url_for('get_video', filename='movie-out.mp4'))
    return render_template('index.html')

@app.route('/videos/<filename>')
def get_video(filename):
    return send_from_directory(VIDEO_DIR, filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000, debug=True)
