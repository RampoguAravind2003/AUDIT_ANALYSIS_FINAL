import html
import json
import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account


DEFAULT_PROJECT_ID = "kossip-helpers"
DEFAULT_DATASET = "content_bases_metabase"
DEFAULT_SEMESTER_TABLE = "all_users_question_attempt_details_for_question_set_units"
DEFAULT_ASSESSMENT_TABLE = "all_users_question_attempt_details_for_question_set_units"
DEFAULT_ASSESSMENT_TOPIC_TABLE = "niat_learning_performance_semester_wise_topin_assessment_scores_for_curriculum_team"
DEFAULT_USERS_TABLE = "niat_and_intensive_offline_users_details"
DEFAULT_CONTENT_TABLE = "content_all_products_unit_wise_content_hierarchy_details"
DEFAULT_SCHEDULE_TABLE = "niat_and_intensive_offline_section_wise_daily_learning_schedule_details"
DEFAULT_PROGRESS_TABLE = "niat_learning_progress_course_wise_stats"
DEFAULT_SKILL_GRADED_TABLE = "curriculum_ops_niat_2025_users_batch_wise_skill_and_graded_assessment_scores"
DEFAULT_UNLOCKED_UNITS_TABLE = "curriculum_ops_niat_2025_users_batch_wise_unlocked_units_completion_details"
DEFAULT_QUIZ_ATTEMPTS_TABLE = "curriculum_ops_niat_2025_users_batch_wise_quiz_best_attempts_and_completion_details"
DEFAULT_SESSION_ADHERENCE_TABLE = "curriculum_ops_niat_2025_users_week_wise_session_completion_adherence_details"
DEFAULT_PORTAL_COURSES_TABLE = "curriculum_ops_semester_subject_wise_portal_course_details"

SERIES_RANGES = [
    {"name": "300", "min": 0, "max": 350},
    {"name": "350", "min": 350, "max": 400},
    {"name": "400", "min": 400, "max": 450},
    {"name": "450", "min": 450, "max": 500},
    {"name": "500", "min": 500, "max": 550},
    {"name": "550+", "min": 550, "max": float("inf")},
]

ALLOTTED_HOURS_BY_SEMESTER = {
    "Semester 1": {
        "NRI Institute of Technology": 510,
        "NRI": 510,
        "S-Vyasa": 673,
        "S-VYASA": 673,
        "Annamacharya University": 540,
        "Annamacharya": 540,
        "Vivekananda global University": 464,
        "VGU": 464,
        "NSRIT": 346,
        "NSRIT University": 346,
        "CDU": 522,
        "Chaitanya Deemed-to-be University": 522,
        "A Dy Patil University": 434,
        "A Dy Patil": 434,
        "MRV University": 485,
        "MRV": 485,
        "Malla Reddy Vishwavidyapeeth": 485,
        "Yenepoya University": 544,
        "Yenapoya University": 544,
        "Yenepoya": 544,
        "Noida International": 480,
        "Noida International University": 480,
        "NIU": 480,
        "Chalapathy": 360,
        "Chalapathy (CITY)": 360,
        "Chalapathi": 360,
        "Sanjay Godhawat University": 354,
        "Sanjay Ghodawat University": 354,
        "SGU": 354,
        "Crescent University": 310,
        "Crescent": 310,
        "Academy of Maritime education & Technology": 469,
        "AMET": 469,
        "Takshashila University": 408,
        "Takshasila University": 408,
        "Takshashila": 408,
        "Aurora University": 500,
        "Aurora": 500,
        "NIAT Chevella": 600,
    },
    "Semester 2": {
        "Sanjay Ghodawat University": 730,
        "Sanjay Godhawat University": 730,
        "SGU": 730,
        "Vivekananda global University": 501,
        "VGU": 501,
        "Yenepoya University": 611,
        "Yenapoya University": 611,
        "Yenepoya": 611,
        "S-Vyasa": 597,
        "S-VYASA": 597,
        "A Dy Patil University": 569,
        "A Dy Patil": 569,
        "Takshashila University": 441,
        "Takshasila University": 441,
        "Takshashila": 441,
        "Academy of Maritime education & Technology": 520,
        "AMET": 520,
        "Noida International": 441,
        "Noida International University": 441,
        "NIU": 441,
        "Annamacharya University": 625,
        "Annamacharya": 625,
        "NRI Institute of Technology": 621,
        "NRI": 621,
        "MRV University": 450,
        "MRV": 450,
        "Malla Reddy Vishwavidyapeeth": 450,
        "CDU": 582,
        "Chaitanya Deemed-to-be University": 582,
        "Crescent University": 380,
        "Crescent": 380,
        "Chalapathy": 506,
        "Chalapathy (CITY)": 506,
        "Chalapathi": 506,
        "NSRIT": 489,
        "NSRIT University": 489,
        "Aurora University": 500,
        "Aurora": 500,
        "BITS": 814,
        "NIAT Chevella": 600,
    },
}

SEMESTER_DATES_BY_SEMESTER = {
    "Semester 1": {
        "A Dy Patil University": {"start": "Aug 4, 2025", "end": "Dec 15, 2025"},
        "AMET": {"start": "Sep 1, 2025", "end": "Jan 27, 2026"},
        "Annamacharya University": {"start": "Aug 11, 2025", "end": "Jan 6, 2026"},
        "Aurora University": {"start": "Sep 15, 2025", "end": "Jun 15, 2026"},
        "Chaitanya Deemed-to-be University": {"start": "Aug 4, 2025", "end": "Dec 24, 2025"},
        "Chalapathy (CITY)": {"start": "Aug 25, 2025", "end": "Jan 24, 2026"},
        "Crescent University": {"start": "Sep 8, 2025", "end": "Dec 24, 2025"},
        "Malla Reddy Vishwavidyapeeth": {"start": "Aug 4, 2025", "end": "Dec 31, 2025"},
        "NIAT Chevella": {"start": "Aug 25, 2025", "end": "Jun 6, 2026"},
        "Noida International University": {"start": "Aug 25, 2025", "end": "Dec 22, 2025"},
        "NRI": {"start": "Aug 18, 2025", "end": "Dec 30, 2025"},
        "NSRIT University": {"start": "Aug 18, 2025", "end": "Dec 30, 2025"},
        "S-VYASA": {"start": "Aug 11, 2025", "end": "Jan 20, 2026"},
        "Sanjay Ghodawat University": {"start": "Aug 11, 2025", "end": "Dec 15, 2025"},
        "Takshasila University": {"start": "Sep 15, 2025", "end": "Jan 21, 2026"},
        "Vivekananda global University": {"start": "Aug 25, 2025", "end": "Dec 20, 2025"},
        "Yenapoya University": {"start": "Aug 4, 2025", "end": "Dec 23, 2025"},
    },
    "Semester 2": {
        "Sanjay Ghodawat University": {"start": "Jan 5, 2026", "end": "Jun 13, 2026"},
        "Vivekananda global University": {"start": "Jan 2, 2026", "end": "May 30, 2026"},
        "Yenepoya University": {"start": "Jan 20, 2026", "end": "Jun 5, 2026"},
        "Yenapoya University": {"start": "Jan 20, 2026", "end": "Jun 5, 2026"},
        "S-VYASA": {"start": "Feb 16, 2026", "end": "Jul 7, 2026"},
        "A Dy Patil University": {"start": "Jan 5, 2026", "end": "May 15, 2026"},
        "Takshashila University": {"start": "Feb 9, 2026", "end": "Jun 13, 2026"},
        "Takshasila University": {"start": "Feb 9, 2026", "end": "Jun 13, 2026"},
        "AMET": {"start": "Feb 2, 2026", "end": "Jun 9, 2026"},
        "Noida International University": {"start": "Jan 12, 2026", "end": "Jun 6, 2026"},
        "Noida International": {"start": "Jan 12, 2026", "end": "Jun 6, 2026"},
        "Annamacharya University": {"start": "Jan 2, 2026", "end": "Jun 4, 2026"},
        "NRI": {"start": "Jan 16, 2026", "end": "Jun 20, 2026"},
        "NRI Institute of Technology": {"start": "Jan 16, 2026", "end": "Jun 20, 2026"},
        "MRV University": {"start": "Jan 2, 2026", "end": "May 9, 2026"},
        "Malla Reddy Vishwavidyapeeth": {"start": "Jan 2, 2026", "end": "May 9, 2026"},
        "Chaitanya Deemed-to-be University": {"start": "Jan 19, 2026", "end": "May 18, 2026"},
        "CDU": {"start": "Jan 19, 2026", "end": "May 18, 2026"},
        "Crescent University": {"start": "Jan 19, 2026", "end": "May 19, 2026"},
        "Chalapathy (CITY)": {"start": "Jan 27, 2026", "end": "Jul 11, 2026"},
        "Chalapathy": {"start": "Jan 27, 2026", "end": "Jul 11, 2026"},
        "NSRIT University": {"start": "Feb 9, 2026", "end": "Jul 13, 2026"},
        "NSRIT": {"start": "Feb 9, 2026", "end": "Jul 13, 2026"},
        "Aurora University": {"start": "Aug 12, 2025", "end": "Feb 22, 2026"},
        "BITS": {"start": "Jan 28, 2026", "end": "Aug 15, 2026"},
    },
}


ASSESSMENT_SLOTS_BY_SEMESTER = {
    "Semester 1": 75,
    "Semester 2": 75,
}

DELIVERY_MODE_BY_SEMESTER = {
    "Semester 2": {
        "BITS": "Hybrid Delivery",
        "Sanjay Ghodawat University": "Co Delivery",
        "Annamacharya University": "Co Delivery",
        "NRI Institute of Technology": "Co Delivery",
        "Yenepoya University": "Co Delivery",
        "S-VYASA": "Co Delivery",
        "CDU": "Co Delivery",
        "A Dy Patil University": "Full Delivery",
        "AMET": "Full Delivery",
        "Chalapathy": "Hybrid Delivery",
        "Vivekananda global University": "Full Delivery",
        "NSRIT": "Hybrid Delivery",
        "MRV University": "Full Delivery",
        "Takshashila University": "Co Delivery",
        "Noida International": "Co Delivery",
        "Crescent University": "Co Delivery",
    },
}

WORKING_DAYS_BY_SEMESTER = {
    "Semester 2": {
        "BITS": 127,
        "Sanjay Ghodawat University": 115,
        "Annamacharya University": 100,
        "NRI Institute of Technology": 116,
        "Yenepoya University": 98,
        "S-VYASA": 84,
        "CDU": 83.5,
        "A Dy Patil University": 92,
        "AMET": 85,
        "Chalapathy": 83,
        "Vivekananda global University": 72,
        "NSRIT": 109,
        "MRV University": 75,
        "Takshashila University": 86,
        "Noida International": 86,
        "Crescent University": 65,
    },
}

EXECUTION_DAYS_BY_SEMESTER = {
    "Semester 2": {
        "BITS": 116,
        "Sanjay Ghodawat University": 104,
        "Annamacharya University": 89,
        "NRI Institute of Technology": 104,
        "Yenepoya University": 87,
        "S-VYASA": 75,
        "CDU": 74,
        "A Dy Patil University": 81,
        "AMET": 74,
        "Chalapathy": 72,
        "Vivekananda global University": 63,
        "NSRIT": 70,
        "MRV University": 64,
        "Takshashila University": 74,
        "Noida International": 74,
        "Crescent University": 54,
    },
}

EXECUTION_WEEKS_BY_SEMESTER = {
    "Semester 2": {
        "BITS": 23.2,
        "Sanjay Ghodawat University": 17.33333333,
        "Annamacharya University": 15,
        "NRI Institute of Technology": 17,
        "Yenepoya University": 14.5,
        "S-VYASA": 15,
        "CDU": 12.33333333,
        "A Dy Patil University": 13.5,
        "AMET": 12.33333333,
        "Chalapathy": 12,
        "Vivekananda global University": 10.5,
        "NSRIT": 10,
        "MRV University": 10.66666667,
        "Takshashila University": 12.33333333,
        "Noida International": 12.33333333,
        "Crescent University": 10.8,
    },
}

COURSE_MAPPING_BY_SEMESTER = {
    "Semester 1": {
        "GENERATIVE_AI": "Introduction to Generative AI",
        "MATHEMATICS": "Mathematics",
        "BUILD_YOUR_OWN_STATIC_WEBSITE": "Web Application Development 1",
        "COMMUNICATIVE_ENGLISH_FOUNDATION": "Communicative English Foundation",
        "PROGRAMMING_FOUNDATIONS": "Computer Programming",
        "QUANTITATIVE_APTITUDE": "Numerical Ability",
        "ENGINEERING_GRAPHICS": "Engineering Drawing",
    },
    "Semester 2": {
        "WEB_APPLICATION_DEVELOPMENT_2": "Web Application Development 2",
        "WA2": "Web Application Development 2",
        "DBMS": "Database Management Systems",
        "DATABASE_MANAGEMENT": "Database Management Systems",
        "DATA_STRUCTURES": "Data Structures",
        "DS": "Data Structures",
        "NUMERICAL_APTITUDE": "Numerical Ability",
        "NA": "Numerical Ability",
        "QUANTITATIVE_APTITUDE": "Numerical Ability",
        "ENGLISH_ADVANCED": "Advanced Communicative English",
        "EA": "Advanced Communicative English",
        "COMMUNICATIVE_ENGLISH_FOUNDATION": "Advanced Communicative English",
        "BUSINESS_ENGLISH": "Advanced Communicative English",
        "BE": "Basic Electronics",
        "LLM": "Building LLM Applications",
        "LARGE_LANGUAGE_MODELS": "Building LLM Applications",
        "GENERATIVE_AI": "Building LLM Applications",
        "PHYSICS": "Physics",
        "PHY": "Physics",
        "CHEMISTRY": "Chemistry",
        "CHE": "Chemistry",
        "YOGA": "Yoga and Wellness",
        "TDP": "Internship / Projects",
        "HVS": "Humanities and Constitution",
        "HUMAN_VALUES": "Humanities and Constitution",
        "ASSESSMENT": "Assessment",
        "AS": "Basic Electrical Engineering",
        "IKS": "Indian Knowledge Systems",
        "INDIAN_KNOWLEDGE_SYSTEM": "Indian Knowledge Systems",
        "LINEAR_ALGEBRA": "Mathematics",
        "LA_C": "Mathematics",
        "ENVIRONMENTAL_SCIENCE": "Environmental Studies",
        "ENV": "Environmental Studies",
        "INDIAN_CONSTITUTION": "Humanities and Constitution",
        "IC": "Humanities and Constitution",
        "LANGUAGE_ELECTIVE": "Foreign Language",
        "LA_E": "Foreign Language",
        "ENGINEERING_DRAWING": "Engineering Drawing",
        "ED": "Engineering Drawing",
        "CO_CURRICULAR_ACTIVITIES": "Co-curricular Activities",
        "CC": "Co-curricular Activities",
        "CLOUD_COMPUTING": "Cloud Computing",
        "PROGRAMMING_FOUNDATIONS": "Data Structures",
        "BUILD_YOUR_OWN_STATIC_WEBSITE": "Web Application Development 2",
        "MATHEMATICS": "Mathematics",
    },
}

