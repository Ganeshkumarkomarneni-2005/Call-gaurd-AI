# CallGuard AI — Dataset Card

**Version:** 1.0  
**Last Updated:** 2026-09-21

---

## Overview

CallGuard AI uses five datasets:

| Dataset | Purpose | License | Status |
|---------|---------|---------|--------|
| CLINC150 | Intent classification | Creative Commons | AVAILABLE — HuggingFace |
| BANKING77 | Financial intent understanding | CC BY 4.0 | AVAILABLE — HuggingFace |
| FTC Do-Not-Call / Robocall data | Robocall/spam patterns | Public Domain | AVAILABLE — FTC website |
| ASVspoof | Synthetic speech detection research | Research use | AVAILABLE — asvspoof.org |
| CallGuard Custom Dataset | Primary training/evaluation | Proprietary (project) | CREATED — synthetic (1,100 records) |

---

## Dataset 1: CLINC150

### Overview
CLINC150 is a benchmark dataset for task-oriented dialogue systems, covering 150 intent classes across 10 domains, plus out-of-scope queries.

### Source
- **Repository:** https://github.com/clinc/oos-eval
- **HuggingFace:** `clinc_oos` (splits: `plus`, `imbalanced`, `small`)
- **Paper:** Larson et al., 2019

### Usage in CallGuard
- Primary intent classification training data
- Out-of-scope detection (maps to `UNKNOWN` intent)
- Domains used: banking, travel, utility, meta, kitchen, auto, tickets, work, small-talk

### Class Mapping to CallGuard Intents

| CLINC150 Domain | CallGuard Intent |
|-----------------|-----------------|
| banking | CUSTOMER_SERVICE |
| travel | DELIVERY / OTHER |
| utility | OTHER |
| out_of_scope | UNKNOWN |
| Small-talk / personal | PERSONAL |

> [!NOTE]
> CLINC150 does not include RECRUITMENT, FRAUD, or PROMOTIONAL intents.
> These must come from the custom CallGuard dataset.

### License
Creative Commons Attribution 3.0 Unported (CC BY 3.0)

### Limitations
- English language only
- Written/typed utterances, not transcribed speech
- No recruitment or fraud categories
- No multi-intent examples

### Preprocessing Applied
1. Lowercase
2. Strip whitespace
3. Remove duplicates
4. Map to CallGuard intent schema
5. Stratified 80/10/10 split

### Class Distribution (approximate)
- 150 intent classes × ~100 samples each = ~15,000 training examples
- 100 out-of-scope examples per split

---

## Dataset 2: BANKING77

### Overview
BANKING77 is a banking-domain intent classification dataset with 77 intents, focused on customer service scenarios.

### Source
- **HuggingFace:** `PolyAI/banking77`
- **Paper:** Casanueva et al., 2020

### Usage in CallGuard
- Enriching CUSTOMER_SERVICE intent examples
- Understanding financial terminology in calls

> [!IMPORTANT]
> BANKING77 is NOT a scam/fraud dataset.
> It covers legitimate banking customer service intents only.
> Do NOT use BANKING77 examples to train fraud detection.

### Class Mapping to CallGuard Intents

| BANKING77 Intent | CallGuard Intent |
|-----------------|-----------------|
| All 77 intents | CUSTOMER_SERVICE |

### License
Creative Commons Attribution 4.0 International (CC BY 4.0)

### Limitations
- Banking domain only
- No recruitment, fraud, promotional content
- English only
- Written queries, not speech transcriptions

### Preprocessing Applied
1. Lowercase
2. Deduplicate
3. Map all → CUSTOMER_SERVICE

---

## Dataset 3: FTC Do Not Call / Robocall Data

### Overview
The Federal Trade Commission (FTC) publishes Do Not Call (DNC) registry complaint data, including information about reported robocall and unwanted telemarketing calls.

### Source
- **FTC DNC Data:** https://www.ftc.gov/policy/open-government/data-sets/do-not-call-data
- **FTC Robocall Data:** https://www.ftc.gov/policy/open-government/data-sets/robocall-data
- Published monthly; public domain

### Usage in CallGuard
- Understanding reported robocall patterns
- Identifying promotional/spam call categories
- Training data for PROMOTIONAL and ROBOCALL classification

> [!IMPORTANT]
> FTC complaint data represents CONSUMER REPORTS, not confirmed fraud.
> A complaint does not mean the call was definitely fraudulent.
> Use as a probabilistic signal, not as ground truth for fraud labeling.

### Key Fields Available
- `Company_Phone_Number` — reported number
- `Subject` — call subject/topic (e.g., "medical/prescription", "debt reduction")
- `Sale_State`, `State` — location data
- `Date_of_DNC_Violation` — report date
- `Type` — Robocall, Prerecorded message, Live call

### Limitations
- Self-reported complaints — unverified
- Limited to US context
- No conversation transcripts
- High class imbalance (some categories very rare)
- Privacy/PII considerations for phone numbers

### Preprocessing Required
1. Remove PII (phone numbers) before training
2. Extract subject categories → map to CallGuard intents
3. Filter to relevant categories (recruitment fraud, prizes/lotteries, medical)
4. Treat all labels as WEAK SUPERVISION, not ground truth

---

## Dataset 4: ASVspoof

### Overview
ASVspoof is a research benchmark dataset for spoofed and synthetic speech detection. It covers physical access attacks, logical access attacks, and deepfake speech.

