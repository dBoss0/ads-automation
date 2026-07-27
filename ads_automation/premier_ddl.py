"""
Premier PHD Data Dictionary V2.2 (Feb 2024) — authoritative schema reference.
Source: PINC AI Healthcare Database PHD Data Dictionary V2.2 (02-15-2024)

Catalog : rhealth_premier_phd
Schema  : bronze_native_premier_phd

IMPORTANT — PATDEMO naming:
  PHD documentation refers to the main patient table as "PATDEMO".
  The actual Databricks table is named `pat` (not `patdemo`).
  All SQL must use `pat`. Other table names match their doc names (lowercase).

PHD doc name → actual Databricks table name:
  PATDEMO      → pat
  PATAPRDRG    → pataprdrg
  PATBILL      → patbill
  PATCPT       → patcpt
  PATICD_DIAG  → paticd_diag
  PATICD_PROC  → paticd_proc
  Lookup/Add-on tables → lowercase of doc name
"""

from typing import List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# Full PHD data dictionary — one dict per field
# Keys: table_name (actual Databricks name, lowercase), field_name, data_type,
#       description, valid_values, table_category, is_join_key
# ─────────────────────────────────────────────────────────────────────────────

PHD_DICTIONARY: List[Dict] = [

    # ── PAT (PHD doc name: PATDEMO) ───────────────────────────────────────────
    {"table_name":"pat","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier (de-identified). PHD doc: PATDEMO.","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"pat","field_name":"medrec_key","data_type":"Integer","description":"Unique patient identifier (de-identified); tracks patient across encounters at same hospital","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"pat","field_name":"admit_date","data_type":"Date","description":"Admission date","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"discharge_date","data_type":"Date","description":"Discharge date","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"disc_mon","data_type":"Integer","description":"Discharge month formatted YYYYQMM (Q=calendar quarter). Use to link with PROV_ENROLLMENT.","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"pat","field_name":"prov_id","data_type":"Integer","description":"Hospital entity ID (de-identified)","valid_values":"See PROVIDERS","table_category":"patient_table","is_join_key":True},
    {"table_name":"pat","field_name":"i_o_ind","data_type":"Char(1)","description":"Inpatient/Outpatient indicator","valid_values":"I=Inpatient|O=Outpatient","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"pat_type","data_type":"Char(2)","description":"Premier mapped field for service type of hospital encounter","valid_values":"08=Inpatient|10=Skilled Nursing|22=Long Term Care|23=Rehabilitation|24=Psychiatric|25=Hospice|26=Chemical Dependency|27=Same Day Surgery|28=Emergency|29=Observation|30=Diagnostic Testing|31=Recurring/Series|32=Pre-Surgical Testing|33=Home Health|34=Clinic|35=Organ Donor|90=Other","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"ms_drg","data_type":"Smallint","description":"Medicare Severity Diagnosis-Related Group. Inpatient encounters only. Effective 10/1/2007.","valid_values":"See MSDRG","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"ms_drg_mdc","data_type":"Char(7)","description":"Major Diagnostic Category — broad classification by body system","valid_values":"See MSDRGMDC","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"point_of_origin","data_type":"Char(2)","description":"UB-04 Point of Origin (formerly Source of Admission)","valid_values":"See POORIGIN","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"adm_type","data_type":"Smallint","description":"UB-04 Admission type code","valid_values":"1=Emergency|2=Urgent|3=Elective|4=Newborn|5=Trauma Center|9=Unknown","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"disc_status","data_type":"Smallint","description":"UB-04 Discharge status code","valid_values":"1=Home|2=Transferred|3=SNF|20=Expired|7=Left AMA|30=Still patient|50=Hospice home|See DISSTAT","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"mart_status","data_type":"Char(1)","description":"UB-04 Marital Status","valid_values":"M=Married|S=Single|O=Other|U=Unknown","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"age","data_type":"Smallint","description":"Patient age in years (admission date minus DOB). Age 90+ capped at 89 per HIPAA.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"gender","data_type":"Char(1)","description":"UB-04 Gender designation","valid_values":"M=Male|F=Female|U=Unknown","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"race","data_type":"Char(1)","description":"UB-04 Race designation","valid_values":"W=White|B=Black|H=Hispanic|A=Asian|O=Other|U=Unknown","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"hispanic_ind","data_type":"Char(1)","description":"Hispanic indicator from UB-04 Ethnicity","valid_values":"Y=Yes|N=No|U=Unknown","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"admphy_spec","data_type":"Smallint","description":"Admitting physician specialty code. Value 900 when not provided.","valid_values":"See PHYSPEC","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"adm_phy","data_type":"Integer","description":"Admitting physician ID (de-identified). Use with prov_id for unique physician.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"attphy_spec","data_type":"Smallint","description":"Attending physician specialty code. Value 900 when not provided.","valid_values":"See PHYSPEC","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"att_phy","data_type":"Integer","description":"Attending physician ID (de-identified). Use with prov_id for unique physician.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"std_payor","data_type":"Smallint","description":"Premier standard payer categories","valid_values":"300=Medicare Traditional|310=Medicare MGD Cap|320=Medicare MGD Non-Cap|330=Medicaid Traditional|340=Medicaid MGD Cap|350=Medicaid MGD Non-Cap|360=Managed Care Non-Cap|370=Managed Care Cap|380=Commercial Indemnity|390=Charity|400=Indigent|410=Self Pay|420=Workers Comp|430=Direct Employer|440=Other Gov|900=Other","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"los","data_type":"Smallint","description":"Hospital submitted length of stay. Inpatient encounters only.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"pat_charges","data_type":"Decimal(12,2)","description":"Total charge amount of billed items during the hospital encounter","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"pat_cost","data_type":"Decimal(12,2)","description":"Total cost to treat the patient. Total Cost = Variable Cost + Fixed Cost.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"pat_fix_cost","data_type":"Decimal(12,2)","description":"Total fixed cost — depreciation, overhead, management","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"pat_var_cost","data_type":"Decimal(12,2)","description":"Total variable cost — supplies, hands-on care","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"pat","field_name":"publish_type","data_type":"Char(2)","description":"Data validation tier. CP = passed all checks incl. financial reconciliation. CV = passed validity checks only.","valid_values":"CP=Comparative Publish|CV=Comparative Valid","table_category":"patient_table","is_join_key":False},

    # ── PATAPRDRG ─────────────────────────────────────────────────────────────
    {"table_name":"pataprdrg","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier (de-identified)","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"pataprdrg","field_name":"medrec_key","data_type":"Integer","description":"Unique patient identifier (de-identified)","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"pataprdrg","field_name":"apr_drg","data_type":"Smallint","description":"3M APR-DRG grouper. Inpatient encounters only. Additional license required.","valid_values":"See APRDRG","table_category":"patient_table","is_join_key":False},
    {"table_name":"pataprdrg","field_name":"apr_sev","data_type":"Smallint","description":"3M APR-DRG Severity of Illness. Inpatient only.","valid_values":"0=Not assigned|1=Minor|2=Moderate|3=Major|4=Extreme","table_category":"patient_table","is_join_key":False},
    {"table_name":"pataprdrg","field_name":"apr_mort","data_type":"Smallint","description":"3M APR-DRG Risk of Mortality. Inpatient only.","valid_values":"0=Not assigned|1=Minor|2=Moderate|3=Major|4=Extreme","table_category":"patient_table","is_join_key":False},

    # ── PATBILL ───────────────────────────────────────────────────────────────
    {"table_name":"patbill","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier (de-identified)","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"patbill","field_name":"std_chg_code","data_type":"Char(15)","description":"Premier Standard Charge Master code","valid_values":"See CHGMSTR","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"hosp_chg_id","data_type":"Integer","description":"Unique hospital charge item identifier (de-identified)","valid_values":"See HOSPCHG","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"serv_date","data_type":"Date","description":"Date for each charge item. Dates before admit_date can represent pre-admission services.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"hosp_qty","data_type":"Decimal(12,2)","description":"Hospital submitted quantity for charge item","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"std_qty","data_type":"Decimal(18,8)","description":"Standard quantity for charge item","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"bill_charges","data_type":"Decimal(12,2)","description":"Total charged amount for charge item","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"bill_cost","data_type":"Decimal(12,2)","description":"Total cost for charge item. Total = Variable + Fixed.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"bill_var_cost","data_type":"Decimal(12,2)","description":"Variable cost for charge item","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patbill","field_name":"bill_fix_cost","data_type":"Decimal(12,2)","description":"Fixed cost for charge item","valid_values":"","table_category":"patient_table","is_join_key":False},

    # ── PATCPT ────────────────────────────────────────────────────────────────
    {"table_name":"patcpt","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier (de-identified)","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"patcpt","field_name":"cpt_code","data_type":"Char(7)","description":"CPT or HCPCS code. Hospitals not required to submit; some submit only select CPT codes.","valid_values":"See CPTCODE","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_pos","data_type":"Smallint","description":"CPT position (order received from hospital). Used to distinguish same CPT submitted twice.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"proc_date","data_type":"Date","description":"Date procedure was performed. Can be null. Available for discharge dates on/after 7-1-2012.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_order_phy","data_type":"Integer","description":"CPT Order Physician ID (de-identified). Available for discharge dates on/after 7-1-2012.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_order_phy_spec","data_type":"Smallint","description":"CPT order physician specialty code. Value 900 when not provided.","valid_values":"See PHYSPEC","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_proc_phy","data_type":"Integer","description":"CPT Procedure Physician ID (de-identified). Available for discharge dates on/after 7-1-2012.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_proc_phy_spec","data_type":"Smallint","description":"CPT procedure physician specialty code. Value 900 when not provided.","valid_values":"See PHYSPEC","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_mod_code_1","data_type":"Char(2)","description":"CPT Modifier Code 1","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_mod_code_2","data_type":"Char(2)","description":"CPT Modifier Code 2","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_mod_code_3","data_type":"Char(2)","description":"CPT Modifier Code 3","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"patcpt","field_name":"cpt_mod_code_4","data_type":"Char(2)","description":"CPT Modifier Code 4","valid_values":"","table_category":"patient_table","is_join_key":False},

    # ── PATICD_DIAG ───────────────────────────────────────────────────────────
    {"table_name":"paticd_diag","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier (de-identified)","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"paticd_diag","field_name":"icd_version","data_type":"Smallint","description":"ICD code set: ICD-9 for discharges prior to 10/1/2015; ICD-10 on/after.","valid_values":"9|10","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_diag","field_name":"icd_code","data_type":"Char(10)","description":"ICD-9 or ICD-10 diagnosis code. Use icd_version to differentiate (some codes overlap).","valid_values":"See ICDCODE","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_diag","field_name":"icd_pri_sec","data_type":"Char(1)","description":"Indicates whether ICD diagnosis is Admitting, Principal, or Secondary","valid_values":"A=Admitting|P=Principal|S=Secondary","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_diag","field_name":"icd_poa","data_type":"Char(1)","description":"Present on Admission flag","valid_values":"Y=Present|N=Not present|U=Unknown|W=Undetermined|E=Exempt|P=Procedure|1=Exempt|9=No code","table_category":"patient_table","is_join_key":False},

    # ── PATICD_PROC ───────────────────────────────────────────────────────────
    {"table_name":"paticd_proc","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier (de-identified)","valid_values":"","table_category":"patient_table","is_join_key":True},
    {"table_name":"paticd_proc","field_name":"icd_version","data_type":"Smallint","description":"ICD code set: ICD-9 for discharges prior to 10/1/2015; ICD-10 on/after.","valid_values":"9|10","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_proc","field_name":"icd_code","data_type":"Char(10)","description":"ICD-9 or ICD-10 procedure code. Use icd_version to differentiate.","valid_values":"See ICDCODE","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_proc","field_name":"icd_pri_sec","data_type":"Char(1)","description":"Indicates whether ICD procedure is Principal or Secondary","valid_values":"P=Principal|S=Secondary","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_proc","field_name":"proc_date","data_type":"Date","description":"Date procedure was performed. Field can be null.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_proc","field_name":"proc_phy","data_type":"Integer","description":"Procedure physician ID (de-identified). Use with prov_id for unique physician.","valid_values":"","table_category":"patient_table","is_join_key":False},
    {"table_name":"paticd_proc","field_name":"procphy_spec","data_type":"Smallint","description":"Procedure physician specialty code. Value 900 when not provided.","valid_values":"See PHYSPEC","table_category":"patient_table","is_join_key":False},

    # ── LAB_RES ───────────────────────────────────────────────────────────────
    {"table_name":"lab_res","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier. Microbiology lab results add-on table.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"lab_res","field_name":"specimen_key","data_type":"Integer","description":"Specimen identifier","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"collection_datetime","data_type":"Timestamp","description":"Collection date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"specimen_source_code","data_type":"Char(25)","description":"SNOMED specimen source code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"specimen_source_desc","data_type":"Char(150)","description":"Specimen source description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"body_site_category_code","data_type":"Char(25)","description":"SNOMED body site category code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"body_site_category_desc","data_type":"Char(150)","description":"Body site category description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"lab_test_code","data_type":"Char(25)","description":"Lab test code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"lab_test_desc","data_type":"Char(175)","description":"Lab test description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"lab_test_code_type","data_type":"Char(20)","description":"Lab test code type","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"lab_test_result_datetime","data_type":"Timestamp","description":"Result date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"observation","data_type":"Char(150)","description":"Observation notes","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_res","field_name":"data_source_ind","data_type":"Smallint","description":"Source indicator","valid_values":"3=Retired source|4=Current source","table_category":"addon_table","is_join_key":False},

    # ── LAB_SENS ──────────────────────────────────────────────────────────────
    {"table_name":"lab_sens","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier. Lab sensitivity results add-on table.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"lab_sens","field_name":"specimen_key","data_type":"Integer","description":"Specimen identifier","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"collection_datetime","data_type":"Timestamp","description":"Collection date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"result_organism","data_type":"Char(100)","description":"Organism identified","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"susc_test_method_code","data_type":"Char(25)","description":"Susceptibility test method code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"susc_test_method_desc","data_type":"Char(150)","description":"Test method description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"susc_test_method_code_type","data_type":"Char(20)","description":"Code type","valid_values":"null|LOINC|NON-STANDARD","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"medication","data_type":"Char(100)","description":"Medication tested for susceptibility","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"susc_test_result_datetime","data_type":"Timestamp","description":"Result date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"susc_test_result","data_type":"Char(50)","description":"Test result value","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"interpretation","data_type":"Char(50)","description":"Interpretation of result","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"lab_sens","field_name":"data_source_ind","data_type":"Smallint","description":"Source indicator","valid_values":"3=Retired|4=Current","table_category":"addon_table","is_join_key":False},

    # ── GEN_LAB (PHD doc: GENLAB) ─────────────────────────────────────────────
    {"table_name":"gen_lab","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier. General lab results add-on table.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"gen_lab","field_name":"order_key","data_type":"Char(25)","description":"Lab order identifier","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"collection_datetime","data_type":"Timestamp","description":"Collection date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"specimen_source_code","data_type":"Char(20)","description":"SNOMED specimen source code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"specimen_source_desc","data_type":"Char(100)","description":"Specimen source description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_code","data_type":"Char(25)","description":"Lab test code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_desc","data_type":"Char(200)","description":"Lab test description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_code_type","data_type":"Char(20)","description":"Lab test code type","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_result_datetime","data_type":"Timestamp","description":"Result date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_result","data_type":"Char(4000)","description":"Lab result value","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_result_unit","data_type":"Char(225)","description":"Result unit of measure","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"lab_test_result_status","data_type":"Char(25)","description":"Result status","valid_values":"C=Corrected|F=Final","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"reference_interval","data_type":"Char(225)","description":"Normal reference range","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"numeric_value_operator","data_type":"Char(10)","description":"Numeric comparison operator (>, <, =)","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"numeric_value","data_type":"Decimal(38,8)","description":"Numeric result value","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"gen_lab","field_name":"abnormal_flag","data_type":"Char(50)","description":"Abnormal indicator","valid_values":"","table_category":"addon_table","is_join_key":False},

    # ── VITALS ────────────────────────────────────────────────────────────────
    {"table_name":"vitals","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier. Vitals data add-on table.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"vitals","field_name":"facility_test_name","data_type":"Char(150)","description":"Facility-specific test/vital name","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"observation_datetime","data_type":"Timestamp","description":"Observation date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"result_datetime","data_type":"Timestamp","description":"Result date and time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"lab_test_code","data_type":"Char(25)","description":"Lab/vital test code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"lab_test_desc","data_type":"Char(125)","description":"Test description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"lab_test_code_type","data_type":"Char(20)","description":"Code type","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"lab_test_result","data_type":"Char(350)","description":"Result value","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"lab_test_result_unit","data_type":"Char(75)","description":"Result unit of measure","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"lab_test_result_status","data_type":"Char(25)","description":"Result status","valid_values":"C=Corrected|F=Final|I=In Lab|O=Order Received|P=Preliminary|R=Results Entered|U=Final|X=No Results","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"numeric_value_operator","data_type":"Char(10)","description":"Numeric comparison operator","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"numeric_value","data_type":"Decimal(28,6)","description":"Numeric vital value","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"vitals","field_name":"abnormal_flag","data_type":"Char(25)","description":"Abnormal indicator","valid_values":"Normal|Low|High","table_category":"addon_table","is_join_key":False},

    # ── MOTHER_INFANT_LINK ────────────────────────────────────────────────────
    {"table_name":"mother_infant_link","field_name":"infant_pat_key","data_type":"Integer","description":"Infant encounter ID. Links birth records to mother delivery records.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"mother_infant_link","field_name":"mother_pat_key","data_type":"Integer","description":"Mother encounter ID (de-identified)","valid_values":"","table_category":"addon_table","is_join_key":True},

    # ── MORTALITY ─────────────────────────────────────────────────────────────
    {"table_name":"mortality","field_name":"medrec_key","data_type":"Integer","description":"Unique patient identifier. Table is patient-level (not encounter-level). Additional license required.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"mortality","field_name":"death_date","data_type":"Date","description":"Date patient expired. Null = matched but no death found — include nulls in denominator for survival analysis. Latency ~30 days.","valid_values":"","table_category":"addon_table","is_join_key":False},

    # ── PAT_SDOH ──────────────────────────────────────────────────────────────
    {"table_name":"pat_sdoh","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier. SDOH at ZIP/County level. Additional license required.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"pat_sdoh","field_name":"acs_avg_hh_size_ctgy","data_type":"Char(10)","description":"Avg household size category [AHRQ SDOH/ACS ZCTA]. Available from 2011.","valid_values":"1.0-1.9|2.0-2.4|2.5-2.9|3.0-3.9|>=4","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"acs_gini_index_ctgy","data_type":"Char(15)","description":"Income inequality Gini index, categorized [AHRQ SDOH/ACS ZCTA]","valid_values":"0.00-0.19|0.20-0.29|0.30-0.39|0.40-0.49|0.50-0.59|>=0.60","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"acs_median_hh_income_ctgy","data_type":"Char(15)","description":"Median household income category [AHRQ SDOH/ACS ZCTA]","valid_values":"0-15000|15001-25000|25001-35000|35001-50000|50001-75000|75001-100000|100001-150000|150001-200000|>200000","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"acs_education_wgt_ctgy","data_type":"Char(10)","description":"Weighted education score (10=<HS, 12=HS, 14=some college, 16=bachelor, 18.5=grad)","valid_values":"10.0-10.9|11.0-11.9|12.0-12.9|13.0-13.9|14.0-14.9|15.0-15.9|16.0-16.9|17.0-18.5","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"svi_rpl_theme1_socioeco_ctgy","data_type":"Char(10)","description":"Socioeconomic status percentile rank [CDC/ATSDR SVI]. Available from 2010.","valid_values":"0-10%|11-20%|21-30%|31-40%|41-50%|51-60%|61-70%|71-80%|81-90%|91-100%","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"svi_rpl_theme2_hh_dsb_ctgy","data_type":"Char(10)","description":"Household characteristics and disability percentile rank [CDC/ATSDR SVI]","valid_values":"0-10%|11-20%|21-30%|31-40%|41-50%|51-60%|61-70%|71-80%|81-90%|91-100%","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"svi_rpl_theme3_mino_ctgy","data_type":"Char(10)","description":"Minority status percentile rank [CDC/ATSDR SVI]","valid_values":"0-10%|11-20%|21-30%|31-40%|41-50%|51-60%|61-70%|71-80%|81-90%|91-100%","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"svi_rpl_theme4_hh_trans_ctgy","data_type":"Char(10)","description":"Housing type and transportation percentile rank [CDC/ATSDR SVI]","valid_values":"0-10%|11-20%|21-30%|31-40%|41-50%|51-60%|61-70%|71-80%|81-90%|91-100%","table_category":"addon_table","is_join_key":False},
    {"table_name":"pat_sdoh","field_name":"svi_rpl_themes_all_ctgy","data_type":"Char(10)","description":"Overall SVI percentile rank [CDC/ATSDR SVI]","valid_values":"0-10%|11-20%|21-30%|31-40%|41-50%|51-60%|61-70%|71-80%|81-90%|91-100%","table_category":"addon_table","is_join_key":False},

    # ── PROC_SUPPLY ───────────────────────────────────────────────────────────
    {"table_name":"proc_supply","field_name":"pat_key","data_type":"Integer","description":"Unique hospital encounter identifier. Devices and supplies used in procedures. Additional license required.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"proc_supply","field_name":"procedure_key","data_type":"Integer","description":"Procedure identifier","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"scheduled_proc_date","data_type":"Date","description":"Scheduled procedure date","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"procedure_location","data_type":"Char(10)","description":"Location where procedure performed","valid_values":"OR|EP|CATHLAB|OTHER","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"procedure_desc","data_type":"Char(750)","description":"Procedure description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"proc_long_desc","data_type":"Char(2500)","description":"Long procedure description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"proc_phy_key","data_type":"Integer","description":"Procedure physician ID (de-identified)","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"wheels_in_datetime","data_type":"Timestamp","description":"Time patient entered OR","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"wheels_out_datetime","data_type":"Timestamp","description":"Time patient exited OR","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"proc_start_datetime","data_type":"Timestamp","description":"Procedure start time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"proc_stop_datetime","data_type":"Timestamp","description":"Procedure end time","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"asa_score","data_type":"Char(3)","description":"ASA physical status classification (1=Healthy to 5E=Emergency critical, 6=Brain dead)","valid_values":"1|2|3|4|5|6|1E|2E|3E|4E|5E","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"top_parent_vendor_name","data_type":"Char(75)","description":"Manufacturer/vendor name","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"mfg_catalog_number","data_type":"Char(75)","description":"Manufacturer catalog number","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"product_desc","data_type":"Char(4000)","description":"Product description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"contract_category","data_type":"Char(100)","description":"Contract category","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"unspsc_commodity_code","data_type":"Char(10)","description":"UNSPSC commodity code","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"unspsc_commodity_desc","data_type":"Char(150)","description":"UNSPSC commodity description","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"used_qty","data_type":"Integer","description":"Quantity of supply used","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"wasted_qty","data_type":"Integer","description":"Quantity of supply wasted","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"proc_supply","field_name":"implantable_ind","data_type":"Smallint","description":"Implantable device indicator","valid_values":"0=No|1=Yes","table_category":"addon_table","is_join_key":False},

    # ── TOKENS ────────────────────────────────────────────────────────────────
    {"table_name":"tokens","field_name":"medrec_key","data_type":"Integer","description":"Unique patient identifier. Datavant tokens for patient matching across datasets.","valid_values":"","table_category":"addon_table","is_join_key":True},
    {"table_name":"tokens","field_name":"token1","data_type":"Char(50)","description":"Datavant Token 1","valid_values":"","table_category":"addon_table","is_join_key":False},
    {"table_name":"tokens","field_name":"token2","data_type":"Char(50)","description":"Datavant Token 2","valid_values":"","table_category":"addon_table","is_join_key":False},

    # ── ADMTYPE ───────────────────────────────────────────────────────────────
    {"table_name":"admtype","field_name":"adm_type","data_type":"Smallint","description":"UB-04 Admission type code. Decode for pat.adm_type.","valid_values":"1=Emergency|2=Urgent|3=Elective|4=Newborn|5=Trauma Center|9=Information not available","table_category":"lookup_table","is_join_key":True},
    {"table_name":"admtype","field_name":"adm_type_desc","data_type":"Char(40)","description":"UB-04 Admission type description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── APRDRG ────────────────────────────────────────────────────────────────
    {"table_name":"aprdrg","field_name":"apr_drg","data_type":"Smallint","description":"3M APR-DRG grouper code. Additional licensing fee applies.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"aprdrg","field_name":"apr_drg_desc","data_type":"Char(40)","description":"APR-DRG description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── CHGMSTR ───────────────────────────────────────────────────────────────
    {"table_name":"chgmstr","field_name":"std_chg_code","data_type":"Char(15)","description":"Premier Standard Charge Master code. Decode for patbill.std_chg_code.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"chgmstr","field_name":"std_chg_desc","data_type":"Char(50)","description":"Standard charge description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"clin_dtl_code","data_type":"Integer","description":"Clinical detail code","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"clin_dtl_desc","data_type":"Char(50)","description":"Clinical detail description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"clin_sum_code","data_type":"Char(15)","description":"Clinical summary code","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"clin_sum_desc","data_type":"Char(50)","description":"Clinical summary description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"std_dept_code","data_type":"Smallint","description":"Standard department code","valid_values":"250=Pharmacy","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"std_dept_desc","data_type":"Char(40)","description":"Standard department description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"sum_dept_desc","data_type":"Char(30)","description":"Summary department description (higher aggregation)","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_cat_code","data_type":"Char(15)","description":"Product category code. Populated only for Dept Code 250 (Pharmacy); else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_cat_desc","data_type":"Char(60)","description":"Product category description. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_class_code","data_type":"Char(15)","description":"Product class code. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_class_desc","data_type":"Char(60)","description":"Product class description. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_name_code","data_type":"Char(15)","description":"Product name code. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_name_desc","data_type":"Char(60)","description":"Product name description. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_name_meth_code","data_type":"Char(15)","description":"Product name + method code. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"chgmstr","field_name":"prod_name_meth_desc","data_type":"Char(60)","description":"Product name + method description. Populated only for Dept 250; else Unknown.","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── CPTCODE ───────────────────────────────────────────────────────────────
    {"table_name":"cptcode","field_name":"cpt_code","data_type":"Char(7)","description":"CPT or HCPCS code. Decode for patcpt.cpt_code.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"cptcode","field_name":"cpt_desc","data_type":"Char(40)","description":"CPT or HCPCS description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── DISSTAT ───────────────────────────────────────────────────────────────
    {"table_name":"disstat","field_name":"disc_status","data_type":"Smallint","description":"UB-04 Discharge status code. Decode for pat.disc_status.","valid_values":"1=Home|2=Transferred|3=SNF|4=ICF|5=Cancer/children hosp|6=Home health|7=Left AMA|9=Admitted inpatient|20=Expired|21=Court/law|30=Still patient|40=Expired home|41=Expired facility|42=Expired unknown|43=Federal hosp|50=Hospice home|51=Hospice facility|61=Swing bed|62=Rehab|63=LTCH|64=Nursing Medicaid|65=Psychiatric|66=CAH|69=Disaster|70=Other institution|71=Other OPS|72=Same institution OPS|81=Planned readmit|99=Unknown","table_category":"lookup_table","is_join_key":True},
    {"table_name":"disstat","field_name":"disc_status_desc","data_type":"Char(40)","description":"UB-04 Discharge status description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── HOSPCHG ───────────────────────────────────────────────────────────────
    {"table_name":"hospchg","field_name":"hosp_chg_id","data_type":"Integer","description":"Unique hospital charge identifier (de-identified). Decode for patbill.hosp_chg_id.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"hospchg","field_name":"hosp_chg_desc","data_type":"Char(60)","description":"Hospital billing description for this charge item","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── ICDCODE ───────────────────────────────────────────────────────────────
    {"table_name":"icdcode","field_name":"icd_version","data_type":"Smallint","description":"ICD code set indicator. Always JOIN on both icd_version AND icd_code.","valid_values":"9|10","table_category":"lookup_table","is_join_key":True},
    {"table_name":"icdcode","field_name":"icd_code","data_type":"Char(10)","description":"ICD-9 or ICD-10 diagnosis or procedure code","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"icdcode","field_name":"icd_desc","data_type":"Char(40)","description":"ICD diagnosis or procedure description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"icdcode","field_name":"ccs_cat_level1_code","data_type":"Char(10)","description":"AHRQ HCUP CCS category code: Level 1","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"icdcode","field_name":"ccs_cat_level1_desc","data_type":"Char(150)","description":"CCS Level 1 description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"icdcode","field_name":"ccs_cat_level2_code","data_type":"Char(10)","description":"CCS category code: Level 2","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"icdcode","field_name":"ccs_cat_level2_desc","data_type":"Char(150)","description":"CCS Level 2 description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"icdcode","field_name":"icd_diag_proc","data_type":"Char(1)","description":"D=Diagnosis (join paticd_diag), P=Procedure (join paticd_proc)","valid_values":"D=Diagnosis|P=Procedure","table_category":"lookup_table","is_join_key":False},

    # ── ICDPOA ────────────────────────────────────────────────────────────────
    {"table_name":"icdpoa","field_name":"icd_poa","data_type":"Char(1)","description":"Present on Admission flag. Decode for paticd_diag.icd_poa.","valid_values":"1=Exempt|9=No code|E=Exempt|N=Not present|P=Procedure|U=Unknown|W=Undetermined|Y=Present","table_category":"lookup_table","is_join_key":True},
    {"table_name":"icdpoa","field_name":"icd_poa_desc","data_type":"Char(40)","description":"Present on Admission description","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"icdpoa","field_name":"icd_poa_sum_desc","data_type":"Char(10)","description":"Present on Admission summary","valid_values":"Yes|No|Exempt","table_category":"lookup_table","is_join_key":False},

    # ── MSDRG ─────────────────────────────────────────────────────────────────
    {"table_name":"msdrg","field_name":"ms_drg","data_type":"Smallint","description":"Medicare Severity Diagnosis Related Group code. Decode for pat.ms_drg.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"msdrg","field_name":"ms_drg_desc","data_type":"Char(40)","description":"MS-DRG description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── MSDRGMDC ──────────────────────────────────────────────────────────────
    {"table_name":"msdrgmdc","field_name":"ms_drg_mdc","data_type":"Char(7)","description":"Major Diagnostic Category code. Decode for pat.ms_drg_mdc.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"msdrgmdc","field_name":"ms_drg_mdc_desc","data_type":"Char(40)","description":"MDC description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── PATTYPE ───────────────────────────────────────────────────────────────
    {"table_name":"pattype","field_name":"pat_type","data_type":"Char(2)","description":"Premier standard patient type code. Decode for pat.pat_type.","valid_values":"08=Inpatient|10=Skilled Nursing|22=Long Term Care|23=Rehabilitation|24=Psychiatric|25=Hospice|26=Chemical Dependency|27=Same Day Surgery|28=Emergency|29=Observation|30=Diagnostic Testing|31=Recurring/Series|32=Pre-Surgical Testing|33=Home Health|34=Clinic|35=Organ Donor|90=Other","table_category":"lookup_table","is_join_key":True},
    {"table_name":"pattype","field_name":"pat_type_desc","data_type":"Char(40)","description":"Patient type description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── PAYOR ─────────────────────────────────────────────────────────────────
    {"table_name":"payor","field_name":"std_payor","data_type":"Smallint","description":"Premier standard payer code. Decode for pat.std_payor.","valid_values":"300=Medicare Traditional|310=Medicare MGD Cap|320=Medicare MGD Non-Cap|330=Medicaid Traditional|340=Medicaid MGD Cap|350=Medicaid MGD Non-Cap|360=Managed Care Non-Cap|370=Managed Care Cap|380=Commercial Indemnity|390=Charity|400=Indigent|410=Self Pay|420=Workers Comp|430=Direct Employer|440=Other Gov|900=Other","table_category":"lookup_table","is_join_key":True},
    {"table_name":"payor","field_name":"std_payor_desc","data_type":"Char(40)","description":"Payer description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── PHYSPEC ───────────────────────────────────────────────────────────────
    {"table_name":"physpec","field_name":"phy_spec","data_type":"Smallint","description":"Standard physician specialty code. Value 900 = Unknown/Not provided. Decode for admphy_spec, attphy_spec, procphy_spec, cpt_order_phy_spec.","valid_values":"4001=Abdominal Surgery|4002=Addiction Medicine|4004=Allergy & Immunology|4008=Anesthesiology|4011=Cardiovascular Diseases|4012=Cardiovascular Surgery|4023=Critical Care Medicine|4025=Dermatology|4028=Emergency Medicine|4033=Gastroenterology|4040=Gynecology|4043=Hematology|4050=Internal Medicine|4058=Neurology|4067=Obstetrics/Gynecology|4070=Orthopedic Surgery|4096=Physical Medicine & Rehabilitation|4098=Plastic Surgery|4100=Psychiatry|4104=Pulmonary Disease|4105=Radiation Oncology|4109=Rheumatology|4115=Thoracic Surgery|4117=Trauma Surgery|4119=Urology|4121=Vascular Surgery|900=Unknown","table_category":"lookup_table","is_join_key":True},
    {"table_name":"physpec","field_name":"phy_spec_desc","data_type":"Char(40)","description":"Physician specialty description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── POORIGIN ──────────────────────────────────────────────────────────────
    {"table_name":"poorigin","field_name":"point_of_origin","data_type":"Char(2)","description":"UB-04 Point of Origin code. Decode for pat.point_of_origin.","valid_values":"0=Psych/substance|1=Non-healthcare|2=Clinic|3=HMO referral|4=Transfer from hospital|5=SNF/ICF|6=Health facility|7=ER|8=Court/law|9=Unknown|A=Rural primary care|B=HHA|C=Readmit same HHA|D=Same hospital DU|E=Ambulatory surgery|F=Hospice|G=Disaster","table_category":"lookup_table","is_join_key":True},
    {"table_name":"poorigin","field_name":"point_of_origin_desc","data_type":"Char(50)","description":"Point of Origin description","valid_values":"","table_category":"lookup_table","is_join_key":False},

    # ── PROVIDERS ─────────────────────────────────────────────────────────────
    {"table_name":"providers","field_name":"prov_id","data_type":"Integer","description":"Hospital entity ID (de-identified). Decode for pat.prov_id.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"providers","field_name":"urban_rural","data_type":"Char(10)","description":"Hospital proximity to city center","valid_values":"URBAN|RURAL","table_category":"lookup_table","is_join_key":False},
    {"table_name":"providers","field_name":"teaching","data_type":"Char(3)","description":"Teaching hospital indicator","valid_values":"YES|NO","table_category":"lookup_table","is_join_key":False},
    {"table_name":"providers","field_name":"beds_grp","data_type":"Char(11)","description":"Total bed count grouped","valid_values":"000-099|100-199|200-299|300-399|400-499|500+|Unavailable","table_category":"lookup_table","is_join_key":False},
    {"table_name":"providers","field_name":"prov_region","data_type":"Char(30)","description":"US Census Region","valid_values":"MIDWEST|NORTHEAST|SOUTH|WEST","table_category":"lookup_table","is_join_key":False},
    {"table_name":"providers","field_name":"prov_division","data_type":"Char(30)","description":"US Census Division","valid_values":"EAST NORTH CENTRAL|EAST SOUTH CENTRAL|MIDDLE ATLANTIC|MOUNTAIN|NEW ENGLAND|PACIFIC|SOUTH ATLANTIC|WEST NORTH CENTRAL|WEST SOUTH CENTRAL","table_category":"lookup_table","is_join_key":False},
    {"table_name":"providers","field_name":"cost_type","data_type":"Char(20)","description":"Cost methodology. Procedural = RVU-based costing; RCC = Ratio of Cost to Charges.","valid_values":"PROCEDURAL|RCC","table_category":"lookup_table","is_join_key":False},

    # ── PROV_ENROLLMENT ───────────────────────────────────────────────────────
    {"table_name":"prov_enrollment","field_name":"prov_id","data_type":"Integer","description":"Hospital entity ID. JOIN pat ON prov_id + disc_mon to apply projection weights.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"prov_enrollment","field_name":"disc_mon","data_type":"Integer","description":"Discharge month YYYYQMM. JOIN with pat.disc_mon.","valid_values":"","table_category":"lookup_table","is_join_key":True},
    {"table_name":"prov_enrollment","field_name":"ip_dx_count","data_type":"Integer","description":"Count of inpatient discharges in PHD for this provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"op_dx_count","data_type":"Integer","description":"Count of outpatient discharges in PHD for this provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"all_dx_count","data_type":"Integer","description":"Count of all discharges in PHD for this provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"ip_min_dx_date","data_type":"Date","description":"Minimum inpatient discharge date for provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"op_min_dx_date","data_type":"Date","description":"Minimum outpatient discharge date for provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"all_min_dx_date","data_type":"Date","description":"Minimum discharge date for provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"ip_max_dx_date","data_type":"Date","description":"Maximum inpatient discharge date. Used for 90-day hospital data contribution check.","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"op_max_dx_date","data_type":"Date","description":"Maximum outpatient discharge date for provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"all_max_dx_date","data_type":"Date","description":"Maximum discharge date for provider/discharge month","valid_values":"","table_category":"lookup_table","is_join_key":False},
    {"table_name":"prov_enrollment","field_name":"ip_proj_wgt","data_type":"Decimal(10,6)","description":"Inpatient projection weight for national estimates (AHA Annual Survey basis). JOIN on prov_id + disc_mon; filter i_o_ind = I.","valid_values":"","table_category":"lookup_table","is_join_key":False},
]


# ─────────────────────────────────────────────────────────────────────────────
# Quick-lookup helpers used by notebook_generator.py
# ─────────────────────────────────────────────────────────────────────────────

def get_table_fields(table_name: str):
    """Return all field dicts for a given table (lowercase match)."""
    t = table_name.lower()
    return [r for r in PHD_DICTIONARY if r["table_name"] == t]


def get_field(table_name: str, field_name: str):
    """Return single field dict or None."""
    t, f = table_name.lower(), field_name.lower()
    for r in PHD_DICTIONARY:
        if r["table_name"] == t and r["field_name"] == f:
            return r
    return None


def get_valid_values(table_name: str, field_name: str) -> str:
    """Return pipe-separated valid values string for a field."""
    row = get_field(table_name, field_name)
    return row["valid_values"] if row else ""


def get_all_table_names() -> list:
    """Return sorted list of unique table names in the dictionary."""
    return sorted(set(r["table_name"] for r in PHD_DICTIONARY))


# ─────────────────────────────────────────────────────────────────────────────
# Delta table DDL notebook generator
# Catalog : rhealth_premier_phd
# Schema  : bronze_native_premier_phd  (actual PHD tables)
# Scratch : caller supplies scratch_catalog + scratch_schema
# ─────────────────────────────────────────────────────────────────────────────

def generate_delta_ddl_notebook(
    scratch_catalog: str,
    scratch_schema: str,
    table_name: str = "premier_phd_data_dictionary_v2_2",
) -> str:
    """
    Generate a Databricks SOURCE-format SQL notebook that creates the
    Premier PHD Data Dictionary as a Delta table in the scratch schema.
    Run this once per environment to set up the reference table.

    Args:
        scratch_catalog:  e.g. "rhealth_datasets_scratch_space"
        scratch_schema:   e.g. "scratch_dbx_prphd_ads_automation_poc"
        table_name:       Target Delta table name
    """
    fqn = f"{scratch_catalog}.{scratch_schema}.{table_name}"
    cell_sep = "\n-- COMMAND ----------\n"
    notebook_header = "-- Databricks notebook source"

    cells = []

    cells.append(
        "-- MAGIC %md\n"
        f"-- MAGIC # Premier PHD Data Dictionary V2.2 — Delta Table Setup\n"
        "-- MAGIC\n"
        f"-- MAGIC Creates `{fqn}` as a permanent Delta table.  \n"
        "-- MAGIC Run once per environment.  \n"
        "-- MAGIC Source: PINC AI Healthcare Database PHD Data Dictionary V2.2 (Feb 2024)  \n"
        "-- MAGIC\n"
        "-- MAGIC PHD catalog: `rhealth_premier_phd.bronze_native_premier_phd`  \n"
        "-- MAGIC **Key naming note:** PATDEMO in the PHD docs = table `pat` in Databricks."
    )

    cells.append(f"DROP TABLE IF EXISTS {fqn};")

    cells.append(
        f"CREATE TABLE {fqn} (\n"
        f"    table_name       STRING  COMMENT 'Actual Databricks table name (lowercase). PATDEMO doc = pat actual.',\n"
        f"    field_name       STRING  COMMENT 'Column name (lowercase)',\n"
        f"    data_type        STRING  COMMENT 'Data type from PHD dictionary',\n"
        f"    description      STRING  COMMENT 'Field description',\n"
        f"    valid_values     STRING  COMMENT 'Pipe-separated valid values',\n"
        f"    table_category   STRING  COMMENT 'patient_table | lookup_table | addon_table',\n"
        f"    is_join_key      BOOLEAN COMMENT 'True if used as a join key'\n"
        f")\n"
        f"USING DELTA\n"
        f"COMMENT 'Premier Healthcare Database PHD Data Dictionary V2.2 (Feb 2024). "
        f"Full schema: patient tables, lookup tables, and add-on tables.'\n"
        f"TBLPROPERTIES (\n"
        f"    'source' = 'PHD_Data_Dictionary_V2.2_02-15-2024',\n"
        f"    'patdemo_actual_table' = 'pat',\n"
        f"    'phd_catalog' = 'rhealth_premier_phd.bronze_native_premier_phd'\n"
        f");"
    )

    chunk_size = 50
    rows = PHD_DICTIONARY
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        vals = []
        for r in chunk:
            def esc(s):
                return str(s).replace("'", "''")
            is_key = "true" if r["is_join_key"] else "false"
            vals.append(
                f"  ('{esc(r['table_name'])}', '{esc(r['field_name'])}', "
                f"'{esc(r['data_type'])}', '{esc(r['description'])}', "
                f"'{esc(r['valid_values'])}', '{esc(r['table_category'])}', {is_key})"
            )
        vals_sql = ",\n".join(vals)
        cells.append(f"INSERT INTO {fqn}\nVALUES\n{vals_sql};")

    total = len(PHD_DICTIONARY)
    table_count = len(get_all_table_names())
    cells.append(
        f"-- Verify: expect {total} rows across {table_count} tables\n"
        f"SELECT table_category, COUNT(*) AS field_count, COUNT(DISTINCT table_name) AS table_count\n"
        f"FROM {fqn}\n"
        f"GROUP BY table_category\n"
        f"ORDER BY table_category;"
    )

    cells.append(
        f"-- Preview core attrition fields (pat, paticd_proc, patcpt, paticd_diag, prov_enrollment)\n"
        f"SELECT table_name, field_name, data_type, valid_values\n"
        f"FROM {fqn}\n"
        f"WHERE table_name IN ('pat', 'paticd_proc', 'patcpt', 'paticd_diag', 'prov_enrollment')\n"
        f"ORDER BY table_name, field_name;"
    )

    return notebook_header + "\n" + cell_sep.join(cells)
