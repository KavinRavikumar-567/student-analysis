import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import sqlite3

# Set Page Config
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 1. Custom CSS Theme & Starfield Injection
# ----------------------------------------------------
# Generate randomized star shadows for pure CSS parallax starfield background
@st.cache_data
def generate_stars_css(num_stars, max_w=2500, max_h=2000):
    stars = []
    for _ in range(num_stars):
        x = np.random.randint(0, max_w)
        y = np.random.randint(0, max_h)
        opacity = np.random.uniform(0.2, 0.8)
        stars.append(f"{x}px {y}px rgba(255, 255, 255, {opacity:.2f})")
    return ", ".join(stars)

# Generate star shadows once
stars_1 = generate_stars_css(100)
stars_2 = generate_stars_css(70)
stars_3 = generate_stars_css(45)

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

# Inject custom monochrome theme CSS
st.markdown(f"""
    <style>
        /* Import clean fonts */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        /* App container overrides */
        .stApp {{
            background-color: #faf8f5 !important;
            background-image: none !important;
            font-family: 'Inter', sans-serif;
            color: #1b3a5b !important;
        }}

        /* Make sure all markdown text uses the correct font */
        .stMarkdown, div[data-testid="stMarkdownContainer"] p {{
            font-family: 'Inter', sans-serif !important;
            color: #4a607a !important;
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{
            font-family: 'Space Grotesk', sans-serif !important;
            color: #1b3a5b !important;
            font-weight: 700 !important;
        }}

        /* Styled Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: #faf8f5 !important;
            border-right: 1px solid #e2e8f0 !important;
        }}

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {{
            color: #1b3a5b !important;
            font-family: 'Space Grotesk', sans-serif;
        }}

        /* Universal Container Override: custom minimalist white cards */
        div[data-testid="stBorderedContainer"] {{
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            padding: 24px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s ease-in-out !important;
        }}
        
        div[data-testid="stBorderedContainer"]:hover {{
            transform: translateY(-2px) !important;
            border-color: #1b3a5b !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        }}

        /* Custom KPI styles */
        .kpi-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #4a607a !important;
            margin-bottom: 6px;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 500;
        }}
        .kpi-val {{
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.1;
            font-family: 'Space Grotesk', sans-serif;
            margin-bottom: 4px;
        }}
        .kpi-val.blue {{ color: #1b3a5b !important; }}
        .kpi-val.violet {{ color: #4a607a !important; }}
        .kpi-val.mint {{ color: #2f855a !important; }}
        .kpi-val.red {{ color: #c53030 !important; }}

        /* Top Navbar Floating Header Styling */
        .navbar-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            background: #ffffff;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}

        .navbar-title {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.65rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            background: linear-gradient(45deg, #1b3a5b, #4a607a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* Hide default Streamlit elements for clean UI */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        /* Keep the sidebar expand button visible when collapsed */
        [data-testid="collapsedControl"] {{
            visibility: visible !important;
            color: #1b3a5b !important;
        }}

        /* Custom scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: #faf8f5;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #cbd5e1;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #1b3a5b;
        }}

        /* Forms, inputs and buttons style adjustments in Streamlit */
        div[data-testid="stForm"] {{
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            background: #ffffff !important;
        }}

        /* Base button style reset */
        .stButton>button, button, button[kind="primary"], button[kind="secondary"], button[data-testid="stFormSubmitButton"] {{
            transition: all 0.2s ease-in-out !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* Primary/Action buttons styling */
        button[kind="primary"],
        button[data-testid="stFormSubmitButton"] {{
            background-color: #1b3a5b !important;
            color: #faf8f5 !important;
            border: 1px solid #1b3a5b !important;
            font-weight: 600 !important;
        }}
        button[kind="primary"]:hover,
        button[data-testid="stFormSubmitButton"]:hover {{
            background-color: #112a46 !important;
            border-color: #112a46 !important;
            color: #faf8f5 !important;
        }}

        /* Secondary / suggestion button styling */
        .stButton>button,
        button[kind="secondary"] {{
            background-color: #ffffff !important;
            color: #1b3a5b !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 500 !important;
        }}
        .stButton>button:hover,
        button[kind="secondary"]:hover {{
            background-color: #f8fafc !important;
            border-color: #1b3a5b !important;
            color: #1b3a5b !important;
        }}

        /* Ensure child label elements inside buttons inherit the parent button's text color */
        .stButton>button p, .stButton>button span, .stButton>button div,
        button p, button span, button div,
        button[kind="primary"] p, button[kind="primary"] span, button[kind="primary"] div,
        button[kind="secondary"] p, button[kind="secondary"] span, button[kind="secondary"] div,
        button[data-testid="stFormSubmitButton"] p, button[data-testid="stFormSubmitButton"] span, button[data-testid="stFormSubmitButton"] div {{
            color: inherit !important;
            font-weight: inherit !important;
        }}

        /* Custom file uploader style */
        div[data-testid="stFileUploader"] {{
            border: 1px dashed #cbd5e1 !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            padding: 14px !important;
        }}
        div[data-testid="stFileUploader"] section {{
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
        }}
        div[data-testid="stFileUploader"] label {{
            color: #1b3a5b !important;
            font-weight: 600 !important;
        }}

        /* Selectbox and Multiselect Dropdowns styling */
        div[data-baseweb="select"] {{
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
        }}
        div[data-baseweb="select"] * {{
            color: #1b3a5b !important;
        }}

        /* Multiselect tag pills style */
        span[role="button"] {{
            background-color: #f1f5f9 !important;
            color: #1b3a5b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }}
        span[role="button"] * {{
            color: #1b3a5b !important;
        }}

        /* Text inputs styling */
        div[data-testid="stTextInput"] input {{
            background-color: #ffffff !important;
            color: #1b3a5b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
        }}
        div[data-testid="stTextInput"] input:focus {{
            border-color: #1b3a5b !important;
            box-shadow: 0 0 0 1px #1b3a5b !important;
        }}

        /* Slider elements styling */
        div[role="slider"] {{
            background-color: #1b3a5b !important;
            border: 2px solid #ffffff !important;
        }}
        div[data-testid="stSlider"] [data-direction="horizontal"] {{
            background-color: #1b3a5b !important;
        }}
    </style>
""", unsafe_allow_html=True)


