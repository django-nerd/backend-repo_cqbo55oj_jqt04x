import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import create_document, get_documents, db
from schemas import QuickScan, AdviceReport, AdviceItem, Workflow, ContactRequest, Pitch

app = FastAPI(title="Flomote API", description="Slimmer werken met AI – QuickScan, workflows en contact")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Flomote Backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# -----------------
# QuickScan → Advice
# -----------------

class QuickScanRequest(QuickScan):
    pass

@app.post("/api/quickscan", response_model=AdviceReport)
def run_quickscan(payload: QuickScanRequest):
    # Store the quickscan submission
    try:
        create_document("quickscan", payload)
    except Exception as e:
        # Not fatal for returning advice, but surface info
        print("DB insert error:", e)

    recommendations: List[AdviceItem] = []

    sector = payload.sector.lower()
    employees = payload.employees
    challenges = [c.lower() for c in payload.challenges]

    def rec(category, title, impact, effort, description):
        recommendations.append(AdviceItem(
            category=category,
            title=title,
            impact=impact,
            effort=effort,
            description=description
        ))

    # Simple rules to tailor suggestions
    if "marketing" in challenges or sector in ["agency", "detailhandel", "retail", "horeca"]:
        rec("marketing", "Automatische social posts", "hoog", "laag",
            "Genereer en plan wekelijks social posts vanuit blog/nieuws met AI en een planner.")
        rec("marketing", "Nieuwsbrief generator", "middel", "laag",
            "Zet blog/updates om naar maandelijkse nieuwsbrief, inclusief onderwerpregels en A/B varianten.")

    if "klantenservice" in challenges or sector in ["dienstverlening", "saas", "webshop", "e-commerce"]:
        rec("klantenservice", "Website chatbot / FAQ bot", "hoog", "middel",
            "24/7 chatbot gevoed met je kennisbank en beleidsdocumenten voor snellere antwoorden.")
        rec("klantenservice", "Inbox triage met AI", "middel", "laag",
            "Automatisch categoriseren en samenvatten van binnenkomende mails, met voorgestelde antwoorden.")

    if employees >= 5 or "administratie" in challenges or sector in ["bouw", "zorg", "productie"]:
        rec("financien", "Factuurverwerking (OCR + boeking)", "hoog", "middel",
            "Herken facturen automatisch, extraheer bedragen en match met bestellingen/uren.")

    if "analyse" in challenges or sector in ["saas", "consultancy", "it"]:
        rec("analyse", "Rapportage samenvattingen", "middel", "laag",
            "Maak maandrapporten met belangrijkste KPI's, trends en aanbevelingen.")

    if not recommendations:
        rec("operations", "Proces intake workshop", "middel", "laag",
            "Korte sessie waarin we snel kansen voor automatisering in kaart brengen.")

    summary = "We hebben kansen geïdentificeerd om tijd te besparen en kwaliteit te verhogen met gerichte AI-workflows."

    return AdviceReport(summary=summary, recommendations=recommendations)

# -----------------
# Use cases (static examples served from DB if available)
# -----------------

@app.get("/api/use-cases")
def get_use_cases():
    examples = [
        {"category": "marketing", "title": "Social media calendar", "description": "Automatisch posts genereren en plannen."},
        {"category": "analyse", "title": "KPI samenvattingen", "description": "Wekelijkse inzichten en trends."},
        {"category": "klantenservice", "title": "FAQ chatbot", "description": "Snelle antwoorden met je eigen kennisbank."},
        {"category": "hr", "title": "Vacature screening", "description": "CV's scoren en samenvatten met AI."},
    ]
    try:
        docs = get_documents("workflow", {}, limit=50)
        for d in docs:
            examples.append({
                "category": d.get("category", "overig"),
                "title": d.get("title", "Workflow"),
                "description": d.get("description", "")
            })
    except Exception:
        pass
    return {"items": examples}

# -----------------
# Contact & Pitch mail generator
# -----------------

@app.post("/api/contact")
def create_contact(req: ContactRequest):
    try:
        create_document("contactrequest", req)
    except Exception as e:
        print("DB insert error:", e)
    return {"status": "ok", "message": "Dank voor je bericht! We nemen snel contact op."}

@app.post("/api/pitch")
def generate_pitch(req: Pitch):
    # Simple templated pitch based on inputs (no external LLM calls for now)
    salutation = f"Hoi {req.name}," if req.tone != "formeel" else f"Geachte {req.name},"
    company_line = f" bij {req.company}" if req.company else ""
    sector_line = f" in de {req.sector} sector" if req.sector else ""
    pains = ", ".join(req.pain_points) if req.pain_points else "terugkerende handmatige taken"

    body = (
        f"{salutation}\n\n"
        f"Ik help mkb-teams{company_line}{sector_line} slimmer werken met praktische AI-automatiseringen. "
        f"Op basis van wat ik zie, kunnen we direct waarde leveren door {pains} te automatiseren.\n\n"
        f"Een korte QuickScan laat zien welke workflows de meeste impact hebben (zoals social posts, nieuwsbrief, chatbot of factuurverwerking). "
        f"Binnen 2 weken staat de eerste workflow live.\n\n"
        f"Zullen we een kennismaking inplannen?\n\n"
        f"Groet,\nFlomote"
    )

    return {"subject": "Slimmer werken met AI – voorstel", "body": body}

# -----------------
# Simple dashboard data for chosen workflows
# -----------------

class WorkflowCreate(Workflow):
    pass

@app.get("/api/workflows")
def list_workflows():
    try:
        docs = get_documents("workflow", {}, limit=100)
        for d in docs:
            d["id"] = str(d.get("_id"))
        return {"items": docs}
    except Exception:
        # Fallback sample
        return {"items": [
            {"id": "1", "category": "marketing", "title": "Social posts", "status": "actief"},
            {"id": "2", "category": "klantenservice", "title": "FAQ chatbot", "status": "gepland"},
        ]}

@app.post("/api/workflows")
def create_workflow(payload: WorkflowCreate):
    try:
        _id = create_document("workflow", payload)
        return {"id": _id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
