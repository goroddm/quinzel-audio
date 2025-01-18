import whisper

# Загрузка модели
model = whisper.load_model("base")  # Используйте "small", "medium" или "large" для большей точности

# Ввод аудиофайла
audio_path = "/Users/gorodeckiy.d4/work/Quinzel-voice/chunks/chunk_0026.wav"

# Распознавание речи
result = model.transcribe(audio_path)

# Вывод результата
print("Распознанный текст:")
print(result["text"])