# ----------------------------------------------------
# 2. Mock Data Generator
# ----------------------------------------------------
@st.cache_data
def generate_mock_data():
    np.random.seed(42)
    n_students = 200
    
    first_names = ["Aria", "Orion", "Nova", "Atlas", "Lyra", "Caelum", "Vega", "Leo", "Luna", "Sirius",
                   "Aurora", "Phoenix", "Helios", "Selene", "Zephyr", "Cassiopeia", "Andromeda", "Draco",
                   "Cygnus", "Castor", "Pollux", "Rigel", "Antares", "Spica", "Altair", "Aldebaran"]
    last_names = ["Stardust", "Voidwalker", "Nova", "Galactic", "Solaris", "Nebula", "Cosmos", "Astra",
                  "Vortex", "Skyward", "Deepspace", "Horizon", "Comet", "Meteor", "Eclipse", "Quasar"]
    
    names = [f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for _ in range(n_students)]
    # De-duplicate names if any
    names = list(set(names))
    while len(names) < n_students:
        names.append(f"{np.random.choice(first_names)} {np.random.choice(last_names)}")
    names = names[:n_students]
    
    departments = ["Computer Science", "Data Science", "Mathematics", "Physics", "Engineering"]
    semesters = ["Fall 2025", "Spring 2026", "Fall 2026"]
    
    student_ids = [f"STU{100+i}" for i in range(n_students)]
    depts = np.random.choice(departments, n_students)
    sems = np.random.choice(semesters, n_students)
    
    # GPA normally distributed around 7.2 (scale out of 10)
    gpa = np.random.normal(7.2, 1.4, n_students)
    gpa = np.clip(gpa, 3.0, 10.0)
    
    # Attendance %: bimodal distribution representing normal and struggling cohorts
    attendance_class = np.random.choice([0, 1], n_students, p=[0.85, 0.15])
    attendance = np.where(
        attendance_class == 0,
        np.random.normal(86, 8, n_students),
        np.random.normal(48, 15, n_students)
    )
    attendance = np.clip(attendance, 20.0, 100.0)
    
    # Exam scores correlated with GPA
    exam_scores = gpa * 9.5 + np.random.normal(0, 5, n_students)
    exam_scores = np.clip(exam_scores, 0.0, 100.0)
    
    # Assignment scores correlated with GPA and Attendance
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


