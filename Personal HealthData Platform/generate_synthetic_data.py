"""
generate_synthetic_data.py
==========================
Generates synthetic health data for multiple customers.

New folder structure (per-customer):
  customers/
  └── {customer_id}/
      ├── DICOM/
      │   └── *.dcm
      ├── BloodReports/
      │   └── *.pdf
      ├── Wearables/
      │   └── *.csv
      └── Genomics/           ← placeholder, ready for future use

Run:
    python generate_synthetic_data.py
"""

import os
import uuid
import json
import random
import struct
import csv
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import (
    ExplicitVRLittleEndian, generate_uid,
    CTImageStorage, MRImageStorage
)

fake = Faker()
random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# Customer definitions
# ─────────────────────────────────────────────

CUSTOMERS = [
    {"name": "Amara Patel",    "age": 34, "gender": "F", "condition": "Hypertension"},
    {"name": "John Whitfield", "age": 58, "gender": "M", "condition": "Diabetes Type 2"},
    {"name": "Mei Lin",        "age": 42, "gender": "F", "condition": "Anaemia"},
    {"name": "Carlos Rivera",  "age": 27, "gender": "M", "condition": "Healthy"},
    {"name": "Fatima Al-Sayed","age": 65, "gender": "F", "condition": "Osteoporosis"},
]


def make_customer_id(name: str) -> str:
    """Stable short ID based on name."""
    slug = name.lower().replace(" ", "_").replace("-", "")
    short = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))[:8].upper()
    return f"CUST_{slug}_{short}"




