# 🤖 AI-Summary

**AI-Summary** — это веб-сервис для создания умных выжимок из YouTube видео и веб-страниц с помощью искусственного интеллекта. Просто вставьте ссылку, и нейросеть создаст краткое резюме содержимого.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![React](https://img.shields.io/badge/React-18.2-61dafb.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Возможности

- 📹 **YouTube видео** — автоматическое получение транскриптов и создание выжимок
- 🌐 **Веб-страницы** — парсинг и суммаризация статей, блогов и новостей
- 🚀 **Асинхронная обработка** — Celery + Redis для фоновых задач
- 🎨 **Современный UI** — React с TailwindCSS и поддержкой Markdown
- ⚡ **Real-time статус** — автоматическое обновление прогресса обработки

## 🛠 Технологический стек

### Backend
- **FastAPI** — современный веб-фреймворк для API
- **Celery** — распределённая очередь задач
- **Redis** — брокер сообщений и кэш
- **Google Gemini API** — генерация выжимок с помощью Gemini 1.5 Flash
- **youtube-transcript-api** — получение транскриптов YouTube
- **BeautifulSoup4** — парсинг HTML-страниц

### Frontend
- **React 18** — UI библиотека
- **Vite** — современный сборщик
- **TailwindCSS** — утилитарный CSS-фреймворк
- **Axios** — HTTP-клиент
- **React Markdown** — рендеринг Markdown

### DevOps
- **Docker** — контейнеризация Redis
- **Python venv** — изолированное окружение Python

## 📋 Требования

- **Python** 3.10 или выше
- **Node.js** 18 или выше
- **Docker** и **Docker Compose**
- **Google Gemini API ключ** ([получить здесь](https://makersuite.google.com/app/apikey))

## 🚀 Как запустить локально

### 1. Клонирование репозитория

```bash
git clone https://github.com/Ilyat9/ai-summary.git
cd ai-summary
```

### 2. Настройка Backend

**Терминал 1: Backend Setup**

```bash
# Переходим в папку backend
cd backend

# Создаём виртуальное окружение
python -m venv venv

# Активируем виртуальное окружение
# На macOS/Linux:
source venv/bin/activate
# На Windows:
venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаём файл .env с вашим API ключом
cp ../.env.example .env
# Откройте .env и добавьте свой GEMINI_API_KEY
```

### 3. Запуск Redis через Docker

**Терминал 2: Docker**

```bash
# Из корневой папки проекта
docker-compose up -d

# Проверка что Redis запущен
docker ps
```

### 4. Запуск Celery Worker

**Терминал 3: Celery Worker**

```bash
cd backend
source venv/bin/activate  # Активируем виртуальное окружение

# Запускаем Celery worker
celery -A worker.celery_app worker --loglevel=info
```

### 5. Запуск FastAPI сервера

**Терминал 4: FastAPI**

```bash
cd backend
source venv/bin/activate  # Активируем виртуальное окружение

# Запускаем FastAPI сервер
python main.py
```

Сервер будет доступен по адресу: **http://localhost:8000**

API документация: **http://localhost:8000/docs**

### 6. Настройка и запуск Frontend

**Терминал 5: Frontend**

```bash
# Переходим в папку frontend
cd frontend

# Устанавливаем зависимости
npm install

# Запускаем dev-сервер
npm run dev
```

Frontend будет доступен по адресу: **http://localhost:5173**

## 🎯 Использование

1. Откройте **http://localhost:5173** в браузере
2. Вставьте ссылку на YouTube видео или веб-страницу
3. Нажмите "Создать выжимку"
4. Дождитесь обработки (обычно 10-30 секунд)
5. Получите готовую выжимку в формате Markdown

### Примеры ссылок для тестирования:

- YouTube: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Статья: `https://en.wikipedia.org/wiki/Artificial_intelligence`

## 📁 Структура проекта

```
ai-summary/
├── backend/
│   ├── main.py              # FastAPI endpoints
│   ├── worker.py            # Celery tasks
│   ├── requirements.txt     # Python зависимости
│   └── .env                 # Переменные окружения (не в Git)
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Главный компонент
│   │   ├── main.jsx        # Entry point
│   │   └── index.css       # Tailwind styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── docker-compose.yml       # Redis контейнер
├── .gitignore
├── .env.example             # Шаблон переменных
└── README.md
```

## 🔒 Безопасность

- ✅ Файл `.env` с API ключами **исключён из Git**
- ✅ Используйте `.env.example` как шаблон
- ✅ Никогда не коммитьте реальные API ключи

## 🐛 Troubleshooting

### Redis не запускается
```bash
# Остановите все контейнеры и перезапустите
docker-compose down
docker-compose up -d
```

### Celery не видит задачи
```bash
# Убедитесь что Redis запущен
docker ps | grep redis

# Перезапустите Celery worker
# Ctrl+C в терминале Celery, затем
celery -A worker.celery_app worker --loglevel=info
```

### Ошибка CORS
Убедитесь что:
- FastAPI запущен на порту 8000
- Frontend запущен на порту 5173
- В `main.py` правильно настроены CORS origins

## 📝 Roadmap

- [ ] Поддержка PDF документов
- [ ] Настройка длины выжимки
- [ ] История обработанных ссылок
- [ ] Экспорт в различные форматы
- [ ] Поддержка нескольких языков

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 👨‍💻 Автор Ilyat9

Создано с ❤️ 

---

⭐ Если проект был полезен, поставьте звезду на GitHub!