# ----------------------------------------------------
# 3. Schema Auto-Mapping Algorithm
# ----------------------------------------------------
def auto_map_columns(df):
    columns = list(df.columns)
    mapping = {}
    
    # Helper to find column containing keyword
    def find_match(keywords, numeric_only=False):
        for col in columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in keywords):
                if numeric_only and not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                return col
        return None

    # Matches
    mapping['student_id'] = find_match(['id', 'stu', 'code', 'roll', 'enroll', 'reg'])
    mapping['name'] = find_match(['name', 'student', 'full', 'first', 'last'])
    mapping['department'] = find_match(['dept', 'dep', 'major', 'course', 'stream', 'branch', 'class'])
    
    # GPA (prefers numeric)
    mapping['gpa'] = find_match(['gpa', 'grade', 'score', 'mark', 'cgpa', 'points', 'sgpa', 'percentage'], numeric_only=True) or \
                     find_match(['gpa', 'grade', 'score', 'mark', 'cgpa', 'points', 'sgpa', 'percentage'])
        
    # Attendance % (prefers numeric)
    mapping['attendance_pct'] = find_match(['attend', 'presen', 'pct', 'ratio', '%'], numeric_only=True) or \
                                find_match(['attend', 'presen', 'pct', 'ratio', '%'])
        
    # Semester
    mapping['semester'] = find_match(['sem', 'term', 'period', 'year', 'session'])
    
    id_keywords = ['id', 'roll', 'code', 'enroll', 'reg', 'num']
    
    # Fallbacks for missing matches
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


# ----------------------------------------------------
# 4. Data Cleaner & Normalizer
# ----------------------------------------------------
def prepare_data(raw_df, mapping):
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
        
    # 4. GPA (scaled to 10.0 scale)
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
        
    # 5. Attendance % (scaled to 100.0 scale)
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
        
    # Fill mock columns for scores if missing
    exam_col = next((c for c in raw_df.columns if 'exam' in c.lower()), None)
    if exam_col:
        val = pd.to_numeric(raw_df[exam_col], errors='coerce').fillna(0.0)
        max_val = val.max()
        if max_val > 0.0:
            if max_val <= 10.0:
                val = val * 10.0
            elif max_val > 100.0:
                val = (val / max_val) * 100.0
        prepared['exam_score'] = np.round(val, 1)
    else:
        prepared['exam_score'] = np.clip(prepared['gpa'] * 10.0 + np.random.normal(0, 5, len(raw_df)), 0.0, 100.0).round(1)
        
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


# Helper for safe dropdown indexes
def safe_index(col_list, col_name, default=0):
    if col_name in col_list:
        return col_list.index(col_name)
    return default


# ----------------------------------------------------
# 5. Core State Synchronizer
# ----------------------------------------------------
# Setup session state variable for synced semester filter
if 'semester_val' not in st.session_state:
    st.session_state.semester_val = "All Semesters"

def update_from_navbar():
    st.session_state.semester_val = st.session_state.navbar_sem

def update_from_sidebar():
    st.session_state.semester_val = st.session_state.sidebar_sem


# ----------------------------------------------------
# 6. Sidebar Panel (Uploader & Filters)
# ----------------------------------------------------
st.sidebar.markdown("### 🪐 Space Navigation")

# Load mock data directly
df = generate_mock_data()

# Collect dynamic options for filters
depts_list = sorted(list(df['department'].unique()))
sems_list = sorted(list(df['semester'].unique()))

# Add "All Semesters" options
sems_options = ["All Semesters"] + sems_list

