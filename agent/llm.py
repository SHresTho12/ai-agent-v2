import json, random

def call_llm(prompt: str):
    """
    A fake LLM that *sometimes* returns a tool plan as a dict,
    sometimes malformed JSON, and sometimes a direct answer.
    """
    
    p = prompt.lower()
    roll = random.random()

    if roll < 0.35:
        if "weather" in p or "temperature" in p:
            city = "paris" if "paris" in p else ("london" if "london" in p else "dhaka")
            return {"tool":"weather","args":{"city":city}}
        if "%" in p or "add" in p or any(op in p for op in ["+","-","*","/"]):
            return {"tool":"calc","args":{"expr":prompt}}
        if "who is" in p:
            name = prompt.split("who is",1)[1].strip().rstrip("?")
            return {"tool":"kb","args":{"q":name}}
        return {"tool":"weaher","args":{"cty":"paris"}}

    if roll < 0.60:
        return '{"tool": "weather", "args": {"city": "Pa ris" }'

    if roll < 0.80:
        return 'TOOL:calc EXPR="12.5% of 243"'

    if "ada lovelace" in p:
        return "Ada Lovelace was a 19th-century mathematician and early computing pioneer."
    return "I think you are asking about: " + prompt[:60]
