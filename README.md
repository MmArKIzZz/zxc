Это веб-приложение предназначено для перевода координат между различными системами, такими как СК-42, ПЗ-90.11 и другими.

 Доступ к приложению
Фронтенд (Streamlit):
 https:https://aehdkkufsbkldqycrkjdkh.streamlit.app/

Бэкенд (FastAPI):
 https://zxc-4egb.onrender.com

 Организация проекта
.
├── backend/
│   └── main.py
├── frontend/
│   └── app.py
├── requirements.txt
└── README.md
Функционал
Импорт данных из Excel-файлов с координатами

Настройка параметров преобразования координат

Создание отчетов в формате markdown

Загрузка результатов преобразования и отчетов

Удобный веб-интерфейс на Streamlit

REST API, построенный на FastAPI

Руководство по установке
Локальная настройка
Скопируйте репозиторий:

bash
git clone <url-репозитория>
cd coordinate-transformation-system
Подготовьте виртуальное окружение и установите необходимые пакеты:

bash
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
pip install -r requirements.txt
Запустите сервер бэкенда:

bash
cd backend
uvicorn main:app --reload
Запустите фронтенд:

bash
cd frontend
streamlit run app.py
Публикация проекта
Бэкенд (Render.com)
Создайте новый Web Service на Render.com

Подключите репозиторий GitHub

Настройте параметры:

Команда сборки: pip install -r requirements.txt

Команда запуска: uvicorn backend.main:app --host 0.0.0.0 --port $PORT

Запустите сервис

Фронтенд (Streamlit Cloud)
Зарегистрируйтесь на Streamlit Cloud

Подключите репозиторий GitHub

Укажите настройки:

Основной файл: frontend/app.py

Версия Python: 3.9 и выше

Обновите BACKEND_URL в frontend/app.py, указав адрес вашего бэкенда

Опубликуйте приложение

Как пользоваться
Откройте Streamlit приложение в браузере

Загрузите Excel-файл с координатами (столбцы: x, y, z)

Настройте параметры преобразования

Нажмите "Преобразовать координаты"

Просмотрите и сохраните результаты