# Verify session state boundaries in case options changed due to uploading new CSV
if st.session_state.semester_val not in sems_options:
    st.session_state.semester_val = "All Semesters"

# Render Sidebar Semester Filter (synced)
sidebar_sem_idx = sems_options.index(st.session_state.semester_val)
st.sidebar.selectbox(
    "Semester Selector",
    options=sems_options,
    index=sidebar_sem_idx,
    key="sidebar_sem",
    on_change=update_from_sidebar
)

# Sidebar Department Filter (multiselect)
selected_depts = st.sidebar.multiselect(
    "Departments",
    options=depts_list,
    default=depts_list
)

# Sidebar GPA Slider (reacts to loaded data range)
min_gpa_data = float(df['gpa'].min())
max_gpa_data = float(df['gpa'].max())
if min_gpa_data == max_gpa_data:
    min_gpa_data = 0.0
    max_gpa_data = 10.0

selected_gpa_range = st.sidebar.slider(
    "GPA Range Filter",
    min_value=min_gpa_data,
    max_value=max_gpa_data,
    value=(min_gpa_data, max_gpa_data),
    step=0.1
)

# Apply filters
filtered_df = df.copy()

# 1. Semester Filter
if st.session_state.semester_val != "All Semesters":
    filtered_df = filtered_df[filtered_df['semester'] == st.session_state.semester_val]

# 2. Department Filter
if selected_depts:
    filtered_df = filtered_df[filtered_df['department'].isin(selected_depts)]
else:
    # If empty, show nothing to keep layout interactive rather than crashing
    filtered_df = filtered_df.head(0)

# 3. GPA Filter
filtered_df = filtered_df[
    (filtered_df['gpa'] >= selected_gpa_range[0]) & 
    (filtered_df['gpa'] <= selected_gpa_range[1])
]

# Sidebar Download Section
st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Telemetry Reports")
csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="Download Current Dataset (CSV)",
    data=csv_filtered,
    file_name="cleaned_student_telemetry.csv",
    mime="text/csv"
)


# ----------------------------------------------------
# 7. Main Dashboard Area & Navbar
# ----------------------------------------------------
# Custom Top Floating Navbar
navbar_cols = st.columns([4, 1])

with navbar_cols[0]:
    st.markdown('<div class="navbar-bar"><div class="navbar-title">🌌 STUDENT PERFORMANCE ANALYTICS</div></div>', unsafe_allow_html=True)

with navbar_cols[1]:
    # Top navbar semester filter (synced with sidebar)
    navbar_sem_idx = sems_options.index(st.session_state.semester_val)
    st.selectbox(
        "Select Semester",
        options=sems_options,
        index=navbar_sem_idx,
        key="navbar_sem",
        on_change=update_from_navbar,
        label_visibility="collapsed"
    )



# ----------------------------------------------------
# 8. KPI Cards Row
# ----------------------------------------------------
# Calculate stats
total_students = len(filtered_df)
avg_gpa = filtered_df['gpa'].mean() if total_students > 0 else 0.0
avg_attendance = filtered_df['attendance_pct'].mean() if total_students > 0 else 0.0

# At Risk Logic: GPA < 5.0 OR Attendance % < 40
at_risk_df = filtered_df[(filtered_df['gpa'] < 5.0) | (filtered_df['attendance_pct'] < 40)]
at_risk_count = len(at_risk_df)

kpi_cols = st.columns(4)

with kpi_cols[0]:
    with st.container(border=True):
        st.markdown(
            '<div class="kpi-title">Total Students</div>'
            f'<div class="kpi-val mint">{total_students}</div>'
            '<div style="color: #69f0ae; font-size: 0.8rem; font-weight: 500;">🌌 Active Cohort</div>',
            unsafe_allow_html=True
        )

with kpi_cols[1]:
    with st.container(border=True):
        st.markdown(
            '<div class="kpi-title">Average GPA</div>'
            f'<div class="kpi-val blue">{avg_gpa:.2f}</div>'
            '<div style="color: #4fc3f7; font-size: 0.8rem; font-weight: 500;">✨ Out of 10.0</div>',
            unsafe_allow_html=True
        )

