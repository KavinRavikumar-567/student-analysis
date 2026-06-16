import io
import re
import sqlite3
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

    # More comprehensive keywords
    mapping['student_id'] = find_match(['id', 'stu', 'code', 'roll', 'enroll', 'reg'])
    mapping['name'] = find_match(['name', 'student', 'full', 'first', 'last'])
    mapping['department'] = find_match(['dept', 'dep', 'major', 'course', 'stream', 'branch', 'class'])
    mapping['gpa'] = find_match(['gpa', 'grade', 'score', 'mark', 'cgpa', 'points', 'sgpa', 'percentage'], numeric_only=True) or \
                     find_match(['gpa', 'grade', 'score', 'mark', 'cgpa', 'points', 'sgpa', 'percentage'])
    mapping['attendance_pct'] = find_match(['attend', 'presen', 'pct', 'ratio', '%'], numeric_only=True) or \
                                find_match(['attend', 'presen', 'pct', 'ratio', '%'])
    mapping['semester'] = find_match(['sem', 'term', 'period', 'year', 'session'])
    
    id_keywords = ['id', 'roll', 'code', 'enroll', 'reg', 'num']
    
    numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
    text_cols = [c for c in columns if not pd.api.types.is_numeric_dtype(df[c])]
    
    # 1. student_id fallback
    if not mapping['student_id']:
        id_like = [c for c in columns if any(kw in c.lower() for kw in id_keywords)]
        if id_like:
            mapping['student_id'] = id_like[0]
        else:
            mapping['student_id'] = columns[0]
            
    # 2. name fallback
    if not mapping['name']:
        avail_text = [c for c in text_cols if c != mapping['student_id']]
        mapping['name'] = avail_text[0] if avail_text else columns[0]
        
    # 3. department fallback
    if not mapping['department']:
        avail_text = [c for c in text_cols if c not in [mapping['student_id'], mapping['name']]]
        mapping['department'] = avail_text[0] if avail_text else None
        
    # 4. gpa fallback (prevent mapping to student_id or roll number columns)
    if not mapping['gpa']:
        gpa_candidates = [c for c in numeric_cols if c != mapping['student_id'] and not any(kw in c.lower() for kw in id_keywords)]
        if gpa_candidates:
            mapping['gpa'] = gpa_candidates[0]
        else:
            other_numeric = [c for c in numeric_cols if c != mapping['student_id']]
            mapping['gpa'] = other_numeric[0] if other_numeric else columns[0]
            
    # 5. attendance fallback (prevent mapping to GPA or student_id / roll numbers)
    if not mapping['attendance_pct']:
        att_candidates = [c for c in numeric_cols if c not in [mapping['gpa'], mapping['student_id']] and not any(kw in c.lower() for kw in id_keywords)]
        if att_candidates:
            mapping['attendance_pct'] = att_candidates[0]
        else:
            other_numeric = [c for c in numeric_cols if c not in [mapping['gpa'], mapping['student_id']]]
            mapping['attendance_pct'] = other_numeric[0] if other_numeric else (numeric_cols[0] if numeric_cols else columns[0])
            
    # 6. semester fallback
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
        if max_val > 0.0:
            if 2.0 < max_val <= 4.2:
                val = val * (10.0 / 4.0)
            elif 12.0 < max_val <= 100.0:
                val = val * (10.0 / 100.0)
            elif max_val > 100.0:
                val = (val / max_val) * 10.0
        prepared['gpa'] = np.round(val, 2)
    else:
        prepared['gpa'] = 7.0
        
    # 5. Attendance % (normalized to 100.0 scale)
    att_col = mapping.get('attendance_pct')
    if att_col and att_col in raw_df.columns:
        val = pd.to_numeric(raw_df[att_col], errors='coerce').fillna(0.0)
        max_val = val.max()
        if max_val > 0.0:
            if 0.0 <= max_val <= 1.05:
                val = val * 100.0
            elif max_val > 100.0:
                val = (val / max_val) * 100.0
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
        max_val = val.max()
        if max_val > 0.0:
            if max_val <= 10.0:
                val = val * 10.0
            elif max_val > 100.0:
                val = (val / max_val) * 100.0
        prepared['exam_score'] = np.round(val, 1)
    else:
        prepared['exam_score'] = np.clip(prepared['gpa'] * 9.5 + np.random.normal(0, 5, len(raw_df)), 0.0, 100.0).round(1)
        
    assign_col = next((c for c in raw_df.columns if 'assign' in c.lower() or 'hw' in c.lower() or 'project' in c.lower()), None)
    if assign_col:
        val = pd.to_numeric(raw_df[assign_col], errors='coerce').fillna(0.0)
        max_val = val.max()
        if max_val > 0.0:
            if max_val <= 10.0:
                val = val * 10.0
            elif max_val > 100.0:
                val = (val / max_val) * 100.0
        prepared['assignment_score'] = np.round(val, 1)
    else:
        prepared['assignment_score'] = np.clip(prepared['attendance_pct'] * 0.35 + prepared['gpa'] * 6.2 + np.random.normal(0, 5, len(raw_df)), 0.0, 100.0).round(1)
        
    return prepared

