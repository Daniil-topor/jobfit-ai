from __future__ import annotations

import json

import streamlit as st

from jobfit.ai_client import analyze_with_openai, report_as_dict
from jobfit.analyzer import analyze_match
from jobfit.sample_data import SAMPLE_RESUME, SAMPLE_VACANCY


st.set_page_config(page_title="JobFit AI", page_icon="🎯", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 2rem;}
    [data-testid="stMetric"] {
        background: color-mix(in srgb, var(--secondary-background-color) 86%, transparent);
        border: 1px solid color-mix(in srgb, var(--text-color) 14%, transparent);
        border-radius: 14px;
        padding: 16px;
    }
    [data-testid="stMetric"] * {color: var(--text-color) !important;}
    .skill-chip {
        display: inline-block;
        padding: 6px 10px;
        margin: 0 6px 8px 0;
        border-radius: 999px;
        background: color-mix(in srgb, var(--primary-color) 16%, transparent);
        border: 1px solid color-mix(in srgb, var(--primary-color) 35%, transparent);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "resume_input" not in st.session_state:
    st.session_state.resume_input = ""
if "vacancy_input" not in st.session_state:
    st.session_state.vacancy_input = ""

st.title("🎯 JobFit AI")
st.caption("Сопоставляет резюме с вакансией и не позволяет сопроводительному письму выдумывать опыт.")

with st.sidebar:
    st.header("Режим анализа")
    mode = st.radio("Выберите режим", ["Демо без API", "OpenAI API"])
    api_key = ""
    model = "gpt-5.5"
    if mode == "OpenAI API":
        api_key = st.text_input("OPENAI_API_KEY", type="password")
        model = st.text_input("Модель", value=model)
        st.caption("Ключ используется только для текущего запроса и не сохраняется приложением.")
    if st.button("Загрузить пример", use_container_width=True):
        st.session_state.resume_input = SAMPLE_RESUME
        st.session_state.vacancy_input = SAMPLE_VACANCY
        st.session_state.pop("report", None)

left, right = st.columns(2)
with left:
    resume = st.text_area(
        "Резюме",
        key="resume_input",
        height=300,
        placeholder="Вставьте текст резюме...",
    )
with right:
    vacancy = st.text_area(
        "Вакансия",
        key="vacancy_input",
        height=300,
        placeholder="Вставьте описание вакансии...",
    )

draft = st.text_area(
    "Черновик сопроводительного письма для проверки (необязательно)",
    height=140,
)

if st.button("Проанализировать", type="primary", use_container_width=True):
    if not resume.strip() or not vacancy.strip():
        st.error("Добавьте текст резюме и вакансии.")
        st.stop()

    try:
        if mode == "OpenAI API":
            if not api_key:
                st.error("Введите API-ключ или выберите демо-режим.")
                st.stop()
            report = analyze_with_openai(resume, vacancy, draft, api_key, model)
        else:
            report = analyze_match(resume, vacancy, draft)
    except Exception as exc:
        st.error(f"Не удалось выполнить анализ: {exc}")
        st.stop()

    st.session_state.report = report

report = st.session_state.get("report")
if report:
    def skill_chips(items: list[str], empty_text: str) -> None:
        if not items:
            st.caption(empty_text)
            return
        chips = "".join(f'<span class="skill-chip">{item}</span>' for item in items)
        st.markdown(chips, unsafe_allow_html=True)

    st.divider()
    score_col, match_col, gap_col = st.columns(3)
    score_col.metric("Соответствие", f"{report.score}%")
    match_col.metric("Совпавшие навыки", len(report.matched_skills))
    gap_col.metric("Пробелы", len(report.missing_skills))
    st.progress(report.score / 100)

    overview, requirements, letter, export = st.tabs(
        ["Обзор", "Требования", "Письмо", "Экспорт"]
    )
    with overview:
        a, b = st.columns(2)
        with a:
            st.subheader("Подтверждено")
            skill_chips(report.matched_skills, "Совпадений пока не найдено")
        with b:
            st.subheader("Нужно подтвердить или изучить")
            skill_chips(report.missing_skills, "Явных пробелов не найдено")
        if report.schedule_risks:
            st.warning("\n".join(report.schedule_risks))
        if report.unsupported_claims:
            st.error(
                "В письме появились навыки, которых нет в резюме: "
                + ", ".join(report.unsupported_claims)
            )

    with requirements:
        for item in report.requirements:
            icons = {"match": "✅", "partial": "🟡", "gap": "❌", "unknown": "⚪"}
            st.markdown(f"{icons.get(item.status, '⚪')} **{item.requirement}**")
            if item.evidence:
                st.caption(f"Основание: {item.evidence}")

    with letter:
        st.text_area("Черновик", value=report.cover_letter, height=260)
        st.caption("Проверьте факты перед отправкой работодателю.")

    with export:
        payload = json.dumps(report_as_dict(report), ensure_ascii=False, indent=2)
        st.download_button(
            "Скачать JSON",
            data=payload,
            file_name="jobfit-report.json",
            mime="application/json",
        )
        st.code(payload, language="json")