with kpi_cols[2]:
    with st.container(border=True):
        st.markdown(
            '<div class="kpi-title">Average Attendance</div>'
            f'<div class="kpi-val violet">{avg_attendance:.1f}%</div>'
            '<div style="color: #b388ff; font-size: 0.8rem; font-weight: 500;">🚀 Target: >85%</div>',
            unsafe_allow_html=True
        )

with kpi_cols[3]:
    with st.container(border=True):
        st.markdown(
            '<div class="kpi-title">At-Risk Count</div>'
            f'<div class="kpi-val red">{at_risk_count}</div>'
            '<div style="color: #ff5252; font-size: 0.8rem; font-weight: 500;">⚠️ GPA < 5.0 or Att. < 40%</div>',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)


# ----------------------------------------------------
# 12. AI Text-to-SQL Query Console
# ----------------------------------------------------
st.markdown("### 🚀 AI Text-to-SQL Query Console")

with st.container(border=True):
    st.markdown(
        "<p style='font-size: 0.9rem; color: #4a607a; margin-bottom: 12px; font-weight: 500;'>"
        "Ask a question in natural language to query the student telemetry database, or write direct SQL queries."
        "</p>",
        unsafe_allow_html=True
    )
    
    # Pre-defined query template pills/suggestions
    cols_sug = st.columns(4)
    suggestions = [
        "Who has the highest GPA?",
        "Average attendance in Computer Science",
        "Show students with attendance < 50%",
        "List top 5 exam scores in Engineering"
    ]
    
    if 'sql_text_input' not in st.session_state:
        st.session_state.sql_text_input = ""
        
    for i, sug in enumerate(suggestions):
        with cols_sug[i % 4]:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.sql_text_input = sug
                
    # Input box wrapped in a form for single enter/run submission
    with st.form("sql_query_form", clear_on_submit=False):
        user_query = st.text_input(
            "Ask Query (NL or SQL):",
            placeholder="e.g. Show top 5 students by GPA or SELECT name, gpa FROM students WHERE gpa > 9.0",
            key="sql_text_input"
        )
        submit_btn = st.form_submit_button("🚀 Run Telemetry Query", use_container_width=True)
    
    if user_query:
        # Translate and execute
        is_raw_sql = user_query.strip().lower().startswith("select")
        
        # We run the query on df (the cleaned dataframe before sidebar filters, or filtered_df?
        # Let's run on 'df' so the user can query the entire active dataset, which is more powerful!)
        if is_raw_sql:
            sql_query = user_query
            explanation = "Executed custom user SQL query."
        else:
            sql_query, explanation = translate_nlp_to_sql(user_query, df)
            
        res_df, answer = execute_sql_query(sql_query, df)
        
        # Display Generated SQL & Explanation
        st.markdown(f"**Generated SQL Query:**")
        st.code(sql_query, language="sql")
        
        # Results
        st.markdown(f"**Interpretation:** {explanation}")
        st.markdown(f"**Result:** {answer}")
        
        if not res_df.empty:
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No records matched this query.")

st.markdown("<br>", unsafe_allow_html=True)


# ----------------------------------------------------
# 9. Plotly Helpers
# ----------------------------------------------------
def apply_plotly_style(fig, title, subtitle=None):
    title_text = f"<b>{title}</b>"
    top_margin = 55
    if subtitle:
        title_text += f"<br><span style='font-size: 11px; font-weight: normal; color: #4a607a; font-family: Inter;'>{subtitle}</span>"
        top_margin = 75
        
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=14, family="Space Grotesk", color="#1b3a5b"),
            x=0.01,
            y=0.98
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Space Grotesk, sans-serif",
        font_color="#1b3a5b",
        margin=dict(l=45, r=20, t=top_margin, b=45),
        xaxis=dict(
            gridcolor='rgba(27, 58, 91, 0.08)',
            zerolinecolor='rgba(27, 58, 91, 0.15)',
            tickfont=dict(color='#4a607a', family="Inter"),
            title_font=dict(color='#1b3a5b', size=11, family="Space Grotesk")
        ),
        yaxis=dict(
            gridcolor='rgba(27, 58, 91, 0.08)',
            zerolinecolor='rgba(27, 58, 91, 0.15)',
            tickfont=dict(color='#4a607a', family="Inter"),
            title_font=dict(color='#1b3a5b', size=11, family="Space Grotesk")
        )
    )
    return fig


