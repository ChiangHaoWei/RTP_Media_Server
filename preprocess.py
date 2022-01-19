from pydub import AudioSegment

def convert(path:str):
  audio = AudioSegment.from_file(path, "mp4")
  file_name = path.strip('mp4')
  audio.export(f"{file_name}.wav", format="wav")