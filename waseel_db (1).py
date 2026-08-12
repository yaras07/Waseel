"""
Waseel — Data Layer
====================
طبقة بيانات خفيفة (JSON) تدير:
  - ملفات المرضى (Patient Profiles)
  - ملفات مقدمي الرعاية (Caregiver Profiles)
  - سجل الأدوية (Medication Logs)
  - حدود التنبيه (Alert Thresholds)
  - قاعدة معرفة الأدوية (Medication Knowledge Base)

"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional


DB_PATH_DEFAULT = "database_schema.json"


class WaseelDB:
    def __init__(self, db_path: str = DB_PATH_DEFAULT):
        self.db_path = db_path
        if not os.path.exists(self.db_path):
            self._init_empty_db()
        self.data = self._load()

    # ---------- تحميل / حفظ ----------

    def _init_empty_db(self):
        empty = {
            "patients": [],
            "caregivers": [],
            "medication_logs": [],
            "alert_thresholds": [],
            "medication_knowledge_base": [],
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(empty, f, ensure_ascii=False, indent=2)

    def _load(self) -> dict:
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # ---------- Patient Profile ----------

    def add_patient(self, name: str) -> str:
        patient_id = f"P-{uuid.uuid4().hex[:6].upper()}"
        self.data["patients"].append({
            "patient_id": patient_id,
            "name": name,
        })
        self._save()
        return patient_id

    def get_patient(self, patient_id: str) -> Optional[dict]:
        return next((p for p in self.data["patients"] if p["patient_id"] == patient_id), None)

    # ---------- Caregiver Profile ----------

    def add_caregiver(self, name: str, contact_info: str, relationship: str,
                       linked_patient_id: str, severity_threshold: int = 6) -> str:
        caregiver_id = f"C-{uuid.uuid4().hex[:6].upper()}"
        self.data["caregivers"].append({
            "caregiver_id": caregiver_id,
            "name": name,
            "contact_info": contact_info,
            "relationship": relationship,
            "linked_patient_id": linked_patient_id,
            "sms_alert_settings": {
                "enabled": True,
                "missed_dose_alert": True,
                "symptom_severity_threshold": severity_threshold,
            },
        })
        self._save()
        return caregiver_id

    def get_caregivers_for_patient(self, patient_id: str) -> list:
        return [c for c in self.data["caregivers"] if c["linked_patient_id"] == patient_id]

    # ---------- Medication Logs ----------

    def log_medication(self, patient_id: str, medication_id: str, medication_name: str,
                        scheduled_time: str, actual_time: Optional[str] = None,
                        status: str = "taken", symptoms_reported: str = "",
                        severity_score: int = 0) -> dict:
        """يسجّل جرعة (مأخوذة أو فائتة) ويحسب دقائق التأخير تلقائيًا."""
        delay_minutes = 0
        if actual_time and status == "taken":
            sched = datetime.fromisoformat(scheduled_time)
            actual = datetime.fromisoformat(actual_time)
            delay_minutes = max(0, int((actual - sched).total_seconds() // 60))

        log_entry = {
            "log_id": f"L-{uuid.uuid4().hex[:6].upper()}",
            "patient_id": patient_id,
            "medication_id": medication_id,
            "medication_name": medication_name,
            "scheduled_time": scheduled_time,
            "actual_time": actual_time,
            "status": status,  # "taken" | "missed"
            "delay_minutes": delay_minutes,
            "symptoms_reported": symptoms_reported,
            "severity_score": severity_score,
        }
        self.data["medication_logs"].append(log_entry)
        self._save()

        alert = self._check_alert(patient_id, log_entry)
        return {"log": log_entry, "alert_triggered": alert}

    def get_medication_history(self, patient_id: str) -> list:
        return [l for l in self.data["medication_logs"] if l["patient_id"] == patient_id]

    # ---------- Alert Thresholds ----------

    def set_alert_threshold(self, patient_id: str, missed_dose_minutes: int = 30,
                             severity_threshold: int = 6):
        existing = next((a for a in self.data["alert_thresholds"] if a["patient_id"] == patient_id), None)
        if existing:
            existing["missed_dose_minutes_before_alert"] = missed_dose_minutes
            existing["symptom_severity_alert_threshold"] = severity_threshold
        else:
            self.data["alert_thresholds"].append({
                "patient_id": patient_id,
                "missed_dose_minutes_before_alert": missed_dose_minutes,
                "symptom_severity_alert_threshold": severity_threshold,
            })
        self._save()

    def _check_alert(self, patient_id: str, log_entry: dict) -> bool:
        """يقرر إذا لازم يرسل SMS لمقدم الرعاية بناءً على الجرعة الفائتة أو شدة الأعراض."""
        threshold = next((a for a in self.data["alert_thresholds"] if a["patient_id"] == patient_id), None)
        if not threshold:
            return False

        triggered = False
        if log_entry["status"] == "missed":
            triggered = True
        if log_entry["severity_score"] >= threshold["symptom_severity_alert_threshold"]:
            triggered = True

        if triggered:
            self._send_sms_alert(patient_id, log_entry)
        return triggered

    def _send_sms_alert(self, patient_id: str, log_entry: dict):
        """نقطة تكامل لإرسال SMS الفعلي (تُربط لاحقًا بخدمة مثل Twilio)."""
        caregivers = self.get_caregivers_for_patient(patient_id)
        for c in caregivers:
            if c["sms_alert_settings"]["enabled"]:
                print(f"[SMS ALERT] → {c['name']} ({c['contact_info']}): "
                      f"دواء {log_entry['medication_name']} — الحالة: {log_entry['status']}, "
                      f"شدة الأعراض: {log_entry['severity_score']}")

    # ---------- Medication Knowledge Base ----------

    def add_drug(self, trade_name: str, generic_name: str,
                 dosage_instructions_dialect: str, common_symptoms: list) -> str:
        medication_id = f"M-{uuid.uuid4().hex[:6].upper()}"
        self.data["medication_knowledge_base"].append({
            "medication_id": medication_id,
            "trade_name": trade_name,
            "generic_name": generic_name,
            "dosage_instructions_dialect": dosage_instructions_dialect,
            "common_symptoms": common_symptoms,
        })
        self._save()
        return medication_id

    def get_drug(self, medication_id: str) -> Optional[dict]:
        return next((d for d in self.data["medication_knowledge_base"]
                     if d["medication_id"] == medication_id), None)


# ---------------- مثال تشغيل تجريبي (Demo) ----------------
if __name__ == "__main__":
    db = WaseelDB("demo_waseel_db.json")

    pid = db.add_patient("محمد العتيبي")
    cid = db.add_caregiver("سارة العتيبي", "+9665XXXXXXXX", "ابنة", pid, severity_threshold=6)
    db.set_alert_threshold(pid, missed_dose_minutes=30, severity_threshold=6)

    mid = db.add_drug(
        trade_name="بنادول اكسترا",
        generic_name="باراسيتامول + كافيين",
        dosage_instructions_dialect="حبة كل ثمان ساعات بعد الأكل، ولا تتجاوز ثلاث حبات في اليوم",
        common_symptoms=["دوخة", "غثيان خفيف"],
    )

    result = db.log_medication(
        patient_id=pid,
        medication_id=mid,
        medication_name="بنادول اكسترا",
        scheduled_time="2026-08-10T08:00:00",
        actual_time="2026-08-10T08:12:00",
        status="taken",
        symptoms_reported="دوخة خفيفة",
        severity_score=7,
    )

    print("\nسجل الجرعة:", result["log"])
    print("تم تنبيه مقدم الرعاية؟", result["alert_triggered"])
    print("\nسجل الأدوية الكامل للمريض:", db.get_medication_history(pid))
