import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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

# Inject custom space theme CSS
st.markdown(f"""
    <style>
        /* Import futuristic and clean fonts */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        /* Parallax starfields in background */
        @keyframes animStar {{
            from {{ transform: translateY(0px); }}
            to {{ transform: translateY(-2000px); }}
        }}

        .star-field-1 {{
            width: 1px;
            height: 1px;
            background: transparent;
            box-shadow: {stars_1};
            animation: animStar 140s linear infinite;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 0;
        }}

        .star-field-2 {{
            width: 2px;
            height: 2px;
            background: transparent;
            box-shadow: {stars_2};
            animation: animStar 200s linear infinite;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 0;
        }}

        .star-field-3 {{
            width: 3px;
            height: 3px;
            background: transparent;
            box-shadow: {stars_3};
            animation: animStar 260s linear infinite;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 0;
        }}

        /* App container overrides */
        .stApp {{
            background-color: #0a0b14 !important;
            background-image: radial-gradient(ellipse at bottom, #11132a 0%, #05060b 100%) !important;
            font-family: 'Space Grotesk', 'Inter', sans-serif;
            color: #ffffff !important;
        }}

        /* Make sure all markdown text uses the correct font */
        .stMarkdown, div[data-testid="stMarkdownContainer"] p {{
            font-family: 'Inter', sans-serif !important;
            color: #e0e0e0 !important;
        }}

        /* Styled Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: rgba(10, 11, 20, 0.95) !important;
            border-right: 1px solid rgba(79, 195, 247, 0.15) !important;
            backdrop-filter: blur(12px) !important;
        }}

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {{
            color: #ffffff !important;
            font-family: 'Space Grotesk', sans-serif;
        }}

        /* Universal Container Override: custom glassmorphic bordered containers */
        div[data-testid="stBorderedContainer"] {{
            border: 1px solid rgba(79, 195, 247, 0.22) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(8px) !important;
            background: rgba(255, 255, 255, 0.04) !important;
            padding: 24px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }}
        
        div[data-testid="stBorderedContainer"]:hover {{
            transform: translateY(-4px) !important;
            border-color: rgba(179, 136, 255, 0.45) !important;
            box-shadow: 0 12px 40px 0 rgba(79, 195, 247, 0.15), inset 0 0 10px rgba(179, 136, 255, 0.05) !important;
        }}

        /* Custom KPI styles */
        .kpi-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: rgba(255, 255, 255, 0.6) !important;
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
        .kpi-val.blue {{ color: #4fc3f7; text-shadow: 0 0 12px rgba(79, 195, 247, 0.35); }}
        .kpi-val.violet {{ color: #b388ff; text-shadow: 0 0 12px rgba(179, 136, 255, 0.35); }}
        .kpi-val.mint {{ color: #69f0ae; text-shadow: 0 0 12px rgba(105, 240, 174, 0.35); }}
        .kpi-val.red {{ color: #ff5252; text-shadow: 0 0 12px rgba(255, 82, 82, 0.35); }}

        /* Top Navbar Floating Header Styling */
        .navbar-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            border: 1px solid rgba(79, 195, 247, 0.25);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }}

        .navbar-title {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.65rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            background: linear-gradient(45deg, #4fc3f7, #b388ff, #69f0ae);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 15px rgba(79, 195, 247, 0.15);
        }}

        /* Hide default Streamlit elements for clean UI */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        /* Custom scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: rgba(255, 255, 255, 0.02);
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(79, 195, 247, 0.3);
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(179, 136, 255, 0.5);
        }}
    </style>

    <!-- Starfield HTML placeholders -->
    <div class="star-field-1"></div>
    <div class="star-field-2"></div>
    <div class="star-field-3"></div>
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

# CSV File Uploader
uploaded_file = st.sidebar.file_uploader("Upload Student CSV", type=['csv'])

# Dynamic Data Loading
if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)
        
        # Setup initial guesses
        initial_mapping = auto_map_columns(raw_df)
        
        # Schema override expander
        with st.sidebar.expander("⚙️ CSV Schema Mapping", expanded=False):
            st.markdown("<p style='font-size: 0.85rem; color: rgba(255,255,255,0.7);'>We auto-detected these columns. Adjust if needed:</p>", unsafe_allow_html=True)
            
            sel_id = st.selectbox("Student ID", raw_df.columns, index=safe_index(list(raw_df.columns), initial_mapping['student_id']))
            sel_name = st.selectbox("Name", raw_df.columns, index=safe_index(list(raw_df.columns), initial_mapping['name']))
            
            # Optional department
            dept_opts = ["None (Force 'General')"] + list(raw_df.columns)
            dept_idx = safe_index(list(raw_df.columns), initial_mapping['department']) + 1 if initial_mapping['department'] else 0
            sel_dept_choice = st.selectbox("Department", dept_opts, index=dept_idx)
            sel_dept = None if sel_dept_choice == "None (Force 'General')" else sel_dept_choice
            
            # Numeric fields
            sel_gpa = st.selectbox("GPA", raw_df.columns, index=safe_index(list(raw_df.columns), initial_mapping['gpa']))
            sel_att = st.selectbox("Attendance %", raw_df.columns, index=safe_index(list(raw_df.columns), initial_mapping['attendance_pct']))
            
            # Optional Semester
            sem_opts = ["None (Force 'Default Semester')"] + list(raw_df.columns)
            sem_idx = safe_index(list(raw_df.columns), initial_mapping['semester']) + 1 if initial_mapping['semester'] else 0
            sel_sem_choice = st.selectbox("Semester", sem_opts, index=sem_idx)
            sel_sem = None if sel_sem_choice == "None (Force 'Default Semester')" else sel_sem_choice
            
        custom_mapping = {
            'student_id': sel_id,
            'name': sel_name,
            'department': sel_dept,
            'gpa': sel_gpa,
            'attendance_pct': sel_att,
            'semester': sel_sem
        }
        
        df = prepare_data(raw_df, custom_mapping)
        st.sidebar.success("✅ File compiled successfully!")
        
    except Exception as e:
        st.sidebar.error(f"❌ Error loading CSV: {str(e)}")
        st.sidebar.info("Falling back to Space Mock Data.")
        df = generate_mock_data()
else:
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
# 9. Plotly Helpers
# ----------------------------------------------------
def apply_plotly_style(fig, title):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=15, family="Space Grotesk", color="#ffffff"),
            x=0.01,
            y=0.96
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Space Grotesk, sans-serif",
        font_color="#ffffff",
        margin=dict(l=45, r=20, t=55, b=45),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.05)',
            zerolinecolor='rgba(255, 255, 255, 0.08)',
            tickfont=dict(color='rgba(255, 255, 255, 0.7)', family="Inter"),
            title_font=dict(color='rgba(255, 255, 255, 0.8)', size=11, family="Space Grotesk")
        ),
        yaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.05)',
            zerolinecolor='rgba(255, 255, 255, 0.08)',
            tickfont=dict(color='rgba(255, 255, 255, 0.7)', family="Inter"),
            title_font=dict(color='rgba(255, 255, 255, 0.8)', size=11, family="Space Grotesk")
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
                    'A (>=9.0)': '#69f0ae',    # Mint
                    'B (8.0-9.0)': '#4fc3f7',  # Electric Blue
                    'C (7.0-8.0)': '#b388ff',  # Violet
                    'D (5.0-7.0)': '#ffd740',  # Amber
                    'F (<5.0)': '#ff5252'      # Red
                }
            )
            apply_plotly_style(fig_grade, "GRADE DISTRIBUTION")
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
                colorscale=[[0, '#0c0d1b'], [0.4, '#1b1238'], [0.75, '#5c3d99'], [1.0, '#4fc3f7']],
                text=hover_text,
                texttemplate="%{text}",
                textfont={"size": 11, "family": "Space Grotesk", "color": "#ffffff"},
                hovertemplate="Department: %{y}<br>Semester: %{x}<br>Avg Attendance: %{text}<extra></extra>",
                colorbar=dict(
                    title=dict(text="Avg %", font=dict(color="#ffffff", size=9)),
                    tickfont=dict(color="rgba(255, 255, 255, 0.7)", size=9)
                )
            ))
            apply_plotly_style(fig_heatmap, "ATTENDANCE HEATMAP BY DEPT & SEMESTER")
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
                color_discrete_sequence=['#4fc3f7', '#b388ff', '#69f0ae', '#ffd740', '#ff8a80', '#ea80fc'],
                labels={'attendance_pct': 'Attendance %', 'gpa': 'GPA', 'department': 'Department'}
            )
            apply_plotly_style(fig_scatter, "ATTENDANCE VS GPA SCATTER PLOT")
            fig_scatter.update_layout(
                showlegend=True,
                legend=dict(
                    title=None,
                    bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#ffffff', size=9, family="Inter"),
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
                color_continuous_scale=[[0, '#b388ff'], [1.0, '#69f0ae']],
                labels={'gpa': 'Average GPA', 'department': ''}
            )
            apply_plotly_style(fig_dept_gpa, "AVERAGE GPA BY DEPARTMENT")
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
            return ['background-color: rgba(255, 82, 82, 0.12); color: #ff8a80; font-family: Inter; border: 1px solid rgba(255, 82, 82, 0.15);'] * len(row)
        
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
            "<div style='border: 1px solid rgba(105, 240, 174, 0.25); border-radius: 12px; padding: 15px; background: rgba(105, 240, 174, 0.05); color: #69f0ae; font-weight: 500; font-size: 0.95rem;'>"
            "🌌 Zero-Gravity Operational Report: All student systems functioning correctly. Zero at-risk students detected under current telemetry filters."
            "</div>",
            unsafe_allow_html=True
        )
