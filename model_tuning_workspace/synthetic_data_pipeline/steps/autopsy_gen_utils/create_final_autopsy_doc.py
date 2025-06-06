def create_final_autopsy_doc(
        general_desc: str,
        evidence_of_injury: str,
        clothing_list: str,
        conclusive_remarks: str,
        victim_name: str,
        case_number: str,
        date_of_exam: str,
):
    return f"""
State Name
State Medical Examiner’s Office
123 Sesame Street

Voice (123)334-2200 – Fax (012)345-6789

Autopsy report

Name: {victim_name} SME case #{case_number}
Date of examination: {date_of_exam}

{conclusive_remarks}

_______________
Juan Doe, MD
Medical Examiner

____________________

External EXAMINATION

Identification
The body is identified at the time of examination by a Medical Examiner tag bearing the decedent’s name
“{victim_name}” and case number {case_number}. Identification was confirmed through fingerprints
CLOTHING AND PERSONAL EFFECTS
The following articles of clothing and personal effects are on or accompany the body at the time of
examination:
{clothing_list}

{general_desc}

{evidence_of_injury}
""".strip()