### Source
- **Website:** https://www.asvspoof.org/
- **ASVspoof 2019:** LA (Logical Access), PA (Physical Access)
- **ASVspoof 2021:** LA, DF (Deepfake)

### Usage in CallGuard
- Research reference for synthetic/AI speech detection
- Feature engineering inspiration for caller type detection

> [!IMPORTANT]
> ASVspoof was designed for anti-spoofing in speaker verification systems.
> The recording conditions (clean studio) may differ from telephone calls.
> Do NOT assume ASVspoof performance translates to real-world telephone audio.
> Caller type detection is treated as a PROBABILISTIC SUPPORTING SIGNAL only.

### Limitations
- Studio-quality recordings — not telephone audio quality
- Not directly applicable to call center audio (G.711/G.729 codec artifacts)
- Language-specific
- New TTS/deepfake systems not covered by older ASVspoof versions
- Cannot guarantee detection of sophisticated new voice cloning

### Download
- Registration required at asvspoof.org
- Academic/research use only

---

## Dataset 5: CallGuard Custom Dataset

### Overview
This is the primary project dataset, created specifically for CallGuard AI. It covers all target scenarios including recruitment calls, fraud calls, promotional calls, and ambiguous cases.

### Source Type
`SYNTHETIC` — Generated by `ml/scripts/synthetic_data_generator.py`

### Current Status
- **Version:** 1.0-synthetic
- **Records:** 1,100
- **Created:** 2026-09-21
- **Format:** JSONL (`ml/datasets/callguard/synthetic_conversations.jsonl`)

### Schema

```json
{
  "conversation_id": "string",
  "scenario": "string",
  "conversation": [
    {
      "speaker": "CALLER|AGENT",
      "text": "string",
      "timestamp_ms": 0
    }
  ],
  "labels": {
    "caller_type": "HUMAN|AI|ROBOCALL|UNKNOWN",
    "intent": "RECRUITMENT|PROMOTIONAL|FRAUD|CUSTOMER_SERVICE|DELIVERY|PERSONAL|OTHER|UNKNOWN",
    "secondary_intent": "string|null",
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "risk_indicators": ["string"],
    "action": "AI_HANDLE|NOTIFY|TRANSFER|END|FLAG_FOR_REVIEW",
    "confidence": 0.0
  },
  "metadata": {
    "company": "string|null",
    "position": "string|null",
    "is_legitimate_recruitment": "bool|null",
    "generated_at": "string",
    "generator_version": "string"
  }
}
```

### Scenarios Covered

| Scenario | Count | Labels |
|----------|-------|--------|
| Human recruiter (legitimate) | 100 | HUMAN, RECRUITMENT, LOW |
| AI recruiter (legitimate) | 100 | AI, RECRUITMENT, LOW |
| AI interview scheduler | 100 | AI, RECRUITMENT, LOW |
| AI promotional caller | 100 | AI, PROMOTIONAL, LOW-MEDIUM |
| Human scammer | 100 | HUMAN, FRAUD, HIGH-CRITICAL |
| AI scammer | 100 | AI, FRAUD, HIGH-CRITICAL |
| Fake recruiter requesting payment | 100 | HUMAN/AI, RECRUITMENT+FRAUD, HIGH-CRITICAL |
| OTP fraud | 100 | HUMAN/AI, FRAUD, CRITICAL |
| Legitimate customer service | 100 | HUMAN/AI, CUSTOMER_SERVICE, LOW |
| Delivery notification | 100 | AI, DELIVERY, LOW |
| Unknown / ambiguous caller | 100 | UNKNOWN, UNKNOWN, MEDIUM |

### Quality Notes

> [!WARNING]
> This is a SYNTHETIC dataset. Real-world performance will differ.
> Key limitations:
> - Conversations are generated from templates, not real call recordings
> - May not capture natural speech disfluencies, code-switching, or dialects
> - Trained models must be evaluated on real calls before production use

### Target Dataset Evolution

| Version | Records | Source | Status |
|---------|---------|--------|--------|
| 1.0-synthetic | 1,100 | Synthetic generator | CURRENT |
| 2.0-augmented | 3,000+ | Synthetic + public sources | PLANNED |
| 3.0-real | TBD | Real call transcripts (with consent) | FUTURE |

### Class Balance Check

Run `ml/scripts/dataset_validator.py` → `check_class_balance()` before training.

### Leakage Check

Run `ml/scripts/dataset_validator.py` → `check_for_leakage()` before final evaluation to ensure no training examples appear in the test set.

---

## Data Ethics and Privacy

- No real caller phone numbers are stored in any dataset
- No real personal identifiable information (PII) in training data
- Synthetic conversations do not correspond to real individuals
- FTC data PII removed before any processing
- For future real call data: explicit consent must be obtained before recording and transcription

---

## Dataset Download Instructions

### CLINC150
```python
from datasets import load_dataset
dataset = load_dataset("clinc_oos", "plus")
```

### BANKING77
```python
from datasets import load_dataset
dataset = load_dataset("PolyAI/banking77")
```

### FTC Data
1. Visit: https://www.ftc.gov/policy/open-government/data-sets/do-not-call-data
2. Download the latest CSV
3. Place in: `ml/datasets/ftc/`

### ASVspoof
1. Visit: https://www.asvspoof.org/
2. Register and download ASVspoof 2019 LA partition
3. Place audio in: `ml/datasets/asvspoof/`

### CallGuard Custom
Already generated at: `ml/datasets/callguard/synthetic_conversations.jsonl`