# ----------------------------------------------------
# 3. API Endpoints
# ----------------------------------------------------

@app.post("/api/upload")
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


@app.get("/api/insights")
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


def translate_nlp_to_sql(nlp_query: str, df: pd.DataFrame) -> tuple[str, str]:
    nlp_query_lower = nlp_query.lower().strip()
    
    # Extract unique categories dynamically
    depts = [str(d) for d in df['department'].unique() if pd.notna(d)] if 'department' in df.columns else []
    sems = [str(s) for s in df['semester'].unique() if pd.notna(s)] if 'semester' in df.columns else []
    stu_ids = [str(i) for i in df['student_id'].unique() if pd.notna(i)] if 'student_id' in df.columns else []
    stu_names = [str(n) for n in df['name'].unique() if pd.notna(n)] if 'name' in df.columns else []
    
    select_clause = "SELECT *"
    where_conditions = []
    order_clause = ""
    limit_clause = ""
    explanation_parts = []
    
    col_clean = {
        'student_id': 'Student ID',
        'name': 'Student Name',
        'department': 'Department',
        'gpa': 'GPA',
        'attendance_pct': 'Attendance %',
        'exam_score': 'Exam Score',
        'assignment_score': 'Assignment Score',
        'semester': 'Semester'
    }
    
    # Determine the select operation
    is_avg = any(kw in nlp_query_lower for kw in ["average", "avg", "mean"])
    is_count = any(kw in nlp_query_lower for kw in ["how many", "count", "number of", "total count", "amount of"])
    is_sum = any(kw in nlp_query_lower for kw in ["sum", "total sum"])
    
    # Identify target column for numeric aggregation
    target_col = None
    if "gpa" in nlp_query_lower:
        target_col = "gpa"
    elif "attendance" in nlp_query_lower or "present" in nlp_query_lower:
        target_col = "attendance_pct"
    elif "exam" in nlp_query_lower:
        target_col = "exam_score"
    elif "assignment" in nlp_query_lower or "hw" in nlp_query_lower or "project" in nlp_query_lower:
        target_col = "assignment_score"
        
    if is_count:
        select_clause = "SELECT COUNT(*) AS total_students"
        explanation_parts.append("counting the total number of students")
    elif is_avg and target_col:
        select_clause = f"SELECT AVG({target_col}) AS average_{target_col}"
        explanation_parts.append(f"calculating the average {col_clean[target_col]}")
    elif is_sum and target_col:
        select_clause = f"SELECT SUM({target_col}) AS sum_{target_col}"
        explanation_parts.append(f"calculating the sum of {col_clean[target_col]}")
    else:
        # User is requesting records
        cols_requested = []
        if any(kw in nlp_query_lower for kw in ["show names", "list names", "name of", "who is", "who has", "identify"]):
            cols_requested.append("name")
        if "gpa" in nlp_query_lower:
            cols_requested.append("gpa")
        if "attendance" in nlp_query_lower:
            cols_requested.append("attendance_pct")
        if "exam" in nlp_query_lower:
            cols_requested.append("exam_score")
        if "assignment" in nlp_query_lower or "hw" in nlp_query_lower or "project" in nlp_query_lower:
            cols_requested.append("assignment_score")
        if "department" in nlp_query_lower or "major" in nlp_query_lower:
            cols_requested.append("department")
        if "semester" in nlp_query_lower:
            cols_requested.append("semester")
            
        if cols_requested:
            if "name" not in cols_requested:
                cols_requested.insert(0, "name")
            if "student_id" not in cols_requested:
                cols_requested.insert(0, "student_id")
            # De-duplicate
            cols_requested = list(dict.fromkeys(cols_requested))
            select_clause = f"SELECT {', '.join(cols_requested)}"
            explanation_parts.append(f"retrieving {', '.join([col_clean.get(c, c) for c in cols_requested])}")
        else:
            select_clause = "SELECT student_id, name, department, gpa, attendance_pct, exam_score, assignment_score, semester"
            explanation_parts.append("retrieving student records")

    # 1. Filter by Department (with word boundary, supporting abbreviations)
    dept_map = {
        "cs": "Computer Science",
        "comp sci": "Computer Science",
        "ds": "Data Science",
        "data sci": "Data Science",
        "math": "Mathematics",
        "maths": "Mathematics",
        "physics": "Physics",
        "eng": "Engineering"
    }
    
    matched_depts = []
    # Try exact matches from dataset
    for d in depts:
        pattern = r'\b' + re.escape(d.lower()) + r'\b'
        if re.search(pattern, nlp_query_lower):
            matched_depts.append(d)
            
    # Try abbreviation matches if no exact match found
    if not matched_depts:
        for abbrev, full_name in dept_map.items():
            if re.search(r'\b' + re.escape(abbrev) + r'\b', nlp_query_lower):
                if full_name in depts:
                    matched_depts.append(full_name)
                    break
                    
    if matched_depts:
        matched_depts = sorted(matched_depts, key=len, reverse=True)
        actual_match = matched_depts[0]
        where_conditions.append(f"department = '{actual_match}'")
        explanation_parts.append(f"filtering for department '{actual_match}'")

    # 2. Filter by Semester (supporting abbreviations like 'fall 25' -> 'Fall 2025')
    matched_sems = []
    for s in sems:
        pattern = r'\b' + re.escape(s.lower()) + r'\b'
        if re.search(pattern, nlp_query_lower):
            matched_sems.append(s)
            
    # Try short year format matching if no exact matches (e.g., "fall 25" -> "Fall 2025")
    if not matched_sems:
        for s in sems:
            s_clean = s.lower()
            year_match = re.search(r'20(\d{2})', s_clean)
            if year_match:
                year_short = year_match.group(1)
                season = s_clean.split()[0]
                short_pattern = r'\b' + re.escape(season) + r'\s+' + re.escape(year_short) + r'\b'
                if re.search(short_pattern, nlp_query_lower):
                    matched_sems.append(s)
                    break
                    
    if matched_sems:
        actual_match = matched_sems[0]
        where_conditions.append(f"semester = '{actual_match}'")
        explanation_parts.append(f"filtering for semester '{actual_match}'")

    # 3. Filter by Student ID
    id_match = re.search(r'\bstu\d+\b', nlp_query_lower)
    if id_match:
        matched_id = id_match.group(0).upper()
        where_conditions.append(f"student_id = '{matched_id}'")
        explanation_parts.append(f"filtering for student ID '{matched_id}'")
    else:
        # Filter by Name
        for n in stu_names:
            if n.lower() in nlp_query_lower:
                where_conditions.append(f"name = '{n}'")
                explanation_parts.append(f"filtering for student named '{n}'")
                break

    # Extract limit value and exclude it from conditional filters
    limit_val = 1
    top_x_match = re.search(r'\b(?:top|best|lowest|bottom|first|last|limit)\s+(\d+)\b', nlp_query_lower)
    limit_number_str = None
    if top_x_match:
        limit_val = int(top_x_match.group(1))
        limit_number_str = top_x_match.group(1)

    # Extract comparisons with numbers (excluding the limit quantity number)
    all_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', nlp_query_lower)
    numbers = []
    limit_excluded = False
    for num in all_numbers:
        if limit_number_str and num == limit_number_str and not limit_excluded:
            limit_excluded = True
            continue
        numbers.append(num)
    
    def parse_operator(query_slice):
        if any(kw in query_slice for kw in ["greater than or equal", "at least", "minimum of", "min of", ">="]):
            return ">=", "greater than or equal to"
        if any(kw in query_slice for kw in ["less than or equal", "at most", "maximum of", "max of", "<="]):
            return "<=", "less than or equal to"
        if any(kw in query_slice for kw in ["greater than", "more than", "above", "higher than", "over", "exceed", ">"]):
            return ">", "greater than"
        if any(kw in query_slice for kw in ["less than", "below", "under", "lower than", "poorer than", "<"]):
            return "<", "less than"
        if any(kw in query_slice for kw in ["equal to", "equals", "is", "="]):
            return "=", "equal to"
        return ">", "greater than"

    # Handle "between X and Y" queries
    between_match = re.search(r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)', nlp_query_lower)
    if between_match:
        val1 = float(between_match.group(1))
        val2 = float(between_match.group(2))
        
        # Sort values
        v_min = min(val1, val2)
        v_max = max(val1, val2)
        
        # Determine column target
        if v_max <= 10.0 and any(kw in nlp_query_lower for kw in ['gpa', 'cgpa', 'grade']):
            where_conditions.append(f"gpa >= {v_min} AND gpa <= {v_max}")
            explanation_parts.append(f"GPA between {v_min} and {v_max}")
            numbers = [num for num in numbers if num != between_match.group(1) and num != between_match.group(2)]
        elif any(kw in nlp_query_lower for kw in ['attendance', 'present', 'attend']):
            where_conditions.append(f"attendance_pct >= {v_min} AND attendance_pct <= {v_max}")
            explanation_parts.append(f"Attendance % between {v_min}% and {v_max}%")
            numbers = [num for num in numbers if num != between_match.group(1) and num != between_match.group(2)]
        elif any(kw in nlp_query_lower for kw in ['exam', 'test', 'marks']):
            where_conditions.append(f"exam_score >= {v_min} AND exam_score <= {v_max}")
            explanation_parts.append(f"Exam Score between {v_min}% and {v_max}%")
            numbers = [num for num in numbers if num != between_match.group(1) and num != between_match.group(2)]
        elif any(kw in nlp_query_lower for kw in ['assignment', 'project', 'hw', 'homework']):
            where_conditions.append(f"assignment_score >= {v_min} AND assignment_score <= {v_max}")
            explanation_parts.append(f"Assignment Score between {v_min}% and {v_max}%")
            numbers = [num for num in numbers if num != between_match.group(1) and num != between_match.group(2)]

    # Standard GPA condition
    if any(kw in nlp_query_lower for kw in ['gpa', 'cgpa', 'grade']):
        gpa_idx = nlp_query_lower.find('gpa')
        if gpa_idx == -1:
            gpa_idx = nlp_query_lower.find('cgpa')
        if gpa_idx == -1:
            gpa_idx = nlp_query_lower.find('grade')
            
        gpa_val = None
        min_dist = 9999
        for n in numbers:
            fval = float(n)
            if fval <= 10.0:
                n_idx = nlp_query_lower.find(n)
                dist = abs(n_idx - gpa_idx)
                if dist < min_dist:
                    min_dist = dist
                    gpa_val = fval
        if gpa_val is not None:
            n_str = str(int(gpa_val)) if gpa_val.is_integer() else str(gpa_val)
            n_idx = nlp_query_lower.find(n_str)
            start = min(gpa_idx, n_idx)
            end = max(gpa_idx, n_idx)
            slice_text = nlp_query_lower[start:end]
            op, op_desc = parse_operator(slice_text)
            
            where_conditions.append(f"gpa {op} {n_str}")
            explanation_parts.append(f"GPA {op_desc} {n_str}")

    # Standard Attendance condition
    if any(kw in nlp_query_lower for kw in ['attendance', 'present', 'attend']):
        att_idx = nlp_query_lower.find('attendance')
        if att_idx == -1:
            att_idx = nlp_query_lower.find('present')
        if att_idx == -1:
            att_idx = nlp_query_lower.find('attend')
            
        att_val = None
        min_dist = 9999
        for n in numbers:
            fval = float(n)
            if fval > 10.0 or fval <= 1.0:
                if fval <= 1.0:
                    fval = fval * 100.0
                n_idx = nlp_query_lower.find(n)
                dist = abs(n_idx - att_idx)
                if dist < min_dist:
                    min_dist = dist
                    att_val = fval
        if att_val is not None:
            n_str = str(int(att_val)) if att_val.is_integer() else str(att_val)
            orig_n_strs = [n for n in numbers if float(n) == att_val or (float(n)*100.0 == att_val)]
            if orig_n_strs:
                orig_n_str = orig_n_strs[0]
                n_idx = nlp_query_lower.find(orig_n_str)
                start = min(att_idx, n_idx)
                end = max(att_idx, n_idx)
                slice_text = nlp_query_lower[start:end]
                op, op_desc = parse_operator(slice_text)
                
                where_conditions.append(f"attendance_pct {op} {n_str}")
                explanation_parts.append(f"Attendance % {op_desc} {n_str}%")

    # Standard Exam score condition
    if any(kw in nlp_query_lower for kw in ['exam', 'test', 'midterm', 'marks']):
        exam_idx = nlp_query_lower.find('exam')
        if exam_idx == -1:
            exam_idx = nlp_query_lower.find('test')
        if exam_idx == -1:
            exam_idx = nlp_query_lower.find('marks')
            
        exam_val = None
        min_dist = 9999
        for n in numbers:
            fval = float(n)
            if fval > 10.0:
                n_idx = nlp_query_lower.find(n)
                dist = abs(n_idx - exam_idx)
                if dist < min_dist:
                    min_dist = dist
                    exam_val = fval
        if exam_val is not None:
            n_str = str(int(exam_val)) if exam_val.is_integer() else str(exam_val)
            n_idx = nlp_query_lower.find(n_str)
            start = min(exam_idx, n_idx)
            end = max(exam_idx, n_idx)
            slice_text = nlp_query_lower[start:end]
            op, op_desc = parse_operator(slice_text)
            
            where_conditions.append(f"exam_score {op} {n_str}")
            explanation_parts.append(f"Exam Score {op_desc} {n_str}%")

    # Standard Assignment score condition
    if any(kw in nlp_query_lower for kw in ['assignment', 'project', 'hw', 'homework']):
        assign_idx = nlp_query_lower.find('assignment')
        if assign_idx == -1:
            assign_idx = nlp_query_lower.find('project')
        if assign_idx == -1:
            assign_idx = nlp_query_lower.find('hw')
            
        assign_val = None
        min_dist = 9999
        for n in numbers:
            fval = float(n)
            if fval > 10.0:
                n_idx = nlp_query_lower.find(n)
                dist = abs(n_idx - assign_idx)
                if dist < min_dist:
                    min_dist = dist
                    assign_val = fval
        if assign_val is not None:
            n_str = str(int(assign_val)) if assign_val.is_integer() else str(assign_val)
            n_idx = nlp_query_lower.find(n_str)
            start = min(assign_idx, n_idx)
            end = max(assign_idx, n_idx)
            slice_text = nlp_query_lower[start:end]
            op, op_desc = parse_operator(slice_text)
            
            where_conditions.append(f"assignment_score {op} {n_str}")
            explanation_parts.append(f"Assignment Score {op_desc} {n_str}%")

    # Sorting & Extremes (ORDER BY and LIMIT)
    is_highest = any(kw in nlp_query_lower for kw in ["highest", "top", "best", "maximum", "max", "greatest", "most", "high"])
    is_lowest = any(kw in nlp_query_lower for kw in ["lowest", "bottom", "worst", "minimum", "min", "poorest", "least", "low"])
    
    order_col = None
    if "gpa" in nlp_query_lower:
        order_col = "gpa"
    elif "attendance" in nlp_query_lower or "present" in nlp_query_lower:
        order_col = "attendance_pct"
    elif "exam" in nlp_query_lower:
        order_col = "exam_score"
    elif "assignment" in nlp_query_lower or "hw" in nlp_query_lower or "project" in nlp_query_lower:
        order_col = "assignment_score"
        
    if (is_highest or is_lowest) and not order_col:
        order_col = "gpa"
        
    if order_col:
        has_explicit_limit = top_x_match is not None
        is_singular_superlative = any(kw in nlp_query_lower for kw in ["highest", "lowest", "best", "worst", "maximum", "minimum", "greatest", "least", "who is", "who has"])
        
        if is_lowest:
            order_clause = f" ORDER BY {order_col} ASC"
            if has_explicit_limit or is_singular_superlative:
                limit_clause = f" LIMIT {limit_val}"
                explanation_parts.append(f"ordered by lowest {col_clean[order_col]} (bottom {limit_val})")
            else:
                explanation_parts.append(f"ordered by lowest {col_clean[order_col]}")
        elif is_highest:
            order_clause = f" ORDER BY {order_col} DESC"
            if has_explicit_limit or is_singular_superlative:
                limit_clause = f" LIMIT {limit_val}"
                explanation_parts.append(f"ordered by highest {col_clean[order_col]} (top {limit_val})")
            else:
                explanation_parts.append(f"ordered by highest {col_clean[order_col]}")

    # Construct complete SQL Query
    sql_query = select_clause + " FROM students"
    if where_conditions:
        sql_query += " WHERE " + " AND ".join(where_conditions)
    if order_clause:
        sql_query += order_clause
    if limit_clause:
        sql_query += limit_clause
        
    sql_query += ";"
    
    if explanation_parts:
        explanation = "Generated SQL query by " + ", and ".join(explanation_parts) + "."
    else:
        explanation = "Generated default query listing student records."
        
    return sql_query, explanation