COURSE_ALIAS_GROUPS_BY_SEMESTER = {
    "Semester 1": {
        "Introduction to Generative AI": [
            "generative ai",
            "introduction to generative ai",
            "workshop technology introduction to generative ai",
        ],
        "Mathematics": [
            "mathematics",
            "mathematics for computer science",
            "engineering mathematics 1",
            "discrete mathematics",
            "linear algebra and optimization",
            "mathematics for computing",
            "mathematics for data science i",
            "logical mathematics for software engineers i",
            "calculus and differential equations",
        ],
        "Web Application Development 1": [
            "build your own static website",
            "build your own responsive website",
            "modern responsive web design",
            "responsive web design using flexbox",
            "html css",
            "web application development i",
            "web application development 1",
            "frontend development 1",
            "frontend development fundamentals",
            "fundamentals of web development",
            "web technologies",
            "web technologies laboratory",
            "web application development 1 laboratory",
        ],
        "Communicative English Foundation": [
            "communicative english foundation",
            "communication english foundation",
            "english foundation",
            "aec 1",
            "cambridge english b1",
            "writing practice",
        ],
        "Computer Programming": [
            "programming foundations",
            "programing foundation",
            "python programming",
            "problem solving with python programming",
            "computer programming",
            "introduction to niat",
            "niat practice page",
            "logical thinking",
            "oops",
            "more python problem solving",
            "introduction to programming",
            "problem solving using programming i",
            "problem solving with python",
            "problem solving with python programming 1",
            "computer programming laboratory",
            "problem solving using programming i laboratory",
            "computer systems and their fundaments",
            "developer foundations",
            "introduction to computing systems",
        ],
        "Numerical Ability": [
            "quantitative aptitude",
            "numerical aptitude",
        ],
        "Physics": [
            "applied physics for data science",
            "applied physics for data science lab",
            "fundamentals of quantum computing",
        ],
        "Basic Electrical Engineering": [
            "basic electrical electronics engineering",
        ],
        "Basic Electronics": [
            "basic electronics",
        ],
        "Foreign Language": [
            "foreign language 1",
            "foreign language - 1",
            "foreign language",
        ],
        "Yoga and Wellness": [
            "essence of yoga",
            "physical wellness and yoga",
        ],
        "Indian Knowledge Systems": [
            "indian knowledge system",
        ],
        "Internship / Projects": [
            "trans disciplinary project",
        ],
        "Co-curricular Activities": [
            "co curricular activities i",
            "co curricular activities - i",
            "induction training",
        ],
        "Environmental Studies": [
            "mnc i evs",
        ],
        "Humanities and Constitution": [
            "uhv2",
        ],
        "University Electives": [
            "elective i",
            "sec 1",
            "vac 1",
            "professional skills for engineers",
        ],
        "Engineering Drawing": [
            "engineering graphics",
        ],
    },
    "Semester 2": {
        "Web Application Development 2": [
            "web application development 2",
            "web application development 2 laboratory",
            "front end full stack development",
            "front end full stack development laboratory",
            "frontend development 2",
            "frontend development advanced",
            "build your own dynamic web application",
            "js essentials",
            "javascript essentials",
            "js programming",
            "introduction to react js",
            "react js",
            "js essentials",
            "introduction to react js",
        ],
        "Database Management Systems": [
            "database management systems",
            "database management systems laboratory",
            "introduction to database",
            "introduction to databases",
            "introduction to database management systems",
            "introduction to database management systems lab",
            "introduction to dbms",
            "dbms fundamentals",
            "mongodb",
        ],
        "Data Structures": [
            "data structures",
            "data structures laboratory",
            "data structures and algorithm",
            "data structures and algorithms",
            "data structures and algorithms laboratory",
            "data structures using c++",
            "problem solving techniques with c++",
            "datastructures and ai",
            "datastructures and ai laboratory",
            "dsa",
            "dsa foundation",
            "dsa level 1",
            "dsa extra coding questions",
            "dsa beginner",
            "niat dsa",
            "academy dsa",
            "phase 1 data structures and algorithms",
            "foundations of data structures and algorithms",
        ],
        "Numerical Ability": [
            "numerical aptitude",
            "quantitative aptitude",
            "numerical ability",
        ],
        "Advanced Communicative English": [
            "english advanced",
            "advanced communicative english",
            "advanced technical english",
            "communicative english advanced",
            "technical communication for engineers",
            "aec 2",
            "english b1 level learner program",
        ],
        "Building LLM Applications": [
            "large language models",
            "llm",
            "generative ai",
            "building llm applications",
            "foundations of generative ai",
            "building rest api s with flask",
            "building rest apis with flask",
        ],
        "Physics": [
            "engineering physics",
            "engineering physics laboratory",
            "modern physics",
            "quantum physics",
            "fqc",
        ],
        "Chemistry": [
            "engineering chemistry laboratory",
            "material chemistry for cse",
        ],
        "Yoga and Wellness": [
            "application of yoga in mind body management",
            "yoga",
        ],
        "Indian Knowledge Systems": [
            "indian knowledge systems",
            "indian knowledge system",
        ],
        "Mathematics": [
            "engineering mathematics 2",
            "linear algebra and calculus",
            "mathematics for problem solving",
            "logical mathematics for software engineers ii",
            "probability and statistics",
            "linear algebra",
            "linear algebra calculus",
            "calculus",
        ],
        "Environmental Studies": [
            "environmental science",
            "environmental science university slot",
            "environmental sciences",
            "environmental studies",
        ],
        "Humanities and Constitution": [
            "constitution of india",
            "universal human values",
            "human values",
            "human values ethics",
            "hvs",
        ],
        "Foreign Language": [
            "foreign language 2",
            "foreign language -2",
            "foreign language",
            "language elective",
            "la e",
        ],
        "Engineering Drawing": [
            "engineering drawing",
            "computer aided engineering graphics",
            "caeg",
            "design drafting",
        ],
        "Basic Electrical Engineering": [
            "applied science",
            "applied science basic electrical engineering",
            "basic electrical engineering",
        ],
        "Basic Electronics": [
            "basic electronics",
        ],
        "Backend Development": [
            "back end development",
            "back end development node js mongodb",
        ],
        "Command Line Interfaces and Scripting": [
            "command line interfaces and scripting",
        ],
        "Object Oriented Programming": [
            "object oriented programming",
            "introduction to logic",
        ],
        "Co-curricular Activities": [
            "co curricular activities - 2",
            "co curricular activities 2",
        ],
        "Internship / Projects": [
            "internship",
            "trans disciplinary project",
            "tdp",
        ],
        "Assessment": [
            "assessment",
            "module test",
            "module exam",
            "mid exam",
            "mid test",
            "internal exam",
            "internal test",
        ],
        "Biology": [
            "foundation option 1 general biology",
        ],
        "University Electives": [
            "sec 2",
            "vac 2",
            "base 44 workshop",
            "university slot",
        ],
        "Cloud Computing": [
            "cloud computing",
        ],
    },
}


NON_CORE_COURSES_BY_SEMESTER = {
    "Semester 1": {
        "Assessment",
        "Module Quiz",
    },
    "Semester 2": {
        "Assessment",
        "Module Quiz",
    },
}


def get_config(key: str, default: str = "") -> str:
    if key in st.secrets:
        return str(st.secrets[key])
    return os.getenv(key, default)


def sql_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def to_iso_date(value: str) -> str:
    if not value:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    return datetime.strptime(value, "%b %d, %Y").strftime("%Y-%m-%d")


def shift_iso_date(iso_date: str, year_delta: int = 0) -> str:
    if not iso_date or year_delta == 0:
        return iso_date
    parts = [int(part) for part in iso_date.split("-")]
    return f"{parts[0] + year_delta:04d}-{parts[1]:02d}-{parts[2]:02d}"


def should_apply_batch_filter(batch: str) -> bool:
    return bool(batch and batch.strip() and not re.match(r"^niat\s+\d+$", batch.strip(), re.IGNORECASE))


def get_batch_year_shift(batch: str) -> int:
    match = re.match(r"^niat\s+(\d{2})$", batch.strip(), re.IGNORECASE) if batch else None
    return int(match.group(1)) - 25 if match else 0


def get_date_based_available_semesters(batch: str):
    today = datetime.now().date()
    available = []
    for semester_name, windows in SEMESTER_DATES_BY_SEMESTER.items():
        shifted_starts = []
        for window in windows.values():
            shifted_start = shift_iso_date(to_iso_date(window["start"]), get_batch_year_shift(batch))
            if shifted_start:
                shifted_starts.append(datetime.strptime(shifted_start, "%Y-%m-%d").date())
        if shifted_starts and min(shifted_starts) <= today:
            available.append(semester_name)
    return sorted(available, key=lambda value: int(re.search(r"\d+", value).group()))


@st.cache_data(ttl=600, show_spinner=False)
def fetch_available_semesters_for_batch(batch: str):
    refs = get_table_refs()
    checks = []
    for semester_name in sorted(SEMESTER_DATES_BY_SEMESTER.keys(), key=lambda value: int(re.search(r"\d+", value).group())):
        where_clauses = ["TRIM(COALESCE(s.institute_name, '')) != ''"]
        window_clause = get_semester_window_clause(semester_name, batch, "s.institute_name", "DATE(s.session_date)")
        if window_clause:
            where_clauses.append(window_clause)
        if should_apply_batch_filter(batch):
            where_clauses.append(f"LOWER(COALESCE(s.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")
        checks.append(
            f"SELECT '{sql_escape(semester_name)}' AS semester, COUNT(1) AS row_count FROM {refs['schedule']} s WHERE {' AND '.join(where_clauses)}"
        )
    if not checks:
        return []
    sql = " UNION ALL ".join(checks)
    results = run_query(sql)
    available = results[results["row_count"] > 0]["semester"].tolist() if not results.empty else []
    return sorted(available, key=lambda value: int(re.search(r"\d+", value).group()))


def get_available_semesters_for_batch(batch: str):
    try:
        available = fetch_available_semesters_for_batch(batch)
        if available:
            return available
    except Exception:
        pass
    return get_date_based_available_semesters(batch)


def get_semester_window_clause(semester: str, batch: str, institute_expr: str, date_expr: str) -> str:
    windows = SEMESTER_DATES_BY_SEMESTER.get(semester)
    if not windows:
        return ""
    year_shift = get_batch_year_shift(batch)
    clauses = []
    for institute_name, window in windows.items():
        start = shift_iso_date(to_iso_date(window["start"]), year_shift)
        end = shift_iso_date(to_iso_date(window["end"]), year_shift)
        clauses.append(
            f"(LOWER({institute_expr}) = '{sql_escape(institute_name.lower())}' AND {date_expr} BETWEEN '{start}' AND '{end}')"
        )
    return f"({' OR '.join(clauses)})" if clauses else ""


def get_course_mapping(semester: str) -> dict:
    return COURSE_MAPPING_BY_SEMESTER.get(semester, COURSE_MAPPING_BY_SEMESTER["Semester 1"])


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


QUIZ_ALIAS_PATTERNS = [
    "module quiz",
    "module quizzes",
    "quiz",
    "quizzes",
    "skill assessment",
    "skill assessments",
]


def normalize_course_name(course_name: str, semester: str) -> str:
    raw = str(course_name or "").strip()
    if not raw:
        return raw
    course_map = get_course_mapping(semester)
    if raw in course_map:
        return course_map[raw]
    normalized_raw = normalize_text(raw)
    if any(pattern in normalized_raw for pattern in QUIZ_ALIAS_PATTERNS):
        return "Module Quiz"
    alias_groups = COURSE_ALIAS_GROUPS_BY_SEMESTER.get(semester, {})
    for canonical_name, aliases in alias_groups.items():
        if any(normalized_raw == normalize_text(alias) or normalize_text(alias) in normalized_raw for alias in aliases):
            return canonical_name
    return raw


def get_allotted_hours(name: str, semester: str):
    sem_hours = ALLOTTED_HOURS_BY_SEMESTER.get(semester, ALLOTTED_HOURS_BY_SEMESTER["Semester 1"])
    if name in sem_hours:
        return sem_hours[name]
    lowered = name.lower()
    for key, value in sem_hours.items():
        if lowered.find(key.lower().split(" ")[0]) != -1:
            return value
    return None


def get_semester_dates_for_institute(name: str, semester: str, batch: str = ""):
    sem_dates = SEMESTER_DATES_BY_SEMESTER.get(semester, SEMESTER_DATES_BY_SEMESTER["Semester 1"])
    matched_dates = None
    if name in sem_dates:
        matched_dates = sem_dates[name]
    else:
        lowered = name.lower()
        for key, value in sem_dates.items():
            if lowered.find(key.lower().split(" ")[0]) != -1:
                matched_dates = value
                break
    if matched_dates is None:
        return None
    if not batch:
        return matched_dates
    year_shift = get_batch_year_shift(batch)
    return {
        "start": shift_iso_date(to_iso_date(matched_dates["start"]), year_shift),
        "end": shift_iso_date(to_iso_date(matched_dates["end"]), year_shift),
    }


def format_display_date(value: str) -> str:
    if not value:
        return "--"
    iso_value = to_iso_date(value)
    return datetime.strptime(iso_value, "%Y-%m-%d").strftime("%d/%m/%Y")


def format_today_display_date() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def count_weekdays_between(start_iso: str, end_iso: str):
    if not start_iso or not end_iso:
        return None
    start_date = datetime.strptime(start_iso, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_iso, "%Y-%m-%d").date()
    if end_date < start_date:
        return None
    total = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            total += 1
        current += pd.Timedelta(days=1)
    return total


def calculate_expected_slots_to_date(dates: dict | None, allotted_hours):
    if not dates or allotted_hours is None:
        return None
    start_date = datetime.strptime(dates["start"], "%Y-%m-%d").date()
    end_date = datetime.strptime(dates["end"], "%Y-%m-%d").date()
    today = datetime.now().date()
    if today < start_date:
        return 0
    # Pace expected slots across the full semester window so the number only
    # reaches the allotted total once the configured end date is reached.
    total_working_days = count_weekdays_between(dates["start"], dates["end"])
    if not total_working_days:
        return None
    effective_date = min(today, end_date)
    elapsed_weekdays = count_weekdays_between(dates["start"], effective_date.strftime("%Y-%m-%d"))
    if elapsed_weekdays is None:
        return None
    elapsed_working_days = min(float(elapsed_weekdays), float(total_working_days))
    slots_per_day = float(allotted_hours) / float(total_working_days)
    return min(float(allotted_hours), elapsed_working_days * slots_per_day)


def calculate_completion_from_actual(actual_sessions, scheduled_sessions):
    if actual_sessions is None or scheduled_sessions is None:
        return None
    if float(scheduled_sessions) <= 0:
        return None
    return min(100.0, (float(actual_sessions) / float(scheduled_sessions)) * 100.0)


def estimate_scheduled_sessions(session_df: pd.DataFrame):
    if session_df.empty:
        return 0.0
    scheduled_total = 0.0
    for _, row in session_df.iterrows():
        completed_sessions = pd.to_numeric(row.get("sessions"), errors="coerce")
        completion_percent = pd.to_numeric(row.get("completion"), errors="coerce")
        if pd.isna(completed_sessions) or float(completed_sessions) <= 0:
            continue
        if pd.isna(completion_percent) or float(completion_percent) <= 0:
            scheduled_total += float(completed_sessions)
            continue
        scheduled_total += float(completed_sessions) / (float(completion_percent) / 100.0)
    return scheduled_total


def get_semester_config_value(name: str, semester: str, config_by_semester: dict):
    semester_values = config_by_semester.get(semester, {})
    if name in semester_values:
        return semester_values[name]
    lowered = name.lower()
    for key, value in semester_values.items():
        if lowered.find(key.lower().split(" ")[0]) != -1:
            return value
    return None


def build_university_timeline_rows(universities, semester: str, batch: str):
    assessment_slots = ASSESSMENT_SLOTS_BY_SEMESTER.get(semester, 0)
    rows = []
    for item in sorted(universities, key=lambda value: value["name"]):
        university_name = item["name"]
        dates = get_semester_dates_for_institute(university_name, semester, batch)
        allotted_hours = item.get("allottedHours")
        working_days = get_semester_config_value(university_name, semester, WORKING_DAYS_BY_SEMESTER)
        execution_days = get_semester_config_value(university_name, semester, EXECUTION_DAYS_BY_SEMESTER)
        execution_weeks = get_semester_config_value(university_name, semester, EXECUTION_WEEKS_BY_SEMESTER)
        if working_days is None and dates:
            working_days = count_weekdays_between(dates["start"], dates["end"])
        if execution_days is None and allotted_hours is not None:
            execution_days = round(allotted_hours / 7)
        if execution_weeks is None and execution_days is not None:
            execution_weeks = round(execution_days / 6, 1)
        expected_slots = calculate_expected_slots_to_date(dates, allotted_hours)
        rows.append(
            {
                "University": university_name,
                "Start Date": format_display_date(dates["start"]) if dates else "--",
                "End Date": format_display_date(dates["end"]) if dates else "--",
                "Delivery Mode": get_semester_config_value(university_name, semester, DELIVERY_MODE_BY_SEMESTER) or "--",
                "Working Days": round(float(working_days), 1) if working_days is not None else None,
                "Total NIAT Slots": round(float(allotted_hours) + assessment_slots, 1) if allotted_hours is not None else None,
                "NIAT Assessment Slots": assessment_slots,
                "Net NIAT Executional Slots": round(float(allotted_hours), 1) if allotted_hours is not None else None,
                "Expected Slots": round(float(expected_slots), 1) if expected_slots is not None else None,
                "Total NIAT Executional Days": round(float(execution_days), 1) if execution_days is not None else None,
                "Net NIAT No. of Weeks": round(float(execution_weeks), 1) if execution_weeks is not None else None,
            }
        )
    return pd.DataFrame(rows)



