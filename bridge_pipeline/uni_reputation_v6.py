"""UNI relationship-evidence enrichment for the BRIDGE v5 scoring pipeline.

This module refines evidence meaning without changing axis weights, eligibility
thresholds, or the public scoring formula. Headline-only matches are kept as
conservative candidates; they never claim to measure the whole university.
"""
from __future__ import annotations
from typing import Iterable

POLICY_VERSION = "uni-rel-2026.10-1"

R_POSITIVE = {"신뢰":"trust","만족":"satisfaction","소통":"mutuality","상생":"mutuality","협력":"mutuality","호평":"satisfaction"}
R_NEGATIVE = {"불신":"distrust","불만":"dissatisfaction","반발":"dissatisfaction","갈등":"relationship_strain","중단":"relationship_exit","철회":"relationship_exit","이탈":"relationship_exit"}
IDENTITY = {"인재상":"talent_identity","교육이념":"institutional_identity","대학 비전":"institutional_identity","특성화":"distinctive_identity","정체성":"institutional_identity","브랜드":"brand_identity"}
LIFECYCLE = {"사과":"acknowledged","해명":"explained","조사":"investigating","시정":"corrected","개선":"implemented","이행":"implemented","재발 방지":"implemented","회복":"recovered","정상화":"recovered","재발":"recurred","반복":"recurred","미이행":"unresolved"}

def _matches(title: str, vocabulary: dict[str,str]) -> list[tuple[str,str]]:
    return [(term,concept) for term,concept in vocabulary.items() if term in title]

def classify_uni_evidence(title: str) -> list[dict]:
    evidence=[]
    for term,concept in _matches(title,R_POSITIVE):
        evidence.append({"axis":"R","type":f"uni_relation_{concept}","direction":1,"magnitude":12.0,"confidence":.58,"term":term,"review_status":"auto"})
    for term,concept in _matches(title,R_NEGATIVE):
        evidence.append({"axis":"R","type":f"uni_relation_{concept}","direction":-1,"magnitude":14.0,"confidence":.55,"term":term,"review_status":"pending"})
    for term,concept in _matches(title,IDENTITY):
        evidence.append({"axis":"I","type":f"uni_identity_{concept}","direction":0,"magnitude":10.0,"confidence":.50,"term":term,"review_status":"auto"})
    for term,stage in _matches(title,LIFECYCLE):
        direction=-1 if stage in {"recurred","unresolved"} else 1
        evidence.append({"axis":"E","type":f"uni_lifecycle_{stage}","direction":direction,"magnitude":12.0,"confidence":.52,"term":term,"review_status":"pending" if direction<0 else "auto"})
    unique={}
    for row in evidence:
        unique.setdefault((row["axis"],row["type"]),row)
    return list(unique.values())

def diagnostics(signals: Iterable[dict]) -> dict:
    types=[str(row.get("signal_type") or "") for row in signals]
    enriched=[value for value in types if value.startswith("uni_")]
    return {"policy_version":POLICY_VERSION,
            "relationship_concepts":sorted({v.removeprefix("uni_relation_") for v in enriched if v.startswith("uni_relation_")}),
            "identity_concepts":sorted({v.removeprefix("uni_identity_") for v in enriched if v.startswith("uni_identity_")}),
            "lifecycle_stages":sorted({v.removeprefix("uni_lifecycle_") for v in enriched if v.startswith("uni_lifecycle_")}),
            "enriched_evidence_count":len(enriched)}
