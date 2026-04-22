# Insurance Claims Processing Agent

This project automates the processing of FNOL (First Notice of Loss) documents.
It reads a claim document, pulls out the important fields, checks for anything missing,
and decides which queue the claim should go to.

## What it does

1. Reads a PDF or TXT claim document
2. Uses an AI model (Groq / Llama3) to extract structured data from it
3. Checks if any required fields are missing
4. Applies routing rules to send the claim to the right team

## Routing logic

| Situation | Goes to |
|-----------|---------|
| Description mentions fraud/staged/inconsistent | Investigation Flag |
| Claim type is injury | Specialist Queue |
| Any required field is missing | Manual Review |
| Damage is under Rs.25,000 and all fields are filled | Fast-track |
| Damage is Rs.25,000 or more | Manual Review |

## Setup

### 1. Get a free Groq API key

Sign up at https://console.groq.com, go to API Keys, and create one. It's free.

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Set the API key

Windows:
```
set GROQ_API_KEY=your-key-here
```

Mac/Linux:
```
export GROQ_API_KEY=your-key-here
```

## Running it

Process all sample files:
```
python main.py --demo
```

Process one file:
```
python main.py fast_track_auto.txt
```

Save output to JSON:
```
python main.py --demo --output results.json
```

## Output format

```json
{
  "filename": "fast_track_auto.txt",
  "extractedFields": {
    "policy_number": "POL-2024-AUTO-00145",
    "policyholder_name": "Rajesh Kumar Sharma",
    "incident_date": "15-Mar-2024",
    "estimated_damage": 18500,
    "claim_type": "auto"
  },
  "missingFields": [],
  "recommendedRoute": "Fast-track",
  "reasoning": "Damage Rs.18,500 is under the Rs.25,000 limit. All fields present."
}
```

## Files

```
claims-agent/
├── main.py                    - runs the program
├── agent.py                   - extraction, validation, routing
├── extractor.py               - reads PDF and TXT files
├── requirements.txt
├── fast_track_auto.txt
├── high_damage_manual.txt
├── investigation_fraud.txt
├── manual_missing_fields.txt
└── specialist_injury.txt
```

## Stack

- Python 3.10+
- Groq API (free) with Llama3
- pdfplumber for PDF reading