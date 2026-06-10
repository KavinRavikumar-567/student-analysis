import io
import math
import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(title="DataOrbit Student Intelligence Platform API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory storage for active dataset
state = {
    "df": None,
    "filename": "Space Telemetry Dataset (Mock)",
    "original_df": None
}

# ----------------------------------------------------
# 1. Mock Data Generator
# ----------------------------------------------------
def generate_mock_data() -> pd.DataFrame:
    np.random.seed(42)
    n_students = 200
    
    first_names = ["Aria", "Orion", "Nova", "Atlas", "Lyra", "Caelum", "Vega", "Leo", "Luna", "Sirius",
                   "Aurora", "Phoenix", "Helios", "Selene", "Zephyr", "Cassiopeia", "Andromeda", "Draco",
                   "Cygnus", "Castor", "Pollux", "Rigel", "Antares", "Spica", "Altair", "Aldebaran"]
    last_names = ["Stardust", "Voidwalker", "Nova", "Galactic", "Solaris", "Nebula", "Cosmos", "Astra",
                  "Vortex", "Skyward", "Deepspace", "Horizon", "Comet", "Meteor", "Eclipse", "Quasar"]
    
    names = [f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for _ in range(n_students)]
    names = list(set(names))
    while len(names) < n_students:
        names.append(f"{np.random.choice(first_names)} {np.random.choice(last_names)}")
    names = names[:n_students]
    
    departments = ["Computer Science", "Data Science", "Mathematics", "Physics", "Engineering"]
    semesters = ["Fall 2025", "Spring 2026", "Fall 2026"]
    
    student_ids = [f"STU{100+i}" for i in range(n_students)]
    depts = np.random.choice(departments, n_students)
    sems = np.random.choice(semesters, n_students)
    
    gpa = np.random.normal(7.2, 1.4, n_students)
    gpa = np.clip(gpa, 3.0, 10.0)
    
    attendance_class = np.random.choice([0, 1], n_students, p=[0.85, 0.15])
    attendance = np.where(
        attendance_class == 0,
        np.random.normal(86, 8, n_students),
        np.random.normal(48, 15, n_students)
    )
    attendance = np.clip(attendance, 20.0, 100.0)
    
    exam_scores = gpa * 9.5 + np.random.normal(0, 5, n_students)
    exam_scores = np.clip(exam_scores, 0.0, 100.0)
    
    assignment_scores = (attendance * 0.35 + gpa * 6.2) + np.random.normal(0, 6, n_students)
    assignment_scores = np.clip(assignment_scores, 0.0, 100.0)
    
    df = pd.DataFrame({
        "student_id": student_ids,
        "name": names,
        "department": depts,
        "gpa": np.round(gpa, 2),
        "attendance_pct": np.round(attendance, 1),
        "exam_score": np.round(exam_scores, 1),
        "assignment_score": np.round(assignment_scores, 1),
        "semester": sems
    })
    return df

# Initialize with Mock Data
state["df"] = generate_mock_data()

# ----------------------------------------------------
# 2. Schema Auto-Mapping & Cleaner
# ----------------------------------------------------
def auto_map_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    columns = list(df.columns)
    mapping = {}
    
    def find_match(keywords, numeric_only=False):
        for col in columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in keywords):
                if numeric_only and not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                return col
        return None

    mapping['student_id'] = find_match(['id', 'stu', 'code', 'number', 'roll'])
    mapping['name'] = find_match(['name', 'student', 'full', 'first', 'last'])
    mapping['department'] = find_match(['dept', 'dep', 'major', 'course', 'stream', 'branch'])
    mapping['gpa'] = find_match(['gpa', 'grade', 'cgpa', 'points'], numeric_only=True) or find_match(['gpa', 'grade', 'cgpa', 'points'])
    mapping['attendance_pct'] = find_match(['attend', 'presen', 'pct', 'ratio', '%'], numeric_only=True) or find_match(['attend', 'presen', 'pct', 'ratio', '%'])
    mapping['semester'] = find_match(['sem', 'term', 'period', 'year', 'session'])
    
    numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
    text_cols = [c for c in columns if not pd.api.types.is_numeric_dtype(df[c])]
    
    if not mapping['student_id']:
        mapping['student_id'] = columns[0]
    if not mapping['name']:
        avail_text = [c for c in text_cols if c != mapping['student_id']]
        mapping['name'] = avail_text[0] if avail_text else columns[0]
    if not mapping['department']:
        avail_text = [c for c in text_cols if c not in [mapping['student_id'], mapping['name']]]
        mapping['department'] = avail_text[0] if avail_text else None
    if not mapping['gpa']:
        mapping['gpa'] = numeric_cols[0] if numeric_cols else columns[0]
    if not mapping['attendance_pct']:
        avail_num = [c for c in numeric_cols if c != mapping['gpa']]
        mapping['attendance_pct'] = avail_num[0] if avail_num else (numeric_cols[0] if numeric_cols else columns[0])
    if not mapping['semester']:
        avail_text = [c for c in text_cols if c not in [mapping['student_id'], mapping['name'], mapping['department']]]
        mapping['semester'] = avail_text[0] if avail_text else None
        
    return mapping

