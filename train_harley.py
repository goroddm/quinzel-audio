import os

from trainer import Trainer, TrainerArgs
from TTS.config.shared_configs import BaseAudioConfig
from TTS.tts.configs.glow_tts_config import GlowTTSConfig
from TTS.tts.configs.shared_configs import BaseDatasetConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.glow_tts import GlowTTS
from TTS.tts.utils.text.tokenizer import TTSTokenizer
from TTS.utils.audio import AudioProcessor

def main():
    # --- Редактируйте под себя ---
    DATASET_PATH = os.path.join(os.getcwd(), "voice_samples")    # здесь лежат файлы .wav и metadata.csv
    OUTPUT_PATH  = os.path.join(os.getcwd(), "harley_output_generate_model")  # где сохранять модель и логи
    META_FILE    = os.path.join(os.getcwd(), "meta_voice_samples.txt")  # имя файла с транскриптами
    # -----------------------------

    # 1) Конфигурация датасета
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",          # LJSpeech-формат: читает metadata.csv
        meta_file_train=META_FILE,     # имя CSV
        path=os.getcwd()#DATASET_PATH
    )
    for dataset in dataset_config:
        print(dataset)
    # 2) Конфигурация аудио
    # Часто для русской речи достаточно 22050, можно сделать 24000 / 48000
    audio_config = BaseAudioConfig(
        sample_rate=22050,
        resample=True,        # если ваши wav уже в нужном sample_rate
        do_trim_silence=False,  # можно отключить, если данные и так чистые
        trim_db=23.0
    )

    # 3) Конфигурация GlowTTS
    config = GlowTTSConfig(
        # ========== ВАЖНО: Параметры обучения ==========
        batch_size=8,              # уменьшите или увеличьте под вашу GPU
        eval_batch_size=8,
        epochs=50,                # общее число эпох (на самом деле, можно Early Stop)
        run_eval=True,              # запускать ли eval
        test_delay_epochs=-1,       # начать eval сразу
        print_step=25,              # логгировать каждые N шагов
        mixed_precision=True,       # ускорение на современных GPU
        # ==============================================

        num_loader_workers=2,
        num_eval_loader_workers=2,
        precompute_num_workers=2,
        #eval_step=200,            # чтобы не слишком часто
        save_step=200,            # чекпоинты реже

        text_cleaner="basic_cleaners",   # для русского текста "basic_cleaners"
                                         # или "cyrillic_cleaners" (если в вашей версии TTS есть)
        use_phonemes=True,              # если хотите фонемы, ставьте True + укажите phoneme_language="ru"
        phoneme_language="ru",
        phoneme_cache_path=os.path.join(OUTPUT_PATH, "phoneme_cache"),
        audio=audio_config,  # <-- ВАЖНО: привязываем сюда

        output_path=OUTPUT_PATH,         # куда сохранять модель

        # Это нужно, чтоб загружались наши датасеты
        datasets=[dataset_config],

        # single-speaker
        use_speaker_embedding=False,     # отключаем мультиспикер

        # Границы входного текста, аудио
        min_text_len=0,
        max_text_len=500,
        min_audio_len=300,
        max_audio_len=500000,
    )

    # Инициализация AudioProcessor
    ap = AudioProcessor.init_from_config(config)
    from TTS.tts.utils.text.tokenizer import DEF_LANG_TO_PHONEMIZER
    DEF_LANG_TO_PHONEMIZER["ru"] = "gruut"

    # Инициализация Tokenizer (для преобразования текста в IDs)
    tokenizer, config = TTSTokenizer.init_from_config(config)

    # Загрузка сэмплов (списков [text, audio_file, speaker])
    # Для ljspeech-форматтера:
    #   text = колонка из CSV,
    #   audio_file = chunk_XXXX.wav,
    #   speaker_name = "ljspeech" по умолчанию
    train_samples, eval_samples = load_tts_samples(
        dataset_config,
        eval_split=True,
        eval_split_max_size=config.eval_split_max_size,
        eval_split_size=0.010416666666666666#config.eval_split_size,
    )

    # Если точно уверены, что у вас маленький датасет, можно вручную
    # разнести часть файлов на валидацию, а в load_tts_samples(..., eval_split=False)
    # иначе Coqui TTS автоматически выделит процент.

    # Инициализируем модель (без SpeakerManager, т.к. 1 голос)
    model = GlowTTS(config, ap, tokenizer)

    # Инициализация Trainer
    trainer = Trainer(
        TrainerArgs(),       # можно сюда передать аргументы типа gpu_core=0 и т.д.
        config,
        OUTPUT_PATH,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples
    )

    # Запуск обучения
    trainer.fit()

if __name__ == '__main__':
    main()