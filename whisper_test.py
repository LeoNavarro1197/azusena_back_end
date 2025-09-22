import whisper
import ffmpeg
import os

file_path = "./query_01.mp3"
print(os.path.exists(file_path))

#Cargar el modelo
modelo = whisper.load_model("tiny")
#Transcribir el audio a texto
resultado = modelo.transcribe(file_path)
#Imprimir la transcripción
print(f"\nTranscripción:\n {resultado['text']}\n")



def test_whisper_transcription(audio_file_path):
    print("Cargando el modelo de Whisper...")
    model = whisper.load_model("large")
    print("Modelo cargado. Transcribiendo...")
    try:
        result = model.transcribe(audio_file_path)
        print("--- Resultado de la transcripción ---")
        print(result["text"])
    except Exception as e:
        print(f"Ocurrió un error durante la transcripción: {e}")


test_whisper_transcription(file_path)