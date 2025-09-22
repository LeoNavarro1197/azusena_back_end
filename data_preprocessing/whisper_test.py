import whisper
import os

file_path = "query_01.mp3"



print('list dir')
print(os.listdir())
print('abspath')

absolute_path = os.path.abspath(file_path)
print(absolute_path)

print('file exist')
def file_exists(filename, path=os.getcwd()):
    """
    Verifica si el archivo especificado existe en el directorio especificado.
    """
    files = os.listdir(path)
    return filename in files

def test_whisper_transcription(audio_file_path):
    print("Cargando el modelo de Whisper...")
    model = whisper.load_model("base")
    print("Modelo cargado. Transcribiendo...")
    try:
        result = model.transcribe(audio_file_path)  # Usa la variable correcta aquí
        print("--- Resultado de la transcripción ---")
        print(result["text"])
    except Exception as e:
        print(f"Ocurrió un error durante la transcripción: {e}")

if file_exists(file_path):
    print('°---exist---°')
    test_whisper_transcription(file_path)
else:
    print("No se detectó el archivo")


