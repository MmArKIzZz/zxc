from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import pandas as pd
import json
from sympy import symbols, Matrix, N, latex
from datetime import datetime
from io import BytesIO
import base64
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os


app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = Path(__file__).parent
PARAMETERS_PATH = BASE_DIR / "parameters.json"
if not PARAMETERS_PATH.exists():
    PARAMETERS_PATH = Path("backend/parameters.json")
    if not PARAMETERS_PATH.exists():
        raise RuntimeError(f"Не удалось найти файл parameters.json ни в корне, ни в {PARAMETERS_PATH}")

# ---------------------
# Функции для работы с координатами
# ---------------------

def load_parameters(path=PARAMETERS_PATH):
    """Загружает параметры из JSON"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Ошибка чтения параметров из {path}: {str(e)}")

def GSK_2011(sk1, sk2, parameters_path, df=None):
    if sk1 == "СК-95" and sk2 == "СК-42":
        df_temp = GSK_2011("СК-95", "ПЗ-90.11", parameters_path, df=df)
        df_result = GSK_2011("ПЗ-90.11", "СК-42", parameters_path, df=df_temp)
        return df_result

    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X Y Z')

    formula = (1 + m) * Matrix([[1, ωz, -ωy], [-ωz, 1, ωx], [ωy, -ωx, 1]]) @ Matrix([[X], [Y], [Z]]) + Matrix([[ΔX], [ΔY], [ΔZ]])

    with open(parameters_path, 'r', encoding='utf-8') as f:
        parameters = json.load(f)

    if sk1 not in parameters:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")

    param = parameters[sk1]
    elements_const = {
        ΔX: param["ΔX"],
        ΔY: param["ΔY"],
        ΔZ: param["ΔZ"],
        ωx: param["ωx"],
        ωy: param["ωy"],
        ωz: param["ωz"],
        m: param["m"] * 1e-6
    }

    if df is None:
        raise ValueError("Нужно передать DataFrame")

    transformed = []

    for _, row in df.iterrows():
        elements = {
            **elements_const,
            X: row["X"],
            Y: row["Y"],
            Z: row["Z"],
        }

        results_vector = formula.subs(elements).applyfunc(N)
        transformed.append([
            row["Name"],
            float(results_vector[0]),
            float(results_vector[1]),
            float(results_vector[2]),
        ])

    # Создание DataFrame с правильными колонками
    df_result = pd.DataFrame(transformed, columns=["Name", "X", "Y", "Z"])

    return df_result


def generate_report_md(df_before, sk1, sk2, parameters_path, md_path):
    ΔX, ΔY, ΔZ, ωx, ωy, ωz, m = symbols('ΔX ΔY ΔZ ωx ωy ωz m')
    X, Y, Z = symbols('X Y Z')
    general_formula = (1 + m) * Matrix([[1, ωz, -ωy], [-ωz, 1, ωx], [ωy, -ωx, 1]]) @ Matrix([[X], [Y], [Z]]) + Matrix(
        [[ΔX], [ΔY], [ΔZ]])

    with open(parameters_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
    p = params.get(sk1)
    if p is None:
        raise ValueError(f"Система {sk1} не найдена в {parameters_path}")

    # Конвертируем параметры в float для точного отображения
    subs_common = {
        ΔX: float(p["ΔX"]),
        ΔY: float(p["ΔY"]),
        ΔZ: float(p["ΔZ"]),
        ωx: float(p["ωx"]),
        ωy: float(p["ωy"]),
        ωz: float(p["ωz"]),
        m: float(p["m"]) * 1e-6
    }

    # Вычисляем преобразованные координаты
    rows = []
    for _, r in df_before.iterrows():
        subs = {**subs_common, X: float(r["X"]), Y: float(r["Y"]), Z: float(r["Z"])}
        rv = general_formula.subs(subs).applyfunc(N)
        rows.append({
            "Name": r["Name"],
            "X_new": float(rv[0]),
            "Y_new": float(rv[1]),
            "Z_new": float(rv[2])
        })
    df_after = pd.DataFrame(rows)

    # Генерация отчета
    with open(md_path, 'w', encoding='utf-8') as md:
        md.write("# Отчёт по преобразованию координат\n\n")
        md.write(f"**Исходная система координат:** {sk1}\n\n")
        md.write(f"**Целевая система координат:** {sk2}\n\n")
        md.write(f"**Дата преобразования:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        md.write("## 1. Общая формула преобразования\n\n")
        md.write("Общая формула преобразования координат между системами:\n\n")
        md.write(f"$$\n{latex(general_formula)}\n$$\n\n")

        md.write("## 2. Параметры преобразования\n\n")
        md.write("Использованные параметры преобразования:\n\n")
        md.write(f"- ΔX = {p['ΔX']} м\n")
        md.write(f"- ΔY = {p['ΔY']} м\n")
        md.write(f"- ΔZ = {p['ΔZ']} м\n")
        md.write(f"- ωx = {p['ωx']} рад\n")
        md.write(f"- ωy = {p['ωy']} рад\n")
        md.write(f"- ωz = {p['ωz']} рад\n")
        md.write(f"- m = {p['m']} ppm\n\n")

        md.write("## 3. Пример преобразования\n\n")
        first_row = df_before.iloc[0]
        md.write(f"Преобразование для точки **{first_row['Name']}**:\n\n")
        md.write(f"- Исходные координаты:\n")
        md.write(f"  - X = {first_row['X']} м\n")
        md.write(f"  - Y = {first_row['Y']} м\n")
        md.write(f"  - Z = {first_row['Z']} м\n\n")

        # Правильная подстановка значений в формулу
        subs_example = {
            X: first_row["X"],
            Y: first_row["Y"],
            Z: first_row["Z"],
            **subs_common
        }

        # Вычисляем каждую часть формулы отдельно для наглядности
        rotation_matrix = Matrix([
            [1, subs_example[ωz], -subs_example[ωy]],
            [-subs_example[ωz], 1, subs_example[ωx]],
            [subs_example[ωy], -subs_example[ωx], 1]
        ])

        scale_factor = (1 + subs_example[m])
        original_vector = Matrix([[subs_example[X]], [subs_example[Y]], [subs_example[Z]]])
        translation_vector = Matrix([[subs_example[ΔX]], [subs_example[ΔY]], [subs_example[ΔZ]]])

        # Формула с подставленными значениями
        formula_parts = [
            f"{scale_factor:.8f} × {latex(rotation_matrix)} × {latex(original_vector)} + {latex(translation_vector)}"
        ]

        md.write("- Формула с подставленными значениями:\n\n")
        for part in formula_parts:
            md.write(f"$$\n{part}\n$$\n\n")

        # Численный результат
        result = scale_factor * (rotation_matrix @ original_vector) + translation_vector
        md.write(f"- Численный результат:\n")
        md.write(f"  - X' = {float(result[0]):.6f} м\n")
        md.write(f"  - Y' = {float(result[1]):.6f} м\n")
        md.write(f"  - Z' = {float(result[2]):.6f} м\n\n")

        md.write("## 4. Таблица преобразованных координат\n\n")
        md.write("| Название точки | X (м) | Y (м) | Z (м) | X' (м) | Y' (м) | Z' (м) |\n")
        md.write("|----------------|-------|-------|-------|--------|--------|--------|\n")
        for _, (before, after) in enumerate(zip(df_before.itertuples(), df_after.itertuples())):
            md.write(f"| {before.Name} | {before.X:.6f} | {before.Y:.6f} | {before.Z:.6f} | "
                     f"{after.X_new:.6f} | {after.Y_new:.6f} | {after.Z_new:.6f} |\n")
        md.write("\n")

        md.write("## 5. Статистика преобразованных координат\n\n")
        stats = df_after[["X_new", "Y_new", "Z_new"]].describe().loc[["mean", "std", "min", "max"]]
        md.write("| Метрика | X' (м) | Y' (м) | Z' (м) |\n")
        md.write("|---------|--------|--------|--------|\n")
        for stat in stats.index:
            md.write(
                f"| {stat} | {stats.loc[stat, 'X_new']:.6f} | {stats.loc[stat, 'Y_new']:.6f} | {stats.loc[stat, 'Z_new']:.6f} |\n")

    return df_after

# ---------------------
# Маршруты FastAPI
# ---------------------
@app.get("/")
async def read_root():
    return {
        "API": "Coordinate Transformation Service",
        "status": "running",
        "parameters_file": str(PARAMETERS_PATH),
        "endpoints": {
            "systems": "/systems",
            "transform": "/transform",
            "health": "/health"
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервера"""
    try:
        # Проверяем доступность файла параметров
        params = load_parameters()
        if not isinstance(params, dict):
            raise ValueError("Parameters file is not valid JSON")

        return {
            "status": "healthy",
            "parameters_file": str(PARAMETERS_PATH),
            "parameters_systems": list(params.keys())[:3] + ["..."],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "parameters_path": str(PARAMETERS_PATH),
                "current_directory": str(Path.cwd())
            }
        )


