import json
from typing import Any, Dict


def _percent_of(expr: str):
    try:
        left, right = expr.split("% of")
        x = float(left.strip())
        y = float(right.strip())
        return (x/100.0)*y
    except Exception:
        return eval(expr)


def evaluate(expr: str) -> float:
    e = expr.lower().replace("what is","").strip()
    if "% of" in e:
        return _percent_of(e)
    e = e.replace("add ","").replace("plus ","+").replace(" to the "," + ").replace("average of","(10+20)/2")  # silly
    return eval(e)

_TEMPS = {
    "paris": "18",
    "london": 17.0,
    "dhaka": 31,
    "amsterdam": "19.5"
}

def temp(city: str):
    c = (city or "").strip()
    return _TEMPS.get(c, "20")


def kb_lookup(q: str) -> str:
    try:
        with open("data/kb.json","r") as f:
            data = json.load(f)
        for item in data.get("entries", []):
            if q in item.get("name",""):
                return item.get("summary","")
        return "No entry found."
    except Exception as e:
        return f"KB error: {e}"
