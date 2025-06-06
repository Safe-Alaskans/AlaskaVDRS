import random
from datetime import timedelta

from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.synthetic_data_pipeline.features.mortality_cause import MortalityCauseFeature
from model_tuning_workspace.synthetic_data_pipeline.features.participants import ParticipantsFeature
from model_tuning_workspace.synthetic_data_pipeline.features.timeline import TimelineFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.pipeline import PipelineStep, PipelineContext
from model_tuning_workspace.utils.yaml_parsing import parse_yaml_response


class GenerateToxicologyReportStep(PipelineStep):

    def __init__(self, syth_data_gen_model: ModelExecutor):
        super().__init__(step_name="generate_toxicology_report")
        self.synth_data_gen_model = syth_data_gen_model

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        participants_ft = context.get_feature("participants", ParticipantsFeature)
        victim = participants_ft.get_victim()
        victim_name = victim.full_name
        victim_dob = victim.age_feature.get_dob().strftime("%Y-%m-%d")

        mortality_cause_ft = context.get_feature("mortality_cause", MortalityCauseFeature)
        cause_of_death_details_str = mortality_cause_ft.build_prompt()

        timeline_ft = context.get_feature("timeline", TimelineFeature)
        case_date = timeline_ft.date_of_incident.get_date_of_case()
        weeks_after_incident_before_report = random.randint(4,9)
        days_after = random.randint(weeks_after_incident_before_report*7, weeks_after_incident_before_report*7+6)
        report_date = case_date + timedelta(days=days_after)
        report_datetime = f"{report_date.strftime('%Y-%m-%d')} {random.randint(7, 18)}:{str(random.randint(0, 59)).zfill(2)}"

        patient_id = _generate_patient_id()

        resp = self.synth_data_gen_model.execute(
            sys_msg=_write_sys_msg(),
            user_input=_write_usr_msg(cause_of_death_details_str)
        )

        parsed_yaml = parse_yaml_response(resp)
        toxicology_report = create_toxicology_report(
            victim_name=victim_name,
            victim_dob=victim_dob,
            patient_id=patient_id,
            report_datetime=report_datetime,
            parsed_yaml=parsed_yaml
        )

        context.set_output(self.step_name, toxicology_report)
        return resp, True


def create_toxicology_report(
    victim_name: str,
    victim_dob: str,
    patient_id: str,
    report_datetime: str,
    parsed_yaml: dict
) -> str:
    # Format specimens section
    specimens_text = ""
    for specimen in parsed_yaml.get('specimens_retrieved', []):
        specimens_text += (
            f"{specimen['id']} {specimen['tube/container']} "
            f"{specimen.get('volume', '')} {specimen['matrix']}\n"
        )

    # Format positive findings section
    positive_findings = parsed_yaml.get('positive_findings', [])
    if positive_findings:
        findings_text = "\n".join([
            f"{finding['compound']} {finding['concentration']} [{finding['matrix']}] - {finding['method']}"
            for finding in positive_findings
        ])
        detailed_findings = positive_findings[0].get('detailed_findings', '')
    else:
        findings_text = "None Detected"
        detailed_findings = ("Examination of the specimen(s) submitted did not reveal any positive findings of "
                           "toxicological significance by procedures outlined in the accompanying Analysis Summary.")

    return f"""
Labs CONFIDENTIAL
123 Sesame Street
Phone: 123-456-7891 Fax: 123-456-7891 e-mail: labs@labs.com

Toxicology Report
Report Issued {report_datetime}

Patient Name: {victim_name}
Patient ID: {patient_id}
DOB: {victim_dob}
Sex: Female
Workorder: {str(random.randint(10000, 99999))}

To: State Medical Examiners Office
Attn: Juan Doe
456 Highway, NY 12345

Page 1 of 2

Positive Findings:
{findings_text}

See Detailed Findings section for additional information

Testing Requested:
Test Test Name
8051TI Postmortem, Basic, Tissue (Forensic)

Specimens Received:
{specimens_text}

All sample volumes/weights are approximations.
Specimens received on {report_datetime[:10]}.

Detailed Findings:
{detailed_findings}

Sample Comments:
001 Physician/Pathologist Name: Juan Doe
003 Tissue specimen required homogenization: 0000-003
004 Labs generated homogenized Tissue sample: 0000-004
Unless alternate arrangements are made by you, the remainder of the submitted specimens will be discarded two (2)
years from the date of this report; and generated data will be discarded five (5) years from the date the analyses were
performed.
Workorder 0000 was electronically signed on
1/32/2024 18:02 by:
John Smith, Ph.D., F-ABFT
Forensic Toxicologist
Analysis Summary and Reporting Limits:
All of the following tests were performed for this case. For each test, the compounds listed were included in the scope. The
Reporting Limit listed for each compound represents the lowest concentration of the compound that will be reported as being
positive. If the compound is listed as None Detected, it is not present above the Reporting Limit. Please refer to the Positive
Findings section of the report for those compounds that were identified as being present.
Test 8051TI - Postmortem, Basic, Tissue (Forensic) - Liver Tissue
-Analysis by Enzyme-Linked Immunosorbent Assay (ELISA) for:
Analyte Rpt. Limit Analyte Rpt. Limit
Amphetamines 80 ng/g
Fentanyl / Acetyl Fentanyl
Barbiturates 0.16 mcg/g
Methadone / Metabolite
Benzodiazepines 400 ng/g Buprenorphine /
Methamphetamine / MDMA
Metabolite 2.0 ng/g Cannabinoids 40 ng/g
Opiates
Cocaine / Metabolites 80 ng/g
Oxycodone / Oxymorphone
Phencyclidine
4.0 ng/g
100 ng/g
80 ng/g
80 ng/g
40 ng/g
40 ng/g
-Analysis by Headspace Gas Chromatography (GC) for:
Analyte Rpt. Limit Analyte Rpt. Limit
Acetone 20 mg/100 g
Ethanol 80 mg/100 g
Isopropanol
Methanol
20 mg/100 g
40 mg/100 g
Digital data review may have taken place remotely by qualified staff utilizing a secure VPN connection for some or all of the reported results. This is in accordance with and
follows CLIA regulations.
v.27.0
""".strip()

