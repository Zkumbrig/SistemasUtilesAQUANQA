import re

import pandas as pd


CECO_OMITTED_ACTIVITIES = (
    "cosecha",
    "lavado de jarras",
    "acopio",
    "estibador",
    "estibadores",
)
CECO_OMITTED_CODE_PREFIXES = (
    "MANTCAM-007-",
    "OPER-014-",
    "PODA-020-",
    "COSEC-008-",
    "FITO-016-",
    "FERT-003-",
    "OSM-015-",
)
CECO_EVALUATED_COL = (
    "Cecos Evaluados (sin actividades omitidas)"
)
CECO_EVALUATED_COUNT_COL = (
    "Cantidad Cecos Evaluados (sin actividades omitidas)"
)
ACTIVITY_CODE_PATTERN = re.compile(
    r"([A-Za-z]+(?:\s*CAM)?-\d{3}-L\d{3})",
    flags=re.IGNORECASE,
)


KEYWORDS = {
    "persona": ["nombre", "persona", "empleado", "trabajador", "name", "employee"],
    "documento": [
        "documento",
        "doc",
        "dni",
        "cedula",
        "cédula",
        "identificacion",
        "identificación",
        "ruc",
        "nro doc",
    ],
    "fecha": ["fecha", "date", "dia", "día", "day"],
    "ceco": ["ceco", "centro de costo", "centro costo", "cost center"],
    "actividad": ["actividad", "labor", "trabajo", "task"],
    "cod_actividad": [
        "cod actividad",
        "cod. actividad",
        "codigo actividad",
        "código actividad",
        "activity code",
    ],
}


def _normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "nat", "none"}:
        return ""
    return text


def _is_omitted_activity_for_ceco(value: str) -> bool:
    normalized = " ".join(value.lower().split())
    return any(term in normalized for term in CECO_OMITTED_ACTIVITIES)


def _normalize_activity_code(value: str) -> str:
    return value.upper().replace(" ", "").strip()


def _extract_activity_code(value) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    match = ACTIVITY_CODE_PATTERN.search(text)
    if not match:
        return ""
    return _normalize_activity_code(match.group(1))


def _is_omitted_code_for_ceco(value: str) -> bool:
    if not value:
        return False
    normalized = _normalize_activity_code(value)
    return any(normalized.startswith(prefix) for prefix in CECO_OMITTED_CODE_PREFIXES)


def _infer_activity_code_column(
    df: pd.DataFrame,
    excluded_cols: set[str],
    min_score: float = 0.45,
) -> str | None:
    best_col = None
    best_score = 0.0
    for col in df.columns:
        if col in excluded_cols:
            continue
        sample = df[col].dropna().astype(str).head(500)
        if sample.empty:
            continue
        extracted = sample.apply(_extract_activity_code)
        score = float((extracted != "").mean())
        if score > best_score:
            best_col = col
            best_score = score
    if best_col and best_score >= min_score:
        return best_col
    return None


def _activity_signature(activity: str, code: str) -> str:
    if activity and code:
        return f"{activity} ({code})"
    if activity:
        return activity
    if code:
        return f"(Sin actividad) ({code})"
    return ""


def _detect_column(df: pd.DataFrame, keywords: list[str], fallback: str | None = None) -> str | None:
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in keywords):
            return col
    return fallback


def suggest_columns(df: pd.DataFrame) -> dict[str, str | None]:
    if len(df.columns) == 0:
        return {"persona": None, "documento": None, "fecha": None, "ceco": None, "actividad": None}

    person_fallback = df.columns[0]
    return {
        "persona": _detect_column(df, KEYWORDS["persona"], fallback=person_fallback),
        "documento": _detect_column(df, KEYWORDS["documento"], fallback=None),
        "fecha": _detect_column(df, KEYWORDS["fecha"], fallback=None),
        "ceco": _detect_column(df, KEYWORDS["ceco"], fallback=None),
        "actividad": _detect_column(df, KEYWORDS["actividad"], fallback=None),
        "cod_actividad": _detect_column(df, KEYWORDS["cod_actividad"], fallback=None),
    }


