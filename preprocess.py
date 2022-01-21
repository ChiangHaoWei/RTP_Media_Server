import moviepy.editor as mp
import os

def convert(path:str):
  clip = mp.VideoFileClip(path)
  file_name = path[:path.find('.mp4')]
  clip.audio.write_audiofile(f"{file_name}.wav")

def convert_all():
  files = os.listdir(".")
  for file in os.listdir('.'):
    if file.endswith(".mp4") and file[:file.find(".mp4")]+".wav" not in files:
      convert(file)
# from pydub import AudioSegment

# def convert(path:str):
#   print(path)
#   AudioSegment.converter = r'C:\FFmpeg\bin\ffmpeg.exe'
#   AudioSegment.ffprobe =r"C:\FFmpeg\bin\ffprobe.exe"
#   audio = AudioSegment.from_file(path, "mp4")
#   file_name = path.strip('.mp4')
#   audio.export(f"{file_name}.wav", format="wav")

# convert("movie.mp4")

# import subprocess
# def convert(path:str):
  # file_name = path.rstrip('.mp4')
  # command = f"ffmpeg -i {path} -ab 160k -ac 2 -ar 44100 -vn {file_name}.wav"
  # subprocess.call(command, shell=True)