def _write_sys_msg():
    return """
# Context
You are a forensic Toxicologist and you are being provided some details of a new case by the user.

# Your task
Your task is to provide 3 separate pieces of information:
- Specimens retrieved
- Positive findings

## Specimens retrieved
You should provide a concise list of the specimens you expect to receive for testing.

## Positive findings
If any of the specimens test positive for any substances, you should list them.

## Detailed findings
If any of the specimens test positive, you should provide a detailed explanation of the findings.

# Output format
The output should be in the below YAML format. You will provide just the yaml, with no additional text before or after.
```yaml
specimens_retrieved:
  - id: {increment from 001}
    - tube/container: {type of tube or container}
    - volume: {volume of specimen}
    - matrix: {type of matrix}
  - ...
  
positive_findings:
  - id: {increment from 1}
    - compound: {name of compound}
    - concentration: {concentration of compound}
    - matrix: {type of matrix tested}
    - method: {shorthand method of testing. e.g. LC-MS/MS}
    - detailed_findings: {standard explanation of findings - this will be a long string with new lines and will be added at the end of the report}
  - ...

# Reporting limits
The below text will be added  at the end of the report later on to provide the reporting limits for each compound tested. No need to include it in your output.
\"Analysis Summary and Reporting Limits:
All of the following tests were performed for this case. For each test, the compounds listed were included in the scope. The
Reporting Limit listed for each compound represents the lowest concentration of the compound that will be reported as being
positive. If the compound is listed as None Detected, it is not present above the Reporting Limit. 
Test 8051TI - Postmortem, Basic, Tissue (Forensic) - Liver Tissue
-Analysis by Enzyme-Linked Immunosorbent Assay (ELISA) for:
Analyte Rpt. Limit Analyte Rpt. Limit
Amphetamines 80 ng/g
Fentanyl / Acetyl Fentanyl
Barbiturates 0.16 mcg/g
Methadone / Metabolite
Benzodiazepines 400 ng/g Buprenorphine /
Methamphetamine / MDMA
Metabolite 2.0 ng/g Cannabinoids 40 ng/g
Opiates
Cocaine / Metabolites 80 ng/g
Oxycodone / Oxymorphone
Phencyclidine
4.0 ng/g
100 ng/g
80 ng/g
80 ng/g
40 ng/g
40 ng/g
-Analysis by Headspace Gas Chromatography (GC) for:
Analyte Rpt. Limit Analyte Rpt. Limit
Acetone 20 mg/100 g
Ethanol 80 mg/100 g
Isopropanol
Methanol
20 mg/100 g
40 mg/100 g\"
""".strip()


def _write_usr_msg(
        cause_of_death_details_str: str,
) -> str:
    return (
        f"# Details of case:\n"
        f"{cause_of_death_details_str}\n\n"
    )


def _generate_patient_id():
    id_prefix = str(random.randint(1, 9999)).zfill(4)
    id_num = str(random.randint(0, 99999)).zfill(5)
    return f"{id_prefix}-{id_num}"