def normalize_dates(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce", dayfirst=True)
    normalized = dt.dt.strftime("%Y-%m-%d")
    invalid_mask = normalized.isna() | (normalized == "NaT")
    if invalid_mask.any():
        normalized.loc[invalid_mask] = (
            series.loc[invalid_mask].astype(str).str.strip().str[:10]
        )
    normalized = normalized.fillna("").replace({"NaT": "", "nan": "", "None": ""})
    return normalized


def detect_file_dates(df: pd.DataFrame, date_col: str | None) -> list[str]:
    if not date_col or date_col not in df.columns:
        return []
    normalized_dates = normalize_dates(df[date_col]).apply(_normalize_text)
    return sorted({value for value in normalized_dates.tolist() if value})


def _require_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"No se encontraron columnas requeridas: {', '.join(missing)}")


def validate_people_ceco_activity(
    df: pd.DataFrame,
    person_col: str,
    ceco_col: str,
    activity_col: str,
    date_col: str | None = None,
    document_col: str | None = None,
    activity_code_col: str | None = None,
) -> pd.DataFrame:
    _require_columns(df, [person_col, ceco_col, activity_col])
    stats_rows = []
    excluded_cols = {person_col, ceco_col, activity_col}
    effective_activity_code_col = (
        activity_code_col if activity_code_col and activity_code_col in df.columns else None
    )
    if not effective_activity_code_col:
        effective_activity_code_col = _infer_activity_code_column(df, excluded_cols)

    for person_value, person_df in df.groupby(person_col, dropna=False):
        person_name = _normalize_text(person_value) or "(Sin nombre)"
        cecos = person_df[ceco_col].apply(_normalize_text)
        activities = person_df[activity_col].apply(_normalize_text)
        if effective_activity_code_col and effective_activity_code_col in person_df.columns:
            activity_codes = person_df[effective_activity_code_col].apply(_extract_activity_code)
        else:
            activity_codes = person_df[activity_col].apply(_extract_activity_code)

        unique_cecos = sorted({value for value in cecos.tolist() if value})
        omit_by_name = activities.apply(_is_omitted_activity_for_ceco)
        omit_by_code = activity_codes.apply(_is_omitted_code_for_ceco)
        include_ceco_mask = ~(omit_by_name | omit_by_code)
        cecos_for_validation = cecos[include_ceco_mask]
        unique_cecos_for_validation = sorted(
            {value for value in cecos_for_validation.tolist() if value}
        )
        activity_signatures = sorted(
            {
                _activity_signature(activity, code)
                for activity, code in zip(activities.tolist(), activity_codes.tolist())
                if _activity_signature(activity, code)
            }
        )
        unique_activities = sorted({value for value in activities.tolist() if value})
        omitted_rows_for_ceco = int((~include_ceco_mask).sum())

        missing_ceco_count = int((cecos == "").sum())
        missing_activity_count = int((activities == "").sum())

        has_multiple_cecos = len(unique_cecos_for_validation) > 1
        has_multiple_activities = (
            len(activity_signatures) > 1
            if effective_activity_code_col
            else len(unique_activities) > 1
        )
        has_empty_ceco = missing_ceco_count > 0
        has_empty_activity = missing_activity_count > 0

        person_dates = []
        has_multiple_dates_person = False
        if date_col and date_col in person_df.columns:
            person_dates = sorted(
                {
                    value
                    for value in normalize_dates(person_df[date_col]).apply(_normalize_text).tolist()
                    if value
                }
            )
            has_multiple_dates_person = len(person_dates) > 1

        observations = []
        if has_multiple_cecos:
            observations.append("Tiene mas de un CECO")
        if has_multiple_activities:
            observations.append("Tiene mas de una Actividad")
        if has_empty_ceco:
            observations.append("Tiene CECO vacio")
        if has_empty_activity:
            observations.append("Tiene Actividad vacia")
        if has_multiple_dates_person:
            observations.append("Tiene mas de una fecha en el archivo")
        if omitted_rows_for_ceco > 0:
            observations.append(
                "Se omitieron actividades para validar CECO "
                "(Cosecha/Lavado de Jarras/Acopio/Estibadores y Cod. Actividad omitido)"
            )

        # Por ahora solo consideramos CECO y vacios como problema (actividades diferentes se mapeara luego).
        has_issues = has_multiple_cecos or has_empty_ceco or has_empty_activity

        document_value = "N/A"
        if document_col and document_col in person_df.columns:
            document_value = _normalize_text(person_df[document_col].iloc[0]) or "N/A"

        stats_rows.append(
            {
                "Persona": person_name,
                "Documento": document_value,
                "Filas Persona": int(len(person_df)),
                "Cecos Unicos": ", ".join(unique_cecos) if unique_cecos else "Ninguno",
                CECO_EVALUATED_COL: ", ".join(
                    unique_cecos_for_validation
                )
                if unique_cecos_for_validation
                else "Ninguno",
                "Filas Omitidas CECO": omitted_rows_for_ceco,
                "Cantidad Cecos Unicos": int(len(unique_cecos)),
                CECO_EVALUATED_COUNT_COL: int(
                    len(unique_cecos_for_validation)
                ),
                "Cecos Diferentes": has_multiple_cecos,
                "Ceco Vacio (filas)": missing_ceco_count,
                "Tiene Ceco Vacio": has_empty_ceco,
                "Actividades Unicas": ", ".join(unique_activities) if unique_activities else "Ninguna",
                "Actividades (con Cod. Actividad)": ", ".join(activity_signatures) if activity_signatures else "Ninguna",
                "Cantidad Actividades Unicas": int(len(unique_activities)),
                "Cantidad Actividades (con Cod. Actividad)": int(len(activity_signatures)),
                "Actividades Diferentes": has_multiple_activities,
                "Actividad Vacia (filas)": missing_activity_count,
                "Tiene Actividad Vacia": has_empty_activity,
                "Fechas Persona": ", ".join(person_dates) if person_dates else "Sin fecha",
                "Tiene Multiples Fechas Persona": has_multiple_dates_person,
                "Observaciones": " | ".join(observations) if observations else "OK",
                "Tiene Problemas": has_issues,
            }
        )

    if not stats_rows:
        return pd.DataFrame(
            columns=[
                "Persona",
                "Documento",
                "Filas Persona",
                "Cecos Unicos",
                CECO_EVALUATED_COL,
                "Filas Omitidas CECO",
                "Cantidad Cecos Unicos",
                CECO_EVALUATED_COUNT_COL,
                "Cecos Diferentes",
                "Ceco Vacio (filas)",
                "Tiene Ceco Vacio",
                "Actividades Unicas",
                "Actividades (con Cod. Actividad)",
                "Cantidad Actividades Unicas",
                "Cantidad Actividades (con Cod. Actividad)",
                "Actividades Diferentes",
                "Actividad Vacia (filas)",
                "Tiene Actividad Vacia",
                "Fechas Persona",
                "Tiene Multiples Fechas Persona",
                "Observaciones",
                "Tiene Problemas",
            ]
        )

    stats_df = pd.DataFrame(stats_rows)
    stats_df = stats_df.sort_values(
        by=["Tiene Problemas", "Persona"], ascending=[False, True]
    ).reset_index(drop=True)
    return stats_df


def summarize_validation(stats_df: pd.DataFrame, file_dates: list[str]) -> dict[str, int]:
    if stats_df.empty:
        return {
            "total_personas": 0,
            "con_problemas": 0,
            "cecos_diferentes": 0,
            "actividades_diferentes": 0,
            "con_vacios": 0,
            "fechas_archivo": len(file_dates),
        }

    empty_any_mask = stats_df["Tiene Ceco Vacio"] | stats_df["Tiene Actividad Vacia"]
    return {
        "total_personas": int(len(stats_df)),
        "con_problemas": int(stats_df["Tiene Problemas"].sum()),
        "cecos_diferentes": int(stats_df["Cecos Diferentes"].sum()),
        "actividades_diferentes": int(stats_df["Actividades Diferentes"].sum()),
        "con_vacios": int(empty_any_mask.sum()),
        "fechas_archivo": len(file_dates),
    }
