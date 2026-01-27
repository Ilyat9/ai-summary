from celery import Celery
import os
from dotenv import load_dotenv
import yt_dlp
from bs4 import BeautifulSoup
import requests
import re
import google.generativeai as genai

load_dotenv()
key = os.getenv('GEMINI_API_KEY')
print(f"DEBUG: Key found: {key[:5]}***" if key else "DEBUG: Key NOT found")
genai.configure(api_key=key)

celery_app = Celery(
    'ai_summary',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


def extract_youtube_id(url: str) -> str | None:
    """
    Извлекает ID видео из YouTube URL
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def clean_vtt_text(text: str) -> str:
    """
    Очищает текст субтитров от VTT таймкодов и служебных тегов
    """
    # Удаляем заголовок WEBVTT
    text = re.sub(r'^WEBVTT\s*\n', '', text, flags=re.MULTILINE)
    
    # Удаляем строки с таймкодами (00:00:00.000 --> 00:00:05.000)
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}.*\n', '', text)
    
    # Удаляем строки вида "00:00:00.000" или просто числа (индексы субтитров)
    text = re.sub(r'^\d+\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*\n', '', text, flags=re.MULTILINE)
    
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Удаляем пустые строки и лишние пробелы
    text = re.sub(r'\n\s*\n', '\n', text)
    text = ' '.join(text.split())
    
    return text.strip()


def parse_youtube(url: str) -> str:
    """
    Получает транскрипт ютуб видео через yt_dlp
    """
    # Настройка SOCKS5 прокси для обхода блокировок
    proxy = 'socks5://10.0.2.2:7897'
    
    # Конфигурация yt_dlp
    ydl_opts = {
        'proxy': proxy,
        'quiet': True,
        'no_warnings': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['ru', 'en'],
        'skip_download': True,
        'ignoreerrors': True,
    }
    
    # Проверяем наличие файла cookies
    cookies_file = 'cookies.txt'
    if os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Получаем информацию о видео
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise ValueError("Не удалось получить информацию о видео")
            
            # Ищем субтитры (сначала русские, потом английские)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            # Объединяем обычные и автоматические субтитры
            all_subs = {**automatic_captions, **subtitles}
            
            subtitle_url = None
            
            # Приоритет: ru -> en
            for lang in ['ru', 'en']:
                if lang in all_subs:
                    # Ищем формат vtt или srv3 (они содержат текст)
                    for fmt in all_subs[lang]:
                        if fmt.get('ext') in ['vtt', 'srv3']:
                            subtitle_url = fmt.get('url')
                            break
                    if subtitle_url:
                        break
            
            if not subtitle_url:
                raise ValueError("Субтитры недоступны для этого видео")
            
            # Скачиваем субтитры через прокси
            proxies = {
                'http': proxy,
                'https': proxy,
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(subtitle_url, headers=headers, proxies=proxies, timeout=15)
            response.raise_for_status()
            
            # Получаем текст и очищаем от VTT форматирования
            subtitle_text = response.text
            clean_text = clean_vtt_text(subtitle_text)
            
            if not clean_text:
                raise ValueError("Текст субтитров пуст после очистки")
            
            return clean_text
            
    except yt_dlp.utils.DownloadError as e:
        raise Exception(f"Ошибка загрузки через yt_dlp: {str(e)}")
    except Exception as e:
        raise Exception(f"Ошибка получения транскрипта: {str(e)}")


def parse_web(url: str) -> str:
    """
    Парсит текст с веб-страницы
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Извлекаем текст
        text = soup.get_text(separator=' ', strip=True)
        
        # Очищаем от лишних пробелов
        text = ' '.join(text.split())
        
        return text
    except Exception as e:
        raise Exception(f"Ошибка парсинга веб-страницы: {str(e)}")


def generate_summary(text: str) -> str:
    try:
        model_name = 'gemini-1.5-flash'

        # Ограничиваем текст (Gemini токен лимит)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        try:
            # Инициализируем модель
            model = genai.GenerativeModel(model_name)
        
            # Формируем промпт
            prompt = f"""Ты помощник, который создаёт краткие и информативные выжимки из текстов. Отвечай на русском языке.

Создай подробную выжимку следующего текста, выделив ключевые моменты:

{text}"""
        
            # Генерируем ответ
            response = model.generate_content(prompt)
        
            summary = response.text
            return summary
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("Flash model not found, searching for available models...")
                available_models = [m.name for m in genai.list_models() 
                                   if 'generateContent' in m.supported_generation_methods]
                
                if not available_models:
                    raise Exception("No generative models available for this API key.")
                
                new_model_name = available_models[0]
                print(f"Switching to model: {new_model_name}")
                model = genai.GenerativeModel(new_model_name)
                response = model.generate_content(prompt)
                return response.text
            else:
                raise e

    except Exception as e:
        raise Exception(f"Ошибка генерации саммари: {str(e)}")


@celery_app.task(bind=True, max_retries=3)
def process_url(self, url: str) -> str:
    try:
        # Определяем тип URL и парсим
        if 'youtube.com' in url or 'youtu.be' in url:
            text = parse_youtube(url)
        else:
            text = parse_web(url)
        
        if not text or len(text) < 100:
            raise ValueError("Недостаточно текста для создания выжимки")
        
        # Генерируем саммари
        summary = generate_summary(text)
        
        return summary
        
    except Exception as e:
        # Retry логика
        try:
            raise self.retry(exc=e, countdown=5)
        except self.MaxRetriesExceededError:
            return f"❌ Ошибка обработки: {str(e)}"