# ----------------------------------------------------
# 10. Visualization Grid (2x2 Grid)
# ----------------------------------------------------
row1_cols = st.columns(2)

# Row 1 Left: Grade Distribution Bar Chart
with row1_cols[0]:
    with st.container(border=True):
        if total_students > 0:
            bins = [0, 5.0, 7.0, 8.0, 9.0, 10.001]
            labels = ['F (<5.0)', 'D (5.0-7.0)', 'C (7.0-8.0)', 'B (8.0-9.0)', 'A (>=9.0)']
            
            # Group into buckets
            buckets = pd.cut(filtered_df['gpa'], bins=bins, labels=labels, right=False)
            counts = buckets.value_counts().reindex(labels).reset_index()
            counts.columns = ['Grade Bucket', 'Students']
            
            fig_grade = px.bar(
                counts,
                x='Grade Bucket',
                y='Students',
                color='Grade Bucket',
                color_discrete_map={
                    'A (>=9.0)': '#2f855a',    # Mint
                    'B (8.0-9.0)': '#1b3a5b',  # Electric Blue
                    'C (7.0-8.0)': '#4a607a',  # Violet
                    'D (5.0-7.0)': '#b7791f',  # Amber
                    'F (<5.0)': '#c53030'      # Red
                }
            )
            apply_plotly_style(fig_grade, "GRADE DISTRIBUTION", "Count of cohort students grouped into academic grade letters")
            fig_grade.update_layout(showlegend=False)
            st.plotly_chart(fig_grade, use_container_width=True)
        else:
            st.info("No data available for Grade Distribution.")

# Row 1 Right: Attendance Heatmap by Department & Semester
with row1_cols[1]:
    with st.container(border=True):
        if total_students > 0:
            # Pivot data: Department on Y-axis, Semester on X-axis, Average Attendance on Z
            heatmap_data = filtered_df.groupby(['department', 'semester'])['attendance_pct'].mean().unstack().fillna(0)
            
            # Format display strings for hover
            hover_text = [[f"{val:.1f}%" for val in row] for row in heatmap_data.values]
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale=[
                    [0.0, '#fbf3be'],
                    [0.25, '#c3e8ca'],
                    [0.5, '#b6e3f9'],
                    [0.75, '#7ec8f2'],
                    [1.0, '#4ca8e6']
                ],
                text=hover_text,
                texttemplate="%{text}",
                textfont={"size": 11, "family": "Space Grotesk", "color": "#1b3a5b"},
                hovertemplate="Department: %{y}<br>Semester: %{x}<br>Avg Attendance: %{text}<extra></extra>",
                colorbar=dict(
                    title=dict(text="Avg %", font=dict(color="#1b3a5b", size=9)),
                    tickfont=dict(color="#4a607a", size=9)
                )
            ))
            apply_plotly_style(fig_heatmap, "ATTENDANCE HEATMAP BY DEPT & SEMESTER", "Average attendance percentages by academic department and semester")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("No data available for Attendance Heatmap.")

st.markdown("<br>", unsafe_allow_html=True)
row2_cols = st.columns(2)