def create_folder_structure(base_dir: Path, customer_id: str) -> dict:
    """Create per-customer subfolder tree and return paths."""
    root = base_dir / customer_id
    paths = {
        "root":         root,
        "dicom":        root / "DICOM",
        "blood":        root / "BloodReports",
        "wearables":    root / "Wearables",
        "genomics":     root / "Genomics",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


# ─────────────────────────────────────────────
# DICOM generator
# ─────────────────────────────────────────────

MODALITIES = ["CT", "MR", "XR"]

def generate_dicom(customer: dict, out_dir: Path, n_files: int = 2):
    """Create n synthetic DICOM files for a customer."""
    paths = []
    dob = datetime.now() - timedelta(days=customer["age"] * 365)

    for i in range(n_files):
        modality = random.choice(MODALITIES)
        uid_prefix = "1.2.840.10008.5.1.4.1.1."
        sop_class = CTImageStorage if modality == "CT" else MRImageStorage

        # File meta
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID    = sop_class
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.TransferSyntaxUID          = ExplicitVRLittleEndian

        ds = Dataset()
        ds.file_meta = file_meta
        ds.is_implicit_VR = False
        ds.is_little_endian = True

        # Patient info
        ds.PatientName    = customer["name"].replace(" ", "^")
        ds.PatientID      = customer["customer_id"]
        ds.PatientBirthDate = dob.strftime("%Y%m%d")
        ds.PatientSex     = customer["gender"]
        ds.PatientAge     = f"{customer['age']:03d}Y"

        # Study info
        ds.StudyInstanceUID   = generate_uid()
        ds.SeriesInstanceUID  = generate_uid()
        ds.SOPInstanceUID     = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID        = sop_class
        ds.StudyDate          = datetime.now().strftime("%Y%m%d")
        ds.StudyTime          = datetime.now().strftime("%H%M%S")
        ds.Modality           = modality
        ds.StudyDescription   = f"Routine {modality} scan"
        ds.InstitutionName    = "HealthPlatform Synthetic Hospital"

        # Image data (64×64 grayscale)
        rows, cols = 64, 64
        pixel_array = np.random.randint(0, 4096, (rows, cols), dtype=np.uint16)
        ds.Rows            = rows
        ds.Columns         = cols
        ds.BitsAllocated   = 16
        ds.BitsStored      = 12
        ds.HighBit         = 11
        ds.PixelRepresentation = 0
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.PixelData       = pixel_array.tobytes()

        fname = out_dir / f"{modality}_{i+1:02d}_{customer['customer_id'][:8]}.dcm"
        pydicom.dcmwrite(str(fname), ds, write_like_original=False)
        paths.append(fname)
        print(f"  [DICOM]  {fname.name}")

    return paths


# ─────────────────────────────────────────────
# Blood Report PDF generator
# ─────────────────────────────────────────────

BLOOD_PANELS = {
    "Healthy": {
        "Haemoglobin (g/dL)":       (13.5, 17.5, lambda: round(random.uniform(13.8, 17.2), 1)),
        "WBC (×10³/µL)":            (4.5,  11.0, lambda: round(random.uniform(5.0, 9.0),  1)),
        "Platelets (×10³/µL)":      (150,  400,  lambda: random.randint(180, 350)),
        "Glucose (mg/dL)":          (70,   100,  lambda: random.randint(75, 95)),
        "HbA1c (%)":                (4.0,  5.6,  lambda: round(random.uniform(4.2, 5.4), 1)),
        "Creatinine (mg/dL)":       (0.6,  1.2,  lambda: round(random.uniform(0.7, 1.1), 2)),
        "Total Cholesterol (mg/dL)":(0,    200,  lambda: random.randint(150, 195)),
    },
    "Hypertension": {
        "Haemoglobin (g/dL)":       (13.5, 17.5, lambda: round(random.uniform(13.0, 15.0), 1)),
        "WBC (×10³/µL)":            (4.5,  11.0, lambda: round(random.uniform(5.5, 10.5),  1)),
        "Platelets (×10³/µL)":      (150,  400,  lambda: random.randint(160, 380)),
        "Glucose (mg/dL)":          (70,   100,  lambda: random.randint(85, 110)),
        "HbA1c (%)":                (4.0,  5.6,  lambda: round(random.uniform(5.0, 6.0), 1)),
        "Creatinine (mg/dL)":       (0.6,  1.2,  lambda: round(random.uniform(0.9, 1.4), 2)),
        "Total Cholesterol (mg/dL)":(0,    200,  lambda: random.randint(200, 240)),
    },
    "Diabetes Type 2": {
        "Haemoglobin (g/dL)":       (13.5, 17.5, lambda: round(random.uniform(11.5, 14.0), 1)),
        "WBC (×10³/µL)":            (4.5,  11.0, lambda: round(random.uniform(6.0, 11.0),  1)),
        "Platelets (×10³/µL)":      (150,  400,  lambda: random.randint(170, 390)),
        "Glucose (mg/dL)":          (70,   100,  lambda: random.randint(120, 200)),
        "HbA1c (%)":                (4.0,  5.6,  lambda: round(random.uniform(6.5, 10.0), 1)),
        "Creatinine (mg/dL)":       (0.6,  1.2,  lambda: round(random.uniform(1.0, 1.8), 2)),
        "Total Cholesterol (mg/dL)":(0,    200,  lambda: random.randint(210, 260)),
    },
    "Anaemia": {
        "Haemoglobin (g/dL)":       (13.5, 17.5, lambda: round(random.uniform(7.0, 11.0), 1)),
        "WBC (×10³/µL)":            (4.5,  11.0, lambda: round(random.uniform(3.5, 6.0),  1)),
        "Platelets (×10³/µL)":      (150,  400,  lambda: random.randint(100, 200)),
        "Glucose (mg/dL)":          (70,   100,  lambda: random.randint(72, 95)),
        "HbA1c (%)":                (4.0,  5.6,  lambda: round(random.uniform(4.0, 5.5), 1)),
        "Creatinine (mg/dL)":       (0.6,  1.2,  lambda: round(random.uniform(0.6, 1.0), 2)),
        "Total Cholesterol (mg/dL)":(0,    200,  lambda: random.randint(145, 190)),
    },
    "Osteoporosis": {
        "Haemoglobin (g/dL)":       (13.5, 17.5, lambda: round(random.uniform(11.0, 13.5), 1)),
        "WBC (×10³/µL)":            (4.5,  11.0, lambda: round(random.uniform(4.0, 7.0),   1)),
        "Platelets (×10³/µL)":      (150,  400,  lambda: random.randint(140, 280)),
        "Glucose (mg/dL)":          (70,   100,  lambda: random.randint(75, 98)),
        "HbA1c (%)":                (4.0,  5.6,  lambda: round(random.uniform(4.5, 5.8), 1)),
        "Creatinine (mg/dL)":       (0.6,  1.2,  lambda: round(random.uniform(0.7, 1.3), 2)),
        "Total Cholesterol (mg/dL)":(0,    200,  lambda: random.randint(155, 205)),
        "Calcium (mg/dL)":          (8.5,  10.5, lambda: round(random.uniform(7.5, 8.4), 1)),
        "Vitamin D (ng/mL)":        (30,   100,  lambda: random.randint(8, 25)),
    },
}


def flag(value, lo, hi):
    if value < lo:
        return "LOW ↓"
    if value > hi:
        return "HIGH ↑"
    return "Normal"


def generate_blood_report_pdf(customer: dict, out_dir: Path):
    """Create a formatted PDF blood report for a customer."""
    fname = out_dir / f"BloodReport_{customer['customer_id'][:8]}_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc   = SimpleDocTemplate(str(fname), pagesize=A4,
                              topMargin=2*cm, bottomMargin=2*cm,
                              leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                 fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1a3a5c"))
    sub_style   = ParagraphStyle("Sub", parent=styles["Normal"],
                                 fontSize=10, textColor=colors.HexColor("#555555"))
    h2_style    = ParagraphStyle("H2", parent=styles["Heading2"],
                                 fontSize=13, textColor=colors.HexColor("#1a3a5c"), spaceBefore=14)

    elements = []

    # Header
    elements.append(Paragraph("HealthPlatform Diagnostics", title_style))
    elements.append(Paragraph("Complete Blood Count & Metabolic Panel", sub_style))
    elements.append(Spacer(1, 0.4*cm))

    # Patient info table
    dob = datetime.now() - timedelta(days=customer["age"] * 365)
    info_data = [
        ["Patient Name:",  customer["name"],       "Patient ID:",  customer["customer_id"]],
        ["Date of Birth:", dob.strftime("%d %b %Y"), "Gender:",    "Female" if customer["gender"]=="F" else "Male"],
        ["Age:",           f"{customer['age']} years", "Report Date:", datetime.now().strftime("%d %b %Y")],
        ["Condition:",     customer["condition"],   "Lab Ref:",     f"LAB-{random.randint(10000,99999)}"],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("BACKGROUND",(0,0), (-1,-1), colors.HexColor("#f0f4f8")),
        ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f0f4f8"), colors.white]),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.6*cm))

    # Results table
    elements.append(Paragraph("Laboratory Results", h2_style))
    panel = BLOOD_PANELS.get(customer["condition"], BLOOD_PANELS["Healthy"])

    header_row  = [
        Paragraph("<b>Test</b>",            styles["Normal"]),
        Paragraph("<b>Result</b>",          styles["Normal"]),
        Paragraph("<b>Reference Range</b>", styles["Normal"]),
        Paragraph("<b>Status</b>",          styles["Normal"]),
    ]
    rows = [header_row]
    for test, (lo, hi, gen) in panel.items():
        val    = gen()
        status = flag(val, lo, hi)
        color  = (colors.HexColor("#c0392b") if "LOW" in status or "HIGH" in status
                  else colors.HexColor("#27ae60"))
        rows.append([
            test,
            str(val),
            f"{lo} – {hi}",
            Paragraph(f'<font color="{color.hexval()}">{status}</font>', styles["Normal"]),
        ])

    results_table = Table(rows, colWidths=[8*cm, 2.5*cm, 4*cm, 3*cm])
    ts = TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f7f9fc")]),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("ALIGN",       (1,0), (2,-1),  "CENTER"),
    ])
    results_table.setStyle(ts)
    elements.append(results_table)

    # Footer note
    elements.append(Spacer(1, 0.8*cm))
    elements.append(Paragraph(
        "<i>This is a synthetic report generated for development and testing purposes only. "
        "Not for clinical use.</i>",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.grey)
    ))

    doc.build(elements)
    print(f"  [PDF]    {fname.name}")
    return fname


