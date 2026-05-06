# RxBridge — Backend Code Generation Prompt

**Task**: Generate complete, production-ready FastAPI backend
**Read `architecture.md` first** — all schema, routes, and logic is defined there.

---

## CRITICAL RULES FOR CODE GENERATION

1. **Never use `json_encoders`** in Pydantic — use `model_config = ConfigDict(from_attributes=True)`
2. **Never use `orm_mode = True`** — that's Pydantic v1 syntax
3. **Every SQLAlchemy query uses `await session.execute(select(...))`** — never `session.query()`
4. **All route functions are `async def`** with `db: AsyncSession = Depends(get_db)`
5. **Never return raw SQLAlchemy objects** — always `.model_dump()` or use `from_attributes=True`
6. **All primary keys**: `Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))`
7. **Relationships**: use `relationship()` with `lazy="select"` (default) — never lazy="joined" in async
8. **For async relationship loading**: use `selectinload` in queries: `select(Model).options(selectinload(Model.relation))`
9. **Never import models inside other models** — all cross-model references use string names: `ForeignKey("table.col")`
10. **Gemini SDK**: `import google.generativeai as genai` — use `genai.GenerativeModel("gemini-2.0-flash")`
11. **JSON stripping for Gemini**: always `.strip().replace("```json","").replace("```","").strip()` before `json.loads()`
12. **Every route logs to audit_logs** via `await audit_service.log_action(...)`
13. **Consent gate on every doctor→patient data access**: call `await consent_gate.assert_consent()`
14. **Lab reports**: hash computed on insert, immutable afterward — amendments create new rows
15. **WebSocket manager**: singleton `manager = ConnectionManager()` at module level

---

## GENERATION ORDER (generate in this exact sequence to avoid import errors)

### Phase 1 — Foundation
1. `app/core/config.py`
2. `app/db/database.py`
3. `app/models/user.py`
4. `app/models/patient.py`
5. `app/models/doctor.py`
6. `app/models/lab.py`
7. `app/models/consent.py`
8. `app/models/diagnosis.py`
9. `app/models/lab_report.py`
10. `app/models/medication.py`
11. `app/models/recovery.py`
12. `app/models/report.py`
13. `app/models/calendar_event.py`
14. `app/models/sos_alert.py`
15. `app/models/notification.py`
16. `app/models/audit_log.py`
17. `app/models/pipeline_run.py`
18. `app/schemas/schemas.py`
19. `app/core/security.py`
20. `app/core/consent_gate.py`

### Phase 2 — Services
21. `app/services/audit_service.py`
22. `app/services/gemini_service.py`
23. `app/services/recovery_service.py`
24. `app/services/notification_service.py`
25. `app/services/report_service.py`

### Phase 3 — Agents
26. `app/agents/agent_9_vision.py`
27. `app/agents/agent_1_symptom.py`
28. `app/agents/agent_2_diagnosis.py`
29. `app/agents/agent_3_drug.py`
30. `app/agents/agent_4_resistance.py`
31. `app/agents/agent_5_safety.py`
32. `app/agents/agent_6_explainability.py`
33. `app/agents/agent_7_report.py`
34. `app/agents/agent_8_monitoring.py`
35. `app/agents/orchestrator.py`

### Phase 4 — API Routes
36. `app/api/websocket.py`
37. `app/api/routes/auth.py`
38. `app/api/routes/patients.py`
39. `app/api/routes/doctors.py`
40. `app/api/routes/labs.py`
41. `app/api/routes/diagnoses.py`
42. `app/api/routes/medications.py`
43. `app/api/routes/recovery.py`
44. `app/api/routes/reports.py`
45. `app/api/routes/calendar.py`
46. `app/api/routes/sos.py`
47. `app/api/routes/notifications.py`
48. `app/api/routes/ai_assist.py`
49. `app/api/routes/admin.py`
50. `app/api/routes/data.py`
51. `app/main.py`

---

## CONSISTENCY CHECKLIST
- No `session.query()` calls.
- Every doctor-patient data access has `assert_consent()`.
- Every sensitive action has `audit_service.log_action()`.
- No cross-patient data leakage.
- Lab reports are hashed and immutable.
- SOS alert broadcasts patient name only.
- Pydantic schemas use `ConfigDict(from_attributes=True)`.

---

## RESPONSE ENVELOPE
```python
# Success
return {"success": True, "data": result, "error": None}

# Error
raise HTTPException(status_code=403, detail="Patient consent required")
```
