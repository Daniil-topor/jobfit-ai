from __future__ import annotations

import json
from dataclasses import asdict

from .models import MatchReport, RequirementMatch


SYSTEM_PROMPT = """Ты анализируешь соответствие кандидата вакансии.
Опирайся только на факты из резюме и вакансии. Не приписывай кандидату опыт или навыки.
Верни только JSON с полями: score (0-100), matched_skills, missing_skills,
requirements (requirement, status, evidence), schedule_risks, unsupported_claims, cover_letter.
Статус требования: match, partial, gap или unknown. Сопроводительное письмо — до 1200 знаков.
"""


def _json_payload(resume: str, vacancy: str, draft: str) -> str:
    return json.dumps(
        {"resume": resume, "vacancy": vacancy, "draft_to_check": draft},
        ensure_ascii=False,
    )


def analyze_with_openai(
    resume: str,
    vacancy: str,
    draft: str,
    api_key: str,
    model: str = "gpt-5.5",
) -> MatchReport:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Установите зависимости: pip install -r requirements.txt") from exc

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=_json_payload(resume, vacancy, draft),
        text={"format": {"type": "json_object"}},
    )
    data = json.loads(response.output_text)
    requirements = [RequirementMatch(**item) for item in data.get("requirements", [])]
    return MatchReport(
        score=int(data.get("score", 0)),
        matched_skills=list(data.get("matched_skills", [])),
        missing_skills=list(data.get("missing_skills", [])),
        requirements=requirements,
        schedule_risks=list(data.get("schedule_risks", [])),
        unsupported_claims=list(data.get("unsupported_claims", [])),
        cover_letter=str(data.get("cover_letter", "")),
    )


def report_as_dict(report: MatchReport) -> dict:
    return asdict(report)