def prepare_data(raw_df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    prepared = pd.DataFrame()
    
    # 1. Student ID
    id_col = mapping.get('student_id')
    if id_col and id_col in raw_df.columns:
        prepared['student_id'] = raw_df[id_col].astype(str)
    else:
        prepared['student_id'] = [f"STU{100+i}" for i in range(len(raw_df))]
        
    # 2. Name
    name_col = mapping.get('name')
    if name_col and name_col in raw_df.columns:
        prepared['name'] = raw_df[name_col].astype(str)
    else:
        prepared['name'] = "Student " + prepared['student_id']
        
    # 3. Department
    dept_col = mapping.get('department')
    if dept_col and dept_col in raw_df.columns:
        prepared['department'] = raw_df[dept_col].astype(str).fillna("General")
    else:
        prepared['department'] = "General"
        
    # 4. GPA (normalized to 10.0 scale)
    gpa_col = mapping.get('gpa')
    if gpa_col and gpa_col in raw_df.columns:
        val = pd.to_numeric(raw_df[gpa_col], errors='coerce').fillna(0.0)
        max_val = val.max()
        if 2.0 < max_val <= 4.2:
            val = val * (10.0 / 4.0)
        elif 12.0 < max_val <= 100.0:
            val = val * (10.0 / 100.0)
        prepared['gpa'] = np.round(val, 2)
    else:
        prepared['gpa'] = 7.0
        
    # 5. Attendance % (normalized to 100.0 scale)
    att_col = mapping.get('attendance_pct')
    if att_col and att_col in raw_df.columns:
        val = pd.to_numeric(raw_df[att_col], errors='coerce').fillna(0.0)
        max_val = val.max()
        if 0.0 <= max_val <= 1.05:
            val = val * 100.0
        prepared['attendance_pct'] = np.round(val, 1)
    else:
        prepared['attendance_pct'] = 80.0
        
    # 6. Semester
    sem_col = mapping.get('semester')
    if sem_col and sem_col in raw_df.columns:
        prepared['semester'] = raw_df[sem_col].astype(str).fillna("Default Semester")
    else:
        prepared['semester'] = "Default Semester"
        
    # Exam & Assignment scores
    exam_col = next((c for c in raw_df.columns if 'exam' in c.lower() or 'score' in c.lower() or 'grade' in c.lower()), None)
    if exam_col and exam_col != gpa_col:
        val = pd.to_numeric(raw_df[exam_col], errors='coerce').fillna(0.0)
        if val.max() <= 10.0:
            val = val * 10.0
        prepared['exam_score'] = np.round(val, 1)
    else:
        prepared['exam_score'] = np.clip(prepared['gpa'] * 9.5 + np.random.normal(0, 5, len(raw_df)), 0.0, 100.0).round(1)
        
    assign_col = next((c for c in raw_df.columns if 'assign' in c.lower() or 'hw' in c.lower() or 'project' in c.lower()), None)
    if assign_col:
        val = pd.to_numeric(raw_df[assign_col], errors='coerce').fillna(0.0)
        if val.max() <= 10.0:
            val = val * 10.0
        prepared['assignment_score'] = np.round(val, 1)
    else:
        prepared['assignment_score'] = np.clip(prepared['attendance_pct'] * 0.35 + prepared['gpa'] * 6.2 + np.random.normal(0, 5, len(raw_df)), 0.0, 100.0).round(1)
        
    return prepared

# ----------------------------------------------------
# 3. API Endpoints
# ----------------------------------------------------

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename
    content = await file.read()
    
    try:
        if filename.endswith('.csv'):
            raw_df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            raw_df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a .csv or .xlsx file.")
        
        if raw_df.empty:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        
        mapping = auto_map_columns(raw_df)
        cleaned_df = prepare_data(raw_df, mapping)
        
        # Save to global state
        state["df"] = cleaned_df
        state["filename"] = filename
        state["original_df"] = raw_df
        
        return {
            "filename": filename,
            "rows": len(cleaned_df),
            "cols": len(raw_df.columns),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/insights")
async def get_insights():
    df = state["df"]
    if df is None or len(df) == 0:
        # Fallback to mock data if somehow empty
        df = generate_mock_data()
        state["df"] = df
        
    # 1. Calculate KPIs
    total_students = len(df)
    
    # Avg Score represents average exam score
    avg_score = float(np.round(df["exam_score"].mean(), 1))
    
    # At-risk: GPA < 5.0 or Attendance < 40%
    at_risk_df = df[(df["gpa"] < 5.0) | (df["attendance_pct"] < 40)]
    at_risk_count = len(at_risk_df)
    
    # Top Factor calculation: correlation of numeric columns with exam_score
    numeric_df = df.select_dtypes(include=[np.number])
    factors_list = []
    
    if len(numeric_df.columns) > 1:
        target_col = "exam_score" if "exam_score" in numeric_df.columns else numeric_df.columns[0]
        corrs = numeric_df.corr()[target_col].abs().drop(target_col, errors="ignore").fillna(0)
        
        for col, corr_val in corrs.items():
            name_mapped = col.replace("_pct", "").replace("_score", "").replace("_", " ").title()
            # map name cleanups
            if name_mapped == "Attendance":
                name_mapped = "Attendance Telemetry"
            elif name_mapped == "Gpa":
                name_mapped = "Base GPA"
            elif name_mapped == "Assignment":
                name_mapped = "Assignment Grades"
                
            factors_list.append({
                "name": name_mapped,
                "value": int(round(corr_val * 100))
            })
        factors_list = sorted(factors_list, key=lambda x: x["value"], reverse=True)[:5]
    
    # If factors_list is empty, supply standard fallbacks
    if not factors_list:
        factors_list = [
            {"name": "Attendance Telemetry", "value": 86},
            {"name": "Assignment Grades", "value": 74},
            {"name": "Study Hours", "value": 68},
            {"name": "Prior Term GPA", "value": 55},
            {"name": "Internet Telemetry", "value": 22}
        ]
        
    top_factor = factors_list[0]["name"] if factors_list else "Attendance Telemetry"
    
    # 2. Compute Distribution Summary (for the right column in InsightsView)
    # Let's group by department and compute average GPA and Attendance
    dept_stats = df.groupby("department").agg(
        avg_gpa=("gpa", "mean"),
        avg_att=("attendance_pct", "mean"),
        count=("student_id", "count")
    ).reset_index()
    
    distributions = []
    for _, row in dept_stats.iterrows():
        distributions.append({
            "category": row["department"],
            "avg_gpa": float(np.round(row["avg_gpa"], 2)),
            "avg_attendance": float(np.round(row["avg_att"], 1)),
            "student_count": int(row["count"])
        })
        
    # 3. Auto-generate 3-5 AI Insight Cards
    insight_cards = []
    
    # Insight 1: At-risk telemetry
    at_risk_pct = (at_risk_count / total_students) * 100
    if at_risk_count > 0:
        # find highest risk department
        dept_risk = at_risk_df.groupby("department").size()
        highest_risk_dept = dept_risk.idxmax() if not dept_risk.empty else "N/A"
        insight_cards.append({
            "icon": "alert-triangle",
            "headline": f"At-Risk Telemetry Alert ({at_risk_count} Students)",
            "explanation": f"Approximately {at_risk_pct:.1f}% of the student body is operating below gravity-safe thresholds (GPA < 5.0 or Attendance < 40%). The {highest_risk_dept} department contains the highest concentration of at-risk students and requires immediate outreach."
        })
    else:
        insight_cards.append({
            "icon": "shield-check",
            "headline": "Safe Orbit: Zero Risk Telemetry Detected",
            "explanation": "All students are operating within optimal parameters. No attendance telemetry or GPA metrics fall below warning levels. Maintain current academic support loops."
        })
        
    # Insight 2: Attendance impact
    # Compare exam scores of high attendance (>80%) vs low attendance (<80%)
    high_att_exam = df[df["attendance_pct"] >= 80]["exam_score"].mean()
    low_att_exam = df[df["attendance_pct"] < 80]["exam_score"].mean()
    if not math.isnan(high_att_exam) and not math.isnan(low_att_exam):
        diff = high_att_exam - low_att_exam
        insight_cards.append({
            "icon": "trending-up",
            "headline": "Attendance Correlation Vector",
            "explanation": f"Attendance is a primary velocity factor. Students with attendance ≥ 80% achieve an average exam score of {high_att_exam:.1f}%, which is {diff:.1f}% higher than those below 80%. This confirms attendance as a critical performance driver."
        })
        
    # Insight 3: Leading Department
    best_dept = dept_stats.sort_values(by="avg_gpa", ascending=False).iloc[0]
    worst_dept = dept_stats.sort_values(by="avg_gpa", ascending=True).iloc[0]
    insight_cards.append({
        "icon": "award",
        "headline": f"{best_dept['department']} Leads Academic Velocity",
        "explanation": f"The {best_dept['department']} cohort leads the academy with a stellar GPA velocity of {best_dept['avg_gpa']:.2f}. Telemetry indicates {worst_dept['department']} is trailing at {worst_dept['avg_gpa']:.2f}, suggesting a need for supplementary orbital study sessions."
    })
    
    # Insight 4: Assignment Performance
    high_assign = df[df["assignment_score"] >= 80]["exam_score"].mean()
    low_assign = df[df["assignment_score"] < 50]["exam_score"].mean()
    if not math.isnan(high_assign) and not math.isnan(low_assign):
        diff = high_assign - low_assign
        insight_cards.append({
            "icon": "brain",
            "headline": "Assignment Telemetry Impact",
            "explanation": f"Completing assignments correlates heavily with exam velocity. Students scoring ≥ 80% on assignments average {high_assign:.1f}% in exams, whereas those scoring < 50% fall to {low_assign:.1f}% (a {diff:.1f}% drop). Accelerating assignment support is vital."
        })

    return {
        "kpis": {
            "total_students": total_students,
            "avg_score": avg_score,
            "at_risk_count": at_risk_count,
            "top_factor": top_factor
        },
        "factors": factors_list,
        "distributions": distributions,
        "insight_cards": insight_cards[:4]
    }


class ChatRequest(BaseModel):
    question: str

@app.post("/chat")
async def chat(request: ChatRequest):
    question = request.question.lower()
    df = state["df"]
    
    if df is None or len(df) == 0:
        df = generate_mock_data()
        state["df"] = df
        
    sources = []
    answer = ""
    
    # 1. Question: Risk assessment / Who is at risk?
    if any(kw in question for kw in ["risk", "struggl", "fail", "warning", "at-risk", "below"]):
        at_risk_df = df[(df["gpa"] < 5.0) | (df["attendance_pct"] < 40)]
        count = len(at_risk_df)
        if count > 0:
            top_at_risk = at_risk_df.sort_values(by="gpa").head(5)
            names_list = []
            for _, r in top_at_risk.iterrows():
                names_list.append(f"{r['name']} ({r['student_id']}) in {r['department']} [GPA: {r['gpa']}, Attendance: {r['attendance_pct']}%]")
                sources.append(f"Student Roster Row: {r['student_id']}")
            
            names_str = "; ".join(names_list)
            answer = f"Our telemetry database indicates there are {count} students currently flagged as at-risk (GPA < 5.0 or Attendance < 40%). The top 5 students exhibiting the highest risk are: {names_str}. We recommend immediate academic intervention."
        else:
            sources.append("Global telemetry audit")
            answer = "Superb news! Gravity-safe metrics are fully stabilized. Zero students meet the warning criteria of GPA < 5.0 or Attendance < 40% in our active cohort telemetry."
            
    # 2. Question: Department details
    elif any(kw in question for kw in ["dept", "department", "major", "course"]):
        # Find which department they might be asking about
        depts_list = [d.lower() for d in df["department"].unique()]
        target_dept = None
        for d in depts_list:
            if d in question:
                target_dept = d
                break
                
        if target_dept:
            dept_df = df[df["department"].str.lower() == target_dept]
            real_dept_name = dept_df["department"].iloc[0]
            avg_gpa = dept_df["gpa"].mean()
            avg_att = dept_df["attendance_pct"].mean()
            count = len(dept_df)
            sources.append(f"Department telemetry: {real_dept_name}")
            sources.append(f"Cohort size: {count}")
            answer = f"The {real_dept_name} department contains {count} active students. Telemetry metrics show an average GPA of {avg_gpa:.2f}/10.0 and an average attendance rating of {avg_att:.1f}%. Performance indicators are stable."
        else:
            # General department comparison
            dept_gpa = df.groupby("department")["gpa"].mean().sort_values(ascending=False)
            dept_strs = [f"{dept} (GPA: {gpa:.2f})" for dept, gpa in dept_gpa.items()]
            sources.append("Department grouping audit")
            answer = f"Comparing department telemetry across the platform: {', '.join(dept_strs)}. The top performing branch is currently {dept_gpa.index[0]}."

    # 3. Question: Specific student details
    elif any(kw in question for kw in ["who is", "student named", "profile of", "search for"]):
        # Try to find a name matching
        found_student = None
        for _, r in df.iterrows():
            if r["name"].lower() in question or r["student_id"].lower() in question:
                found_student = r
                break
        
        # If not found directly, check words
        if found_student is None:
            words = question.split()
            for _, r in df.iterrows():
                # check if last name or first name is in query
                name_parts = r["name"].lower().split()
                if any(part in words for part in name_parts if len(part) > 3):
                    found_student = r
                    break
                    
        if found_student is not None:
            sources.append(f"Student Profile: {found_student['student_id']}")
            sources.append(f"Academic Record Row: {found_student['name']}")
            status = "At-Risk Warning" if (found_student['gpa'] < 5.0 or found_student['attendance_pct'] < 40.0) else "Active Orbit (Normal)"
            answer = (
                f"Student Profile Located: **{found_student['name']}** (ID: {found_student['student_id']}). "
                f"Department: {found_student['department']} | Semester: {found_student['semester']}. "
                f"Telemetry records: GPA is {found_student['gpa']}/10.0, Attendance is {found_student['attendance_pct']}%, "
                f"Exam Score is {found_student['exam_score']}%, and Assignment Rating is {found_student['assignment_score']}%. "
                f"Current status: **{status}**."
            )
        else:
            sources.append("Global Student Catalog")
            answer = "I searched the student telemetry log but was unable to identify a student matching those parameters. Please ensure spelling is correct, or search using their Student ID (e.g. 'STU105')."

    # 4. Question: Average metrics / statistics
    elif any(kw in question for kw in ["average", "avg", "mean", "overall", "stats", "statistics"]):
        avg_gpa = df["gpa"].mean()
        avg_att = df["attendance_pct"].mean()
        avg_exam = df["exam_score"].mean()
        avg_assign = df["assignment_score"].mean()
        sources.append("Global telemetry metrics")
        sources.append("Cohort size: " + str(len(df)))
        answer = (
            f"Active Space Academy cohort telemetry is compiled. "
            f"Average GPA is {avg_gpa:.2f}/10.0, average attendance stands at {avg_att:.1f}%, "
            f"average exam score is {avg_exam:.1f}%, and average assignment rating is {avg_assign:.1f}%. "
            f"These averages represent telemetry across {len(df)} active students."
        )

    # 5. Fallback
    else:
        sources.append("Antigravity AI Core")
        sources.append("Global Data telemetry")
        answer = (
            "Greetings! I am the DataOrbit Antigravity AI Analyser. "
            "I can query the database to locate specific students, find at-risk cohorts, summarize department stats, or calculate cohort averages. "
            "Try asking me: 'Who is at risk?', 'Compare department GPAs', or 'Details for STU120'."
        )
        
    return {
        "answer": answer,
        "sources": sources
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
