import csv
import os
import subprocess
import pysrt
import json
import datetime

# Параметры


def extract_subtitles(mkv_file, subtitle_file):
    """
    Извлекает все субтитры из MKV-файла в текущую папку.
    """
    base_name = os.path.splitext(mkv_file)[0]
    cmd = f'ffmpeg -i "{mkv_file}" -map 0:5 -c:s srt "{subtitle_file}.srt" -y'
    subprocess.run(cmd, shell=True, check=True)
    print(f"Субтитры извлечены: {base_name}_track_*.srt")


def parse_selected_subtitles(subtitle_file, episode_name):
    """
    Читает субтитры и объединяет помеченные ("+") фрагменты.
    """
    subs = pysrt.open(subtitle_file)
    selected_segments = []
    current_segment_lenth_seconds = 0
    for current_segment in subs:
        if "+" in str(current_segment.index):
            index = str(current_segment.index).replace('+', '')
            index = int(index)
            #    start_time = current_segment.start
            #    end_time = current_segment.end
            name = f"{episode_name}_{index:04d}.wav"
            text = current_segment.text
            text = text.replace('\n', ' ').replace('"', '')
            selected_segments.append((name, current_segment.start, current_segment.end, text))
#                current_segment.append(sub)
#                current_segment_lenth_seconds += sub.duration.seconds
#                if current_segment_lenth_seconds > 6:
#                    if current_segment: selected_segments.append(current_segment)
#                    current_segment = []
#                    current_segment_lenth_seconds = 0
#            else:
#                # Завершаем текущую группу
#                if current_segment: selected_segments.append(current_segment)
#                current_segment = []
#                current_segment_lenth_seconds = 0


    # Объединяем фрагменты в группы
    #result = []
    #for group in selected_segments:
    #    #if len(group) == 1:
    #    #    result.append((group[0].start, group[0].end, group[0].text.replace("+", "")))
    #    start_time = group.start
    #    end_time = group.end
    #    text = " ".join([s.text.replace("+", "").strip() for s in group])
    #    index  = str(group.index).replace('+','')
    #    index = int(index)
    #    result.append((index, end_time, text))

    return selected_segments


def srt_time_to_ffmpeg_str(srt_time):
    """
    Преобразует pysrt.SubRipTime в строку HH:MM:SS.mmm
    """
    return f"{srt_time.hours:02}:{srt_time.minutes:02}:{srt_time.seconds:02}.{srt_time.milliseconds:03}"


def timedelta_to_str(delta):
    """
    Конвертирует timedelta в строку HH:MM:SS.mmm
    """
    total_seconds = delta.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"


def extract_audio_segments(mkv_file, segments, OUTPUT_DIR):
    """
    Вырезает аудиофрагменты из MKV по таймкодам.
    Таймкоды в metadata пересчитываются относительно каждого аудиофайла.
    """
    chunks = []
    for i, (name, start, end, text) in enumerate(segments):
        start_str = srt_time_to_ffmpeg_str(start)

        end_time = datetime.timedelta(
            hours=end.hours,
            minutes=end.minutes,
            seconds=end.seconds,
            milliseconds=end.milliseconds
        ) + datetime.timedelta(milliseconds=70)
        end_str = f"{int(end_time.total_seconds() // 3600):02}:{int((end_time.total_seconds() % 3600) // 60):02}:{int(end_time.total_seconds() % 60):02}.{int(end_time.microseconds // 1000):03}"
        #end_str = srt_time_to_ffmpeg_str(end_time)

        chunk_filename = name
        chunk_path = os.path.join(OUTPUT_DIR, chunk_filename)

        cmd = [
            "ffmpeg",
            "-i", mkv_file,
            "-ss", start_str,
            "-to", end_str,
            "-vn",  # Без видео
            "-c:a", "pcm_s16le",  # Несжатый PCM
            "-ar", "48000",  # 48 кГц
            "-ac", "2",  # Стерео
            chunk_path,
            "-y"
        ]
        subprocess.run(cmd, check=True)

        # Вычисляем относительные таймкоды
        start_delta = datetime.timedelta()
        end_delta = datetime.timedelta(hours=end.hours, minutes=end.minutes, seconds=end.seconds, milliseconds=end.milliseconds) - \
                    datetime.timedelta(hours=start.hours, minutes=start.minutes, seconds=start.seconds, milliseconds=start.milliseconds)

        relative_start = timedelta_to_str(start_delta)
        relative_end = timedelta_to_str(end_delta)

        chunks.append({
            "file": chunk_filename,
            "subtitles": [
                {
                    "start_time": relative_start,
                    "end_time": relative_end,
                    "text": text
                }
            ]
        })

    return chunks


def save_metadata(metadata, output_file):
    """
    Сохраняет метаданные в JSON.
    """
    with open(output_file, mode="w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter='|', quoting=csv.QUOTE_MINIMAL)
        for data in metadata:
            name, start, end, text = data
            writer.writerow([name, text])

    #with open(output_file, "w", encoding="utf-8") as f:
    #    json.dump(metadata, f, ensure_ascii=False, indent=4)
    print(f"Метафайл сохранён: {output_file}")



episode_name = 's4e3' #input("Введите префикс для названия чанков ").strip()
OUTPUT_DIR = os.path.join(os.getcwd(), episode_name)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():

    METADATA_FILE = os.path.join(OUTPUT_DIR, f"{episode_name}.csv")
    # Получение имени файла MKV
    mkv_file = os.path.join(OUTPUT_DIR, f"{episode_name}.mkv")
    subtitle_file = os.path.join(OUTPUT_DIR, f"{episode_name}.str")

    if not os.path.exists(subtitle_file):
         # Шаг 1: Извлечение субтитров
        print("Извлечение субтитров...")
        extract_subtitles(mkv_file, subtitle_file)
        print("Готово, разметьте субтитры и запустите скрипт еще раз")
        exit(1)

    # Шаг 3: Обработка субтитров
    print("Чтение и объединение выбранных фрагментов...")
    selected_segments = parse_selected_subtitles(subtitle_file, episode_name)

    # Шаг 4: Вырезка аудио
    #print("Вырезка аудиофрагментов...")
    audio_chunks = extract_audio_segments(mkv_file, selected_segments, OUTPUT_DIR)

    # Шаг 5: Сохранение метаданных
    print("Создание метафайла...")
    save_metadata(selected_segments, METADATA_FILE)

    print("Процесс завершён! Все результаты находятся в папке data.")


if __name__ == "__main__":
    main()
