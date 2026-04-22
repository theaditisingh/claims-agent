import json
import re
import os
from typing import Any
from groq import Groq

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError(
        "GROQ_API_KEY is not set.\n"
    )

client = Groq(api_key=api_key)

MANDATORY_FIELDS = [
    "policy_number",
    "policyholder_name",
    "effective_dates",
    "incident_date",
    "incident_time",
    "incident_location",
    "incident_description",
    "claimant_name",
    "claimant_contact",
    "asset_type",
    "asset_id",
    "estimated_damage",
    "claim_type",
    "initial_estimate",
]

FRAUD_KEYWORDS = ["fraud", "inconsistent", "staged", "fabricated", "suspicious", "fake"]

FAST_TRACK_LIMIT = 25000

PROMPT = """You are an insurance claims analyst. Extract all fields from the FNOL document below.

Return ONLY valid JSON, no explanation, no markdown, no backticks.

Fields to extract (set null if not found):
{
  "policy_number": null,
  "policyholder_name": null,
  "effective_dates": null,
  "incident_date": null,
  "incident_time": null,
  "incident_location": null,
  "incident_description": null,
  "claimant_name": null,
  "claimant_contact": null,
  "third_parties": null,
  "asset_type": null,
  "asset_id": null,
  "estimated_damage": null,
  "claim_type": null,
  "attachments": null,
  "initial_estimate": null,
  "police_report_number": null,
  "driver_name": null,
  "vehicle_make": null,
  "vehicle_model": null,
  "vehicle_year": null,
  "vehicle_vin": null,
  "plate_number": null
}

Notes:
- estimated_damage and initial_estimate should be plain numbers, no currency symbols
- claim_type is usually: auto, property, injury, liability, or theft
- Keep date formats exactly as they appear in the document

DOCUMENT:
"""


def process_claim(text, filename="unknown"):
    print(f"\nProcessing: {filename}")

    fields = extract_fields(text)
    print(f"Fields extracted: {sum(1 for v in fields.values() if v is not None)}")

    missing = get_missing_fields(fields)
    print(f"Missing: {missing if missing else 'none'}")

    route, reason = decide_route(fields, missing)
    print(f"Route: {route}")

    return {
        "filename": filename,
        "extractedFields": fields,
        "missingFields": missing,
        "recommendedRoute": route,
        "reasoning": reason,
    }


def extract_fields(text):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You extract insurance claim data and return only valid JSON. No extra text."
            },
            {
                "role": "user",
                "content": PROMPT + text
            }
        ],
        temperature=0,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        print("Could not parse JSON from model response.")
        return {f: None for f in MANDATORY_FIELDS}


def get_missing_fields(fields):
    missing = []
    for field in MANDATORY_FIELDS:
        val = fields.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing.append(field)
    return missing


def decide_route(fields, missing):
    description = (fields.get("incident_description") or "").lower()
    claim_type = (fields.get("claim_type") or "").lower().strip()

    flagged = [kw for kw in FRAUD_KEYWORDS if kw in description]
    if flagged:
        return (
            "Investigation Flag",
            f"Possible fraud detected. Keywords found: {', '.join(flagged)}."
        )

    if "injur" in claim_type:
        return (
            "Specialist Queue",
            "Injury claim detected. Sending to specialist queue for medical review."
        )

    if missing:
        return (
            "Manual Review",
            f"The following mandatory fields are missing: {', '.join(missing)}."
        )

    damage = parse_number(fields.get("estimated_damage"))
    if damage is not None and damage < FAST_TRACK_LIMIT:
        return (
            "Fast-track",
            f"Damage amount Rs.{damage:,.0f} is under the Rs.{FAST_TRACK_LIMIT:,} limit. All fields present. Approved for fast-track."
        )

    if damage is not None:
        return (
            "Manual Review",
            f"Damage amount Rs.{damage:,.0f} exceeds Rs.{FAST_TRACK_LIMIT:,}. Needs manual review."
        )

    return (
        "Manual Review",
        "Could not read damage amount. Sending for manual review."
    )


def parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None