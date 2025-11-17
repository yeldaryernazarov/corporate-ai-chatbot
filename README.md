# AI-Чатбот для корпоративных сервисов

## Описание проекта

Корпоративный AI-чатбот с тремя специализированными агентами для автоматизации работы с финансами, юридическими вопросами и проектным управлением.

## Структура агентов

### 1. Финансовый ассистент
- Ответы по вопросам бюджетов, лимитов, оплат
- Напоминания о платежах
- Контроль финансовых лимитов

### 2. Юридический ассистент
- Поиск нормативных документов
- Типовые контракты
- Разъяснения правовых процедур

### 3. Проектный ассистент
- Контроль дедлайнов
- Статусы задач
- Уведомления о рисках

## Технологический стек

- **Python 3.10+**
- **LangChain** - для работы с LLM
- **OpenAI API** - GPT-4 mini и Embeddings
- **Pinecone** - векторная база данных
- **n8n** - оркестрация workflow
- **Telegram Bot API** - интерфейс пользователя
- **Docker** - контейнеризация

## Архитектура решения

```
Пользователь → Telegram Bot → n8n Workflow → Python Backend
                                                    ↓
                                            OpenAI Embeddings
                                                    ↓
                                            Pinecone Search
                                                    ↓
                                            GPT-4 mini (Response)
                                                    ↓
                                            Telegram Bot → Пользователь
```

## Установка и настройка

### Предварительные требования

1. Python 3.10 или выше
2. Аккаунты и API ключи:
   - OpenAI API Key
   - Pinecone API Key
   - Telegram Bot Token
   - n8n (SaaS или self-hosted)

### Шаги установки

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd corporate-ai-chatbot

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить свои ключи

# 5. Инициализировать векторную базу данных
python scripts/init_pinecone.py

# 6. Загрузить документы в Pinecone
python scripts/load_documents.py

# 7. Запустить бота
python src/main.py
```

## Структура проекта

```
corporate-ai-chatbot/
├── src/
│   ├── agents/              # Модули агентов
│   │   ├── finance_agent.py
│   │   ├── legal_agent.py
│   │   └── project_agent.py
│   ├── core/                # Основные компоненты
│   │   ├── llm_client.py
│   │   ├── vector_store.py
│   │   └── telegram_bot.py
│   ├── utils/               # Вспомогательные функции
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── error_handler.py
│   └── main.py              # Точка входа
├── scripts/                 # Утилиты для настройки
│   ├── init_pinecone.py
│   └── load_documents.py
├── data/                    # Документы для загрузки
│   ├── finance/
│   ├── legal/
│   └── project/
├── tests/                   # Тесты
│   ├── test_agents.py
│   └── test_cases.py
├── n8n/                     # Конфигурация n8n
│   └── workflow.json
├── docs/                    # Документация
│   ├── architecture.md
│   └── presentation.pptx
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Конфигурация

Все настройки хранятся в файле `.env`:

```env
# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=corporate-kb

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# n8n
N8N_WEBHOOK_URL=your_n8n_webhook_url

# Settings
MAX_RESPONSE_TIME=3
MIN_ACCURACY=0.85
```

## Использование

### Запуск через Telegram

1. Найдите бота в Telegram: `@your_bot_name`
2. Начните диалог командой `/start`
3. Выберите агента:
   - `/finance` - Финансовый ассистент
   - `/legal` - Юридический ассистент
   - `/project` - Проектный ассистент
4. Задайте вопрос

### Примеры запросов

**Финансовый агент:**
- "Какой лимит бюджета на маркетинг в этом квартале?"
- "Когда нужно оплатить счет за аренду офиса?"

**Юридический агент:**
- "Где найти типовой договор о конфиденциальности?"
- "Какие документы нужны для регистрации филиала?"

**Проектный агент:**
- "Какие задачи просрочены в проекте X?"
- "Есть ли риски срыва дедлайнов?"

## Обработка ошибок

Система обрабатывает следующие типы ошибок:
- Отсутствие данных в базе знаний
- Сбои API (OpenAI, Pinecone, Telegram)
- Превышение времени ответа
- Некорректные запросы

## Тестирование

```bash
# Запустить все тесты
pytest tests/

# Запустить тесты агентов
pytest tests/test_agents.py

# Запустить тестовые кейсы
pytest tests/test_cases.py -v
```

## Метрики качества

- **Точность ответов**: ≥85%
- **Время ответа**: ≤3 секунды
- **Доступность**: 99%

## Deployment

### Docker

```bash
# Собрать образ
docker build -t corporate-ai-chatbot .

# Запустить контейнер
docker-compose up -d
```

### Cloud Deployment

Инструкции по развертыванию в облаке находятся в `docs/deployment.md`

## Безопасность

- Все API ключи хранятся в переменных окружения
- Конфиденциальные данные не логируются
- Доступ к боту только для авторизованных пользователей
- Шифрование данных при передаче

## Поддержка

Для вопросов и предложений создайте issue в репозитории.

## Лицензия

Все права на проект принадлежат Организатору согласно условиям конкурса.
