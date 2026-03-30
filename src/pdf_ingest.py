from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber


@dataclass
class ParsedApplication:
    app_id: Optional[int] = None
    major: Optional[str] = None
    term: Optional[str] = None
    grad_type: Optional[int] = None  # 0=Undergraduate, 1=Graduate, 2=PhD
    admissions_status: Optional[str] = None
    student_type: Optional[str] = None
    gpa: Optional[float] = None
    missing_items: List[str] | None = None
    decision_status: Optional[str] = None
    decision_reason: Optional[str] = None
    applicant_name: Optional[str] = None
    muid: Optional[str] = None
    gender: Optional[int] = None      # 0=Male,1=Female,2=Other
    email_address: Optional[str] = None
    phys_address: Optional[str] = None
    documents: List[Dict[str, Any]] | None = None


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def extract_all_text(pdf_path: str | Path) -> List[str]:
    pages: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(normalize_whitespace(text))
    return pages


def search(pattern: str, text: str, flags: int = 0) -> Optional[re.Match[str]]:
    return re.search(pattern, text, flags)


def map_grad_type(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    lowered = text.lower()
    if "phd" in lowered or "ph.d" in lowered or "doctoral" in lowered:
        return 2
    if "graduate" in lowered or "master" in lowered or "ms" in lowered or "ma" in lowered:
        return 1
    if "undergraduate" in lowered or "bachelor" in lowered:
        return 0
    return None


def parse_page_one(page1: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    missing = search(r"Missing:\s*(.+)", page1)
    if missing:
        items = [item.strip() for item in re.split(r",|;", missing.group(1)) if item.strip()]
        data["missing_items"] = items

    major = search(r"Major:\s*(.+?)\s+MUID", page1, re.S)
    if major:
        data["major"] = major.group(1).strip()

    applicant = search(r"Applicant[’']s Name:\s*(.+?)\s+Term applying for:", page1, re.S)
    if applicant:
        value = applicant.group(1).strip(" _")
        if value:
            data["applicant_name"] = value

    lower = page1.lower()
    if "conditional admission" in lower:
        data["decision_status"] = "Conditional Admission"
    elif "denial of admission" in lower:
        data["decision_status"] = "Not Admitted"

    reason_block = search(
        r"future admission consideration\.\)\s*(.+?)\s*(?:Dr\.|Mr\.|Mrs\.|Ms\.)\s+[A-Z]",
        page1,
        re.S
    )

    if reason_block:
        reason = reason_block.group(1)

        # Remove the label if it appears inside the captured block
        reason = reason.replace("Reason for conditional or denied admission:", "")

        # Split into lines and clean them
        lines = [line.strip() for line in reason.splitlines()]

        cleaned_lines = []
        for line in lines:
            if not line:
                continue
            if set(line) == {"_"}:
                continue
            cleaned_lines.append(line)

        if cleaned_lines:
            reason = " ".join(cleaned_lines)
            reason = normalize_whitespace(reason)
            reason = reason.replace("of of", "of")
            data["decision_reason"] = reason
    return data

def parse_summary_page(page4: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}

    term = search(r"Student Type\s+Term\s+.+?\s+([A-Za-z]+\s+20\d{2})", page4, re.S)
    if term:
        data["term"] = term.group(1)

    admissions_status = search(r"Computer Science \(MS\)\s+(Completed App|Incomplete App|Admitted|Denied)", page4)
    if admissions_status:
        data["admissions_status"] = admissions_status.group(1).strip()

    student_type = search(r"Student Type\s+Term\s+(.+?)\s+[A-Za-z]+\s+20\d{2}", page4, re.S)
    if student_type:
        value = normalize_whitespace(student_type.group(1))
        if value:
            data["student_type"] = value
            data["grad_type"] = map_grad_type(value)

    major = search(r"Level Program\s+(.+?)\s+Major Admissions Status", page4, re.S)
    if major:
        value = normalize_whitespace(major.group(1))
        if value:
            data["major"] = value

    email = search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", page4)
    if email:
        data["email_address"] = email.group(0)

    return data


def parse_documents_page(page5: str) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []

    fee = search(r"Application Fee\s+Waived\s+(\d{2}/\d{2}/\d{4})", page5)
    if fee:
        docs.append(
            {
                "display_name": "Application Fee",
                "status": "Waived",
                "date_received": normalize_date(fee.group(1)),
            }
        )

    transcript = search(r"Marshall University Official Transcript\s+Received - Official", page5)
    if transcript:
        docs.append(
            {
                "display_name": "Marshall University Official Transcript",
                "status": "Received - Official",
                "date_received": None,
            }
        )

    return docs


def parse_app_id(pages: List[str]) -> Optional[int]:
    for page in pages:
        match = search(r"App ID-(\d+)", page)
        if match:
            return int(match.group(1))
    return None


def parse_transcript_page(page8: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    gpa = search(r"OVERALL\s+\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)", page8)
    if gpa:
        data["gpa"] = float(gpa.group(1))
    return data


def parse_application_pdf(pdf_path: str | Path) -> Dict[str, Any]:
    pages = extract_all_text(pdf_path)
    if not pages:
        raise ValueError("No text could be extracted from the PDF.")

    data = ParsedApplication(missing_items=[], documents=[])
    data.app_id = parse_app_id(pages)

    parsers = [
        (0, parse_page_one),
        (3, parse_summary_page),
        (4, lambda text: {"documents": parse_documents_page(text)}),
        (7, parse_transcript_page),
    ]

    for index, parser in parsers:
        if index < len(pages):
            parsed = parser(pages[index])
            for key, value in parsed.items():
                if value is None:
                    continue
                if key == "documents":
                    data.documents.extend(value)
                elif key == "missing_items":
                    data.missing_items.extend(value)
                else:
                    setattr(data, key, value)

    if data.grad_type is None:
        data.grad_type = map_grad_type(data.major)

    return asdict(data)

def normalize_date(date_str):
    if not date_str:
        return None
    parts = date_str.split("/")
    if len(parts) == 3:
        mm, dd, yyyy = parts
        return f"{mm.zfill(2)}{dd.zfill(2)}{yyyy}"
    return None

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python pdf_ingest.py <pdf_path>")
        raise SystemExit(1)

    result = parse_application_pdf(sys.argv[1])
    print(json.dumps(result, indent=2))
