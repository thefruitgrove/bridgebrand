"""GOV-specific relationship evidence layered on the common BRIDGE model."""
from __future__ import annotations
from typing import Iterable

POLICY_VERSION="gov-rel-2026.10-1"
PROCEDURE={"공청회":"consultation","의견수렴":"consultation","행정예고":"consultation","적법":"legality","법령 준수":"legality","절차 준수":"procedural_fairness","공정":"procedural_fairness","정보공개":"transparency","공개 설명":"explanation"}
PARTICIPATION={"국민제안":"public_input","주민제안":"public_input","시민참여":"participation","주민참여":"participation","민관협의":"mutual_control","정책 반영":"input_reflected","의견 반영":"input_reflected","답변":"response"}
LIFECYCLE={"공식 확인":"acknowledged","해명":"explained","조사 착수":"investigating","개선안":"planned","시정":"corrected","개선 조치":"implemented","이행":"implemented","집행 완료":"completed","후속조치":"follow_up","감사 결과":"audited","재발":"recurred","반복 지적":"recurred","미이행":"unresolved"}
COLLABORATION={"민관협력":"joint_governance","기관 협업":"interagency","부처 협업":"interagency","공동사업":"joint_delivery","서비스 연계":"service_linkage","공동 대응":"joint_response","업무협약":"agreement_only","MOU":"agreement_only"}
EXPERIENCE={"민원 처리":"complaint_service","온라인 신청":"digital_service","상담":"consultation_service","신고 처리":"report_service","지원금 지급":"benefit_delivery","허가":"authorization","단속":"enforcement","과세":"mandatory_contact"}

def _matches(title,vocabulary):
    return [(term,concept) for term,concept in vocabulary.items() if term.casefold() in title.casefold()]

def classify_gov_evidence(title):
    rows=[]
    for term,concept in _matches(title,PROCEDURE):
        rows.append({"axis":"E","type":f"gov_procedure_{concept}","direction":1,"magnitude":10.0,"confidence":.58,"term":term,"review_status":"auto"})
    for term,concept in _matches(title,PARTICIPATION):
        rows.append({"axis":"R","type":f"gov_participation_{concept}","direction":1,"magnitude":10.0,"confidence":.55,"term":term,"review_status":"auto"})
    for term,stage in _matches(title,LIFECYCLE):
        direction=-1 if stage in {"recurred","unresolved"} else 1
        rows.append({"axis":"E","type":f"gov_lifecycle_{stage}","direction":direction,"magnitude":12.0,"confidence":.55,"term":term,"review_status":"pending" if direction<0 else "auto"})
    for term,concept in _matches(title,COLLABORATION):
        rows.append({"axis":"G","type":f"gov_collaboration_{concept}","direction":1,"magnitude":5.0 if concept=="agreement_only" else 12.0,"confidence":.52,"term":term,"review_status":"auto"})
    for term,concept in _matches(title,EXPERIENCE):
        rows.append({"axis":"D","type":f"gov_experience_{concept}","direction":0,"magnitude":8.0,"confidence":.48,"term":term,"review_status":"auto"})
    unique={}
    for row in rows: unique.setdefault((row["axis"],row["type"]),row)
    return list(unique.values())

def diagnostics(signals:Iterable[dict]):
    types=[str(row.get("signal_type") or "") for row in signals]
    enriched=[v for v in types if v.startswith("gov_")]
    return {"policy_version":POLICY_VERSION,
      "procedure_concepts":sorted({v.removeprefix("gov_procedure_") for v in enriched if v.startswith("gov_procedure_")}),
      "participation_concepts":sorted({v.removeprefix("gov_participation_") for v in enriched if v.startswith("gov_participation_")}),
      "lifecycle_stages":sorted({v.removeprefix("gov_lifecycle_") for v in enriched if v.startswith("gov_lifecycle_")}),
      "collaboration_concepts":sorted({v.removeprefix("gov_collaboration_") for v in enriched if v.startswith("gov_collaboration_")}),
      "experience_paths":sorted({v.removeprefix("gov_experience_") for v in enriched if v.startswith("gov_experience_")}),
      "enriched_evidence_count":len(enriched)}
