from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()

# ✅ Enable CORS (fixes "Failed to fetch" error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can replace * with your domain later (e.g. "https://ritupw112.github.io")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE = "https://api.penpencil.co/qbg/questions/"
HEADERS = {
    "authorization": "Bearer ff670300e8974ed8a8c2ef8f03da7243df5b3f3627723a8a5eaf645c1266c815",
    "user-id": "656709bd475f940018db9bec",
    "organization-id": "5eb393ee95fab7468a79d189",
    "client-type": "QBG",
    "user": "Qbg sub admin",
    "user-name": "Ritu Bhardwaj",
    "roleid": "64cb9aad976ffe2d94ed0e4f",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
}

TYPE_MAP = {
    1: "Single Choice (SCQ)",
    2: "Multi Choice (MCQ)",
    3: "Numerical",
    4: "True or False (TF)",
    5: "Subjective (SUB)",
    6: "Fill in Blanks (FIB)",
    7: "Assertion Reason (AR)",
    8: "Comprehension (COMP)",
    9: "Matching List (ML)"
}

MAX_WORKERS = 10

# ✅ --- Function 1: Check bilingual answer key match
def check_bilingual(qid):
    try:
        resp = requests.get(f"{API_BASE}{qid}", headers=HEADERS)
        if resp.status_code != 200:
            return {"id": qid, "status": "Failed"}
        data = resp.json().get("data", {})
        bi = data.get("bilingual_options", {})
        eng, hin = bi.get("english", []), bi.get("hindi", [])
        if not eng or not hin or len(eng) != len(hin):
            return {"id": qid, "status": "Not Matched"}
        for e, h in zip(eng, hin):
            if e.get("isCorrect") != h.get("isCorrect"):
                return {"id": qid, "status": "Not Matched"}
        return {"id": qid, "status": "Success"}
    except:
        return {"id": qid, "status": "Error"}

# ✅ --- Function 2: Check for 5th option
def check_option_e(qid):
    try:
        resp = requests.get(f"{API_BASE}{qid}", headers=HEADERS)
        if resp.status_code != 200:
            return {"id": qid, "has_option_e": False}
        data = resp.json().get("data", {})
        if "option_e" in (data.get("option") or {}):
            return {"id": qid, "has_option_e": True}
        opts = data.get("bilingual_options", {}).get("english", [])
        return {"id": qid, "has_option_e": len(opts) >= 5}
    except:
        return {"id": qid, "has_option_e": False}

# ✅ --- Function 3: Check question type
def get_type(qid):
    try:
        resp = requests.get(f"{API_BASE}{qid}", headers=HEADERS)
        if resp.status_code != 200:
            return {"id": qid, "type": "Failed"}
        data = resp.json().get("data", {})
        t = data.get("type")
        return {"id": qid, "type": TYPE_MAP.get(t, f"Unknown ({t})")}
    except:
        return {"id": qid, "type": "Error"}

@app.get("/answerkey")
def answer_key(ids: str):
    ids_list = [i.strip() for i in ids.split(",") if i.strip()]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(ex.map(check_bilingual, ids_list))
    return results

@app.get("/optione")
def option_e(ids: str):
    ids_list = [i.strip() for i in ids.split(",") if i.strip()]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(ex.map(check_option_e, ids_list))
    return results

@app.get("/qtype")
def qtype(ids: str):
    ids_list = [i.strip() for i in ids.split(",") if i.strip()]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(ex.map(get_type, ids_list))
    return results
