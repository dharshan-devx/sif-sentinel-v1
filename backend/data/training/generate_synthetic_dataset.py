"""Generate clearly labelled prototype-only training records; never represents operational data."""
import csv
from pathlib import Path

OUTPUT = Path(__file__).with_name("safety_reports.csv")
POSITIVE = [
    ("Technician started maintenance on the pump before energy isolation was verified.", "Maintenance", "Stored Energy", "Energy Isolation", "FAILED", "not verified", "HIGH", "Energy Isolation"),
    ("Worker entered confined space without gas testing before inspection.", "Confined Space Work", "Toxic Atmosphere", "Gas Testing", "FAILED", "not performed", "HIGH", "Confined Space"),
    ("Worker stood below a suspended load during crane lifting without barricading.", "Lifting", "Suspended Load", "Barricading", "FAILED", "not used", "HIGH", "Line of Fire"),
    ("Welder began hot work with no fire watch and permit expired.", "Hot Work", "Fire", "Fire Watch", "FAILED", "expired", "HIGH", "Hot Work"),
    ("Operator bypassed the rotating equipment interlock during operations.", "Operations", "Moving Machinery", "Authorization", "FAILED", "bypassed", "HIGH", "Bypassing Safety Controls"),
    ("Driver reversed the truck without a spotter in the loading area.", "Driving", "Vehicle Movement", "Spotter", "FAILED", "not used", "MEDIUM", "Driving"),
    ("Worker used ladder at height without fall protection.", "Work at Height", "Fall Hazard", "Fall Protection", "FAILED", "not used", "HIGH", "Working at Height"),
    ("Crew opened pressurized pipeline before lockout tagout was performed.", "Pipeline/Line Work", "Pressure", "Lockout Tagout", "FAILED", "not performed", "HIGH", "Energy Isolation"),
]
NEGATIVE = [
    ("Materials were stored outside the designated area and housekeeping was requested.", "Operations", "", "", "UNKNOWN", "", "NON_SIF", ""),
    ("Maintenance activity occurred near equipment and the supervisor recorded the observation.", "Maintenance", "", "", "UNKNOWN", "", "NON_SIF", ""),
    ("Inspection team completed the checklist and found labels were legible.", "Inspection", "", "PPE", "EFFECTIVE", "", "NON_SIF", ""),
    ("The designated walkway was cleaned after routine material handling.", "Material Handling", "", "", "UNKNOWN", "", "NON_SIF", ""),
    ("Vehicle pre-start inspection was completed before the scheduled drive.", "Driving", "", "Vehicle Controls", "EFFECTIVE", "", "NON_SIF", "Driving"),
    ("Approved lifting plan was reviewed by the competent person before the lift.", "Lifting", "Suspended Load", "Lifting Plan", "EFFECTIVE", "", "LOW", "Safe Mechanical Lifting"),
    ("Gas testing was completed and acceptable before confined space entry.", "Confined Space Work", "Toxic Atmosphere", "Gas Testing", "EFFECTIVE", "", "LOW", "Confined Space"),
    ("Energy isolation was verified and documented before scheduled maintenance.", "Maintenance", "Stored Energy", "Energy Isolation", "EFFECTIVE", "", "LOW", "Energy Isolation"),
]


def main() -> None:
    fields = ["id", "report_type", "report_text", "activity", "hazard", "barrier", "barrier_status", "barrier_failure", "sif_potential", "sif_level", "life_saving_rule", "source_type"]
    rows = []
    for index in range(640):
        source = POSITIVE[index % len(POSITIVE)] if index % 2 == 0 else NEGATIVE[index % len(NEGATIVE)]
        text, activity, hazard, barrier, barrier_status, failure, level, rule = source
        rows.append({"id": f"SYN-{index + 1:04d}", "report_type": "NEAR_MISS" if index % 3 else "UNSAFE_CONDITION", "report_text": f"{text} Prototype record {index + 1}.", "activity": activity, "hazard": hazard, "barrier": barrier, "barrier_status": barrier_status, "barrier_failure": failure, "sif_potential": str(level in {"HIGH", "MEDIUM"}).lower(), "sif_level": level, "life_saving_rule": rule, "source_type": "SYNTHETIC"})
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic prototype records to {OUTPUT}")


if __name__ == "__main__":
    main()
