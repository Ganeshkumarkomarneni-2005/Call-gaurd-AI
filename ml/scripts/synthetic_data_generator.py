"""Synthetic conversation dataset generator for CallGuard AI.

Generates multi-turn telephony conversations across 11 distinct operational scenarios:
1. human recruiter (legitimate recruitment discussion)
2. AI recruiter (conversational conversational AI conducting preliminary candidate screening)
3. AI interview scheduler (automated bot coordinating calendar slots)
4. AI promotional (robocall telemarketing promotional pitches)
5. human scammer (IRS tax, law enforcement, tech support impersonation)
6. AI scammer (synthesized voice phishing, urgency, credential harvesting)
7. fake recruiter requesting payment (advance fee recruitment fraud, training fees, check cashing)
8. OTP fraud (caller attempting to trick victim into disclosing 2FA SMS code)
9. legitimate customer service (banking alert verification, utility notification, airline update)
10. delivery notification (courier dispatch driver, Amazon/FedEx delivery confirmation)
11. unknown caller (empty audio, static, misdialed number, disjointed greeting)

Outputs standard JSONL records formatted for CallGuard model training and evaluation.
"""

from __future__ import annotations

import json
import logging
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Sample entities for synthetic variety
RECRUITERS = ["Sarah Jenkins", "Michael Chang", "Amanda Brooks", "David Ross", "Elena Rostova", "Marcus Vance"]
COMPANIES = ["Apex Cloud Systems", "Starlight Health", "FinTech Nexus", "Quantum Dynamics", "Metro Logistics", "Global Core Tech"]
POSITIONS = ["Senior Backend Engineer", "Data Scientist", "DevOps Specialist", "Product Manager", "Systems Architect", "Frontend Lead"]
DATES = ["tomorrow at 2:00 PM", "next Monday at 10:00 AM", "Thursday afternoon at 3:30 PM", "Friday at 11:00 AM"]
BANKS = ["Chase Security Operations", "Wells Fargo Fraud Desk", "Bank of America Alert Center", "Citibank Protection Group"]
COURIERS = ["FedEx Express", "UPS Ground", "DHL Global", "Amazon Logistics"]


