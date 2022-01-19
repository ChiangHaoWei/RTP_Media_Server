from pydub import AudioSegment

def convert(path:str):
  print(path)
  AudioSegment.converter = r'C:\FFmpeg\bin\ffmpeg.exe'
  AudioSegment.ffprobe =r"C:\FFmpeg\bin\ffprobe.exe"
  audio = AudioSegment.from_file(path, "mp4")
  file_name = path.strip('.mp4')
  audio.export(f"{file_name}.wav", format="wav")

convert("movie.mp4")