def build_university_overview_rows(
    universities,
    semester: str,
    batch: str,
    progress_slots_df: pd.DataFrame | None = None,
    new_metrics: dict | None = None,
):
    """
    Builds the University Overview table with all 20 requested fields.

    New metrics dict structure (keyed by institute name):
      new_metrics["quiz"][institute]         → classroom_quiz_attempt_pct, classroom_quiz_pass_pct,
                                               module_quiz_conducted, module_quiz_participation_pct, module_quiz_pass_pct
      new_metrics["practice"][institute]    → practice_completion_pct
      new_metrics["delivery"][institute]    → practice_delivery_pct, module_quiz_conduction_pct, skill_conduction_pct
      new_metrics["skill_graded"][institute]→ skill_conducted, skill_participation_pct, skill_pass_pct, academic_attempt_pct, academic_pass_pct

    Metric formulas:
      Deviation %            = (Actual - Expected Till Date) / Expected Till Date × 100  (negative = behind)
      Session Delivery %     = (Actual Slots Delivered Till Date / Expected Slots Till Date) × 100
      Practice Delivery %    = (practice_delivered_count / planned_practice_sessions) × 100
      Module Quiz Conduction %  = (module_quiz_conducted / planned_module_quizzes) × 100
      Skill Assessment Conduction % = (skill_conducted / planned_skill_assessments) × 100

    Pass threshold: ≥80% score throughout.
    """
    timeline_df = build_university_timeline_rows(universities, semester, batch)

    # ── progress slots (existing) ─────────────────────────────────────────────
    progress_slots: dict = {}
    if progress_slots_df is not None and not progress_slots_df.empty:
        progress_slots = {
            row["institute"]: {
                "delivered_slots": float(row["delivered_slots"]) if pd.notna(row.get("delivered_slots")) else None,
                "lecture_completion_pct": float(row["lecture_completion_pct"]) if pd.notna(row.get("lecture_completion_pct")) else None,
                "practice_completion_pct": float(row["practice_completion_pct"]) if pd.notna(row.get("practice_completion_pct")) else None,
            }
            for _, row in progress_slots_df.dropna(subset=["institute"]).iterrows()
        }

    # ── new metrics lookups ───────────────────────────────────────────────────
    nm = new_metrics or {}
    quiz_data: dict         = nm.get("quiz", {})
    practice_data: dict     = nm.get("practice", {})
    delivery_data: dict     = nm.get("delivery", {})   # from session_adherence
    skill_graded_data: dict = nm.get("skill_graded", {})

    def _get(d: dict, institute: str, key: str):
        row = d.get(institute, {})
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return float(val)

    def _pct(numerator, denominator):
        """Safe percentage: returns None if denominator is zero/None."""
        if numerator is None or denominator is None or denominator == 0:
            return None
        return round(min((numerator / denominator) * 100, 999.9), 1)

    metric_rows = []
    for item in sorted(universities, key=lambda v: v["name"]):
        name = item["name"]

        # ── Actual slots delivered till date ──────────────────────────────────
        delivered = _get(progress_slots, name, "delivered_slots")
        if delivered is None:
            delivered = item.get("avgLecturePracticeSessions", 0)
        allotted = item.get("allottedHours")
        if allotted is not None:
            delivered = min(delivered, float(allotted))
        actual_slots = round(delivered, 1)

        # ── Expected slots till date (from timeline) ──────────────────────────
        # Will be filled after merging with timeline_df; placeholder here.
        # We store actual_slots per university and compute derivations post-merge.

        metric_rows.append({
            "University": name,
            "Actual Slots Delivered Till Date": actual_slots,
            # ── Session Delivery % replaces old Session completion % ───────────
            # Computed post-merge once Expected Slots Till Date is available.
            # ── Practice Completion % (from unlocked_units; fallback to progress table) ──
            "Practice Completion %": round(v, 1) if (v := _get(practice_data, name, "practice_completion_pct")) is not None
                else (round(v2, 1) if (v2 := _get(progress_slots, name, "practice_completion_pct")) is not None else None),
            # ── Classroom Quizzes ─────────────────────────────────────────────
            "Class Room Quizzes Attempt %": round(v, 1) if (v := _get(quiz_data, name, "classroom_quiz_attempt_pct")) is not None else None,
            "Class Room Quizzes Pass %":    round(v, 1) if (v := _get(quiz_data, name, "classroom_quiz_pass_pct")) is not None else None,
            # ── Practice Delivery % (from session_adherence) ─────────────────
            "Practice Delivery %":          round(v, 1) if (v := _get(delivery_data, name, "practice_delivery_pct")) is not None else None,
            # ── Module Quiz ───────────────────────────────────────────────────
            "Module Quiz Conduction %":     round(v, 1) if (v := _get(delivery_data, name, "module_quiz_conduction_pct")) is not None else None,
            "Module Quiz Student Participation %": round(v, 1) if (v := _get(quiz_data, name, "module_quiz_participation_pct")) is not None else None,
            "Module Quiz Pass %":           round(v, 1) if (v := _get(quiz_data, name, "module_quiz_pass_pct")) is not None else None,
            # ── Skill Assessment ──────────────────────────────────────────────
            "Skill Assessment Conduction %":    round(v, 1) if (v := _get(delivery_data, name, "skill_conduction_pct")) is not None else None,
            "Skill Assessment Student Participation %": round(v, 1) if (v := _get(skill_graded_data, name, "skill_participation_pct")) is not None else None,
            "Skill Assessment Pass %":      round(v, 1) if (v := _get(skill_graded_data, name, "skill_pass_pct")) is not None else None,
            # ── Academic Assessments ──────────────────────────────────────────
            "Academic Assessments Attempt %": round(v, 1) if (v := _get(skill_graded_data, name, "academic_attempt_pct")) is not None else None,
            "Academic Assessments Pass %":    round(v, 1) if (v := _get(skill_graded_data, name, "academic_pass_pct")) is not None else None,
        })

    if not metric_rows:
        return timeline_df

    metric_df = pd.DataFrame(metric_rows)
    overview_df = timeline_df.merge(metric_df, on="University", how="left").reset_index(drop=True)

    # ── Derived columns that need Expected Slots Till Date ────────────────────
    # timeline_df already has "Expected Slots" = paced value (slots expected till today).
    # We rename that to "Expected Slots Till Date", then set "Expected Slots" = full-semester total.
    overview_df["Expected Slots Till Date"] = overview_df["Expected Slots"]   # paced-to-date from timeline
    overview_df["Expected Slots"] = overview_df["Net NIAT Executional Slots"] # full semester total

    def _row_pct(row, num_col, denom_col):
        num = row.get(num_col)
        den = row.get(denom_col)
        if num is None or den is None or pd.isna(num) or pd.isna(den) or den == 0:
            return None
        return round(min((float(num) / float(den)) * 100, 999.9), 1)

    overview_df["Session Delivery %"] = overview_df.apply(
        lambda r: _row_pct(r, "Actual Slots Delivered Till Date", "Expected Slots Till Date"), axis=1
    )
    overview_df["Deviation %"] = overview_df.apply(
        lambda r: round(
            (float(r["Actual Slots Delivered Till Date"]) - float(r["Expected Slots Till Date"]))
            / float(r["Expected Slots Till Date"]) * 100, 1
        )
        if pd.notna(r.get("Expected Slots Till Date")) and float(r.get("Expected Slots Till Date", 0) or 0) != 0
        else None,
        axis=1,
    )
    # Practice Delivery %, Module Quiz Conduction %, Skill Assessment Conduction %
    # are already computed per-institute in fetch_session_delivery_metrics and
    # stored directly in metric_rows — no post-merge calculation needed.

    # ── Rename and filter ─────────────────────────────────────────────────────
    overview_df = overview_df.rename(columns={"University": "Universities"})
    overview_df = overview_df[
        overview_df["Universities"].astype(str).str.strip().str.casefold() != "aurora university"
    ].reset_index(drop=True)

    return overview_df[
        [
            "Universities",
            "Delivery Mode",
            "Start Date",
            "End Date",
            "Expected Slots",
            "Expected Slots Till Date",
            "Actual Slots Delivered Till Date",
            "Deviation %",
            "Session Delivery %",
            "Class Room Quizzes Attempt %",
            "Class Room Quizzes Pass %",
            "Practice Delivery %",
            "Practice Completion %",
            "Module Quiz Conduction %",
            "Module Quiz Student Participation %",
            "Module Quiz Pass %",
            "Skill Assessment Conduction %",
            "Skill Assessment Student Participation %",
            "Skill Assessment Pass %",
            "Academic Assessments Attempt %",
            "Academic Assessments Pass %",
        ]
    ]


def get_available_sections(data_df: pd.DataFrame, university_name: str):
    if data_df.empty or not university_name:
        return []
    section_values = data_df[data_df["institute"] == university_name]["section"].dropna().unique().tolist()
    return sorted([section for section in section_values if section and str(section).strip().lower() != "unknown"])



def queue_course_breakdown_navigation(university_name: str):
    if university_name:
        st.session_state["pending_selected_university"] = university_name
        st.session_state["pending_selected_section_label"] = "All Sections"
        st.session_state["pending_current_view"] = "Course Breakdown"



def queue_overview_navigation():
    st.session_state["pending_selected_section_label"] = "All Sections"
    st.session_state["pending_current_view"] = "University Overview"



def open_course_breakdown_from_timeline():
    queue_course_breakdown_navigation(st.session_state.get("timeline_selected_university"))


def apply_pending_navigation_state(active_universities, available_sections):
    pending_university = st.session_state.pop("pending_selected_university", None)
    pending_section = st.session_state.pop("pending_selected_section_label", None)
    pending_view = st.session_state.pop("pending_current_view", None)
    if pending_university in active_universities:
        st.session_state["selected_university"] = pending_university
    if pending_section in available_sections:
        st.session_state["selected_section_label"] = pending_section
    elif pending_section:
        st.session_state["selected_section_label"] = "All Sections"
    if pending_view:
        st.session_state["current_view"] = pending_view


def get_series_for_value(value: float) -> dict:
    for series in SERIES_RANGES:
        if value >= series["min"] and value < series["max"]:
            return series
    return SERIES_RANGES[-1]


def get_series_for_allotted_hours(name: str, semester: str):
    hours = get_allotted_hours(name, semester)
    if hours is None:
        return None
    return get_series_for_value(hours)



@st.cache_resource(show_spinner=False)
def get_bigquery_client():
    project_id = get_config("BQ_PROJECT_ID", DEFAULT_PROJECT_ID)

    credentials = service_account.Credentials.from_service_account_file(
        "service-account.json"
    )

    return bigquery.Client(
        project=project_id,
        credentials=credentials
    )


def format_table_ref(table_ref: str, default_table: str) -> str:
    project_id = get_config("BQ_PROJECT_ID", DEFAULT_PROJECT_ID)
    dataset = get_config("BQ_DATASET", DEFAULT_DATASET)
    raw = table_ref.strip() if table_ref else default_table
    parts = [part.strip() for part in raw.split(".") if part.strip()]
    if len(parts) == 3:
        return f"`{parts[0]}.{parts[1]}.{parts[2]}`"
    if len(parts) == 2:
        return f"`{project_id}.{parts[0]}.{parts[1]}`"
    return f"`{project_id}.{dataset}.{parts[0]}`"


def resolve_table_parts(table_ref: str, default_table: str):
    project_id = get_config("BQ_PROJECT_ID", DEFAULT_PROJECT_ID)
    dataset = get_config("BQ_DATASET", DEFAULT_DATASET)
    raw = table_ref.strip() if table_ref else default_table
    parts = [part.strip("` ").strip() for part in raw.split(".") if part.strip("` ").strip()]
    if len(parts) == 3:
        return {"project": parts[0], "dataset": parts[1], "table": parts[2]}
    if len(parts) == 2:
        return {"project": project_id, "dataset": parts[0], "table": parts[1]}
    return {"project": project_id, "dataset": dataset, "table": parts[0]}


def get_table_refs():
    return {
        "semester": format_table_ref(get_config("BQ_SEMESTER_TABLE", DEFAULT_SEMESTER_TABLE), DEFAULT_SEMESTER_TABLE),
        "assessment": format_table_ref(get_config("BQ_ASSESSMENT_TABLE", DEFAULT_ASSESSMENT_TABLE), DEFAULT_ASSESSMENT_TABLE),
        "assessment_topic": format_table_ref(
            get_config("BQ_ASSESSMENT_TOPIC_TABLE", DEFAULT_ASSESSMENT_TOPIC_TABLE),
            DEFAULT_ASSESSMENT_TOPIC_TABLE,
        ),
        "users": format_table_ref(get_config("BQ_USERS_TABLE", DEFAULT_USERS_TABLE), DEFAULT_USERS_TABLE),
        "content": format_table_ref(get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE), DEFAULT_CONTENT_TABLE),
        "schedule": format_table_ref(get_config("BQ_SCHEDULE_TABLE", DEFAULT_SCHEDULE_TABLE), DEFAULT_SCHEDULE_TABLE),
        "progress": format_table_ref(get_config("BQ_PROGRESS_TABLE", DEFAULT_PROGRESS_TABLE), DEFAULT_PROGRESS_TABLE),
        "skill_graded": format_table_ref(get_config("BQ_SKILL_GRADED_TABLE", DEFAULT_SKILL_GRADED_TABLE), DEFAULT_SKILL_GRADED_TABLE),
        "unlocked_units": format_table_ref(get_config("BQ_UNLOCKED_UNITS_TABLE", DEFAULT_UNLOCKED_UNITS_TABLE), DEFAULT_UNLOCKED_UNITS_TABLE),
        "quiz_attempts": format_table_ref(get_config("BQ_QUIZ_ATTEMPTS_TABLE", DEFAULT_QUIZ_ATTEMPTS_TABLE), DEFAULT_QUIZ_ATTEMPTS_TABLE),
        "session_adherence": format_table_ref(get_config("BQ_SESSION_ADHERENCE_TABLE", DEFAULT_SESSION_ADHERENCE_TABLE), DEFAULT_SESSION_ADHERENCE_TABLE),
        "portal_courses": format_table_ref(get_config("BQ_PORTAL_COURSES_TABLE", DEFAULT_PORTAL_COURSES_TABLE), DEFAULT_PORTAL_COURSES_TABLE),
    }


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    client = get_bigquery_client()
    rows = client.query(sql).result()
    return rows.to_dataframe(create_bqstorage_client=False)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_table_columns(table_ref: str, default_table: str) -> set[str]:
    table_parts = resolve_table_parts(table_ref, default_table)
    sql = f"""
        SELECT LOWER(column_name) AS column_name
        FROM `{table_parts["project"]}.{table_parts["dataset"]}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{sql_escape(table_parts["table"])}'
    """
    rows = run_query(sql)
    if rows.empty:
        return set()
    return set(rows["column_name"].dropna().astype(str).str.lower().tolist())


def first_existing_column(columns: set[str], candidates: list[str]):
    for candidate in candidates:
        if candidate.lower() in columns:
            return candidate
    return None


def bq_column(name: str) -> str:
    return f"`{name.replace('`', '')}`"


def build_content_subquery(content_table: str) -> str:
    return f"""
        SELECT
          unit_id,
          ARRAY_AGG(
            course_title IGNORE NULLS
            ORDER BY
              CASE
                WHEN LOWER(course_title) IN ('to be delete', 'niat practice page') THEN 1
                ELSE 0
              END,
              LENGTH(course_title),
              course_title
            LIMIT 1
          )[SAFE_OFFSET(0)] AS course_title
        FROM (
          SELECT DISTINCT
            unit_id,
            NULLIF(TRIM(course_title), '') AS course_title
          FROM {content_table}
        )
        GROUP BY unit_id
    """