def execute_sql_query(sql_query: str, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    try:
        conn = sqlite3.connect(':memory:')
        df.to_sql('students', conn, index=False, if_exists='replace')
        
        res_df = pd.read_sql_query(sql_query, conn)
        conn.close()
        
        if res_df.empty:
            answer = "No records matched the query criteria."
        elif len(res_df) == 1 and len(res_df.columns) == 1:
            val = res_df.iloc[0, 0]
            col_name = res_df.columns[0]
            if "avg" in col_name or "average" in col_name:
                answer = f"The average value is {val:.2f}."
            elif "count" in col_name or "total" in col_name:
                answer = f"The total count is {val}."
            elif "sum" in col_name:
                answer = f"The total sum is {val:.2f}."
            else:
                answer = f"The result is {val}."
        elif len(res_df) == 1:
            row_dict = res_df.iloc[0].to_dict()
            details = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
            answer = f"Found 1 matching record: {details}."
        else:
            answer = f"Retrieved {len(res_df)} matching records."
            
        return res_df, answer
    except Exception as e:
        return pd.DataFrame(), f"SQL execution error: {str(e)}"


class SQLQueryRequest(BaseModel):
    query: str


@app.post("/api/sql-query")
async def sql_query(request: SQLQueryRequest):
    df = state["df"]
    if df is None or len(df) == 0:
        df = generate_mock_data()
        state["df"] = df
        
    query_text = request.query.strip()
    is_raw_sql = query_text.lower().startswith("select")
    
    if is_raw_sql:
        sql_query = query_text
        explanation = "Executed custom user SQL query."
    else:
        sql_query, explanation = translate_nlp_to_sql(query_text, df)
        
    res_df, answer = execute_sql_query(sql_query, df)
    
    # Convert res_df to list of dicts for JSON response
    res_df = res_df.replace({np.nan: None, np.inf: None, -np.inf: None})
    records = res_df.to_dict(orient="records")
    columns = list(res_df.columns)
    
    return {
        "sql_query": sql_query,
        "explanation": explanation,
        "columns": columns,
        "records": records,
        "answer": answer,
        "success": not res_df.empty or answer != "No records matched the query criteria."
    }


class ChatRequest(BaseModel):
    question: str

@app.post("/api/chat")
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