@app.get("/systems")
async def get_systems():
    """Получение списка доступных систем координат"""
    try:
        params = load_parameters()
        return {
            "status": "success",
            "systems": list(params.keys()),
            "count": len(params)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "parameters_path": str(PARAMETERS_PATH)
            }
        )


@app.post("/transform")
async def transform_file(
        file: UploadFile = File(...),
        sk1: str = Query(..., description="Исходная система координат"),
        sk2: str = Query(..., description="Целевая система координат")
):
    """Преобразование координат между системами"""
    try:
        # Проверка входных параметров
        if not sk1 or not sk2:
            raise HTTPException(
                status_code=400,
                detail="Не указаны системы координат (sk1 и sk2 обязательны)"
            )

        # Чтение файла
        file_data = await file.read()
        df = pd.read_excel(BytesIO(file_data))

        # Проверка столбцов
        required_columns = ["Name", "X", "Y", "Z"]
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Неверный формат файла",
                    "required_columns": required_columns,
                    "actual_columns": list(df.columns)
                }
            )

        # Загрузка параметров
        params = load_parameters()

        # Проверка наличия систем координат
        if sk1 not in params:
            available = list(params.keys())
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Система координат '{sk1}' не найдена",
                    "available_systems": available
                }
            )
        if sk2 not in params:
            available = list(params.keys())
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Система координат '{sk2}' не найдена",
                    "available_systems": available
                }
            )

        # Преобразование
        df_transformed = GSK_2011(sk1, sk2, PARAMETERS_PATH, df=df)

        # Генерация отчета
        report_path = BASE_DIR / "report.md"
        generate_report_md(df, sk1, sk2, PARAMETERS_PATH, report_path)

        # Подготовка результата
        output = BytesIO()
        df_transformed.to_excel(output, index=False)
        output.seek(0)

        with open(report_path, "r", encoding="utf-8") as f:
            report_content = f.read()

        return {
            "status": "success",
            "systems": {
                "from": sk1,
                "to": sk2
            },
            "data": base64.b64encode(output.read()).decode(),
            "report": report_content,
            "transformed_points_count": len(df_transformed)
        }

    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Файл не содержит данных")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "type": type(e).__name__
            }
        )