def fetch_semester_data(batch: str, semester: str) -> pd.DataFrame:
    refs = get_table_refs()
    where_clauses = ["TRIM(COALESCE(s.institute_name, '')) != ''"]
    window_clause = get_semester_window_clause(semester, batch, "s.institute_name", "DATE(s.session_date)")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(s.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH content AS (
          {build_content_subquery(refs["content"])}
        ),
        schedule_base AS (
          SELECT
            s.institute_name AS institute,
            COALESCE(NULLIF(TRIM(s.section_name), ''), 'Unknown') AS section,
            s.session_type,
            s.session_status,
            DATE(s.session_date) AS report_date,
            s.session_id,
            COALESCE(content.course_title, s.session_name) AS course_candidate
          FROM {refs["schedule"]} s
          LEFT JOIN content ON s.resource_id = content.unit_id
          WHERE {' AND '.join(where_clauses)}
        ),
        session_course AS (
          SELECT
            institute,
            section,
            session_type,
            session_status,
            report_date,
            session_id,
            ARRAY_AGG(course_candidate ORDER BY occurrences DESC, course_candidate LIMIT 1)[OFFSET(0)] AS course
          FROM (
            SELECT
              institute,
              section,
              session_type,
              session_status,
              report_date,
              session_id,
              course_candidate,
              COUNT(*) AS occurrences
            FROM schedule_base
            GROUP BY institute, section, session_type, session_status, report_date, session_id, course_candidate
          )
          GROUP BY institute, section, session_type, session_status, report_date, session_id
        ),
        roster AS (
          SELECT
            u.institute_name AS institute,
            COALESCE(NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
            COUNT(DISTINCT user_id) AS students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY institute, section
        ),
        roster_counts AS (
          SELECT
            institute,
            COUNT(DISTINCT IF(LOWER(section) != 'unknown', section, NULL)) AS section_count
          FROM roster
          GROUP BY institute
        )
        SELECT
          sc.course AS course,
          sc.institute AS institute,
          sc.section AS section,
          sc.session_type AS session_type,
          COUNT(DISTINCT IF(sc.session_status = 'COMPLETED', sc.session_id, NULL)) AS sessions,
          COALESCE(r.students, 0) AS students,
          ROUND(
            100 * SAFE_DIVIDE(
              COUNT(DISTINCT IF(sc.session_status = 'COMPLETED', sc.session_id, NULL)),
              COUNT(DISTINCT sc.session_id)
            ),
            2
          ) AS completion,
          0 AS avg_time,
          0 AS p80_time,
          COALESCE(rc.section_count, 0) AS section_count,
          '{sql_escape(batch)}' AS batch,
          '{sql_escape(semester)}' AS semester,
          CAST(MAX(sc.report_date) AS STRING) AS report_date
        FROM session_course sc
        LEFT JOIN roster r
          ON r.institute = sc.institute
          AND r.section = sc.section
        LEFT JOIN roster_counts rc
          ON rc.institute = sc.institute
        GROUP BY course, institute, section, session_type, students, section_count
        HAVING sessions > 0
        ORDER BY institute, section, course
    """
    return run_query(sql)


def fetch_progress_delivered_slots(batch: str, semester: str) -> pd.DataFrame:
    refs = get_table_refs()
    progress_table = get_config("BQ_PROGRESS_TABLE", DEFAULT_PROGRESS_TABLE)
    columns = fetch_table_columns(progress_table, DEFAULT_PROGRESS_TABLE)
    required_columns = {"session_type", "sessions_delivered"}
    if not required_columns.issubset(columns):
        return pd.DataFrame(columns=["institute", "delivered_slots", "lecture_delivered_slots", "practice_delivered_slots", "lecture_completion_pct", "practice_completion_pct"])

    institute_col = first_existing_column(
        columns,
        ["institute_name", "institute", "university_name", "university", "college_name", "college"],
    )
    if not institute_col:
        return pd.DataFrame(columns=["institute", "delivered_slots", "lecture_delivered_slots", "practice_delivered_slots", "lecture_completion_pct", "practice_completion_pct"])

    institute_expr = f"CAST(p.{bq_column(institute_col)} AS STRING)"
    section_col = first_existing_column(columns, ["section_name", "section", "student_group", "student_group_name", "group_name"])
    section_expr = f"CAST(p.{bq_column(section_col)} AS STRING)" if section_col else "'All Sections'"
    where_clauses = [f"TRIM(COALESCE({institute_expr}, '')) != ''"]
    date_col = first_existing_column(columns, ["session_date", "report_date", "date", "created_date", "updated_date"])
    if date_col:
        date_expr = f"DATE(p.{bq_column(date_col)})"
        window_clause = get_semester_window_clause(semester, batch, institute_expr, date_expr)
        if window_clause:
            where_clauses.append(window_clause)

    semester_col = first_existing_column(columns, ["semester", "semester_name", "term"])
    completion_col = first_existing_column(columns, ["completed_users_percentage", "completion_percentage", "completed_percentage", "completion_pct"])
    if semester_col:
        semester_values = {semester.lower()}
        semester_number = re.search(r"\d+", semester)
        if semester_number:
            number = semester_number.group()
            semester_values.update({number, f"sem {number}", f"semester {number}", f"semester_{number}"})
        escaped_values = ", ".join(f"'{sql_escape(value)}'" for value in sorted(semester_values))
        where_clauses.append(f"LOWER(CAST(p.{bq_column(semester_col)} AS STRING)) IN ({escaped_values})")

    batch_col = first_existing_column(columns, ["batch_name", "batch", "cohort_name", "cohort"])
    if should_apply_batch_filter(batch) and batch_col:
        where_clauses.append(f"LOWER(CAST(p.{bq_column(batch_col)} AS STRING)) LIKE '%{sql_escape(batch.strip().lower())}%'")

    completion_section_sql = ""
    completion_aggregate_sql = """
          CAST(NULL AS FLOAT64) AS lecture_completion_pct,
          CAST(NULL AS FLOAT64) AS practice_completion_pct
    """
    if completion_col:
        completion_section_sql = f""",
            AVG(
              CASE
                WHEN UPPER(CAST(p.{bq_column("session_type")} AS STRING)) = 'LECTURE'
                  THEN SAFE_CAST(p.{bq_column(completion_col)} AS FLOAT64)
                ELSE NULL
              END
            ) AS section_lecture_completion_pct,
            AVG(
              CASE
                WHEN UPPER(CAST(p.{bq_column("session_type")} AS STRING)) = 'PRACTICE'
                  THEN SAFE_CAST(p.{bq_column(completion_col)} AS FLOAT64)
                ELSE NULL
              END
            ) AS section_practice_completion_pct"""
        completion_aggregate_sql = """
          AVG(section_lecture_completion_pct) AS lecture_completion_pct,
          AVG(section_practice_completion_pct) AS practice_completion_pct
        """

    sql = f"""
        WITH section_slots AS (
          SELECT
            {institute_expr} AS institute,
            COALESCE(NULLIF(TRIM({section_expr}), ''), 'All Sections') AS section,
            SUM(COALESCE(SAFE_CAST(p.{bq_column("sessions_delivered")} AS FLOAT64), 0)) AS section_delivered_slots,
            SUM(
              CASE
                WHEN UPPER(CAST(p.{bq_column("session_type")} AS STRING)) = 'LECTURE'
                  THEN COALESCE(SAFE_CAST(p.{bq_column("sessions_delivered")} AS FLOAT64), 0)
                ELSE 0
              END
            ) AS section_lecture_delivered_slots,
            SUM(
              CASE
                WHEN UPPER(CAST(p.{bq_column("session_type")} AS STRING)) = 'PRACTICE'
                  THEN COALESCE(SAFE_CAST(p.{bq_column("sessions_delivered")} AS FLOAT64), 0)
                ELSE 0
              END
            ) AS section_practice_delivered_slots{completion_section_sql}
          FROM {refs["progress"]} p
          WHERE {' AND '.join(where_clauses)}
            AND UPPER(CAST(p.{bq_column("session_type")} AS STRING)) IN ('LECTURE', 'PRACTICE')
          GROUP BY institute, section
        )
        SELECT
          institute,
          AVG(section_delivered_slots) AS delivered_slots,
          AVG(section_lecture_delivered_slots) AS lecture_delivered_slots,
          AVG(section_practice_delivered_slots) AS practice_delivered_slots,
{completion_aggregate_sql}
        FROM section_slots
        GROUP BY institute
        HAVING delivered_slots > 0
        ORDER BY institute
    """
    return run_query(sql)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_quiz_metrics(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute quiz metrics from quiz_best_attempts_and_completion_details.

    Actual schema used:
      institute_name, batch_name, user_id, quiz_id,
      derived_unit_type, best_attempt_evaluation_result, session_date

    Classification via derived_unit_type:
      CLASSROOM_QUIZ                            → classroom category
      MODULE_QUIZ | DAILY_QUIZ | COURSE_QUIZ    → module category

    Pass/Fail: best_attempt_evaluation_result = 'PASS'

    Aggregation is done at institute level (not per-section AVG) to ensure
    the roster denominator always resolves correctly regardless of section-name
    differences between tables.
    """
    refs = get_table_refs()
    where_clauses = ["TRIM(COALESCE(q.institute_name, '')) != ''"]
    window_clause = get_semester_window_clause(semester, batch, "q.institute_name", "q.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(q.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH institute_roster AS (
          -- Total enrolled students per institute (sum across all sections)
          SELECT
            u.institute_name AS institute,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY institute
        ),
        quiz_base AS (
          -- One row per (user, quiz); best_attempt_evaluation_result is already the best result
          SELECT
            q.institute_name AS institute,
            q.user_id,
            q.quiz_id,
            CASE
              WHEN q.derived_unit_type = 'CLASSROOM_QUIZ'                               THEN 'classroom'
              WHEN q.derived_unit_type IN ('MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')  THEN 'module'
              ELSE 'other'
            END AS quiz_category,
            -- Pass flag: LIKE '%PASS%' covers PASS, PASSED, and any vendor-specific variant
            (UPPER(TRIM(COALESCE(q.best_attempt_evaluation_result, ''))) LIKE '%PASS%') AS is_pass
          FROM {refs["quiz_attempts"]} q
          WHERE {' AND '.join(where_clauses)}
            AND q.derived_unit_type IN ('CLASSROOM_QUIZ', 'MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')
        ),
        quiz_totals AS (
          -- Aggregate directly at institute level; classroom and module are counted independently
          SELECT
            institute,
            -- Classroom: attempted = at least one classroom quiz taken; passed = at least one PASS
            COUNT(DISTINCT IF(quiz_category = 'classroom', user_id, NULL))              AS classroom_attempted,
            COUNT(DISTINCT IF(quiz_category = 'classroom' AND is_pass, user_id, NULL))  AS classroom_passed,
            -- Module: conducted = distinct quiz_ids; attempted/passed = distinct user_ids
            COUNT(DISTINCT IF(quiz_category = 'module', quiz_id, NULL))                 AS module_quiz_conducted,
            COUNT(DISTINCT IF(quiz_category = 'module', user_id, NULL))                 AS module_attempted,
            COUNT(DISTINCT IF(quiz_category = 'module' AND is_pass, user_id, NULL))     AS module_passed
          FROM quiz_base
          GROUP BY institute
        )
        SELECT
          qt.institute,
          -- Classroom Quiz Attempt %: unique users who took a classroom quiz / total enrolled
          ROUND(SAFE_DIVIDE(qt.classroom_attempted, NULLIF(ir.total_students,      0)) * 100, 1) AS classroom_quiz_attempt_pct,
          -- Classroom Quiz Pass %: unique users who passed ≥1 classroom quiz / unique who attempted
          ROUND(SAFE_DIVIDE(qt.classroom_passed,    NULLIF(qt.classroom_attempted, 0)) * 100, 1) AS classroom_quiz_pass_pct,
          qt.module_quiz_conducted,
          -- Module Quiz Participation %: unique users who took a module quiz / total enrolled
          ROUND(SAFE_DIVIDE(qt.module_attempted,    NULLIF(ir.total_students,      0)) * 100, 1) AS module_quiz_participation_pct,
          -- Module Quiz Pass %: unique users who passed ≥1 module quiz / unique who attempted
          ROUND(SAFE_DIVIDE(qt.module_passed,       NULLIF(qt.module_attempted,    0)) * 100, 1) AS module_quiz_pass_pct
        FROM quiz_totals qt
        LEFT JOIN institute_roster ir ON ir.institute = qt.institute
        ORDER BY qt.institute
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["institute", "classroom_quiz_attempt_pct", "classroom_quiz_pass_pct",
                                     "module_quiz_conducted", "module_quiz_participation_pct", "module_quiz_pass_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_practice_completion(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute practice completion metrics from unlocked_units_completion_details.

    Actual schema used:
      institute_name, section_name, batch_name, user_id, unit_id,
      unit_type ('PRACTICE'), derived_unit_type ('MCQ_PRACTICE'),
      unit_completion_status ('COMPLETED' | 'IN_PROGRESS' | 'YET_TO_START'), session_date

    Practice Completion % = students with at least one COMPLETED practice unit / total enrolled.
    """
    refs = get_table_refs()
    where_clauses = [
        "TRIM(COALESCE(uu.institute_name, '')) != ''",
        "uu.unit_type = 'PRACTICE'",
    ]
    window_clause = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(uu.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH institute_roster AS (
          SELECT
            u.institute_name AS institute,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY institute
        ),
        practice_completed AS (
          -- Distinct users who completed at least one practice unit, per institute
          SELECT
            uu.institute_name AS institute,
            COUNT(DISTINCT uu.user_id) AS students_completed_practice
          FROM {refs["unlocked_units"]} uu
          WHERE {' AND '.join(where_clauses)}
            AND uu.unit_completion_status = 'COMPLETED'
          GROUP BY uu.institute_name
        )
        SELECT
          pc.institute,
          -- Practice Completion %: students with ≥1 completed practice unit / total enrolled
          ROUND(SAFE_DIVIDE(pc.students_completed_practice, NULLIF(ir.total_students, 0)) * 100, 1) AS practice_completion_pct
        FROM practice_completed pc
        LEFT JOIN institute_roster ir ON ir.institute = pc.institute
        ORDER BY pc.institute
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["institute", "practice_completion_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_session_delivery_metrics(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute practice delivery, module quiz conduction, and skill assessment
    conduction metrics from week_wise_session_completion_adherence_details.

    Actual schema used:
      institute_name, section_name, batch_name, session_type ('LECTURE'|'PRACTICE'|'EXAM'),
      session_name_enum, session_date, total_sessions_planned, total_sessions_delivered,
      semester_title

    Practice Delivery %      = SUM(delivered PRACTICE) / SUM(planned PRACTICE) × 100
    Module Quiz Conduction % = SUM(delivered EXAM where name contains 'quiz') /
                               SUM(planned  EXAM where name contains 'quiz') × 100
    Skill Assessment Conduction % = SUM(delivered EXAM where name contains 'skill') /
                                    SUM(planned  EXAM where name contains 'skill') × 100

    Note: total_sessions_planned / total_sessions_delivered are cumulative per-row values.
    We take MAX per (institute, section, course_title) to get the latest running total,
    then SUM across courses within an institute.
    """
    refs = get_table_refs()
    where_clauses = ["TRIM(COALESCE(sa.institute_name, '')) != ''"]
    window_clause = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(sa.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH filtered AS (
          SELECT
            sa.institute_name    AS institute,
            sa.section_name      AS section,
            sa.course_title      AS course,
            sa.session_type,
            sa.session_name_enum,
            -- Take the final (max) cumulative totals per section-course combination
            MAX(sa.total_sessions_planned)   AS planned,
            MAX(sa.total_sessions_delivered) AS delivered
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(where_clauses)}
          GROUP BY institute, section, course, session_type, session_name_enum
        ),
        per_institute AS (
          SELECT
            institute,
            -- Practice Delivery
            SUM(CASE WHEN session_type = 'PRACTICE'
                     THEN COALESCE(delivered, 0) ELSE 0 END)          AS practice_delivered,
            SUM(CASE WHEN session_type = 'PRACTICE'
                     THEN COALESCE(planned, 0)   ELSE 0 END)          AS practice_planned,
            -- Module Quiz (EXAM sessions whose name contains 'quiz')
            SUM(CASE WHEN session_type = 'EXAM'
                      AND REGEXP_CONTAINS(LOWER(COALESCE(session_name_enum, '')), r'quiz')
                     THEN COALESCE(delivered, 0) ELSE 0 END)          AS mq_delivered,
            SUM(CASE WHEN session_type = 'EXAM'
                      AND REGEXP_CONTAINS(LOWER(COALESCE(session_name_enum, '')), r'quiz')
                     THEN COALESCE(planned, 0)   ELSE 0 END)          AS mq_planned,
            -- Skill Assessment (EXAM sessions whose name contains 'skill')
            SUM(CASE WHEN session_type = 'EXAM'
                      AND REGEXP_CONTAINS(LOWER(COALESCE(session_name_enum, '')), r'skill')
                     THEN COALESCE(delivered, 0) ELSE 0 END)          AS sa_delivered,
            SUM(CASE WHEN session_type = 'EXAM'
                      AND REGEXP_CONTAINS(LOWER(COALESCE(session_name_enum, '')), r'skill')
                     THEN COALESCE(planned, 0)   ELSE 0 END)          AS sa_planned
          FROM filtered
          GROUP BY institute
        )
        SELECT
          institute,
          ROUND(SAFE_DIVIDE(practice_delivered, NULLIF(practice_planned, 0)) * 100, 1) AS practice_delivery_pct,
          ROUND(SAFE_DIVIDE(mq_delivered,       NULLIF(mq_planned,       0)) * 100, 1) AS module_quiz_conduction_pct,
          ROUND(SAFE_DIVIDE(sa_delivered,       NULLIF(sa_planned,       0)) * 100, 1) AS skill_conduction_pct
        FROM per_institute
        ORDER BY institute
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["institute", "practice_delivery_pct", "module_quiz_conduction_pct", "skill_conduction_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_skill_graded_metrics(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute skill and academic assessment metrics from
    curriculum_ops_niat_2025_users_batch_wise_skill_and_graded_assessment_scores.

    Actual schema used:
      institute_name, section_name, batch_name, user_id, assessment_id,
      assessment_type ('SKILL_ASSESSMENT' | 'GRADED_ASSESSMENT' | *_MOCK variants),
      section_evaluation_result ('PASSED' | 'FAILED'),
      assessment_start_datetime

    Skill:    assessment_type = 'SKILL_ASSESSMENT'   (excludes MOCK)
    Academic: assessment_type = 'GRADED_ASSESSMENT'  (excludes MOCK)
    Pass:     section_evaluation_result = 'PASSED'
    """
    refs = get_table_refs()
    where_clauses = [
        "TRIM(COALESCE(sg.institute_name, '')) != ''",
        "sg.assessment_type IN ('SKILL_ASSESSMENT', 'GRADED_ASSESSMENT')",
    ]
    date_expr = "DATE(sg.assessment_start_datetime)"
    window_clause = get_semester_window_clause(semester, batch, "sg.institute_name", date_expr)
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(sg.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH institute_roster AS (
          SELECT
            u.institute_name AS institute,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY institute
        ),
        sg_base AS (
          SELECT
            sg.institute_name AS institute,
            sg.user_id,
            sg.assessment_id,
            sg.assessment_type,
            -- Pass: section_evaluation_result covers all common pass values
            -- ('PASS', 'PASSED', 'CLEARED', 'ABOVE_CUTOFF', 'ABOVE CUTOFF')
            -- Fail values ('FAIL', 'FAILED', 'NOT_CLEARED', 'BELOW_CUTOFF') are excluded implicitly.
            -- Uses LIKE '%PASS%' as a broad net so no schema variation is missed.
            (UPPER(TRIM(COALESCE(sg.section_evaluation_result, ''))) LIKE '%PASS%') AS is_passed
          FROM {refs["skill_graded"]} sg
          WHERE {' AND '.join(where_clauses)}
        ),
        sg_totals AS (
          -- Aggregate at institute level; SKILL_ASSESSMENT and GRADED_ASSESSMENT are counted separately
          SELECT
            institute,
            COUNT(DISTINCT IF(assessment_type = 'SKILL_ASSESSMENT', assessment_id, NULL))             AS skill_conducted,
            COUNT(DISTINCT IF(assessment_type = 'SKILL_ASSESSMENT', user_id, NULL))                   AS skill_attempted,
            COUNT(DISTINCT IF(assessment_type = 'SKILL_ASSESSMENT' AND is_passed, user_id, NULL))     AS skill_passed,
            COUNT(DISTINCT IF(assessment_type = 'GRADED_ASSESSMENT', user_id, NULL))                  AS academic_attempted,
            COUNT(DISTINCT IF(assessment_type = 'GRADED_ASSESSMENT' AND is_passed, user_id, NULL))    AS academic_passed
          FROM sg_base
          GROUP BY institute
        )
        SELECT
          st.institute,
          st.skill_conducted,
          -- Skill Assessment Participation %: unique users attempted / total enrolled
          ROUND(SAFE_DIVIDE(st.skill_attempted,    NULLIF(ir.total_students,    0)) * 100, 1) AS skill_participation_pct,
          -- Skill Assessment Pass %: passed / attempted (section_evaluation_result = PASSED)
          ROUND(SAFE_DIVIDE(st.skill_passed,       NULLIF(st.skill_attempted,   0)) * 100, 1) AS skill_pass_pct,
          -- Academic Assessments Attempt %: unique users attempted / total enrolled
          ROUND(SAFE_DIVIDE(st.academic_attempted, NULLIF(ir.total_students,    0)) * 100, 1) AS academic_attempt_pct,
          -- Academic Assessments Pass %: passed / attempted (section_evaluation_result = PASSED)
          ROUND(SAFE_DIVIDE(st.academic_passed,    NULLIF(st.academic_attempted, 0)) * 100, 1) AS academic_pass_pct
        FROM sg_totals st
        LEFT JOIN institute_roster ir ON ir.institute = st.institute
        ORDER BY st.institute
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["institute", "skill_conducted", "skill_participation_pct",
                                     "skill_pass_pct", "academic_attempt_pct", "academic_pass_pct"])


def fetch_all_new_metrics(batch: str, semester: str) -> dict:
    """
    Fetches all new metric DataFrames and returns them keyed by name.
    Each inner dict is keyed by institute name for O(1) lookup in build_university_overview_rows.
    """
    quiz_df          = fetch_quiz_metrics(batch, semester)
    practice_df      = fetch_practice_completion(batch, semester)
    delivery_df      = fetch_session_delivery_metrics(batch, semester)
    skill_graded_df  = fetch_skill_graded_metrics(batch, semester)

    def to_dict(df: pd.DataFrame, key: str = "institute") -> dict:
        if df.empty or key not in df.columns:
            return {}
        return {row[key]: row.to_dict() for _, row in df.iterrows()}

    return {
        "quiz":          to_dict(quiz_df),
        "practice":      to_dict(practice_df),
        "delivery":      to_dict(delivery_df),
        "skill_graded":  to_dict(skill_graded_df),
    }


@st.cache_data(ttl=600, show_spinner=False)
def fetch_pass_field_values(batch: str, semester: str) -> dict:
    """
    Diagnostic helper: returns the distinct values of the pass/fail fields
    in quiz_attempts and skill_graded tables so mismatches can be caught quickly.
    """
    refs = get_table_refs()
    batch_filter_q = ""
    if should_apply_batch_filter(batch):
        batch_filter_q = f"AND LOWER(COALESCE(batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'"
    sql = f"""
        SELECT 'quiz: best_attempt_evaluation_result' AS source,
               CAST(best_attempt_evaluation_result AS STRING) AS raw_value,
               COUNT(*) AS row_count
        FROM {refs["quiz_attempts"]}
        WHERE TRIM(COALESCE(institute_name, '')) != '' {batch_filter_q}
          AND derived_unit_type IN ('CLASSROOM_QUIZ','MODULE_QUIZ','DAILY_QUIZ','COURSE_QUIZ')
        GROUP BY source, raw_value
        UNION ALL
        SELECT 'skill_graded: section_evaluation_result' AS source,
               CAST(section_evaluation_result AS STRING) AS raw_value,
               COUNT(*) AS row_count
        FROM {refs["skill_graded"]}
        WHERE TRIM(COALESCE(institute_name, '')) != '' {batch_filter_q}
          AND assessment_type IN ('SKILL_ASSESSMENT','GRADED_ASSESSMENT')
        GROUP BY source, raw_value
        ORDER BY source, raw_value
    """
    try:
        return run_query(sql).to_dict("records")
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def fetch_sem_course_titles(batch: str, semester: str) -> dict:
    """
    Returns {normalized_name → sem_course_title} from portal_courses for the given
    batch/semester.  Used to map content-level course titles to the official semester
    subject names in the Course Breakdown table.
    """
    refs = get_table_refs()
    where_clauses = ["TRIM(COALESCE(pc.sem_course_title, '')) != ''"]
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(pc.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")
    sem_num = ""
    if "1" in semester:
        sem_num = "1"
    elif "2" in semester:
        sem_num = "2"
    if sem_num:
        where_clauses.append(f"LOWER(COALESCE(pc.semester_name, '')) LIKE '%semester {sem_num}%'")
    sql = f"""
        SELECT DISTINCT TRIM(pc.sem_course_title) AS sem_course_title
        FROM {refs["portal_courses"]} pc
        WHERE {' AND '.join(where_clauses)}
        ORDER BY sem_course_title
    """
    try:
        df = run_query(sql)
        if df.empty:
            return {}
        result = {}
        for title in df["sem_course_title"].dropna().unique():
            title = str(title).strip()
            if title:
                result[normalize_text(title)] = title
        return result
    except Exception:
        return {}


def fetch_assessment_data(batch: str, semester: str) -> pd.DataFrame:
    refs = get_table_refs()
    legacy_date_expr = "DATE(COALESCE(a.submission_datetime, a.question_start_datetime))"
    topic_date_expr = "DATE(t.assessment_start_datetime)"

    legacy_where_clauses = [
        "u.user_id IS NOT NULL",
        "TRIM(COALESCE(u.institute_name, '')) != ''",
    ]
    legacy_window_clause = get_semester_window_clause(semester, batch, "u.institute_name", legacy_date_expr)
    if legacy_window_clause:
        legacy_where_clauses.append(legacy_window_clause)
    if should_apply_batch_filter(batch):
        legacy_where_clauses.append(f"LOWER(COALESCE(u.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    topic_institute_expr = "COALESCE(NULLIF(TRIM(t.institute_name), ''), u.institute_name)"
    topic_where_clauses = [
        f"TRIM(COALESCE({topic_institute_expr}, '')) != ''",
    ]
    topic_window_clause = get_semester_window_clause(semester, batch, topic_institute_expr, topic_date_expr)
    if topic_window_clause:
        topic_where_clauses.append(topic_window_clause)
    if should_apply_batch_filter(batch):
        topic_where_clauses.append(f"LOWER(COALESCE(u.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH users AS (
          SELECT DISTINCT
            user_id,
            institute_name,
            section_name,
            batch_name
          FROM {refs["users"]}
        ),
        content AS (
          {build_content_subquery(refs["content"])}
        ),
        legacy_attempts AS (
          SELECT
            u.institute_name AS university,
            COALESCE(NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
            COALESCE(
              content.course_title,
              COALESCE(
                NULLIF(TRIM(a.question_set_title), ''),
                CONCAT('Question Set ', CAST(a.question_set_id AS STRING))
              )
            ) AS course_code,
            'Assessment' AS assessment_type,
            a.user_id AS user_id,
            COALESCE(a.user_score, a.actual_score) AS user_score,
            a.actual_score AS actual_score,
            {legacy_date_expr} AS report_date
          FROM {refs["assessment"]} a
          JOIN users u USING (user_id)
          LEFT JOIN content ON CAST(a.question_set_id AS STRING) = content.unit_id
          WHERE {' AND '.join(legacy_where_clauses)}
            AND COALESCE(a.actual_score, 0) > 0
            AND NOT REGEXP_CONTAINS(LOWER(COALESCE(a.question_set_title, '')), r'skill assessment|graded assessment')
        ),
        topic_attempts AS (
          SELECT
            {topic_institute_expr} AS university,
            COALESCE(NULLIF(TRIM(t.section_name), ''), NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
            COALESCE(
              content.course_title,
              NULLIF(TRIM(REGEXP_EXTRACT(t.assessment_title, r'\\|\\|\\s*(.+)$')), ''),
              NULLIF(TRIM(t.section_tech_stack), ''),
              NULLIF(TRIM(t.assessment_title), ''),
              CONCAT('Assessment ', CAST(t.assessment_id AS STRING))
            ) AS course_code,
            CASE
              WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'graded assessment') THEN 'Graded Assessment'
              ELSE 'Skill Assessment'
            END AS assessment_type,
            t.user_id AS user_id,
            t.user_section_score AS user_score,
            t.section_actual_score AS actual_score,
            {topic_date_expr} AS report_date
          FROM {refs["assessment_topic"]} t
          LEFT JOIN users u USING (user_id)
          LEFT JOIN content ON CAST(t.unit_id AS STRING) = content.unit_id
          WHERE {' AND '.join(topic_where_clauses)}
            AND COALESCE(t.section_actual_score, 0) > 0
            AND (
              REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'graded assessment')
              OR (
                REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'skill assessment')
                AND NOT REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'mock skill assessment')
              )
            )
        ),
        all_attempts AS (
          SELECT * FROM legacy_attempts
          UNION ALL
          SELECT * FROM topic_attempts
        )
        SELECT
          university,
          section,
          course_code,
          assessment_type,
          COUNT(DISTINCT IF(COALESCE(user_score, actual_score) IS NOT NULL, user_id, NULL)) AS avg_participation,
          COUNT(
            DISTINCT IF(
              COALESCE(SAFE_DIVIDE(user_score, NULLIF(actual_score, 0)), 0) > 0.8,
              user_id,
              NULL
            )
          ) AS avg_pass_count,
          ROUND(AVG(COALESCE(SAFE_DIVIDE(user_score, NULLIF(actual_score, 0)), 0)), 4) AS avg_score,
          '{sql_escape(batch)}' AS batch,
          '{sql_escape(semester)}' AS semester,
          CAST(MAX(report_date) AS STRING) AS report_date
        FROM all_attempts
        GROUP BY university, section, course_code, assessment_type
        ORDER BY university, section, course_code, assessment_type
    """
    return run_query(sql)


def summarize_assessment_subset(assessment_df: pd.DataFrame, assessment_type: str | None = None):
    if assessment_df.empty:
        return {"score": None, "participation": None, "pass_count": None}
    scoped_df = assessment_df
    if assessment_type:
        scoped_df = scoped_df[scoped_df["assessment_type"] == assessment_type]
    if scoped_df.empty:
        return {"score": None, "participation": None, "pass_count": None}
    return {
        "score": float(scoped_df["avg_score"].mean()),
        "participation": float(scoped_df["avg_participation"].mean()),
        "pass_count": float(scoped_df["avg_pass_count"].mean()) if "avg_pass_count" in scoped_df.columns else None,
    }


def summarize_academic_assessment_subset(assessment_df: pd.DataFrame):
    if assessment_df.empty:
        return {"score": None, "participation": None, "pass_count": None}
    scoped_df = assessment_df[assessment_df["assessment_type"] != "Skill Assessment"]
    if scoped_df.empty:
        return {"score": None, "participation": None, "pass_count": None}
    return {
        "score": float(scoped_df["avg_score"].mean()),
        "participation": float(scoped_df["avg_participation"].mean()),
        "pass_count": float(scoped_df["avg_pass_count"].mean()) if "avg_pass_count" in scoped_df.columns else None,
    }


def calc_univ_assessment(assessment_df: pd.DataFrame, univ_name: str):
    empty_response = {
        "avgScore": None,
        "avgParticipation": None,
        "avgAcademicScore": None,
        "avgAcademicParticipation": None,
        "avgAcademicPassCount": None,
        "avgSkillScore": None,
        "avgSkillParticipation": None,
        "avgSkillPassCount": None,
        "avgGradedScore": None,
        "avgGradedParticipation": None,
        "avgGradedPassCount": None,
    }
    if assessment_df.empty:
        return empty_response
    univ_data = assessment_df[assessment_df["university"] == univ_name].copy()
    if univ_data.empty:
        return empty_response
    sections = [
        section
        for section in sorted(univ_data["section"].dropna().unique())
        if section and str(section).strip().lower() != "unknown"
    ]
    if len(sections) <= 1:
        overall = summarize_assessment_subset(univ_data)
        academic = summarize_academic_assessment_subset(univ_data)
        skill = summarize_assessment_subset(univ_data, "Skill Assessment")
        graded = summarize_assessment_subset(univ_data, "Graded Assessment")
        return {
            "avgScore": overall["score"],
            "avgParticipation": overall["participation"],
            "avgAcademicScore": academic["score"],
            "avgAcademicParticipation": academic["participation"],
            "avgAcademicPassCount": academic["pass_count"],
            "avgSkillScore": skill["score"],
            "avgSkillParticipation": skill["participation"],
            "avgSkillPassCount": skill["pass_count"],
            "avgGradedScore": graded["score"],
            "avgGradedParticipation": graded["participation"],
            "avgGradedPassCount": graded["pass_count"],
        }
    common_courses = None
    for section in sections:
        section_courses = set(univ_data[univ_data["section"] == section]["course_code"].tolist())
        common_courses = section_courses if common_courses is None else common_courses & section_courses
    if not common_courses:
        return empty_response
    section_avgs = []
    for section in sections:
        section_data = univ_data[(univ_data["section"] == section) & (univ_data["course_code"].isin(common_courses))]
        overall = summarize_assessment_subset(section_data)
        academic = summarize_academic_assessment_subset(section_data)
        skill = summarize_assessment_subset(section_data, "Skill Assessment")
        graded = summarize_assessment_subset(section_data, "Graded Assessment")
        section_avgs.append(
            {
                "score": overall["score"],
                "participation": overall["participation"],
                "academic_score": academic["score"],
                "academic_participation": academic["participation"],
                "academic_pass_count": academic["pass_count"],
                "skill_score": skill["score"],
                "skill_participation": skill["participation"],
                "skill_pass_count": skill["pass_count"],
                "graded_score": graded["score"],
                "graded_participation": graded["participation"],
                "graded_pass_count": graded["pass_count"],
            }
        )

    def average_metric(key: str):
        values = [item[key] for item in section_avgs if item[key] is not None]
        return sum(values) / len(values) if values else None

    return {
        "avgScore": average_metric("score"),
        "avgParticipation": average_metric("participation"),
        "avgAcademicScore": average_metric("academic_score"),
        "avgAcademicParticipation": average_metric("academic_participation"),
        "avgAcademicPassCount": average_metric("academic_pass_count"),
        "avgSkillScore": average_metric("skill_score"),
        "avgSkillParticipation": average_metric("skill_participation"),
        "avgSkillPassCount": average_metric("skill_pass_count"),
        "avgGradedScore": average_metric("graded_score"),
        "avgGradedParticipation": average_metric("graded_participation"),
        "avgGradedPassCount": average_metric("graded_pass_count"),
    }


def calculate_series_data(data_df: pd.DataFrame, assessment_df: pd.DataFrame, analysis_type: str, semester: str):
    institutes = sorted(data_df["institute"].dropna().unique().tolist())
    university_metrics = []

    for institute in institutes:
        institute_df = data_df[data_df["institute"] == institute]
        sections = [
            section
            for section in sorted(institute_df["section"].dropna().unique())
            if section and str(section).strip().lower() != "unknown"
        ]
        roster_section_count = 0
        if "section_count" in institute_df.columns:
            section_count_values = pd.to_numeric(institute_df["section_count"], errors="coerce").dropna()
            section_count_values = section_count_values[section_count_values > 0]
            if not section_count_values.empty:
                roster_section_count = int(section_count_values.max())

        def calc_section_metric(section_df: pd.DataFrame):
            lecture_df = section_df[section_df["session_type"] == "LECTURE"]
            practice_df = section_df[section_df["session_type"] == "PRACTICE"]
            exam_df = section_df[section_df["session_type"] == "EXAM"]
            lecture_sessions = float(lecture_df["sessions"].max()) if not lecture_df.empty else 0
            practice_sessions = float(practice_df["sessions"].max()) if not practice_df.empty else 0
            exam_sessions = float(exam_df["sessions"].max()) if not exam_df.empty else 0
            lecture_practice_sessions = float(lecture_df["sessions"].sum()) + float(practice_df["sessions"].sum())
            return {
                "totalSessions": lecture_sessions + practice_sessions + exam_sessions,
                "lecturePracticeSessions": lecture_practice_sessions,
                "scheduledLectureSessions": estimate_scheduled_sessions(lecture_df),
                "scheduledPracticeSessions": estimate_scheduled_sessions(practice_df),
                "classSize": float(section_df["students"].max()) if not section_df.empty else 0,
                "lectureCompletion": float(lecture_df["completion"].mean()) if not lecture_df.empty else 0,
                "practiceCompletion": float(practice_df["completion"].mean()) if not practice_df.empty else 0,
                "examCompletion": float(exam_df["completion"].mean()) if not exam_df.empty else 0,
                "avgTime": float(section_df["avg_time"].sum()),
                "p80Time": float(section_df["p80_time"].sum()),
                "practiceAvgTime": float(practice_df["avg_time"].sum()) if not practice_df.empty else 0,
                "practiceP80Time": float(practice_df["p80_time"].sum()) if not practice_df.empty else 0,
            }

        section_metrics = [calc_section_metric(institute_df[institute_df["section"] == section]) for section in sections] if sections else [calc_section_metric(institute_df)]
        average = lambda key: sum(metric[key] for metric in section_metrics) / len(section_metrics)
        assessment = calc_univ_assessment(assessment_df, institute)
        allotted_hours = get_allotted_hours(institute, semester)
        if analysis_type == "design":
            series_info = get_series_for_allotted_hours(institute, semester)
            series_name = series_info["name"] if series_info else "Unknown"
        else:
            series_name = get_series_for_value(average("totalSessions"))["name"]
        university_metrics.append(
            {
                "name": institute,
                "sectionCount": roster_section_count or len(sections) or 1,
                "avgSessions": average("totalSessions"),
                "avgLecturePracticeSessions": average("lecturePracticeSessions"),
                "avgScheduledLectureSessions": average("scheduledLectureSessions"),
                "avgScheduledPracticeSessions": average("scheduledPracticeSessions"),
                "avgClassSize": average("classSize"),
                "avgLectureCompletion": average("lectureCompletion"),
                "avgPracticeCompletion": average("practiceCompletion"),
                "avgExamCompletion": average("examCompletion"),
                "avgOverallCompletion": (average("lectureCompletion") + average("practiceCompletion") + average("examCompletion")) / 3,
                "avgWorkload": average("avgTime"),
                "avgP80Workload": average("p80Time"),
                "avgPracticeWorkload": average("practiceAvgTime"),
                "avgPracticeP80Workload": average("practiceP80Time"),
                "series": series_name,
                "allottedHours": allotted_hours,
                "avgAssessmentScore": assessment["avgScore"],
                "avgParticipation": assessment["avgParticipation"],
                "avgAcademicScore": assessment["avgAcademicScore"],
                "avgAcademicParticipation": assessment["avgAcademicParticipation"],
                "avgAcademicPassCount": assessment["avgAcademicPassCount"],
                "avgSkillScore": assessment["avgSkillScore"],
                "avgSkillParticipation": assessment["avgSkillParticipation"],
                "avgSkillPassCount": assessment["avgSkillPassCount"],
                "avgGradedScore": assessment["avgGradedScore"],
                "avgGradedParticipation": assessment["avgGradedParticipation"],
                "avgGradedPassCount": assessment["avgGradedPassCount"],
            }
        )

    series_data = {}
    for series in SERIES_RANGES:
        universities = [item for item in university_metrics if item["series"] == series["name"]]
        if not universities:
            series_data[series["name"]] = {
                "universities": [],
                "avgSessions": 0,
                "avgLecturePracticeSessions": 0,
                "avgClassSize": 0,
                "avgLectureCompletion": 0,
                "avgPracticeCompletion": 0,
                "avgExamCompletion": 0,
                "avgOverallCompletion": 0,
                "totalStudents": 0,
                "avgAssessmentScore": None,
                "avgParticipation": None,
                "avgAcademicScore": None,
                "avgAcademicParticipation": None,
                "avgAcademicPassCount": None,
                "avgSkillScore": None,
                "avgSkillParticipation": None,
                "avgSkillPassCount": None,
                "avgGradedScore": None,
                "avgGradedParticipation": None,
                "avgGradedPassCount": None,
                "avgAllottedHours": 0,
            }
            continue
        average = lambda key: sum(item[key] for item in universities) / len(universities)
        with_score = [item for item in universities if item["avgAssessmentScore"] is not None]
        with_academic_score = [item for item in universities if item["avgAcademicScore"] is not None]
        with_academic_participation = [item for item in universities if item["avgAcademicParticipation"] is not None]
        with_academic_pass_count = [item for item in universities if item["avgAcademicPassCount"] is not None]
        with_skill_score = [item for item in universities if item["avgSkillScore"] is not None]
        with_skill_participation = [item for item in universities if item["avgSkillParticipation"] is not None]
        with_skill_pass_count = [item for item in universities if item["avgSkillPassCount"] is not None]
        with_graded_score = [item for item in universities if item["avgGradedScore"] is not None]
        with_graded_participation = [item for item in universities if item["avgGradedParticipation"] is not None]
        with_graded_pass_count = [item for item in universities if item["avgGradedPassCount"] is not None]
        with_hours = [item for item in universities if item["allottedHours"] is not None]
        series_data[series["name"]] = {
            "universities": universities,
            "avgSessions": average("avgSessions"),
            "avgLecturePracticeSessions": average("avgLecturePracticeSessions"),
            "avgClassSize": average("avgClassSize"),
            "avgLectureCompletion": average("avgLectureCompletion"),
            "avgPracticeCompletion": average("avgPracticeCompletion"),
            "avgExamCompletion": average("avgExamCompletion"),
            "avgOverallCompletion": average("avgOverallCompletion"),
            "totalStudents": sum(round(item["avgClassSize"] * item["sectionCount"]) for item in universities),
            "avgAssessmentScore": sum(item["avgAssessmentScore"] for item in with_score) / len(with_score) if with_score else None,
            "avgParticipation": sum(item["avgParticipation"] for item in with_score) / len(with_score) if with_score else None,
            "avgAcademicScore": sum(item["avgAcademicScore"] for item in with_academic_score) / len(with_academic_score) if with_academic_score else None,
            "avgAcademicParticipation": sum(item["avgAcademicParticipation"] for item in with_academic_participation) / len(with_academic_participation) if with_academic_participation else None,
            "avgAcademicPassCount": sum(item["avgAcademicPassCount"] for item in with_academic_pass_count) / len(with_academic_pass_count) if with_academic_pass_count else None,
            "avgSkillScore": sum(item["avgSkillScore"] for item in with_skill_score) / len(with_skill_score) if with_skill_score else None,
            "avgSkillParticipation": sum(item["avgSkillParticipation"] for item in with_skill_participation) / len(with_skill_participation) if with_skill_participation else None,
            "avgSkillPassCount": sum(item["avgSkillPassCount"] for item in with_skill_pass_count) / len(with_skill_pass_count) if with_skill_pass_count else None,
            "avgGradedScore": sum(item["avgGradedScore"] for item in with_graded_score) / len(with_graded_score) if with_graded_score else None,
            "avgGradedParticipation": sum(item["avgGradedParticipation"] for item in with_graded_participation) / len(with_graded_participation) if with_graded_participation else None,
            "avgGradedPassCount": sum(item["avgGradedPassCount"] for item in with_graded_pass_count) / len(with_graded_pass_count) if with_graded_pass_count else None,
            "avgAllottedHours": sum(item["allottedHours"] for item in with_hours) / len(with_hours) if with_hours else 0,
        }
    return series_data


def summarize_type(course_df: pd.DataFrame, session_type: str):
    rows = course_df[course_df["session_type"] == session_type]
    if rows.empty:
        return None
    return {
        "sessions": float(rows["sessions"].sum()),
        "completion": float(rows["completion"].mean()),
        "avg_time": float(rows["avg_time"].sum()),
        "p80_time": float(rows["p80_time"].sum()),
    }


def get_roster_size_for_scope(data_df: pd.DataFrame, section: str):
    if data_df.empty:
        return 0
    if section:
        return float(data_df["students"].max())
    scoped = data_df.copy()
    scoped["section"] = scoped["section"].fillna("").astype(str).str.strip()
    scoped = scoped[scoped["section"].str.lower() != "unknown"]
    if scoped.empty:
        return float(data_df["students"].max())
    return float(scoped.groupby("section")["students"].max().sum())


def build_university_metrics(data_df: pd.DataFrame, assessment_df: pd.DataFrame, institute: str, section: str, semester: str, sem_course_titles: dict | None = None):
    filtered = data_df[data_df["institute"] == institute].copy()
    if section:
        filtered = filtered[filtered["section"] == section]
    if filtered.empty:
        return None
    filtered["normalized_course"] = filtered["course"].apply(lambda course: normalize_course_name(course, semester))
    # Map normalized course names to official sem_course_title where available
    sem_titles = sem_course_titles or {}

    def _display_course(name: str) -> str:
        return sem_titles.get(normalize_text(name), name)
    lecture_df = filtered[filtered["session_type"] == "LECTURE"]
    practice_df = filtered[filtered["session_type"] == "PRACTICE"]
    exam_df = filtered[filtered["session_type"] == "EXAM"]

    course_records = []
    assessment_filtered = assessment_df[assessment_df["university"] == institute].copy()
    if section:
        assessment_filtered = assessment_filtered[assessment_filtered["section"] == section]
    assessment_filtered["normalized_course"] = assessment_filtered["course_code"].apply(lambda course: normalize_course_name(course, semester)) if not assessment_filtered.empty else []

    for course_name in sorted(filtered["normalized_course"].unique().tolist()):
        course_df = filtered[filtered["normalized_course"] == course_name]
        lecture = summarize_type(course_df, "LECTURE")
        practice = summarize_type(course_df, "PRACTICE")
        exam = summarize_type(course_df, "EXAM")
        assessment_row = assessment_filtered[assessment_filtered["normalized_course"] == course_name]
        overall_assessment_row = summarize_assessment_subset(assessment_row)
        skill_assessment_row = summarize_assessment_subset(assessment_row, "Skill Assessment")
        graded_assessment_row = summarize_assessment_subset(assessment_row, "Graded Assessment")
        course_records.append(
            {
                "Course": _display_course(course_name),
                "Lecture Slots": round(lecture["sessions"], 2) if lecture else 0,
                "Practice Slots": round(practice["sessions"], 2) if practice else 0,
                "Exam Slots": round(exam["sessions"], 2) if exam else 0,
                "Total Slots": round((lecture["sessions"] if lecture else 0) + (practice["sessions"] if practice else 0) + (exam["sessions"] if exam else 0), 2),
                "Lecture %": round(lecture["completion"], 1) if lecture else None,
                "Practice %": round(practice["completion"], 1) if practice else None,
                "Exam %": round(exam["completion"], 1) if exam else None,
                "Score %": round(overall_assessment_row["score"] * 100, 1) if overall_assessment_row["score"] is not None else None,
                "Participation #": round(overall_assessment_row["participation"], 1) if overall_assessment_row["participation"] is not None else None,
                "Skill Score %": round(skill_assessment_row["score"] * 100, 1) if skill_assessment_row["score"] is not None else None,
                "Skill Participation #": round(skill_assessment_row["participation"], 1) if skill_assessment_row["participation"] is not None else None,
                "Academic Assessment Score %": round(graded_assessment_row["score"] * 100, 1) if graded_assessment_row["score"] is not None else None,
                "Academic Assessment Participation #": round(graded_assessment_row["participation"], 1) if graded_assessment_row["participation"] is not None else None,
            }
        )

    overall_assessment = summarize_assessment_subset(assessment_filtered)
    skill_assessment = summarize_assessment_subset(assessment_filtered, "Skill Assessment")
    graded_assessment = summarize_assessment_subset(assessment_filtered, "Graded Assessment")

    return {
        "courseCount": len(course_records),
        "classSize": get_roster_size_for_scope(filtered, section),
        "lectureCount": float(lecture_df["sessions"].sum()) if not lecture_df.empty else 0,
        "practiceCount": float(practice_df["sessions"].sum()) if not practice_df.empty else 0,
        "examCount": float(exam_df["sessions"].sum()) if not exam_df.empty else 0,
        "totalSessions": float(filtered["sessions"].sum()),
        "overallCompletion": float(filtered["completion"].mean()),
        "lectureCompletion": float(lecture_df["completion"].mean()) if not lecture_df.empty else 0,
        "practiceCompletion": float(practice_df["completion"].mean()) if not practice_df.empty else 0,
        "examCompletion": float(exam_df["completion"].mean()) if not exam_df.empty else 0,
        "assessmentScore": float(overall_assessment["score"] * 100) if overall_assessment["score"] is not None else None,
        "assessmentParticipation": overall_assessment["participation"],
        "skillAssessmentScore": float(skill_assessment["score"] * 100) if skill_assessment["score"] is not None else None,
        "skillAssessmentParticipation": skill_assessment["participation"],
        "gradedAssessmentScore": float(graded_assessment["score"] * 100) if graded_assessment["score"] is not None else None,
        "gradedAssessmentParticipation": graded_assessment["participation"],
        "courseTable": pd.DataFrame(course_records),
    }


def filter_course_table(course_table: pd.DataFrame, semester: str):
    if course_table.empty:
        return course_table.copy(), 0
    filtered = course_table.copy()
    excluded_courses = NON_CORE_COURSES_BY_SEMESTER.get(semester, set())
    if excluded_courses:
        filtered = filtered[~filtered["Course"].isin(excluded_courses)].copy()
    hidden_count = len(course_table) - len(filtered)
    if filtered.empty:
        filtered = course_table.copy()
        hidden_count = 0
    filtered = filtered.sort_values(["Total Slots", "Course"], ascending=[False, True]).reset_index(drop=True)
    return filtered, hidden_count


def format_metric_value(value, decimals: int = 1, suffix: str = "", empty: str = "--") -> str:
    if value is None or pd.isna(value):
        return empty
    if isinstance(value, (int, float)):
        if decimals == 0:
            return f"{int(round(value)):,}{suffix}"
        return f"{value:,.{decimals}f}{suffix}"
    return f"{value}{suffix}"


def build_last_updated_label(*frames: pd.DataFrame) -> str:
    timestamps = []
    for frame in frames:
        if frame.empty or "report_date" not in frame.columns:
            continue
        parsed = pd.to_datetime(frame["report_date"], errors="coerce").dropna()
        if not parsed.empty:
            timestamps.append(parsed.max())
    if not timestamps:
        return "Not available"
    return max(timestamps).strftime("%d %b %Y")


def inject_custom_css():
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
                color: #0f172a;
            }
            .block-container {
                max-width: 1320px;
                padding-top: 1.4rem;
                padding-left: 2rem;
                padding-right: 2rem;
                padding-bottom: 2.5rem;
            }
            * {
                box-sizing: border-box;
            }
            div[data-testid="column"] {
                min-width: 0;
            }
            div[data-testid="column"] > div {
                width: 100%;
            }
            [data-testid="stHeader"] {
                background: rgba(248, 250, 252, 0.9);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(148, 163, 184, 0.18);
            }
            [data-testid="stToolbar"] {
                right: 1rem;
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
                border-right: 1px solid rgba(148, 163, 184, 0.2);
            }
            [data-testid="stSidebar"] * {
                color: #e2e8f0;
            }
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] .stRadio > div {
                background: rgba(15, 23, 42, 0.58);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 14px;
            }
            [data-testid="stSidebar"] .stButton button {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                border: none;
                color: white;
                font-weight: 600;
            }
            [data-baseweb="select"] > div {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(148, 163, 184, 0.24);
                border-radius: 14px;
                min-height: 48px;
                box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
            }
            [data-testid="stButton"] button {
                min-height: 44px;
                white-space: normal;
                line-height: 1.2;
            }
            [data-testid="stButton"] button p {
                line-height: 1.2;
            }
            .stSelectbox label p,
            .stRadio label p {
                font-weight: 600;
            }
            .hero-card {
                background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #38bdf8 100%);
                border-radius: 24px;
                color: white;
                padding: 28px 30px;
                box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18);
                margin-bottom: 18px;
                width: 100%;
            }
            .hero-eyebrow {
                font-size: 0.8rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                opacity: 0.8;
                text-transform: uppercase;
                margin-bottom: 8px;
            }
            .hero-title {
                font-size: 2rem;
                font-weight: 700;
                margin: 0;
            }
            .hero-subtitle {
                margin-top: 10px;
                font-size: 0.98rem;
                line-height: 1.6;
                max-width: 900px;
                color: rgba(255, 255, 255, 0.88);
            }
            .hero-meta {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 10px;
                margin-top: 18px;
            }
            .hero-pill {
                background: rgba(255, 255, 255, 0.14);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 999px;
                padding: 8px 12px;
                font-size: 0.85rem;
                font-weight: 600;
                max-width: 100%;
                overflow-wrap: anywhere;
            }
            .section-heading {
                margin: 6px 0 2px 0;
                font-size: 1.2rem;
                font-weight: 700;
                color: #0f172a;
                overflow-wrap: anywhere;
            }
            .section-caption {
                color: #475569;
                margin-bottom: 12px;
                font-size: 0.94rem;
                overflow-wrap: anywhere;
            }
            .metric-row-gap {
                height: 0.75rem;
            }
            .metric-card {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 20px;
                padding: 18px 18px 16px 18px;
                box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
                min-height: 132px;
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            .metric-label {
                color: #475569;
                font-size: 0.86rem;
                font-weight: 600;
                margin-bottom: 10px;
                min-height: 2.35em;
                line-height: 1.25;
                overflow-wrap: anywhere;
            }
            .metric-value {
                color: #0f172a;
                font-size: 1.55rem;
                font-weight: 700;
                line-height: 1.1;
                margin-bottom: 8px;
                overflow-wrap: anywhere;
            }
            .metric-help {
                color: #64748b;
                font-size: 0.8rem;
                line-height: 1.5;
                margin-top: auto;
                overflow-wrap: anywhere;
            }
            .info-card {
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid rgba(148, 163, 184, 0.22);
                border-radius: 18px;
                padding: 14px 16px;
                color: #334155;
                margin-bottom: 12px;
                overflow-wrap: anywhere;
            }
            div[data-testid="stDataFrame"] {
                border: 1px solid rgba(148, 163, 184, 0.24);
                border-radius: 18px;
                overflow: hidden;
                box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
                background: rgba(255, 255, 255, 0.94);
            }
            div[data-testid="stTabs"] [data-baseweb="tab-list"] {
                gap: 0.75rem;
                margin-bottom: 1rem;
            }
            div[data-testid="stTabs"] button {
                font-weight: 600;
                border: 1px solid rgba(148, 163, 184, 0.24);
                border-radius: 999px;
                padding: 0.55rem 1rem;
                background: rgba(255, 255, 255, 0.92);
                color: #334155;
            }
            div[data-testid="stTabs"] button[aria-selected="true"] {
                background: #eff6ff;
                color: #1d4ed8;
                border-color: rgba(59, 130, 246, 0.35);
            }
            div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
                display: none;
            }
            @media (max-width: 900px) {
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                .hero-card {
                    padding: 22px 20px;
                    border-radius: 20px;
                }
                .hero-title {
                    font-size: 1.55rem;
                }
                .metric-card {
                    min-height: auto;
                }
                .metric-label {
                    min-height: 0;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def escape_html(value) -> str:
    return html.escape(str(value), quote=True)


def render_section_header(title: str, caption: str):
    st.markdown(f"<div class='section-heading'>{escape_html(title)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-caption'>{escape_html(caption)}</div>", unsafe_allow_html=True)


def chunk_metric_items(items: list[dict], max_columns: int = 4) -> list[list[dict]]:
    remaining = list(items)
    rows = []
    while remaining:
        if len(remaining) <= max_columns:
            rows.append(remaining)
            break
        row_size = 3 if len(remaining) in (5, 6) else max_columns
        rows.append(remaining[:row_size])
        remaining = remaining[row_size:]
    return rows


def render_metric_row(items):
    metric_rows = chunk_metric_items(items)
    for row_index, row_items in enumerate(metric_rows):
        columns = st.columns(len(row_items), gap="medium")
        for column, item in zip(columns, row_items):
            help_text = f"<div class='metric-help'>{escape_html(item.get('help', ''))}</div>" if item.get("help") else ""
            column.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{escape_html(item['label'])}</div>
                    <div class="metric-value">{escape_html(item['value'])}</div>
                    {help_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
        if row_index < len(metric_rows) - 1:
            st.markdown("<div class='metric-row-gap'></div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="NIAT Analytics Streamlit", layout="wide")
    inject_custom_css()

    with st.sidebar:
        st.markdown("## Audit Analysis")
        st.caption("Live Streamlit dashboard for delivery and assessment tracking.")
        batch = st.selectbox("Batch", ["NIAT 24", "NIAT 25", "NIAT 26"], index=1)
        available_semesters = get_available_semesters_for_batch(batch)
        if not available_semesters:
            st.warning(f"No configured semesters are available yet for {batch}.")
            st.caption("Future batches stay hidden until their semester windows start, so the dashboard avoids irrelevant fetches.")
            st.stop()
        default_semester = available_semesters[-1]
        previous_batch = st.session_state.get("batch")
        previous_semester = st.session_state.get("semester")
        if previous_batch == batch and previous_semester in available_semesters:
            default_semester = previous_semester
        semester = st.selectbox("Semester", available_semesters, index=available_semesters.index(default_semester))
        st.caption(f"Available for {batch}: {', '.join(available_semesters)}")
        analysis_type = st.radio("Grouping Logic", ["overview", "design", "delivered"], format_func=lambda value: value.title())
        load_clicked = st.button("Load latest data", type="primary", use_container_width=True)
        st.markdown("---")
        st.caption("Overview starts with the university timeline table and drills into a single university course breakdown.")
        st.caption("Design groups universities by planned hours. Delivered groups them by completed slots.")
        st.caption("Streamlit Cloud must have BigQuery credentials in app secrets.")

    if load_clicked or "semester_df" not in st.session_state or st.session_state.get("batch") != batch or st.session_state.get("semester") != semester:
        with st.spinner("Fetching data from BigQuery..."):
            semester_df = fetch_semester_data(batch, semester)
            progress_slots_df = fetch_progress_delivered_slots(batch, semester)
            assessment_df = fetch_assessment_data(batch, semester)
            new_metrics = fetch_all_new_metrics(batch, semester)
            sem_course_titles = fetch_sem_course_titles(batch, semester)
            st.session_state["semester_df"] = semester_df
            st.session_state["progress_slots_df"] = progress_slots_df
            st.session_state["assessment_df"] = assessment_df
            st.session_state["new_metrics"] = new_metrics
            st.session_state["sem_course_titles"] = sem_course_titles
            st.session_state["batch"] = batch
            st.session_state["semester"] = semester

    semester_df = st.session_state.get("semester_df", pd.DataFrame())
    progress_slots_df = st.session_state.get("progress_slots_df", pd.DataFrame())
    assessment_df = st.session_state.get("assessment_df", pd.DataFrame())
    new_metrics = st.session_state.get("new_metrics", {})
    sem_course_titles = st.session_state.get("sem_course_titles", {})

    if semester_df.empty:
        st.warning("No semester data returned. Check the selected filters and Streamlit Cloud secrets.")
        st.stop()

    series_analysis_type = "delivered" if analysis_type == "overview" else analysis_type
    series_data = calculate_series_data(semester_df, assessment_df, series_analysis_type, semester)
    active_series = [series["name"] for series in SERIES_RANGES if series_data[series["name"]]["universities"]]
    if not active_series:
        st.warning("No active series available for the selected filters.")
        st.stop()

    series_rows = []
    all_universities = []
    for series in SERIES_RANGES:
        data = series_data[series["name"]]
        if not data["universities"]:
            continue
        all_universities.extend(data["universities"])
        series_rows.append(
            {
                "Series": series["name"],
                "Universities": len(data["universities"]),
                "Students": int(data["totalStudents"]),
                "Avg Slots": round(data["avgSessions"], 1),
                "Avg Delivery %": round(data["avgOverallCompletion"], 1),
                "Avg Score %": round(data["avgAssessmentScore"] * 100, 1) if data["avgAssessmentScore"] is not None else None,
                "Avg Allotted Hours": round(data["avgAllottedHours"], 1) if data["avgAllottedHours"] else None,
            }
        )
    series_df = pd.DataFrame(series_rows)

    total_students = int(semester_df.groupby(["institute", "section"])["students"].max().sum()) if not semester_df.empty else 0
    avg_delivery = sum(item["avgOverallCompletion"] for item in all_universities) / len(all_universities)
    score_values = [item["avgAssessmentScore"] * 100 for item in all_universities if item["avgAssessmentScore"] is not None]
    avg_score = sum(score_values) / len(score_values) if score_values else None
    skill_score_values = [item["avgSkillScore"] * 100 for item in all_universities if item.get("avgSkillScore") is not None]
    avg_skill_score = sum(skill_score_values) / len(skill_score_values) if skill_score_values else None
    graded_score_values = [item["avgGradedScore"] * 100 for item in all_universities if item.get("avgGradedScore") is not None]
    avg_graded_score = sum(graded_score_values) / len(graded_score_values) if graded_score_values else None
    allotted_values = [item["allottedHours"] for item in all_universities if item["allottedHours"] is not None]
    avg_allotted_hours = sum(allotted_values) / len(allotted_values) if allotted_values else None
    last_updated = build_last_updated_label(semester_df, assessment_df)
    analysis_label = {
        "overview": "University overview",
        "design": "Planned schedule bands",
        "delivered": "Delivered slot bands",
    }[analysis_type]

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-eyebrow">Audit Dashboard</div>
            <h1 class="hero-title">NIAT delivery and assessment view</h1>
            <div class="hero-subtitle">Cleaned Streamlit layout focused on series performance, university delivery, and course-level completion. Course tables hide non-core subjects where applicable so the breakdown stays readable.</div>
            <div class="hero-meta">
                <div class="hero-pill">Batch: {escape_html(batch)}</div>
                <div class="hero-pill">Semester: {escape_html(semester)}</div>
                <div class="hero-pill">Grouping: {escape_html(analysis_label)}</div>
                <div class="hero-pill">Last updated: {escape_html(last_updated)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if analysis_type == "overview":
        if st.session_state.get("analysis_type_mode") != "overview" and "pending_current_view" not in st.session_state:
            st.session_state["current_view"] = "University Overview"
        overview_university_options = sorted(item["name"] for item in all_universities)
        if overview_university_options:
            current_section_options = ["All Sections"]
            current_selected_university = st.session_state.get("selected_university")
            if current_selected_university in overview_university_options:
                available_sections = get_available_sections(semester_df, current_selected_university)
                current_section_options = ["All Sections"] + available_sections if available_sections else ["All Sections"]
            apply_pending_navigation_state(overview_university_options, current_section_options)
            if st.session_state.get("selected_university") not in overview_university_options:
                st.session_state["selected_university"] = overview_university_options[0]
        if st.session_state.get("current_view") not in ["University Overview", "Course Breakdown"]:
            st.session_state["current_view"] = "University Overview"
    st.session_state["analysis_type_mode"] = analysis_type

    top_metrics = [
        {"label": "Universities", "value": format_metric_value(semester_df["institute"].nunique(), decimals=0), "help": "Institutions with schedule data in the current view."},
        {"label": "Students", "value": format_metric_value(total_students, decimals=0), "help": "Summed section roster size using the latest section-level student counts."},
    ]
    if analysis_type == "design":
        top_metrics.append({"label": "Avg Allotted Hours", "value": format_metric_value(avg_allotted_hours, decimals=1), "help": "Average planned hours for universities in the selected design view."})
    top_metrics.extend(
        [
            {"label": "Avg Delivery %", "value": format_metric_value(avg_delivery, suffix="%"), "help": "Average university delivery across lecture, practice, and exam completion."},
            {"label": "Avg Score %", "value": format_metric_value(avg_score, suffix="%"), "help": "Average assessment score for universities with assessment data."},
            {"label": "Skill Score %", "value": format_metric_value(avg_skill_score, suffix="%"), "help": "Average skill assessment score for universities with skill assessment data."},
            {"label": "Academic Assessment Score %", "value": format_metric_value(avg_graded_score, suffix="%"), "help": "Average academic assessment score for universities with academic assessment data."},
        ]
    )
    if not (analysis_type == "overview" and st.session_state.get("current_view") == "Course Breakdown"):
        render_metric_row(top_metrics)

    selected_series = None
    series_summary = None
    if analysis_type == "overview":
        universities = sorted(all_universities, key=lambda item: item["name"])
        university_options = [item["name"] for item in universities]
        if not university_options:
            st.warning("No university data available for overview.")
            st.stop()
        if st.session_state.get("selected_university") not in university_options:
            st.session_state["selected_university"] = university_options[0]
        selected_university = st.session_state.get("selected_university", university_options[0])
        sections = get_available_sections(semester_df, selected_university)
        section_options = ["All Sections"] + sections if sections else ["All Sections"]
        if st.session_state.get("selected_section_label") not in section_options:
            st.session_state["selected_section_label"] = "All Sections"
        selected_section_label = st.session_state.get("selected_section_label", "All Sections")
    else:
        render_section_header("Focus selection", "Choose the series, university, and section scope before reviewing the tables below.")
        if st.session_state.get("selected_series") not in active_series:
            st.session_state["selected_series"] = active_series[0]
        filter_col_1, filter_col_2, filter_col_3 = st.columns([1, 1.35, 1], gap="medium", vertical_alignment="bottom")
        with filter_col_1:
            selected_series = st.selectbox("Series", active_series, key="selected_series")
        series_summary = series_data[selected_series]
        universities = sorted(series_summary["universities"], key=lambda item: item["name"])
        university_options = [item["name"] for item in universities]
        section_options = ["All Sections"]
        apply_pending_navigation_state(university_options, section_options)
        if st.session_state.get("selected_university") not in university_options:
            st.session_state["selected_university"] = university_options[0]
        selected_university = st.session_state["selected_university"]
        sections = get_available_sections(semester_df, selected_university)
        section_options = ["All Sections"] + sections if sections else ["All Sections"]
        apply_pending_navigation_state(university_options, section_options)
        selected_university = st.session_state.get("selected_university", selected_university)
        sections = get_available_sections(semester_df, selected_university)
        section_options = ["All Sections"] + sections if sections else ["All Sections"]
        with filter_col_2:
            selected_university = st.selectbox("University", university_options, key="selected_university")
        if st.session_state.get("selected_section_label") not in section_options:
            st.session_state["selected_section_label"] = "All Sections"
        with filter_col_3:
            selected_section_label = st.selectbox("Section", section_options, key="selected_section_label")
    selected_section = "" if selected_section_label == "All Sections" else selected_section_label

    university_rows = pd.DataFrame(
        [
            {
                "University": item["name"],
                "Sections": item["sectionCount"],
                "Allotted Hours": round(item["allottedHours"], 1) if item["allottedHours"] is not None else None,
                "Avg Slots": round(item["avgSessions"], 1),
                "Lecture %": round(item["avgLectureCompletion"], 1),
                "Practice %": round(item["avgPracticeCompletion"], 1),
                "Exam %": round(item["avgExamCompletion"], 1),
                "Avg Delivery %": round(item["avgOverallCompletion"], 1),
                "Avg Score %": round(item["avgAssessmentScore"] * 100, 1) if item["avgAssessmentScore"] is not None else None,
                "Participation #": round(item["avgParticipation"], 1) if item["avgParticipation"] is not None else None,
                "Skill Score %": round(item["avgSkillScore"] * 100, 1) if item.get("avgSkillScore") is not None else None,
                "Skill Participation #": round(item["avgSkillParticipation"], 1) if item.get("avgSkillParticipation") is not None else None,
                "Academic Assessment Score %": round(item["avgGradedScore"] * 100, 1) if item.get("avgGradedScore") is not None else None,
                "Academic Assessment Participation #": round(item["avgGradedParticipation"], 1) if item.get("avgGradedParticipation") is not None else None,
            }
            for item in universities
        ]
    ).sort_values(["Avg Delivery %", "University"], ascending=[False, True]).reset_index(drop=True)

    university_metrics = build_university_metrics(semester_df, assessment_df, selected_university, selected_section, semester, sem_course_titles)
    if university_metrics is None:
        st.warning("No university data available for the current selection.")
        st.stop()
    course_table, hidden_courses = filter_course_table(university_metrics["courseTable"], semester)
    dates = get_semester_dates_for_institute(selected_university, semester, batch)

    timeline_df = build_university_timeline_rows(all_universities, semester, batch)
    overview_df = build_university_overview_rows(all_universities, semester, batch, progress_slots_df, new_metrics)
    if analysis_type == "overview":
        current_view = st.session_state.get("current_view", "University Overview")
    else:
        view_options = ["Series Overview", "University Comparison", "Course Breakdown"]
        if analysis_type == "delivered":
            view_options.insert(2, "University Timeline")
        if st.session_state.get("current_view") not in view_options:
            st.session_state["current_view"] = view_options[0]
        current_view = st.radio("View", view_options, key="current_view", horizontal=True)

    if analysis_type == "overview" and current_view == "University Overview":
        render_section_header("University overview", "Filter by delivery mode and click a university row to open its course breakdown.")
        st.caption(f"Expected slots till date is calculated as of {format_today_display_date()}.")
        delivery_mode_map = {
            "All": None,
            "Full": "Full Delivery",
            "Co": "Co Delivery",
            "Hybrid": "Hybrid Delivery",
        }
        available_modes = set(overview_df["Delivery Mode"].dropna().tolist())
        delivery_mode_options = ["All"] + [label for label, value in delivery_mode_map.items() if value and value in available_modes]
        if st.session_state.get("overview_delivery_mode") not in delivery_mode_options:
            st.session_state["overview_delivery_mode"] = "All"
        filter_labels = ["All", "Full", "Co", "Hybrid"]
        filter_columns = st.columns(len(filter_labels), gap="small")
        selected_delivery_mode = st.session_state.get("overview_delivery_mode", "All")
        for column, label in zip(filter_columns, filter_labels):
            disabled = label not in delivery_mode_options
            button_type = "primary" if selected_delivery_mode == label else "secondary"
            with column:
                if st.button(label, key=f"overview_mode_{label}", use_container_width=True, disabled=disabled, type=button_type):
                    st.session_state["overview_delivery_mode"] = label
                    st.rerun()
        selected_delivery_mode = st.session_state.get("overview_delivery_mode", "All")
        selected_delivery_mode_value = delivery_mode_map.get(selected_delivery_mode)
        filtered_overview_df = overview_df.copy()
        if selected_delivery_mode_value:
            filtered_overview_df = filtered_overview_df[filtered_overview_df["Delivery Mode"] == selected_delivery_mode_value].reset_index(drop=True)
        if filtered_overview_df.empty:
            st.caption("No universities match the selected delivery mode.")
        else:
            overview_table_key = f"overview_university_table_{st.session_state.get('overview_table_nonce', 0)}"
            overview_selection = st.dataframe(
                filtered_overview_df,
                use_container_width=True,
                hide_index=True,
                key=overview_table_key,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Universities":                          st.column_config.TextColumn("Universities"),
                    "Delivery Mode":                         st.column_config.TextColumn("Delivery Mode"),
                    "Start Date":                            st.column_config.TextColumn("Start Date"),
                    "End Date":                              st.column_config.TextColumn("End Date"),
                    "Expected Slots":                        st.column_config.NumberColumn("Expected Slots", format="%.1f"),
                    "Expected Slots Till Date":              st.column_config.NumberColumn("Expected Slots Till Date", format="%.1f"),
                    "Actual Slots Delivered Till Date":      st.column_config.NumberColumn("Actual Slots Delivered Till Date", format="%.1f"),
                    "Deviation %":                           st.column_config.NumberColumn("Deviation %", format="%.1f%%", help="(Actual − Expected Till Date) / Expected Till Date × 100. Negative = behind schedule."),
                    "Session Delivery %":                    st.column_config.NumberColumn("Session Delivery %", format="%.1f%%", help="Actual Slots Delivered Till Date / Expected Slots Till Date × 100"),
                    "Class Room Quizzes Attempt %":          st.column_config.NumberColumn("Class Room Quizzes Attempt %", format="%.1f%%", help="Students who attempted classroom quizzes / total enrolled × 100"),
                    "Class Room Quizzes Pass %":             st.column_config.NumberColumn("Class Room Quizzes Pass %", format="%.1f%%", help="Students scored ≥80% / students who attempted classroom quizzes × 100"),
                    "Practice Delivery %":                   st.column_config.NumberColumn("Practice Delivery %", format="%.1f%%", help="Practice units delivered / planned practice sessions × 100"),
                    "Practice Completion %":                 st.column_config.NumberColumn("Practice Completion %", format="%.1f%%", help="Students who completed practice / total enrolled × 100"),
                    "Module Quiz Conduction %":              st.column_config.NumberColumn("Module Quiz Conduction %", format="%.1f%%", help="Module quizzes conducted / planned module quizzes × 100"),
                    "Module Quiz Student Participation %":   st.column_config.NumberColumn("Module Quiz Student Participation %", format="%.1f%%", help="Students who attempted module quiz / total enrolled × 100"),
                    "Module Quiz Pass %":                    st.column_config.NumberColumn("Module Quiz Pass %", format="%.1f%%", help="Students scored ≥80% / students attempted module quiz × 100"),
                    "Skill Assessment Conduction %":         st.column_config.NumberColumn("Skill Assessment Conduction %", format="%.1f%%", help="Skill assessments conducted / planned skill assessments × 100"),
                    "Skill Assessment Student Participation %": st.column_config.NumberColumn("Skill Assessment Student Participation %", format="%.1f%%", help="Students attempted skill assessment / total enrolled × 100"),
                    "Skill Assessment Pass %":               st.column_config.NumberColumn("Skill Assessment Pass %", format="%.1f%%", help="Students passed (section_evaluation_result=PASSED) / students attempted skill assessment × 100"),
                    "Academic Assessments Attempt %":        st.column_config.NumberColumn("Academic Assessments Attempt %", format="%.1f%%", help="Students who attempted graded assessments / total enrolled × 100"),
                    "Academic Assessments Pass %":           st.column_config.NumberColumn("Academic Assessments Pass %", format="%.1f%%", help="Students passed (section_evaluation_result=PASSED) / students attempted academic assessments × 100"),
                },
            )
            selected_rows = []
            if overview_selection is not None:
                selection_state = getattr(overview_selection, "selection", None)
                if selection_state is not None:
                    selected_rows = list(getattr(selection_state, "rows", []) or [])
                elif isinstance(overview_selection, dict):
                    selected_rows = overview_selection.get("selection", {}).get("rows", []) or []
            if selected_rows:
                clicked_university = filtered_overview_df.iloc[selected_rows[0]]["Universities"]
                queue_course_breakdown_navigation(clicked_university)
                st.session_state["overview_table_nonce"] = st.session_state.get("overview_table_nonce", 0) + 1
                st.rerun()

    elif current_view == "Series Overview":
        render_section_header("Series snapshot", "Each series groups universities by planned or delivered volume based on the selected sidebar logic.")
        series_metrics = [
            {"label": "Selected Series", "value": selected_series, "help": "Current benchmark band used for comparison."},
            {"label": "Universities in Series", "value": format_metric_value(len(universities), decimals=0), "help": "Institutions included in the selected series."},
        ]
        if analysis_type == "design":
            series_metrics.append({"label": "Series Allotted Hours", "value": format_metric_value(series_summary["avgAllottedHours"], decimals=1), "help": "Average planned hours for universities in this design series."})
        series_metrics.extend(
            [
                {"label": "Series Delivery %", "value": format_metric_value(series_summary["avgOverallCompletion"], suffix="%"), "help": "Average delivery across universities in this series."},
                {"label": "Series Score %", "value": format_metric_value(series_summary["avgAssessmentScore"] * 100 if series_summary["avgAssessmentScore"] is not None else None, suffix="%"), "help": "Average assessment score for universities in this series."},
                {"label": "Skill Score %", "value": format_metric_value(series_summary["avgSkillScore"] * 100 if series_summary["avgSkillScore"] is not None else None, suffix="%"), "help": "Average skill assessment score for universities in this series."},
                {"label": "Academic Assessment Score %", "value": format_metric_value(series_summary["avgGradedScore"] * 100 if series_summary["avgGradedScore"] is not None else None, suffix="%"), "help": "Average academic assessment score for universities in this series."},
            ]
        )
        render_metric_row(series_metrics)
        st.dataframe(
            series_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Series": st.column_config.TextColumn("Series"),
                "Universities": st.column_config.NumberColumn("Universities", format="%d"),
                "Students": st.column_config.NumberColumn("Students", format="%d"),
                "Avg Slots": st.column_config.NumberColumn("Avg Slots", format="%.1f"),
                "Avg Delivery %": st.column_config.NumberColumn("Avg Delivery %", format="%.1f%%"),
                "Avg Score %": st.column_config.NumberColumn("Avg Score %", format="%.1f%%"),
                "Skill Score %": st.column_config.NumberColumn("Skill Score %", format="%.1f%%"),
                "Academic Assessment Score %": st.column_config.NumberColumn("Academic Assessment Score %", format="%.1f%%"),
                "Avg Allotted Hours": st.column_config.NumberColumn("Avg Allotted Hours", format="%.1f"),
            },
        )

    elif current_view == "University Comparison":
        render_section_header("University benchmark", "Practice %, Exam %, and Lecture % are completion percentages. Avg Delivery % is the overall university delivery view.")
        st.dataframe(
            university_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "University": st.column_config.TextColumn("University"),
                "Sections": st.column_config.NumberColumn("Sections", format="%d"),
                "Allotted Hours": st.column_config.NumberColumn("Allotted Hours", format="%.1f"),
                "Avg Slots": st.column_config.NumberColumn("Avg Slots", format="%.1f"),
                "Lecture %": st.column_config.NumberColumn("Lecture %", format="%.1f%%"),
                "Practice %": st.column_config.NumberColumn("Practice %", format="%.1f%%"),
                "Exam %": st.column_config.NumberColumn("Exam %", format="%.1f%%"),
                "Avg Delivery %": st.column_config.NumberColumn("Avg Delivery %", format="%.1f%%"),
                "Avg Score %": st.column_config.NumberColumn("Avg Score %", format="%.1f%%"),
                "Participation #": st.column_config.NumberColumn("Participation #", format="%.1f"),
                "Skill Score %": st.column_config.NumberColumn("Skill Score %", format="%.1f%%"),
                "Skill Participation #": st.column_config.NumberColumn("Skill Participation #", format="%.1f"),
                "Academic Assessment Score %": st.column_config.NumberColumn("Academic Assessment Score %", format="%.1f%%"),
                "Academic Assessment Participation #": st.column_config.NumberColumn("Academic Assessment Participation #", format="%.1f"),
            },
        )

    elif current_view == "University Timeline":
        render_section_header("University timeline", "Timeline overview for delivered mode using the configured semester dates and NIAT slot plan by university.")
        delivery_mode_options = ["All delivery modes"] + sorted([value for value in timeline_df["Delivery Mode"].dropna().unique().tolist() if value and value != "--"])
        if st.session_state.get("timeline_delivery_mode") not in delivery_mode_options:
            st.session_state["timeline_delivery_mode"] = "All delivery modes"
        timeline_filter_col_1, timeline_filter_col_2, timeline_action_col = st.columns([1, 1.25, 1.05], gap="medium", vertical_alignment="bottom")
        with timeline_filter_col_1:
            selected_delivery_mode = st.selectbox("Delivery mode filter", delivery_mode_options, key="timeline_delivery_mode")
        filtered_timeline_df = timeline_df.copy()
        if selected_delivery_mode != "All delivery modes":
            filtered_timeline_df = filtered_timeline_df[filtered_timeline_df["Delivery Mode"] == selected_delivery_mode].reset_index(drop=True)
        timeline_university_options = filtered_timeline_df["University"].tolist()
        if timeline_university_options:
            if st.session_state.get("timeline_selected_university") not in timeline_university_options:
                st.session_state["timeline_selected_university"] = timeline_university_options[0]
            with timeline_filter_col_2:
                timeline_selected_university = st.selectbox("Timeline university", timeline_university_options, key="timeline_selected_university")
            with timeline_action_col:
                st.button(
                    "Open Course Breakdown",
                    use_container_width=True,
                    on_click=open_course_breakdown_from_timeline,
                )
        else:
            with timeline_filter_col_2:
                st.caption("No universities match the selected delivery mode.")
        st.dataframe(
            filtered_timeline_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "University": st.column_config.TextColumn("University"),
                "Start Date": st.column_config.TextColumn("Start Date"),
                "End Date": st.column_config.TextColumn("End Date"),
                "Delivery Mode": st.column_config.TextColumn("Delivery Mode"),
                "Working Days": st.column_config.NumberColumn("Working Days", format="%.1f"),
                "Total NIAT Slots": st.column_config.NumberColumn("Total NIAT Slots", format="%.1f"),
                "NIAT Assessment Slots": st.column_config.NumberColumn("NIAT Assessment Slots", format="%.1f"),
                "Net NIAT Executional Slots": st.column_config.NumberColumn("Net NIAT Executional Slots", format="%.1f"),
                "Expected Slots": st.column_config.NumberColumn("Expected Slots", format="%.1f"),
                "Total NIAT Executional Days": st.column_config.NumberColumn("Total NIAT Executional Days", format="%.1f"),
                "Net NIAT No. of Weeks": st.column_config.NumberColumn("Net NIAT No. of Weeks", format="%.1f"),
            },
        )

    elif current_view == "Course Breakdown":
        if analysis_type == "overview":
            nav_col_1, nav_col_2, nav_col_3 = st.columns([0.34, 1.35, 1.1], gap="medium", vertical_alignment="bottom")
            with nav_col_1:
                if st.button("←", key="overview_back_arrow", use_container_width=True):
                    queue_overview_navigation()
                    st.rerun()
            sections = get_available_sections(semester_df, selected_university)
            section_options = ["All Sections"] + sections if sections else ["All Sections"]
            if st.session_state.get("selected_section_label") not in section_options:
                st.session_state["selected_section_label"] = "All Sections"
            with nav_col_2:
                st.selectbox("University", university_options, key="selected_university", disabled=True)
            with nav_col_3:
                selected_section_label = st.selectbox("Section", section_options, key="selected_section_label")
            selected_section = "" if selected_section_label == "All Sections" else selected_section_label
            university_metrics = build_university_metrics(semester_df, assessment_df, selected_university, selected_section, semester, sem_course_titles)
            if university_metrics is None:
                st.warning("No university data available for the current selection.")
                st.stop()
            course_table, hidden_courses = filter_course_table(university_metrics["courseTable"], semester)
        scope_label = selected_section if selected_section else "All sections"
        render_section_header(f"{selected_university} - {scope_label}", "Detailed course view for the selected university and section scope.")
        if dates:
            st.markdown(
                f"<div class='info-card'><strong>Semester window:</strong> {escape_html(dates['start'])} to {escape_html(dates['end'])}</div>",
                unsafe_allow_html=True,
            )
        if hidden_courses:
            st.markdown(
                f"<div class='info-card'><strong>Course cleanup applied:</strong> showing {escape_html(len(course_table))} focus courses and hiding {escape_html(hidden_courses)} support courses to keep the breakdown readable.</div>",
                unsafe_allow_html=True,
            )
        selected_university_meta = next((item for item in universities if item["name"] == selected_university), None)
        detail_metrics = [
            {"label": "Courses Shown", "value": format_metric_value(len(course_table), decimals=0), "help": "Visible courses after removing non-core subjects from the breakdown."},
            {"label": "Students", "value": format_metric_value(university_metrics["classSize"], decimals=0), "help": "Section roster size for the selected scope."},
            {"label": "Allotted Hours", "value": format_metric_value(selected_university_meta["allottedHours"] if selected_university_meta else None, decimals=1), "help": "Planned hours configured for the selected university."},
        ]
        detail_metrics.extend(
            [
                {"label": "Total Slots", "value": format_metric_value(university_metrics["totalSessions"], decimals=1), "help": "Combined lecture, practice, and exam slots."},
                {"label": "Avg Delivery %", "value": format_metric_value(university_metrics["overallCompletion"], suffix="%"), "help": "Overall completion across all session types in this scope."},
            ]
        )
        render_metric_row(detail_metrics)
        render_metric_row(
            [
                {"label": "Lecture %", "value": format_metric_value(university_metrics["lectureCompletion"], suffix="%"), "help": "Lecture completion percentage."},
                {"label": "Practice %", "value": format_metric_value(university_metrics["practiceCompletion"], suffix="%"), "help": "Practice completion percentage, not student completion."},
                {"label": "Exam %", "value": format_metric_value(university_metrics["examCompletion"], suffix="%"), "help": "Exam completion percentage."},
                {"label": "Score %", "value": format_metric_value(university_metrics["assessmentScore"], suffix="%"), "help": "Average assessment score percentage."},
                {"label": "Participation #", "value": format_metric_value(university_metrics["assessmentParticipation"], decimals=1), "help": "Average count of students who attempted the mapped assessments."},
            ]
        )
        render_metric_row(
            [
                {"label": "Skill Score %", "value": format_metric_value(university_metrics["skillAssessmentScore"], suffix="%"), "help": "Average skill assessment score percentage for the mapped courses."},
                {"label": "Skill Participation #", "value": format_metric_value(university_metrics["skillAssessmentParticipation"], decimals=1), "help": "Average count of students who attempted mapped skill assessments."},
                {"label": "Academic Assessment Score %", "value": format_metric_value(university_metrics["gradedAssessmentScore"], suffix="%"), "help": "Average academic assessment score percentage for the mapped courses."},
                {"label": "Academic Assessment Participation #", "value": format_metric_value(university_metrics["gradedAssessmentParticipation"], decimals=1), "help": "Average count of students who attempted mapped academic assessments."},
            ]
        )
        with st.expander("Metric definitions"):
            st.markdown(
                """
                - `Avg Delivery %`: average completion view used for university-level comparison.
                - `Practice %`, `Lecture %`, `Exam %`: completion percentages for those session types.
                - `Score %`: average assessment score percentage.
                - `Participation #`: average number of learners who attempted the mapped assessments.
                - `Skill Score %` / `Skill Participation #`: visible score and attempts for mapped skill assessments.
                - `Academic Assessment Score %` / `Academic Assessment Participation #`: visible score and attempts for mapped academic assessments.
                """
            )
        with st.expander("Pass field diagnostics (debug)"):
            diag = fetch_pass_field_values(batch, semester)
            if diag:
                st.dataframe(pd.DataFrame(diag), use_container_width=True, hide_index=True)
                st.caption("Shows distinct values of best_attempt_evaluation_result (quiz) and section_evaluation_result (skill/graded). Pass comparison uses IN ('PASS','PASSED').")
            else:
                st.caption("No diagnostic data returned.")
        st.dataframe(
            course_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Course": st.column_config.TextColumn("Course"),
                "Lecture Slots": st.column_config.NumberColumn("Lecture Slots", format="%.1f"),
                "Practice Slots": st.column_config.NumberColumn("Practice Slots", format="%.1f"),
                "Exam Slots": st.column_config.NumberColumn("Exam Slots", format="%.1f"),
                "Total Slots": st.column_config.NumberColumn("Total Slots", format="%.1f"),
                "Lecture %": st.column_config.NumberColumn("Lecture %", format="%.1f%%"),
                "Practice %": st.column_config.NumberColumn("Practice %", format="%.1f%%"),
                "Exam %": st.column_config.NumberColumn("Exam %", format="%.1f%%"),
                "Score %": st.column_config.NumberColumn("Score %", format="%.1f%%"),
                "Participation #": st.column_config.NumberColumn("Participation #", format="%.1f"),
                "Skill Score %": st.column_config.NumberColumn("Skill Score %", format="%.1f%%"),
                "Skill Participation #": st.column_config.NumberColumn("Skill Participation #", format="%.1f"),
                "Academic Assessment Score %": st.column_config.NumberColumn("Academic Assessment Score %", format="%.1f%%"),
                "Academic Assessment Participation #": st.column_config.NumberColumn("Academic Assessment Participation #", format="%.1f"),
            },
        )




if __name__ == "__main__":
    main()