# ─────────────────────────────────────────────
# Wearable CSV generator
# ─────────────────────────────────────────────

WEARABLE_PROFILES = {
    "Healthy":        {"hr": (60, 80),  "steps": (6000, 12000), "spo2": (97, 99), "sleep": (6.5, 8.5)},
    "Hypertension":   {"hr": (75, 100), "steps": (3000, 8000),  "spo2": (94, 98), "sleep": (5.0, 7.0)},
    "Diabetes Type 2":{"hr": (70, 95),  "steps": (2000, 7000),  "spo2": (93, 97), "sleep": (5.5, 7.5)},
    "Anaemia":        {"hr": (85, 110), "steps": (1500, 5000),  "spo2": (90, 95), "sleep": (7.0, 9.5)},
    "Osteoporosis":   {"hr": (60, 85),  "steps": (1000, 4000),  "spo2": (95, 98), "sleep": (6.0, 8.0)},
}


def generate_wearable_csv(customer: dict, out_dir: Path, days: int = 30):
    """Create a 30-day wearable CSV for a customer."""
    profile = WEARABLE_PROFILES.get(customer["condition"], WEARABLE_PROFILES["Healthy"])
    fname   = out_dir / f"Wearable_{customer['customer_id'][:8]}_{datetime.now().strftime('%Y%m%d')}.csv"

    start = datetime.now() - timedelta(days=days)
    rows  = []

    for d in range(days):
        day_dt = start + timedelta(days=d)
        # One reading per hour
        for h in range(24):
            ts  = day_dt.replace(hour=h, minute=random.randint(0, 59))
            hr  = random.randint(*profile["hr"])  + random.randint(-5, 5)
            spo2= round(random.uniform(*profile["spo2"]), 1)
            steps_hour = random.randint(0, profile["steps"][1] // 24)
            temp = round(random.uniform(36.2, 37.4), 1)
            rows.append({
                "timestamp":       ts.strftime("%Y-%m-%d %H:%M:%S"),
                "customer_id":     customer["customer_id"],
                "patient_name":    customer["name"],
                "heart_rate_bpm":  max(40, min(200, hr)),
                "spo2_pct":        max(85, min(100, spo2)),
                "steps":           steps_hour,
                "skin_temp_c":     temp,
                "hrv_ms":          random.randint(20, 80),
                "respiratory_rate":random.randint(12, 20),
                "activity":        random.choice(["resting", "walking", "light_activity", "sleep"]),
            })

    # Daily summary row
    with open(fname, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"  [CSV]    {fname.name}  ({len(rows)} rows)")
    return fname


# ─────────────────────────────────────────────
# Manifest / registry
# ─────────────────────────────────────────────

def write_manifest(base_dir: Path, registry: list):
    manifest_path = base_dir / "customers_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"\n✔  Manifest saved → {manifest_path}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    base_dir = Path("customers")
    base_dir.mkdir(exist_ok=True)

    registry = []

    for cust in CUSTOMERS:
        cust["customer_id"] = make_customer_id(cust["name"])
        paths = create_folder_structure(base_dir, cust["customer_id"])

        print(f"\n{'='*55}")
        print(f"  Customer : {cust['name']}")
        print(f"  ID       : {cust['customer_id']}")
        print(f"  Age      : {cust['age']}  |  Gender: {cust['gender']}  |  Condition: {cust['condition']}")
        print(f"{'='*55}")

        # Generate data files
        dicom_files = generate_dicom(cust, paths["dicom"], n_files=2)
        pdf_file    = generate_blood_report_pdf(cust, paths["blood"])
        csv_file    = generate_wearable_csv(cust, paths["wearables"], days=30)

        registry.append({
            "customer_id":  cust["customer_id"],
            "name":         cust["name"],
            "age":          cust["age"],
            "gender":       cust["gender"],
            "condition":    cust["condition"],
            "signup_date":  datetime.now().strftime("%Y-%m-%d"),
            "folders": {
                "root":      str(paths["root"]),
                "dicom":     str(paths["dicom"]),
                "blood":     str(paths["blood"]),
                "wearables": str(paths["wearables"]),
                "genomics":  str(paths["genomics"]),
            },
            "files": {
                "dicom":    [str(p.name) for p in dicom_files],
                "blood":    [pdf_file.name],
                "wearables":[csv_file.name],
            }
        })

    write_manifest(base_dir, registry)

    print("\n" + "="*55)
    print("  DONE — Folder structure generated:")
    print("="*55)
    for entry in registry:
        print(f"\n  {entry['name']} ({entry['customer_id']})")
        print(f"    ├── DICOM/        {len(entry['files']['dicom'])} file(s)")
        print(f"    ├── BloodReports/ {len(entry['files']['blood'])} file(s)")
        print(f"    ├── Wearables/    {len(entry['files']['wearables'])} file(s)")
        print(f"    └── Genomics/     (placeholder)")


if __name__ == "__main__":
    main()