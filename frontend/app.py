import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64
from io import BytesIO

#BACKEND_URL = "https://qwerty-0ykp.onrender.com"
BACKEND_URL = "http://localhost:8000"  # Для локального тестирования

st.title("Система преобразования координат")
st.markdown("Загрузите Excel-файл с координатами x, y, z для преобразования.")

# Проверка доступности сервера
try:
    health_check = requests.get(f"{BACKEND_URL}/health")
    if health_check.status_code != 200:
        st.error("Сервер временно недоступен. Попробуйте позже.")
        st.stop()
except requests.exceptions.RequestException:
    st.error("Не удалось подключиться к серверу. Проверьте соединение.")
    st.stop()

# Получаем доступные системы
try:
    response = requests.get(f"{BACKEND_URL}/systems", timeout=10)
    if response.status_code == 200:
        systems = response.json().get("systems", [])
        if not systems:
            st.warning("Не получены системы координат от сервера. Используются значения по умолчанию.")
            systems = ["СК-42", "ПЗ-90.11"]
    else:
        st.warning(f"Ошибка получения систем координат: {response.status_code}. Используются значения по умолчанию.")
        systems = ["СК-42", "ПЗ-90.11"]
except Exception as e:
    st.error(f"Ошибка подключения: {str(e)}. Используются значения по умолчанию.")
    systems = ["СК-42", "ПЗ-90.11"]
    st.stop()

col1, col2 = st.columns(2)
with col1:
    initial_system = st.selectbox("Выберите начальную систему", systems)
with col2:
    target_system = st.selectbox("Выберите конечную систему", systems)

# Загрузка файла
uploaded_file = st.file_uploader("Выберите Excel-файл", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Предпросмотр данных
        df = pd.read_excel(uploaded_file)
        st.write("Предпросмотр данных:")
        st.dataframe(df.head())

        if st.button("Начать преобразование"):
            with st.spinner("Выполняется преобразование..."):
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(),
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                }

                try:
                    response = requests.post(
                        f"{BACKEND_URL}/transform?sk1={initial_system}&sk2={target_system}",
                        files=files,
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            # Обработка успешного результата
                            excel_data = base64.b64decode(result["data"])
                            transformed_df = pd.read_excel(BytesIO(excel_data))

                            st.success("Преобразование завершено успешно!")
                            st.subheader("Результаты преобразования")
                            st.dataframe(transformed_df)

                            # Создаём временные файлы для скачивания
                            output_filename = f"transformed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            transformed_df.to_excel(output_filename, index=False)

                            report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                            with open(report_filename, "w", encoding="utf-8") as f:
                                f.write(result["report"])

                            # Кнопки скачивания
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(output_filename, "rb") as f:
                                    st.download_button(
                                        label="Скачать результаты (Excel)",
                                        data=f,
                                        file_name=output_filename,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            with col2:
                                with open(report_filename, "rb") as f:
                                    st.download_button(
                                        label="Скачать отчет (Markdown)",
                                        data=f,
                                        file_name=report_filename,
                                        mime="text/markdown"
                                    )
                        else:
                            st.error(f"Ошибка сервера: {result.get('message', 'Неизвестная ошибка')}")
                    else:
                        st.error(f"Ошибка сервера (код {response.status_code}): {response.text}")

                except requests.exceptions.Timeout:
                    st.error("Превышено время ожидания ответа от сервера")
                except requests.exceptions.RequestException as e:
                    st.error(f"Ошибка соединения с сервером: {str(e)}")
                except Exception as e:
                    st.error(f"Неожиданная ошибка: {str(e)}")

    except Exception as e:
        st.error(f"Ошибка обработки файла: {str(e)}")