# Row 2 Left: Attendance vs GPA Scatter Plot
with row2_cols[0]:
    with st.container(border=True):
        if total_students > 0:
            fig_scatter = px.scatter(
                filtered_df,
                x='attendance_pct',
                y='gpa',
                color='department',
                hover_name='name',
                color_discrete_sequence=['#1b3a5b', '#4a607a', '#2f855a', '#b7791f', '#c53030', '#718096'],
                labels={'attendance_pct': 'Attendance %', 'gpa': 'GPA', 'department': 'Department'}
            )
            apply_plotly_style(fig_scatter, "ATTENDANCE VS GPA SCATTER PLOT", "Correlation mapping between attendance ratios and GPAs")
            fig_scatter.update_layout(
                showlegend=True,
                legend=dict(
                    title=None,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#4a607a', size=9, family="Inter"),
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            # Add subtle horizontal line at GPA=5.0 and vertical at attendance=40% to indicate risk thresholds
            fig_scatter.add_shape(
                type="line", x0=20, y0=5.0, x1=100, y1=5.0,
                line=dict(color="rgba(255, 82, 82, 0.45)", width=1.5, dash="dash")
            )
            fig_scatter.add_shape(
                type="line", x0=40, y0=3.0, x1=40, y1=10.0,
                line=dict(color="rgba(255, 82, 82, 0.45)", width=1.5, dash="dash")
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data available for Attendance vs GPA.")

# Row 2 Right: Average GPA by Department Horizontal Bar Chart
with row2_cols[1]:
    with st.container(border=True):
        if total_students > 0:
            dept_gpa = filtered_df.groupby('department')['gpa'].mean().reset_index().sort_values(by='gpa', ascending=True)
            
            fig_dept_gpa = px.bar(
                dept_gpa,
                y='department',
                x='gpa',
                orientation='h',
                color='gpa',
                color_continuous_scale=[[0, '#4a607a'], [1.0, '#1b3a5b']],
                labels={'gpa': 'Average GPA', 'department': ''}
            )
            apply_plotly_style(fig_dept_gpa, "AVERAGE GPA BY DEPARTMENT", "Comparative average GPA performance vectors across streams")
            fig_dept_gpa.update_layout(
                coloraxis_showscale=False,
                xaxis=dict(range=[0, 10])
            )
            st.plotly_chart(fig_dept_gpa, use_container_width=True)
        else:
            st.info("No data available for Avg GPA by Department.")

st.markdown("<br>", unsafe_allow_html=True)


# ----------------------------------------------------
# 11. Bottom Panel: At-Risk Students Data Table
# ----------------------------------------------------
st.markdown("### ⚠️ At-Risk Student Roster")

with st.container(border=True):
    if len(at_risk_df) > 0:
        # Display explanatory text
        st.markdown(
            "<p style='font-size: 0.9rem; color: #ff8a80; margin-bottom: 12px; font-weight: 500;'>"
            "🚀 Zero-Gravity Warning: The following students have GPAs below 5.0 OR attendance below 40%."
            "</p>",
            unsafe_allow_html=True
        )
        
        # Select key columns to show in roster
        roster_df = at_risk_df[[
            'student_id', 'name', 'department', 'semester', 
            'gpa', 'attendance_pct', 'exam_score', 'assignment_score'
        ]].copy()
        
        # Sort by GPA ascending
        roster_df = roster_df.sort_values(by='gpa')
        
        # Clean column labels
        roster_df.columns = [
            'Student ID', 'Full Name', 'Department', 'Semester', 
            'GPA', 'Attendance %', 'Exam Score', 'Assignment Score'
        ]
        
        # Row highlighting styler
        def highlight_at_risk_rows(row):
            # Styler expects a style directive for each element in the row
            return ['background-color: rgba(255, 82, 82, 0.08); color: #c53030; font-family: Inter; border: 1px solid rgba(255, 82, 82, 0.15);'] * len(row)
        
        styled_roster = roster_df.style.apply(highlight_at_risk_rows, axis=1)
        
        # Download button for at-risk roster
        csv_roster = roster_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download At-Risk Roster (CSV)",
            data=csv_roster,
            file_name="at_risk_student_roster.csv",
            mime="text/csv"
        )
        
        # Render the styled dataframe full-width
        st.dataframe(
            styled_roster,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown(
            "<div style='border: 1px solid rgba(47, 133, 90, 0.2); border-radius: 12px; padding: 15px; background: rgba(47, 133, 90, 0.05); color: #2f855a; font-weight: 500; font-size: 0.95rem;'>"
            "🌌 Zero-Gravity Operational Report: All student systems functioning correctly. Zero at-risk students detected under current telemetry filters."
            "</div>",
            unsafe_allow_html=True
        )

