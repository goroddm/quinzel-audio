from TTS.utils.synthesizer import Synthesizer

synthesizer = Synthesizer(
    model_dir="/Users/gorodeckiy.d4/work/Quinzel-audio/harley_output_generate_model/run-January-18-2025_03+03PM-0000000/best_model.pth",
    vc_config="/Users/gorodeckiy.d4/work/Quinzel-audio/harley_output_generate_model/run-January-18-2025_03+03PM-0000000/config.json",
    #speaker_idx=None  # если single-speaker
)

wav = synthesizer.tts("Привет, это Харли Квинн! Как у вас дела?")
synthesizer.save_wav(wav, "harley_test.wav")




from TTS.api import TTS
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

# Загрузка модели
model_name = "tts_models/multilingual/multi-dataset/xtts_v2"  # Замените на нужную модель
tts = TTS(model_name).to(device)

# Ввод текста и путь для сохранения
text = "Привет!!! мой пирожочек! рада тебя видеть"
output_path = "output_audio.wav"

# Генерация аудио
tts.tts_to_file(text=text, file_path=output_path, speaker='Damien Black', language='ru')

print(f"Генерация завершена. Файл сохранён как {output_path}")
