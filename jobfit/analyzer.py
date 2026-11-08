from __future__ import annotations

import re
from collections.abc import Iterable

from .models import MatchReport, RequirementMatch


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "C++": ("c++", "cpp"),
    "MATLAB": ("matlab",),
    "AutoCAD": ("autocad", "автокад"),
    "SolidWorks": ("solidworks", "solid works"),
    "Excel": ("excel", "эксель"),
    "PowerPoint": ("powerpoint", "презентац"),
    "SQL": ("sql",),
    "Git": ("git", "github"),
    "API": ("api", "апи"),
    "ROS 2": ("ros 2", "ros2"),
    "Linux": ("linux",),
    "AI-инструменты": ("codex", "chatgpt", "claude", "ии-инструмент", "ai-инструмент"),
    "Проектный менеджмент": ("project management", "проектн", "agile", "управлени"),
    "Техническая документация": ("техническ", "документац", "тз"),
    "Анализ данных": ("анализ данных", "обработка данных", "аналитик"),
}

REQUIREMENT_MARKERS = (
    "требован",
    "важно",
    "ожидаем",
    "нужно",
    "необходимо",
    "must",
    "required",
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


def _sentences(text: str) -> list[str]:
    chunks = re.split(r"(?:\r?\n)+|(?<=[.!?;])\s+", text)
    return [re.sub(r"^[\s•—\-*\d.)]+", "", item).strip() for item in chunks if item.strip()]


def _detect_skills(text: str) -> set[str]:
    normalized = _normalize(text)
    return {
        canonical
        for canonical, aliases in SKILL_ALIASES.items()
        if any(alias in normalized for alias in aliases)
    }


def _extract_requirements(vacancy: str) -> list[str]:
    sentences = _sentences(vacancy)
    selected = [
        sentence
        for sentence in sentences
        if any(marker in _normalize(sentence) for marker in REQUIREMENT_MARKERS)
        or any(alias in _normalize(sentence) for aliases in SKILL_ALIASES.values() for alias in aliases)
    ]
    if not selected:
        selected = sentences[:8]
    return selected[:12]


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    normalized = _normalize(text)
    return any(_normalize(needle) in normalized for needle in needles)


def _schedule_risks(resume: str, vacancy: str) -> list[str]:
    vacancy_n = _normalize(vacancy)
    resume_n = _normalize(resume)
    risks: list[str] = []

    full_time = _contains_any(vacancy_n, ("полная занятость", "40 часов", "5/2", "полный день"))
    part_time = _contains_any(resume_n, ("20 часов", "частичная занятость", "неполный день"))
    if full_time and part_time:
        risks.append("В вакансии указан полный график, а кандидат ищет частичную занятость.")

    onsite = _contains_any(vacancy_n, ("на месте работодателя", "только офис", "работа в офисе"))
    remote_only = _contains_any(resume_n, ("только удаленно", "только дистанционно"))
    if onsite and remote_only:
        risks.append("Вакансия требует присутствия в офисе, а кандидат указал только удаленную работу.")

    return risks


def _unsupported_claims(resume: str, draft: str) -> list[str]:
    resume_skills = _detect_skills(resume)
    draft_skills = _detect_skills(draft)
    return sorted(draft_skills - resume_skills)


def _cover_letter(resume: str, vacancy: str, matched: list[str]) -> str:
    vacancy_sentences = _sentences(vacancy)
    role = vacancy_sentences[0].rstrip(".!?;: ") if vacancy_sentences else "вакансия"
    evidence = ", ".join(matched[:5]) if matched else "техническое образование и учебные проекты"
    return (
        "Здравствуйте!\n\n"
        f"Меня заинтересовала позиция «{role[:120]}». "
        f"Мой релевантный опыт и навыки: {evidence}. "
        "Умею структурировать техническую информацию, проверять результаты по исходным данным "
        "и доводить учебные и исследовательские задачи до понятного результата.\n\n"
        "Буду рад выполнить тестовое задание и подробнее рассказать о проектах на собеседовании."
    )


def analyze_match(resume: str, vacancy: str, draft: str = "") -> MatchReport:
    resume_skills = _detect_skills(resume)
    vacancy_skills = _detect_skills(vacancy)
    matched = sorted(resume_skills & vacancy_skills)
    missing = sorted(vacancy_skills - resume_skills)

    requirements: list[RequirementMatch] = []
    resume_n = _normalize(resume)
    for requirement in _extract_requirements(vacancy):
        req_skills = _detect_skills(requirement)
        evidence_skills = sorted(req_skills & resume_skills)
        if evidence_skills:
            requirements.append(
                RequirementMatch(requirement, "match", ", ".join(evidence_skills))
            )
        elif req_skills:
            requirements.append(RequirementMatch(requirement, "gap"))
        else:
            key_words = [word for word in re.findall(r"[a-zа-я0-9+]{5,}", _normalize(requirement))]
            overlap = [word for word in key_words if word in resume_n]
            requirements.append(
                RequirementMatch(requirement, "partial" if overlap else "unknown", ", ".join(overlap[:4]))
            )

    denominator = max(len(vacancy_skills), 1)
    score = round(100 * len(matched) / denominator)
    risks = _schedule_risks(resume, vacancy)
    score = max(0, score - 15 * len(risks))

    return MatchReport(
        score=score,
        matched_skills=matched,
        missing_skills=missing,
        requirements=requirements,
        schedule_risks=risks,
        unsupported_claims=_unsupported_claims(resume, draft) if draft else [],
        cover_letter=_cover_letter(resume, vacancy, matched),
    )