def _generate_scenario_data(scenario: str, seed: int) -> Dict[str, Any]:
    """Generate a single conversation record for a given scenario using deterministic variation."""
    rng = random.Random(seed)

    recruiter = rng.choice(RECRUITERS)
    company = rng.choice(COMPANIES)
    position = rng.choice(POSITIONS)
    date_slot = rng.choice(DATES)
    bank = rng.choice(BANKS)
    courier = rng.choice(COURIERS)
    amount = rng.choice(["$450", "$1,200", "$2,850", "$99.99", "$3,500"])
    otp_code = f"{rng.randint(100000, 999999)}"

    record_id = str(uuid.uuid4())

    if scenario == "human_recruiter":
        turns = [
            {"speaker": "caller", "text": f"Hello, am I speaking with the candidate? My name is {recruiter} with {company}.", "timestamp_ms": 500},
            {"speaker": "agent", "text": "Hello, yes this is CallGuard assistant on behalf of the user. How can I help you?", "timestamp_ms": 3200},
            {"speaker": "caller", "text": f"I came across your resume on LinkedIn for our {position} role. Your distributed systems background looks like an ideal fit.", "timestamp_ms": 7100},
            {"speaker": "agent", "text": "That sounds promising. What are the next steps in your recruitment process?", "timestamp_ms": 11500},
            {"speaker": "caller", "text": f"We'd love to schedule a 30-minute introductory call with our engineering director {date_slot}. Does that time window work?", "timestamp_ms": 15800},
            {"speaker": "agent", "text": "I will record this scheduling request and notify the user to confirm their availability.", "timestamp_ms": 20400},
            {"speaker": "caller", "text": f"Excellent, I'll send an invite link from {company.lower().replace(' ', '')}.com. Thank you and have a great day.", "timestamp_ms": 24200},
        ]
        return {
            "id": record_id,
            "scenario": "human_recruiter",
            "caller_type": "human",
            "intent": "recruitment",
            "risk_level": "low",
            "risk_indicators": [],
            "action": "transfer_human",
            "is_recruitment": True,
            "is_legitimate": True,
            "company": company,
            "recruiter_name": recruiter,
            "position": position,
            "interview_date": date_slot,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "ai_recruiter":
        turns = [
            {"speaker": "caller", "text": f"Hello! This is an automated preliminary interview screening system from {company} Talent Acquisition.", "timestamp_ms": 600},
            {"speaker": "agent", "text": "Hello. I am the CallGuard AI representative for the user.", "timestamp_ms": 3500},
            {"speaker": "caller", "text": f"We received an application for {position}. I am calling to ask three quick qualification questions regarding your years of Python experience.", "timestamp_ms": 7800},
            {"speaker": "agent", "text": "The candidate has authorized me to receive details. Please summarize the requirements and provide a direct scheduling link.", "timestamp_ms": 13000},
            {"speaker": "caller", "text": "Understood. The job requires 5+ years with microservices. I am emailing the self-serve interview link to the candidate's address on file.", "timestamp_ms": 18200},
            {"speaker": "agent", "text": "Thank you, message noted and logged.", "timestamp_ms": 22100},
        ]
        return {
            "id": record_id,
            "scenario": "ai_recruiter",
            "caller_type": "ai",
            "intent": "recruitment",
            "risk_level": "low",
            "risk_indicators": [{"indicator_type": "synthetic_voice", "description": "Automated AI conversational recruitment agent detected", "severity": "low", "confidence": 0.92}],
            "action": "continue_ai",
            "is_recruitment": True,
            "is_legitimate": True,
            "company": company,
            "recruiter_name": "Automated Talent AI",
            "position": position,
            "interview_date": "Self-serve calendar link",
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "ai_interview_scheduler":
        turns = [
            {"speaker": "caller", "text": f"Greetings. This is the calendar automation bot from {company}. We are confirming your technical interview scheduled for {date_slot}.", "timestamp_ms": 500},
            {"speaker": "agent", "text": "Hello, CallGuard AI here. We acknowledge the interview slot.", "timestamp_ms": 3900},
            {"speaker": "caller", "text": "To confirm this slot press 1, or state reschedule to choose an alternate time.", "timestamp_ms": 7400},
            {"speaker": "agent", "text": "Please log our confirmation for this scheduled appointment.", "timestamp_ms": 11200},
            {"speaker": "caller", "text": "Thank you, your appointment is confirmed. A calendar invite has been dispatched.", "timestamp_ms": 14600},
        ]
        return {
            "id": record_id,
            "scenario": "ai_interview_scheduler",
            "caller_type": "ai",
            "intent": "interview_scheduling",
            "risk_level": "low",
            "risk_indicators": [],
            "action": "continue_ai",
            "is_recruitment": True,
            "is_legitimate": True,
            "company": company,
            "interview_date": date_slot,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "ai_promotional":
        offer = rng.choice(["residential solar panels with zero down payment", "reduced interest rate auto refinancing", "extended comprehensive vehicle warranty coverage"])
        turns = [
            {"speaker": "caller", "text": f"Congratulations! You have been pre-selected for our exclusive limited-time promotion on {offer}!", "timestamp_ms": 400},
            {"speaker": "agent", "text": "Who is calling and which organization do you represent?", "timestamp_ms": 3200},
            {"speaker": "caller", "text": "Our state-wide clean energy program can slash your monthly utility bill by up to 70 percent. Press 1 immediately to speak to a specialist.", "timestamp_ms": 6800},
            {"speaker": "agent", "text": "The subscriber is registered on the national Do Not Call list. Please remove this number from your solicitation database.", "timestamp_ms": 12100},
            {"speaker": "caller", "text": "Do not miss out on this government approved rebate. Press 1 now before funds expire.", "timestamp_ms": 16400},
        ]
        return {
            "id": record_id,
            "scenario": "ai_promotional",
            "caller_type": "robocall",
            "intent": "promotional",
            "risk_level": "medium",
            "risk_indicators": [
                {"indicator_type": "telemarketing", "description": "Unsolicited promotional robocall pitch", "severity": "medium", "confidence": 0.95},
                {"indicator_type": "synthetic_cadence", "description": "Pre-recorded robotic broadcast pattern", "severity": "medium", "confidence": 0.91},
            ],
            "action": "end_call",
            "is_recruitment": False,
            "is_legitimate": False,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "human_scammer":
        agency = rng.choice(["Internal Revenue Service Criminal Division", "Social Security Administration Enforcement Branch", "Federal Department of Legal Sanctions"])
        turns = [
            {"speaker": "caller", "text": f"Attention. This is Officer John Miller badge number 4921 calling from the {agency}.", "timestamp_ms": 600},
            {"speaker": "agent", "text": "State the reference case ID and purpose of your inquiry.", "timestamp_ms": 4200},
            {"speaker": "caller", "text": f"A federal arrest warrant has been issued in your name due to fraudulent tax evasion of {amount}. You must settle this penalty within two hours or local marshals will arrive.", "timestamp_ms": 8600},
            {"speaker": "agent", "text": "Government agencies communicate formal notices via certified postal mail, not outbound phone calls demanding immediate settlement.", "timestamp_ms": 14900},
            {"speaker": "caller", "text": "Do not argue with federal authorities! You must purchase prepaid voucher cards or transfer funds to avoid immediate arrest and account freezing!", "timestamp_ms": 19800},
        ]
        return {
            "id": record_id,
            "scenario": "human_scammer",
            "caller_type": "human",
            "intent": "fraud_scam",
            "risk_level": "critical",
            "risk_indicators": [
                {"indicator_type": "government_impersonation", "description": "False claim of law enforcement arrest warrant", "severity": "critical", "confidence": 0.99},
                {"indicator_type": "coercive_urgency", "description": "Threats of immediate arrest and account freeze within 2 hours", "severity": "critical", "confidence": 0.98},
                {"indicator_type": "unusual_payment_method", "description": "Demand for prepaid voucher or wire transfer", "severity": "critical", "confidence": 0.97},
            ],
            "action": "block",
            "is_recruitment": False,
            "is_legitimate": False,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "ai_scammer":
        turns = [
            {"speaker": "caller", "text": "Warning: Unauthorized access detected on your digital banking profile from an unknown device in Moscow.", "timestamp_ms": 500},
            {"speaker": "agent", "text": "Which banking institution are you asserting this alert belongs to?", "timestamp_ms": 3800},
            {"speaker": "caller", "text": "To safeguard your balances, press 9 now to be transferred to our emergency automated security firewall.", "timestamp_ms": 7600},
            {"speaker": "agent", "text": "CallGuard has flagged this interactive prompt as an automated credential harvesting attempt.", "timestamp_ms": 12400},
            {"speaker": "caller", "text": "Failure to respond within 60 seconds will result in total account termination. Press 9 immediately.", "timestamp_ms": 16900},
        ]
        return {
            "id": record_id,
            "scenario": "ai_scammer",
            "caller_type": "ai",
            "intent": "fraud_scam",
            "risk_level": "critical",
            "risk_indicators": [
                {"indicator_type": "phishing_alert", "description": "Fabricated unauthorized access emergency", "severity": "critical", "confidence": 0.96},
                {"indicator_type": "artificial_urgency", "description": "60 second account termination ultimatum", "severity": "critical", "confidence": 0.95},
                {"indicator_type": "voice_synthesis", "description": "Deepfake or synthetic speech detected", "severity": "high", "confidence": 0.89},
            ],
            "action": "block",
            "is_recruitment": False,
            "is_legitimate": False,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "fake_recruiter_payment":
        turns = [
            {"speaker": "caller", "text": f"Hello! Great news! You have been selected for an immediate work-from-home position at {company} paying $95 per hour.", "timestamp_ms": 600},
            {"speaker": "agent", "text": "Has an official technical interview or background verification been conducted for this role?", "timestamp_ms": 4100},
            {"speaker": "caller", "text": f"No interview required! Your profile was fast-tracked. However, before shipping your Apple laptop, you must pay a refundable onboarding equipment fee of {amount}.", "timestamp_ms": 8900},
            {"speaker": "agent", "text": "Legitimate employers never charge candidates advance fees for onboarding hardware or software licenses.", "timestamp_ms": 14200},
            {"speaker": "caller", "text": "This is standard company policy for home office setup. You can send the payment via Zelle or cryptocurrency right now to secure your job offer.", "timestamp_ms": 19500},
        ]
        return {
            "id": record_id,
            "scenario": "fake_recruiter_payment",
            "caller_type": "human",
            "intent": "recruitment",
            "risk_level": "critical",
            "risk_indicators": [
                {"indicator_type": "employment_advance_fee_fraud", "description": "Demanding upfront fee for remote job equipment", "severity": "critical", "confidence": 0.99},
                {"indicator_type": "unregulated_payment_channel", "description": "Request for Zelle / cryptocurrency transfer", "severity": "critical", "confidence": 0.98},
                {"indicator_type": "no_interview_hiring", "description": "High-paying job offer without formal interview", "severity": "high", "confidence": 0.92},
            ],
            "action": "block",
            "is_recruitment": True,
            "is_legitimate": False,
            "company": company,
            "position": "Remote Consultant",
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "otp_fraud":
        service = rng.choice(["Google Authenticator", "Coinbase", "Apple ID Account Recovery", "Wireless SIM Carrier"])
        turns = [
            {"speaker": "caller", "text": f"Good afternoon, this is senior security representative Kevin from {service}. We are blocking a fraudulent login attempt right now.", "timestamp_ms": 500},
            {"speaker": "agent", "text": "Please provide your corporate agent identification number.", "timestamp_ms": 3800},
            {"speaker": "caller", "text": f"I just triggered a one-time verification passcode to your registered SMS number ending in 42. Please read back that 6-digit code so I can cancel the intrusion.", "timestamp_ms": 8200},
            {"speaker": "agent", "text": "One-time passcodes clearly state: Do NOT share this code with anyone, including customer service agents.", "timestamp_ms": 13900},
            {"speaker": "caller", "text": f"If you do not give me the code {otp_code} or whatever code you just received, your account will be permanently compromised in 30 seconds!", "timestamp_ms": 18400},
        ]
        return {
            "id": record_id,
            "scenario": "otp_fraud",
            "caller_type": "human",
            "intent": "otp_theft",
            "risk_level": "critical",
            "risk_indicators": [
                {"indicator_type": "otp_harvesting", "description": "Outbound caller requesting SMS two-factor verification code", "severity": "critical", "confidence": 0.99},
                {"indicator_type": "pressure_tactics", "description": "Threatening compromise if code is withheld", "severity": "critical", "confidence": 0.97},
            ],
            "action": "block",
            "is_recruitment": False,
            "is_legitimate": False,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "legitimate_customer_service":
        turns = [
            {"speaker": "caller", "text": f"Hello, this is {bank} automated alert system calling about potential unusual activity on your card ending in 8104.", "timestamp_ms": 500},
            {"speaker": "agent", "text": "CallGuard assistant here. Please state the transaction details for verification.", "timestamp_ms": 3900},
            {"speaker": "caller", "text": f"We detected a charge of {amount} at a merchant named Apex Superstore. Did you authorize this charge? Reply yes or no.", "timestamp_ms": 8100},
            {"speaker": "agent", "text": "I am logging this alert and notifying the account holder to review their banking app directly.", "timestamp_ms": 13200},
            {"speaker": "caller", "text": "Thank you. For your security, we will never ask for your PIN, password, or full card number over the phone. Please check your mobile app.", "timestamp_ms": 17800},
        ]
        return {
            "id": record_id,
            "scenario": "legitimate_customer_service",
            "caller_type": "ai",
            "intent": "customer_service",
            "risk_level": "low",
            "risk_indicators": [],
            "action": "continue_ai",
            "is_recruitment": False,
            "is_legitimate": True,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    elif scenario == "delivery_notification":
        tracking = f"1Z{rng.randint(100000, 999999)}"
        turns = [
            {"speaker": "caller", "text": f"Hi there, this is your {courier} delivery driver. I am downstairs with a package requiring signature, tracking number {tracking}.", "timestamp_ms": 400},
            {"speaker": "agent", "text": "Hello, CallGuard agent here. Can you leave the parcel with the front desk reception?", "timestamp_ms": 3500},
            {"speaker": "caller", "text": "Yes, reception is open so I will drop it there and obtain building security sign-off.", "timestamp_ms": 7200},
            {"speaker": "agent", "text": "Thank you, delivery recorded and notification dispatched to resident.", "timestamp_ms": 11000},
            {"speaker": "caller", "text": "Sounds good, have a nice day!", "timestamp_ms": 13900},
        ]
        return {
            "id": record_id,
            "scenario": "delivery_notification",
            "caller_type": "human",
            "intent": "delivery",
            "risk_level": "low",
            "risk_indicators": [],
            "action": "continue_ai",
            "is_recruitment": False,
            "is_legitimate": True,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }

    else:  # unknown_caller
        turns = [
            {"speaker": "caller", "text": rng.choice(["... Hello? Is ... who is this? ... hello?", "[static noise] ... can you hear me? ... [cough] ... wrong number.", "Hey ... wait, is this Dave? Oh sorry, wrong line."]), "timestamp_ms": 800},
            {"speaker": "agent", "text": "Hello, CallGuard security screener. Who were you trying to reach?", "timestamp_ms": 4200},
            {"speaker": "caller", "text": rng.choice(["... [line dead tone] ...", "Uh, nevermind, dialed the wrong area code.", "... [silence for 5 seconds] ..."]), "timestamp_ms": 7500},
        ]
        return {
            "id": record_id,
            "scenario": "unknown_caller",
            "caller_type": "unknown",
            "intent": "unknown",
            "risk_level": "low",
            "risk_indicators": [],
            "action": "end_call",
            "is_recruitment": False,
            "is_legitimate": False,
            "conversation": turns,
            "full_transcript": " ".join([t["text"] for t in turns]),
        }


def generate_dataset(
    output_path: str = "ml/datasets/callguard/synthetic_conversations.jsonl",
    count_per_scenario: int = 100,
) -> List[Dict[str, Any]]:
    """Generate balanced synthetic conversation dataset covering all 11 scenarios.

    Args:
        output_path: Destination JSONL file path.
        count_per_scenario: Number of conversations to generate per category (~100).

    Returns:
        List[Dict[str, Any]]: List of generated records.
    """
    scenarios = [
        "human_recruiter",
        "ai_recruiter",
        "ai_interview_scheduler",
        "ai_promotional",
        "human_scammer",
        "ai_scammer",
        "fake_recruiter_payment",
        "otp_fraud",
        "legitimate_customer_service",
        "delivery_notification",
        "unknown_caller",
    ]

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    records = []
    seed_base = 42

    for scenario_idx, scenario in enumerate(scenarios):
        for item_idx in range(count_per_scenario):
            seed = seed_base + (scenario_idx * 1000) + item_idx
            rec = _generate_scenario_data(scenario, seed)
            records.append(rec)

    # Shuffle dataset
    random.Random(42).shuffle(records)

    with open(out_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    logger.info(
        "Successfully generated %d synthetic conversations across %d scenarios to %s",
        len(records),
        len(scenarios),
        out_file,
    )
    return records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dest = "ml/datasets/callguard/synthetic_conversations.jsonl"
    print(f"Generating synthetic CallGuard dataset at {dest}...")
    dataset = generate_dataset(output_path=dest, count_per_scenario=100)
    print(f"Done! Generated {len(dataset)} examples.")
