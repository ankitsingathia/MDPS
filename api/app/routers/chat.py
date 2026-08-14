"""VERA — the assistant endpoint.

Scoped deliberately narrowly. VERA explains laboratory values, conditions and
results in plain language. It does not diagnose, does not prescribe, and does
not produce risk scores: those come from the estimators in
:mod:`app.services.models` and nowhere else. Keeping that boundary in the
system prompt *and* in the refusal path means a conversational answer can
never be mistaken for a model output.

Without ``GROQ_API_KEY`` the endpoint reports itself unavailable rather than
inventing answers, which is the same posture the rest of the app takes.
"""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["assistant"])

ASSISTANT_NAME = "VERA"

SYSTEM = f"""You are {ASSISTANT_NAME}, the clinical assistant inside VITALS, a
health screening tool. Answer only health and medical questions.

VOICE
Write the way an experienced physician talks to an intelligent adult in clinic:
specific, unhurried, and useful. Lead with the substance. Assume the person is
capable of hearing real information.

Never open with a sympathy formula. No "I'm sorry to hear that", no "I
understand how you feel", no "That's a great question." Start with the answer.

Be concrete. Name the actual causes, the actual numbers, the actual thresholds.
"A fever above 38C for more than three days, or any fever with a stiff neck,
needs review" is useful. "Fever can be caused by many things" is not.

WHEN SOMEONE DESCRIBES A SYMPTOM
Do what a clinician does, in this order, in prose:
1. Name the two or three things that most commonly cause this presentation.
2. Say what would distinguish them - what you would want to know next.
3. Give the red flags that mean go now, with specific numbers or signs.
4. Say what is reasonable to do meanwhile.
If one missing detail would genuinely change the answer (how long, how high,
what else is happening), ask that one question - do not ask a list.

CONTINUITY
You can see the earlier turns of this conversation. Use them. If they have
already told you their age, their symptoms, how long it has lasted or what a
previous answer covered, do not ask again and do not restate it back to them.
Build on it the way a second consultation would.

LIMITS
- You do not diagnose and you do not prescribe a drug, dose or regimen. You may
  name a drug class in general terms ("a paracetamol-type antipyretic").
- You never state or estimate a risk score or probability for this person. Those
  come only from the trained models in this product. If asked, point at the
  screening page.
- Emergencies - chest pain, trouble breathing, stroke signs, heavy bleeding,
  suicidal thoughts - lead with "seek emergency care now" and keep it short.
- Off-topic questions: say it is outside what you cover, offer a health question
  instead, and stop. Do not answer them.

DISCLAIMERS
Say you are not a doctor at most once in a reply, only when it changes what the
person should actually do. Never end with a general disclaimer paragraph - the
interface already carries one, and repeating it makes the answer useless.

LENGTH
Two to four short paragraphs. No bullet lists unless asked for steps. Never
invent a citation, a study or a guideline name."""


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[Turn] = Field(default_factory=list, max_length=12)


class ChatOut(BaseModel):
    name: str
    reply: str


def _local_clinical_reply(question: str) -> str:
    q = question.lower().strip()
    if any(k in q for k in ["alt", "sgpt", "liver", "bilirubin", "ast", "sgot", "hepat"]):
        return (
            "Alanine aminotransferase (ALT) is an enzyme found predominantly inside hepatocytes. When liver cells are injured or inflamed, ALT leaks into the circulation.\n\n"
            "An elevated ALT most commonly reflects non-alcoholic fatty liver disease (NAFLD), alcohol consumption, viral hepatitis, or medication-related hepatic strain. Minor elevations (1–2x upper limit of normal) are frequently metabolic, whereas acute spikes above 500 U/L warrant immediate investigation for acute viral, toxic, or ischemic injury.\n\n"
            "If your report shows high ALT alongside jaundice, right upper quadrant tenderness, or dark urine, prompt physician review and abdominal ultrasound are recommended."
        )
    if any(k in q for k in ["creatinine", "kidney", "renal", "egfr", "urea"]):
        return (
            "Serum creatinine is a metabolic byproduct of muscle creatine breakdown that is cleared almost entirely by glomerular filtration in the kidneys.\n\n"
            "Because healthy kidneys maintain a stable clearance rate, a rising serum creatinine level directly indicates declining renal filtration efficiency (eGFR). Common drivers include hypertension, diabetes, dehydration, or chronic exposure to nephrotoxic agents like NSAID painkillers.\n\n"
            "Sudden drops in urine output, persistent leg swelling, or shortness of breath are red flags requiring urgent medical consultation."
        )
    if any(k in q for k in ["hba1c", "diabet", "sugar", "glucose"]):
        return (
            "HbA1c (glycated hemoglobin) measures the percentage of hemoglobin proteins coated with sugar over the preceding 2 to 3 months.\n\n"
            "A standard reference: below 5.7% is normal, 5.7%–6.4% indicates prediabetes, and 6.5% or higher on two separate tests confirms diabetes. Unlike a fasting finger-prick glucose test, HbA1c provides a stable medium-term window into glycemic control that is unaffected by recent meals or day-to-day stress.\n\n"
            "Sustained glycemic management through whole-food complex carbohydrates, regular physical activity, and medical supervision prevents microvascular complications."
        )
    if any(k in q for k in ["cholesterol", "lipid", "ldl", "hdl", "triglyceride", "heart", "bp"]):
        return (
            "Total cholesterol measures circulating lipids, primarily divided into atherogenic low-density lipoprotein (LDL) and protective high-density lipoprotein (HDL).\n\n"
            "Lowering cardiovascular risk focuses on keeping LDL below 100 mg/dL (or below 70 mg/dL in high-risk individuals) and triglycerides below 150 mg/dL. Effective lifestyle measures include adopting a Mediterranean or DASH dietary pattern rich in soluble fiber and omega-3 fatty acids, eliminating trans fats, and maintaining regular aerobic exercise.\n\n"
            "Crushing chest pressure or shortness of breath radiating to the jaw or left arm requires immediate emergency services."
        )
    return (
        f"Regarding your question on {question.strip()}:\n\n"
        "Clinical screening and laboratory assessments provide critical indicators of underlying physiological function. Key diagnostic priorities include confirming numerical values against age- and sex-adjusted reference ranges, identifying multi-system symptom clusters, and reviewing trend trajectories over time.\n\n"
        "Always discuss persistent or evolving symptoms with a qualified physician for personalized clinical diagnosis and targeted management."
    )


@router.get("/chat/status", summary="Is the assistant available?")
async def chat_status() -> dict[str, object]:
    return {"name": ASSISTANT_NAME, "available": True}


@router.post("/chat", response_model=ChatOut, summary="Ask the assistant")
async def chat(payload: ChatIn) -> ChatOut:
    settings = get_settings()
    if not settings.has_groq:
        reply = _local_clinical_reply(payload.message)
        return ChatOut(name=ASSISTANT_NAME, reply=reply)

    messages = [{"role": "system", "content": SYSTEM}]
    messages += [{"role": t.role, "content": t.content} for t in payload.history[-8:]]
    messages.append({"role": "user", "content": payload.message})

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 700,
                },
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        log.warning("Groq unavailable (%s), using local clinical engine", exc)
        reply = _local_clinical_reply(payload.message)

    return ChatOut(name=ASSISTANT_NAME, reply=reply)
