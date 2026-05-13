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
            "mathematics 1",
            "math for computer science",
            "mathematics for computer science",
            "mathematics for computing",
            "mathematics for data science",
            "mathematics for data science i",
            "engineering mathematics 1",
            "discrete mathematics",
            "linear algebra and optimization",
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
            "c programming",
            "python programming",
            "problem solving with python programming",
            "problem solving using python programming",
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
            "quantitative skills",
        ],
        "Physics": [
            "applied physics",
            "applied physics for data science",
            "applied physics for data science lab",
            "fundamentals of quantum computing",
        ],
        "Basic Electrical Engineering": [
            "basic electrical electronics engineering",
        ],
        "Basic Electronics": [
            "basic electronics",
            "basic electronics for cse",
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
            "js essentials",
            "javascript essentials",
            "js programming",
            "introduction to react js",
            "react js",
            "node js",
            "nodejs",
            "node.js",
            "node js mongodb",
            "backend node js",
            "backend development node js",
            "back end development node js",
            "back end development node js mongodb",
        ],
        "Database Management Systems": [
            "database management systems",
            "database management system",
            "database management systems laboratory",
            "database systems",
            "introduction to database",
            "introduction to databases",
            "introduction to database management systems",
            "introduction to database management systems lab",
            "introduction to dbms",
            "dbms fundamentals",
            "mongodb",
            "sql",
            "sql basics",
            "sql fundamentals",
            "structured query language",
            "mysql",
            "sql programming",
        ],
        "Data Structures": [
            "data structures",
            "data structure",
            "data structures laboratory",
            "data structures and algorithm",
            "data structures and algorithms",
            "data structures and algorithms laboratory",
            "data structures using c++",
            "data structures using c",
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
            "english advance",
            "advanced communicative english",
            "advanced technical english",
            "communicative english advanced",
            "technical communication for engineers",
            "aec 2",
            "english b1 level learner program",
            "communication english advanced",
            "english course",
            "english",
            "communicative english",
            "english language",
            "english communication",
            "advanced english",
            "advanced communication english",
            "advanced communicative english foundation",
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
            "fundamentals of quantum computing",
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
            "mathematics 2",
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
            "foreign language ii french",
            "foreign language ii",
            "language elective",
            "la e",
        ],
        "Engineering Drawing": [
            "engineering drawing",
            "engineering drawing design drafting",
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
            "Skill Assessment Pass %":      round(item["avgSkillScore"] * 100, 1) if item.get("avgSkillScore") is not None else None,
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
    st.session_state.pop("selected_course_for_detail", None)



def open_course_breakdown_from_timeline():
    queue_course_breakdown_navigation(st.session_state.get("timeline_selected_university"))


def apply_pending_navigation_state(active_universities, available_sections):
    pending_university = st.session_state.pop("pending_selected_university", None)
    pending_section = st.session_state.pop("pending_selected_section_label", None)
    pending_view = st.session_state.pop("pending_current_view", None)
    if pending_university in active_universities:
        if pending_university != st.session_state.get("selected_university"):
            st.session_state.pop("selected_course_for_detail", None)
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

    # Streamlit Cloud: credentials are in st.secrets["gcp_service_account"]
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"])
        )
    else:
        # Local fallback: load from service-account.json file
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


def build_content_subquery_with_course_id(content_table: str, course_id_col: str) -> str:
    """Extended content subquery that also selects portal_course_id for cross-join matching."""
    return f"""
        SELECT
          unit_id,
          MAX(CAST({bq_column(course_id_col)} AS STRING)) AS portal_course_id,
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
            {bq_column(course_id_col)},
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
        quiz_totals AS (
          -- Aggregate directly at institute level; classroom and module are counted independently.
          -- Pass condition uses best_attempt_percentage_score >= 80 to avoid
          -- boolean-column cast issues with best_attempt_evaluation_result and to
          -- produce genuinely different classroom vs module pass rates.
          SELECT
            q.institute_name AS institute,
            -- Classroom: attempted = distinct users with classroom quiz; passed = distinct passers (score ≥ 80)
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ', q.user_id, NULL))
              AS classroom_attempted,
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ'
              AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80,
              q.user_id, NULL))
              AS classroom_passed,
            -- Module: conducted = distinct quiz_ids; attempted/passed = distinct user_ids (score ≥ 80)
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ'),
              q.quiz_id, NULL))
              AS module_quiz_conducted,
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ'),
              q.user_id, NULL))
              AS module_attempted,
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')
              AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80,
              q.user_id, NULL))
              AS module_passed
          FROM {refs["quiz_attempts"]} q
          WHERE {' AND '.join(where_clauses)}
            AND q.derived_unit_type IN ('CLASSROOM_QUIZ', 'MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')
          GROUP BY q.institute_name
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
    except Exception as e:
        st.error(f"fetch_quiz_metrics error: {e}")
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
def fetch_course_delivery_stats(batch: str, semester: str, institute: str) -> pd.DataFrame:
    """
    Returns per-course planned/delivered totals for a single institute.
    Source: session_adherence table (cumulative rows → MAX per slot → SUM across slots).
    """
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "TRIM(COALESCE(sa.course_title, '')) != ''",
    ]
    window_clause = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(sa.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")
    sql = f"""
        WITH slots AS (
          SELECT
            sa.course_title AS course,
            sa.section_name AS section,
            sa.session_type,
            sa.session_name_enum,
            MAX(sa.total_sessions_planned)   AS planned,
            MAX(sa.total_sessions_delivered) AS delivered
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(where_clauses)}
          GROUP BY course, section, session_type, session_name_enum
        )
        SELECT
          course,
          SUM(planned)   AS total_planned,
          SUM(delivered) AS total_delivered,
          ROUND(SAFE_DIVIDE(SUM(delivered), NULLIF(SUM(planned), 0)) * 100, 1) AS adherence_pct
        FROM slots
        GROUP BY course
        ORDER BY course
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_course_delivery_stats error: {e}")
        return pd.DataFrame(columns=["course", "total_planned", "total_delivered", "adherence_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_weekly_delivery(batch: str, semester: str, institute: str, course_title) -> pd.DataFrame:
    """
    Returns week-by-week planned/delivered/adherence for a single institute+course.
    course_title may be a str or tuple[str, ...] (multi-title subjects).
    Derives weekly delta from the cumulative totals in session_adherence.
    """
    if isinstance(course_title, str):
        course_title = (course_title,)
    titles_in = ", ".join(f"LOWER('{sql_escape(t)}')" for t in course_title)
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        f"LOWER(TRIM(COALESCE(sa.course_title, ''))) IN ({titles_in})",
    ]
    window_clause = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(sa.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")
    sql = f"""
        WITH cumulative AS (
          SELECT
            DATE_TRUNC(sa.session_date, WEEK(MONDAY)) AS week_start,
            MAX(sa.total_sessions_planned)   AS cum_planned,
            MAX(sa.total_sessions_delivered) AS cum_delivered
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(where_clauses)}
            AND sa.session_date <= CURRENT_DATE()
          GROUP BY week_start
        ),
        weekly AS (
          SELECT
            week_start,
            cum_planned,
            cum_delivered,
            LAG(cum_planned)   OVER (ORDER BY week_start) AS prev_planned,
            LAG(cum_delivered) OVER (ORDER BY week_start) AS prev_delivered
          FROM cumulative
        )
        SELECT
          week_start,
          FORMAT_DATE('%b %d', week_start) AS week_label,
          COALESCE(cum_planned   - prev_planned,   cum_planned)   AS planned,
          COALESCE(cum_delivered - prev_delivered, cum_delivered) AS delivered,
          ROUND(
            SAFE_DIVIDE(
              COALESCE(cum_delivered - prev_delivered, cum_delivered),
              NULLIF(COALESCE(cum_planned - prev_planned, cum_planned), 0)
            ) * 100, 1
          ) AS adherence_pct
        FROM weekly
        ORDER BY week_start
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_course_weekly_delivery error: {e}")
        return pd.DataFrame(columns=["week_start", "week_label", "planned", "delivered", "adherence_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_session_units(batch: str, semester: str, institute: str, course_title) -> pd.DataFrame:
    """
    Returns per-unit delivery stats using session_adherence.session_name_enum as the unit name.
    Also enriches PRACTICE units with student-level completion from unlocked_units.

    course_title may be a single str or a tuple[str, ...] of all raw titles that belong
    to the same subject (e.g. "Communicative English Advanced" + "English B1 Level Learner
    Program" both map to "Advanced Communicative English").

    session_adherence gives:  unit name (session_name_enum), session_type, planned, delivered
    unlocked_units gives:     student completion count per unit_id (PRACTICE units)
    content bridges:          unit_id ↔ course_title for filtering unlocked_units by course

    Columns: unit, session_type, section, total_sessions, delivered_sessions, completion_pct,
             total_students, students_completed  (NaN for non-PRACTICE types)
    """
    if isinstance(course_title, str):
        course_title = (course_title,)
    titles_in = ", ".join(f"LOWER('{sql_escape(t)}')" for t in course_title)
    refs = get_table_refs()
    sa_where = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        f"LOWER(TRIM(COALESCE(sa.course_title,    ''))) IN ({titles_in})",
        "TRIM(COALESCE(sa.session_name_enum, '')) != ''",
    ]
    sa_window = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if sa_window:
        sa_where.append(sa_window)
    if should_apply_batch_filter(batch):
        sa_where.append(f"LOWER(COALESCE(sa.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    uu_where = [
        f"LOWER(TRIM(COALESCE(uu.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    uu_window = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if uu_window:
        uu_where.append(uu_window)
    if should_apply_batch_filter(batch):
        uu_where.append(f"LOWER(COALESCE(uu.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    sql = f"""
        WITH
        -- ── Session delivery (all unit types) from session_adherence ──────────
        session_units AS (
          SELECT
            sa.session_name_enum                                      AS unit,
            sa.session_type,
            COALESCE(NULLIF(TRIM(sa.section_name), ''), 'Unknown')   AS section,
            MAX(sa.total_sessions_planned)                            AS total_sessions,
            MAX(sa.total_sessions_delivered)                          AS delivered_sessions
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(sa_where)}
          GROUP BY unit, session_type, section
        ),
        -- ── Student-level practice completion from unlocked_units ─────────────
        content AS (
          {build_content_subquery(refs["content"])}
        ),
        roster AS (
          SELECT
            u.institute_name,
            COALESCE(NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY u.institute_name, section
        ),
        practice_completion AS (
          -- Aggregated at section level (not per unit_id) so the JOIN on section
          -- below produces exactly one matching row per section, avoiding duplicates.
          SELECT
            COALESCE(NULLIF(TRIM(uu.section_name), ''), 'Unknown') AS section,
            MAX(r.total_students)                                   AS total_students,
            COUNT(DISTINCT CASE WHEN uu.unit_completion_status = 'COMPLETED' THEN uu.user_id END) AS students_completed
          FROM {refs["unlocked_units"]} uu
          INNER JOIN content c ON uu.unit_id = c.unit_id
          LEFT JOIN roster r
            ON r.institute_name = uu.institute_name
           AND r.section        = COALESCE(NULLIF(TRIM(uu.section_name), ''), 'Unknown')
          WHERE {' AND '.join(uu_where)}
            AND LOWER(TRIM(COALESCE(c.course_title, ''))) IN ({titles_in})
          GROUP BY section
        )
        -- ── Final: delivery stats joined with student completion where available
        SELECT
          su.unit,
          su.session_type,
          su.section,
          su.total_sessions,
          su.delivered_sessions,
          ROUND(SAFE_DIVIDE(su.delivered_sessions, NULLIF(su.total_sessions, 0)) * 100, 1) AS completion_pct,
          r.total_students,
          -- students_completed only meaningful for PRACTICE (from unlocked_units)
          CASE WHEN su.session_type = 'PRACTICE' THEN pc.students_completed ELSE NULL END AS students_completed
        FROM session_units su
        LEFT JOIN roster r
          ON LOWER(TRIM(r.institute_name)) = LOWER('{sql_escape(institute)}')
         AND r.section                     = su.section
        LEFT JOIN practice_completion pc
          ON pc.section = su.section
        ORDER BY su.session_type, su.unit
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_course_session_units error: {e}")
        return pd.DataFrame(columns=["unit", "session_type", "section", "total_sessions", "delivered_sessions", "completion_pct", "total_students", "students_completed"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_quiz_pass_by_course(batch: str, semester: str, institute: str) -> pd.DataFrame:
    """
    Returns per-course quiz pass rates for all courses at a given institute.
    When portal_course_id exists in the content table, also returns portal_course_id
    so the caller can match via ID when titles don't align.

    Columns: course_title, portal_course_id (optional), attempted, passed, pass_pct
    """
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(q.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "q.derived_unit_type IN ('CLASSROOM_QUIZ', 'MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')",
    ]
    window_clause = get_semester_window_clause(semester, batch, "q.institute_name", "q.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(q.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    # Detect portal_course_id in content table for richer grouping
    content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
    content_cols      = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
    content_cid_col   = first_existing_column(content_cols, ["portal_course_id", "course_id"])

    if content_cid_col:
        content_cte = build_content_subquery_with_course_id(refs["content"], content_cid_col)
        extra_select = "MAX(c.portal_course_id) AS portal_course_id,"
    else:
        content_cte = build_content_subquery(refs["content"])
        extra_select = "CAST(NULL AS STRING) AS portal_course_id,"

    sql = f"""
        WITH
        content AS (
          {content_cte}
        )
        SELECT
          c.course_title,
          {extra_select}
          COUNT(DISTINCT q.user_id)                                         AS attempted,
          COUNT(DISTINCT CASE WHEN UPPER(TRIM(COALESCE(q.best_attempt_evaluation_result, ''))) LIKE '%PASS%'
                              THEN q.user_id END)                           AS passed,
          ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN UPPER(TRIM(COALESCE(q.best_attempt_evaluation_result, ''))) LIKE '%PASS%'
                                THEN q.user_id END),
            NULLIF(COUNT(DISTINCT q.user_id), 0)
          ) * 100, 1)                                                       AS pass_pct
        FROM {refs["quiz_attempts"]} q
        INNER JOIN content c ON CAST(q.quiz_id AS STRING) = c.unit_id
        WHERE {' AND '.join(where_clauses)}
          AND TRIM(COALESCE(c.course_title, '')) != ''
        GROUP BY c.course_title
        ORDER BY c.course_title
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["course_title", "portal_course_id", "attempted", "passed", "pass_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_quiz_breakdown(batch: str, semester: str, institute: str, course_title: str, display_course_title: str = "") -> pd.DataFrame:
    """
    Returns per-quiz stats for a specific institute+course.

    Matching strategy (most → least specific):
      1. content.course_title = course_title  (session_adherence title)
      2. content.course_title = display_course_title  (sem_course_title / display name)
      3. content.portal_course_id IN (portal_courses where sem_course_title matches)
         — only when portal_course_id column exists in both tables

    Columns: quiz_id, quiz_name, quiz_type, section, attempted, passed, failed, pass_pct, total_students
    """
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(q.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "q.derived_unit_type IN ('CLASSROOM_QUIZ', 'MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')",
    ]
    window_clause = get_semester_window_clause(semester, batch, "q.institute_name", "q.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if should_apply_batch_filter(batch):
        where_clauses.append(f"LOWER(COALESCE(q.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    # Schedule where for quiz name lookup (institute + date window)
    sched_where = [f"LOWER(TRIM(COALESCE(s.institute_name, ''))) = LOWER('{sql_escape(institute)}')"]
    sched_window = get_semester_window_clause(semester, batch, "s.institute_name", "DATE(s.session_date)")
    if sched_window:
        sched_where.append(sched_window)
    if should_apply_batch_filter(batch):
        sched_where.append(f"LOWER(COALESCE(s.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")

    # ── Detect portal_course_id columns for fallback matching ─────────────────
    content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
    content_cols      = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
    content_cid_col   = first_existing_column(content_cols, ["portal_course_id", "course_id"])

    portal_table_ref  = get_config("BQ_PORTAL_COURSES_TABLE", DEFAULT_PORTAL_COURSES_TABLE)
    portal_cols       = fetch_table_columns(portal_table_ref, DEFAULT_PORTAL_COURSES_TABLE)
    portal_cid_col    = first_existing_column(portal_cols, ["portal_course_id", "course_id"])

    use_portal_fallback = bool(content_cid_col and portal_cid_col)

    # Build the content CTE and course filter expression
    if use_portal_fallback:
        content_cte = build_content_subquery_with_course_id(refs["content"], content_cid_col)
        # Which titles to look up in portal_courses
        portal_title_conditions = []
        for t in {course_title, display_course_title}:
            if t and t.strip():
                portal_title_conditions.append(
                    f"LOWER(TRIM(COALESCE(pc.sem_course_title, ''))) = LOWER('{sql_escape(t.strip())}')"
                )
        portal_title_where = " OR ".join(portal_title_conditions) if portal_title_conditions else "FALSE"
        portal_batch_filter = ""
        if should_apply_batch_filter(batch):
            portal_batch_filter = f"AND LOWER(COALESCE(pc.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'"

        portal_ids_cte = f"""
        portal_course_ids AS (
          SELECT DISTINCT CAST(pc.{bq_column(portal_cid_col)} AS STRING) AS pc_id
          FROM {refs["portal_courses"]} pc
          WHERE ({portal_title_where})
            AND TRIM(COALESCE(CAST(pc.{bq_column(portal_cid_col)} AS STRING), '')) != ''
            {portal_batch_filter}
        ),"""

        # Match by any of: raw course_title, display_course_title, or portal_course_id
        title_conditions = [f"LOWER(TRIM(COALESCE(c.course_title, ''))) = LOWER('{sql_escape(course_title)}')"]
        if display_course_title and display_course_title.strip() and display_course_title.strip().lower() != course_title.strip().lower():
            title_conditions.append(f"LOWER(TRIM(COALESCE(c.course_title, ''))) = LOWER('{sql_escape(display_course_title.strip())}')")
        title_conditions.append("c.portal_course_id IN (SELECT pc_id FROM portal_course_ids)")
        course_filter = "(" + "\n              OR ".join(title_conditions) + ")"
    else:
        content_cte = build_content_subquery(refs["content"])
        portal_ids_cte = ""
        title_conditions = [f"LOWER(TRIM(COALESCE(c.course_title, ''))) = LOWER('{sql_escape(course_title)}')"]
        if display_course_title and display_course_title.strip() and display_course_title.strip().lower() != course_title.strip().lower():
            title_conditions.append(f"LOWER(TRIM(COALESCE(c.course_title, ''))) = LOWER('{sql_escape(display_course_title.strip())}')")
        course_filter = "(" + " OR ".join(title_conditions) + ")"

    sql = f"""
        WITH
        {portal_ids_cte}
        -- ── Quiz names: schedule.resource_id → session_name ─────────────────
        quiz_names AS (
          SELECT
            CAST(s.resource_id AS STRING) AS quiz_id,
            ARRAY_AGG(
              NULLIF(TRIM(s.session_name), '')
              IGNORE NULLS ORDER BY LENGTH(s.session_name) LIMIT 1
            )[SAFE_OFFSET(0)] AS quiz_name
          FROM {refs["schedule"]} s
          WHERE {' AND '.join(sched_where)}
            AND s.resource_id IS NOT NULL
            AND TRIM(COALESCE(s.session_name, '')) != ''
          GROUP BY CAST(s.resource_id AS STRING)
        ),
        -- ── Course filter: content.unit_id → course_title / portal_course_id ─
        content AS (
          {content_cte}
        ),
        -- ── Roster: students per section ──────────────────────────────────────
        roster AS (
          SELECT
            u.institute_name,
            COALESCE(NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY u.institute_name, section
        ),
        -- ── Quiz attempts filtered to this course ─────────────────────────────
        -- Use LEFT JOIN so module/daily/course quizzes that have no entry in the
        -- content hierarchy table are not silently dropped.
        -- Matching logic (any one must be true):
        --   1. content row found AND content matches the course filter
        --   2. no content row (c.unit_id IS NULL) but quiz_id is scheduled for this
        --      institute/date window and is a non-classroom type
        quiz_filtered AS (
          SELECT
            CAST(q.quiz_id AS STRING)                                AS quiz_id,
            q.derived_unit_type                                      AS quiz_type,
            COALESCE(NULLIF(TRIM(q.section_name), ''), 'Unknown')   AS section,
            q.user_id,
            q.best_attempt_evaluation_result,
            SAFE_CAST(q.best_attempt_number AS FLOAT64)              AS best_attempt_number,
            SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64)    AS best_attempt_score
          FROM {refs["quiz_attempts"]} q
          LEFT JOIN content c ON CAST(q.quiz_id AS STRING) = c.unit_id
          WHERE {' AND '.join(where_clauses)}
            AND (
              -- Primary: quiz found in content and course matches
              (c.unit_id IS NOT NULL AND {course_filter})
              OR
              -- Fallback: quiz not in content (module/daily/course quiz) but
              -- is in the schedule for this institute + date window
              (c.unit_id IS NULL
               AND q.derived_unit_type IN ('MODULE_QUIZ', 'DAILY_QUIZ', 'COURSE_QUIZ')
               AND CAST(q.quiz_id AS STRING) IN (SELECT quiz_id FROM quiz_names))
            )
        )
        SELECT
          qf.quiz_id,
          COALESCE(
            MAX(qn.quiz_name),
            qf.quiz_id
          )                                                          AS quiz_name,
          qf.quiz_type,
          qf.section,
          COUNT(DISTINCT qf.user_id)                                 AS attempted,
          COUNT(DISTINCT CASE WHEN UPPER(TRIM(COALESCE(qf.best_attempt_evaluation_result,''))) LIKE '%PASS%'
                              THEN qf.user_id END)                   AS passed,
          COUNT(DISTINCT CASE WHEN UPPER(TRIM(COALESCE(qf.best_attempt_evaluation_result,''))) NOT LIKE '%PASS%'
                              THEN qf.user_id END)                   AS failed,
          ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN UPPER(TRIM(COALESCE(qf.best_attempt_evaluation_result,''))) LIKE '%PASS%'
                                THEN qf.user_id END),
            NULLIF(COUNT(DISTINCT qf.user_id), 0)
          ) * 100, 1)                                                AS pass_pct,
          MAX(r.total_students)                                      AS total_students,
          AVG(qf.best_attempt_number)                                AS avg_best_attempt_number,
          AVG(qf.best_attempt_score)                                 AS avg_best_attempt_score
        FROM quiz_filtered qf
        LEFT JOIN quiz_names qn ON qn.quiz_id = qf.quiz_id
        LEFT JOIN roster r
          ON r.institute_name = '{sql_escape(institute)}'
         AND r.section        = qf.section
        GROUP BY qf.quiz_id, qf.quiz_type, qf.section
        ORDER BY qf.quiz_type, MAX(COALESCE(qn.quiz_name, qf.quiz_id))
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_course_quiz_breakdown error: {e}")
        return pd.DataFrame(columns=["quiz_id", "quiz_name", "quiz_type", "section", "attempted", "passed", "failed", "pass_pct", "total_students", "avg_best_attempt_number", "avg_best_attempt_score"])


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
        sg_totals AS (
          -- Aggregate at institute level; SKILL and GRADED counted separately.
          -- Pass condition inlined to avoid BigQuery boolean-column evaluation quirks.
          SELECT
            sg.institute_name AS institute,
            COUNT(DISTINCT IF(sg.assessment_type = 'SKILL_ASSESSMENT',
              sg.assessment_id, NULL))                                                          AS skill_conducted,
            COUNT(DISTINCT IF(sg.assessment_type = 'SKILL_ASSESSMENT',
              sg.user_id, NULL))                                                                AS skill_attempted,
            COUNT(DISTINCT IF(sg.assessment_type = 'SKILL_ASSESSMENT'
              AND UPPER(TRIM(COALESCE(sg.section_evaluation_result, ''))) LIKE '%PASS%',
              sg.user_id, NULL))                                                                AS skill_passed,
            COUNT(DISTINCT IF(sg.assessment_type = 'GRADED_ASSESSMENT',
              sg.user_id, NULL))                                                                AS academic_attempted,
            COUNT(DISTINCT IF(sg.assessment_type = 'GRADED_ASSESSMENT'
              AND UPPER(TRIM(COALESCE(sg.section_evaluation_result, ''))) LIKE '%PASS%',
              sg.user_id, NULL))                                                                AS academic_passed
          FROM {refs["skill_graded"]} sg
          WHERE {' AND '.join(where_clauses)}
          GROUP BY sg.institute_name
        )
        SELECT
          st.institute,
          st.skill_conducted,
          -- Skill Assessment Participation %: unique users attempted / total enrolled
          ROUND(SAFE_DIVIDE(st.skill_attempted,    NULLIF(ir.total_students,    0)) * 100, 1) AS skill_participation_pct,
          -- Skill Assessment Pass %: passed / attempted (section_evaluation_result LIKE '%PASS%')
          ROUND(SAFE_DIVIDE(st.skill_passed,       NULLIF(st.skill_attempted,   0)) * 100, 1) AS skill_pass_pct,
          -- Academic Assessments Attempt %: unique users attempted / total enrolled
          ROUND(SAFE_DIVIDE(st.academic_attempted, NULLIF(ir.total_students,    0)) * 100, 1) AS academic_attempt_pct,
          -- Academic Assessments Pass %: passed / attempted
          ROUND(SAFE_DIVIDE(st.academic_passed,    NULLIF(st.academic_attempted, 0)) * 100, 1) AS academic_pass_pct
        FROM sg_totals st
        LEFT JOIN institute_roster ir ON ir.institute = st.institute
        ORDER BY st.institute
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_skill_graded_metrics error: {e}")
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
    Returns {normalized_key → sem_course_title} by joining content → portal_courses
    via portal_course_id so that content-level course titles map to the official
    semester subject names.

    Keys added per row (so any lookup form hits the right sem_course_title):
      • normalize_text(content.course_title)
      • normalize_text(normalize_course_name(content.course_title, semester))
      • normalize_text(sem_course_title)          ← direct match fallback
    """
    refs = get_table_refs()

    # Detect portal_course_id column in content and portal_courses tables
    content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
    portal_table_ref  = get_config("BQ_PORTAL_COURSES_TABLE", DEFAULT_PORTAL_COURSES_TABLE)
    content_cols = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
    portal_cols  = fetch_table_columns(portal_table_ref,  DEFAULT_PORTAL_COURSES_TABLE)
    content_cid_col = first_existing_column(content_cols, ["portal_course_id", "course_id"])
    portal_cid_col  = first_existing_column(portal_cols,  ["portal_course_id", "course_id"])
    # The portal_courses table uses "semester_title" (not "semester_name")
    portal_sem_col  = first_existing_column(portal_cols,  ["semester_title", "semester_name", "semester"])

    portal_where = ["TRIM(COALESCE(pc.sem_course_title, '')) != ''"]
    if should_apply_batch_filter(batch):
        portal_where.append(f"LOWER(COALESCE(pc.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")
    sem_num = ""
    if "1" in semester:
        sem_num = "1"
    elif "2" in semester:
        sem_num = "2"
    if sem_num and portal_sem_col:
        portal_where.append(f"LOWER(COALESCE(pc.{bq_column(portal_sem_col)}, '')) LIKE '%semester {sem_num}%'")

    result: dict[str, str] = {}

    # ── Primary path: join content → portal_courses via portal_course_id ─────
    if content_cid_col and portal_cid_col:
        sql = f"""
            SELECT DISTINCT
              TRIM(COALESCE(c.course_title, ''))            AS content_course_title,
              TRIM(pc.sem_course_title)                     AS sem_course_title,
              CAST(pc.{bq_column(portal_cid_col)} AS STRING) AS portal_course_id
            FROM {refs["content"]} c
            INNER JOIN {refs["portal_courses"]} pc
              ON CAST(c.{bq_column(content_cid_col)} AS STRING)
               = CAST(pc.{bq_column(portal_cid_col)} AS STRING)
            WHERE {' AND '.join(portal_where)}
              AND TRIM(COALESCE(c.course_title, '')) != ''
              AND TRIM(COALESCE(CAST(c.{bq_column(content_cid_col)} AS STRING), '')) != ''
        """
        try:
            df = run_query(sql)
            for _, row in df.iterrows():
                ct  = str(row.get("content_course_title") or "").strip()
                st_ = str(row.get("sem_course_title")     or "").strip()
                if not ct or not st_:
                    continue
                # key by raw content title
                result[normalize_text(ct)] = st_
                # key by alias-normalized content title (what _display_course receives)
                result[normalize_text(normalize_course_name(ct, semester))] = st_
                # key by sem_course_title itself (direct lookup fallback)
                result[normalize_text(st_)] = st_
        except Exception:
            pass

    # ── Fallback path: sem_course_title → sem_course_title (if join fails) ──
    if not result:
        sql_fb = f"""
            SELECT DISTINCT TRIM(pc.sem_course_title) AS sem_course_title
            FROM {refs["portal_courses"]} pc
            WHERE {' AND '.join(portal_where)}
            ORDER BY sem_course_title
        """
        try:
            df_fb = run_query(sql_fb)
            for title in df_fb["sem_course_title"].dropna().unique():
                title = str(title).strip()
                if title:
                    result[normalize_text(title)] = title
        except Exception:
            pass

    return result


@st.cache_data(ttl=600, show_spinner=False)
def fetch_portal_course_id_map(batch: str, semester: str) -> dict:
    """
    Returns two-way lookup dict for quiz pass fallback matching:
      {normalize_text(sem_course_title) → portal_course_id}
      {normalize_text(content_course_title) → portal_course_id}   (if join possible)

    Used when quiz data can't be found by title — match via portal_course_id instead.
    """
    refs = get_table_refs()
    portal_table_ref  = get_config("BQ_PORTAL_COURSES_TABLE", DEFAULT_PORTAL_COURSES_TABLE)
    content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
    portal_cols  = fetch_table_columns(portal_table_ref,  DEFAULT_PORTAL_COURSES_TABLE)
    content_cols = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
    portal_cid_col  = first_existing_column(portal_cols,  ["portal_course_id", "course_id"])
    content_cid_col = first_existing_column(content_cols, ["portal_course_id", "course_id"])
    portal_sem_col  = first_existing_column(portal_cols,  ["semester_title", "semester_name", "semester"])
    if not portal_cid_col:
        return {}

    portal_where = [
        "TRIM(COALESCE(pc.sem_course_title, '')) != ''",
        f"TRIM(COALESCE(CAST(pc.{bq_column(portal_cid_col)} AS STRING), '')) != ''",
    ]
    if should_apply_batch_filter(batch):
        portal_where.append(f"LOWER(COALESCE(pc.batch_name, '')) LIKE '%{sql_escape(batch.strip().lower())}%'")
    sem_num = ""
    if "1" in semester:
        sem_num = "1"
    elif "2" in semester:
        sem_num = "2"
    if sem_num and portal_sem_col:
        portal_where.append(f"LOWER(COALESCE(pc.{bq_column(portal_sem_col)}, '')) LIKE '%semester {sem_num}%'")

    result: dict[str, str] = {}

    # Include content course titles if the join is possible
    if content_cid_col:
        sql = f"""
            SELECT DISTINCT
              TRIM(pc.sem_course_title)                       AS sem_course_title,
              CAST(pc.{bq_column(portal_cid_col)} AS STRING) AS portal_course_id,
              TRIM(COALESCE(c.course_title, ''))              AS content_course_title
            FROM {refs["portal_courses"]} pc
            LEFT JOIN {refs["content"]} c
              ON CAST(c.{bq_column(content_cid_col)} AS STRING)
               = CAST(pc.{bq_column(portal_cid_col)} AS STRING)
            WHERE {' AND '.join(portal_where)}
        """
    else:
        sql = f"""
            SELECT DISTINCT
              TRIM(pc.sem_course_title)                       AS sem_course_title,
              CAST(pc.{bq_column(portal_cid_col)} AS STRING) AS portal_course_id,
              CAST(NULL AS STRING)                            AS content_course_title
            FROM {refs["portal_courses"]} pc
            WHERE {' AND '.join(portal_where)}
        """
    try:
        df = run_query(sql)
        for _, row in df.iterrows():
            st_ = str(row.get("sem_course_title")      or "").strip()
            pid = str(row.get("portal_course_id")       or "").strip()
            ct  = str(row.get("content_course_title")   or "").strip()
            if not pid:
                continue
            if st_:
                result[normalize_text(st_)] = pid
            if ct:
                result[normalize_text(ct)] = pid
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


def build_university_metrics(data_df: pd.DataFrame, assessment_df: pd.DataFrame, institute: str, section: str, semester: str, sem_course_titles: dict | None = None, quiz_pass_pct: float | None = None):
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
                "Classroom Quiz Pass %": round(quiz_pass_pct, 1) if quiz_pass_pct is not None else None,
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


def _pct_class(value, green_threshold=75, orange_threshold=50):
    """Returns CSS class name based on percentage value."""
    if value is None:
        return "pct-orange"
    if value >= green_threshold:
        return "pct-green"
    if value >= orange_threshold:
        return "pct-orange"
    return "pct-red"


def _bar_class(value, green_threshold=75, orange_threshold=50):
    if value is None:
        return "bar-orange"
    if value >= green_threshold:
        return "bar-green"
    if value >= orange_threshold:
        return "bar-orange"
    return "bar-red"


def render_course_matrix(course_rows: list[dict], selected_course: str | None) -> str | None:
    """
    Renders the course matrix as styled HTML card rows.
    Each row has a Streamlit button (›) to open course detail.
    Returns the clicked course name or None.
    """
    st.markdown("<div class='course-matrix-header'>Course Matrix</div>", unsafe_allow_html=True)
    st.markdown("<div class='course-matrix-sub'>adherence vs. content engagement</div>", unsafe_allow_html=True)

    # ── Course selector at top for quick navigation ────────────────────────────
    course_names = [r["course"] for r in course_rows]
    sel = st.selectbox(
        "Jump to course:",
        options=course_names,
        index=None,
        placeholder="Select a course to open detail view…",
        key="cm_course_select",
    )
    if sel:
        return sel

    def _safe(v):
        try:
            return None if (v is None or pd.isna(v)) else float(v)
        except (TypeError, ValueError):
            return None

    def _pct_html(val, bar_color="var(--bar-color, #0f172a)"):
        if val is None:
            return '<span style="color:#94a3b8">—</span>', ""
        cls = _pct_class(val)
        bar_w = min(int(val), 100)
        bar_cls = _bar_class(val)
        return (
            f'<span class="cm-pct-val {cls}">{val:.1f}%</span>',
            f'<div class="cm-bar-track"><div class="cm-bar-fill {bar_cls}" style="width:{bar_w}%"></div></div>',
        )

    # Build entire table HTML in one block (avoids inter-element Streamlit spacing)
    rows_html = ""
    for i, row in enumerate(course_rows):
        adh      = _safe(row.get("adherence_pct"))
        comp     = _safe(row.get("completion_pct"))
        quiz     = _safe(row.get("quiz_pass_pct"))
        skill    = _safe(row.get("skill_pct"))
        lec_sl   = _safe(row.get("lecture_slots"))
        prac_sl  = _safe(row.get("practice_slots"))
        exam_sl  = _safe(row.get("exam_slots"))
        tot_sl   = _safe(row.get("total_slots"))
        lec_pct  = _safe(row.get("lecture_pct"))
        prac_pct = _safe(row.get("practice_pct"))
        exam_pct = _safe(row.get("exam_pct"))
        course = escape_html(row.get("course", ""))
        num    = f"{i+1:02d}"

        def _td_pct(val):
            if val is None:
                return '<td style="padding:12px 10px;width:130px"><span style="color:#94a3b8">—</span></td>'
            cls  = _pct_class(val)
            bcls = _bar_class(val)
            bw   = min(int(val), 100)
            return (
                f'<td style="padding:12px 10px;width:130px">'
                f'<span class="{cls}" style="font-weight:700;font-size:0.91rem">{val:.1f}%</span>'
                f'<div style="height:4px;background:#e2e8f0;border-radius:999px;margin-top:4px;overflow:hidden">'
                f'<div class="{bcls}" style="height:4px;border-radius:999px;width:{bw}%"></div></div>'
                f'</td>'
            )

        def _td_simple(val):
            if val is None:
                return '<td style="padding:12px 10px;width:80px"><span style="color:#94a3b8">—</span></td>'
            cls = _pct_class(val)
            return f'<td style="padding:12px 10px;width:80px"><span class="{cls}" style="font-weight:700">{val:.1f}%</span></td>'

        def _td_slot(val):
            if val is None:
                return '<td style="padding:12px 10px;width:70px;text-align:right"><span style="color:#94a3b8">—</span></td>'
            display = int(val) if val == int(val) else f"{val:.1f}"
            return f'<td style="padding:12px 10px;width:70px;text-align:right;font-weight:600;color:#334155">{display}</td>'

        rows_html += (
            f'<tr style="border-bottom:1px solid #f1f5f9">'
            f'<td style="padding:12px 6px 12px 16px;color:#94a3b8;font-size:0.82rem;width:36px">{num}</td>'
            f'<td style="padding:12px 10px;font-weight:600;color:#0f172a">{course}</td>'
            + _td_slot(lec_sl)
            + _td_slot(prac_sl)
            + _td_slot(exam_sl)
            + _td_slot(tot_sl)
            + _td_simple(lec_pct)
            + _td_simple(prac_pct)
            + _td_simple(exam_pct)
            + _td_pct(adh)
            + _td_pct(comp)
            + _td_simple(quiz)
            + _td_simple(skill)
            + f'</tr>'
        )

    table_html = (
        '<div style="overflow-x:auto;width:100%">'
        '<table style="width:100%;min-width:900px;border-collapse:collapse;background:#fff;'
        'border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.07);font-size:0.92rem">'
        '<thead><tr style="background:#f8fafc;border-bottom:1px solid #e2e8f0">'
        '<th style="padding:11px 6px 11px 16px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">#</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">Course</th>'
        '<th style="padding:11px 10px;text-align:right;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Lec Slots</th>'
        '<th style="padding:11px 10px;text-align:right;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Prac Slots</th>'
        '<th style="padding:11px 10px;text-align:right;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Exam Slots</th>'
        '<th style="padding:11px 10px;text-align:right;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Total Slots</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Lecture %</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Practice %</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Exam %</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Adherence</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Completion</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Quiz Pass</th>'
        '<th style="padding:11px 10px;text-align:left;font-size:0.78rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap">Skill %</th>'
        f'</tr></thead><tbody>{rows_html}</tbody></table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    return None


def render_course_detail_header(course_name: str, delivery_row: dict | None, units_df: pd.DataFrame, quiz_pass_pct: float | None):
    """Renders the course title, subtitle, and stats bar."""
    delivered_total = int(delivery_row["total_delivered"]) if delivery_row and delivery_row.get("total_delivered") is not None else "—"
    planned_total   = int(delivery_row["total_planned"])   if delivery_row and delivery_row.get("total_planned")   is not None else "—"
    adherence_pct   = delivery_row["adherence_pct"]        if delivery_row else None

    # Unit counts from units_df (fetch_course_session_units)
    # Each unit appears once per section — deduplicate by unit name for totals
    if units_df is not None and not units_df.empty and "session_type" in units_df.columns:
        udf = units_df.copy()
        udf["_stype"] = udf["session_type"].str.upper()
        # Total distinct unit names per type
        lec_total  = udf[udf["_stype"] == "LECTURE"]["unit"].nunique()
        prac_total = udf[udf["_stype"] == "PRACTICE"]["unit"].nunique()
        exam_total = udf[udf["_stype"].isin(["EXAM", "QUIZ"])]["unit"].nunique()
        # Delivered: units where delivered_sessions > 0 in at least one section
        if "delivered_sessions" in udf.columns:
            delivered_mask = udf["delivered_sessions"].fillna(0) > 0
            lec_done  = udf[(udf["_stype"] == "LECTURE")  & delivered_mask]["unit"].nunique()
            prac_done = udf[(udf["_stype"] == "PRACTICE") & delivered_mask]["unit"].nunique()
            exam_done = udf[udf["_stype"].isin(["EXAM", "QUIZ"]) & delivered_mask]["unit"].nunique()
        else:
            lec_done = prac_done = exam_done = 0
    else:
        lec_total = prac_total = exam_total = 0
        lec_done  = prac_done = exam_done  = 0

    def _unit_stat(done: int, total: int) -> tuple[str, str]:
        """Returns (value_str, sub_str) for a unit stat cell."""
        if total == 0:
            return "—", "no units"
        return f"{done}/{total}", "delivered"

    lec_val,  lec_sub  = _unit_stat(lec_done,  lec_total)
    prac_val, prac_sub = _unit_stat(prac_done, prac_total)
    exam_val, exam_sub = _unit_stat(exam_done, exam_total)

    quiz_accent = "accent-orange" if quiz_pass_pct is not None and quiz_pass_pct < 75 else "accent-green"
    quiz_display = f"{quiz_pass_pct:.1f}" if quiz_pass_pct is not None else "—"
    adh_sub = f"{adherence_pct:.1f}% adherence" if adherence_pct is not None else ""

    st.markdown(
        f"""
        <div class='cd-header-wrap'>
          <span class='cd-title'>{escape_html(course_name)}</span>
        </div>
        <div class='cd-subtitle'>{escape_html(str(delivered_total))}/{escape_html(str(planned_total))} sessions delivered</div>
        <div class='cd-stats-bar'>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>Sessions Planned</div>
            <div class='cd-stat-value'>{escape_html(str(planned_total))}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>Sessions Delivered</div>
            <div class='cd-stat-value'>{escape_html(str(delivered_total))}</div>
            <div class='cd-stat-sub'>{escape_html(adh_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>Lecture Units</div>
            <div class='cd-stat-value'>{escape_html(lec_val)}</div>
            <div class='cd-stat-sub'>{escape_html(lec_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>Practice Units</div>
            <div class='cd-stat-value'>{escape_html(prac_val)}</div>
            <div class='cd-stat-sub'>{escape_html(prac_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>Exam Units</div>
            <div class='cd-stat-value'>{escape_html(exam_val)}</div>
            <div class='cd-stat-sub'>{escape_html(exam_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>Quiz Pass Rate</div>
            <div class='cd-stat-value {quiz_accent}'>{escape_html(quiz_display)}<span style='font-size:1rem;font-weight:500'> %</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tab_schedule_adherence(weekly_df: pd.DataFrame):
    """Renders week-wise delivery bar chart and adherence trend."""
    if weekly_df.empty:
        st.info("No week-wise delivery data available for this course.")
        return
    weekly_df = weekly_df.copy()
    weekly_df["week_label"] = weekly_df.get("week_label", weekly_df.get("week_start", range(len(weekly_df))).astype(str))

    col1, col2 = st.columns([1.6, 1], gap="medium")
    with col1:
        st.markdown("**Week-wise delivery**")
        chart_df = weekly_df.set_index("week_label")[["planned", "delivered"]].rename(
            columns={"planned": "Planned", "delivered": "Delivered"}
        )
        st.bar_chart(chart_df, color=["#cbd5e1", "#0d9488"], use_container_width=True)
    with col2:
        st.markdown("**Adherence trend**")
        if "adherence_pct" in weekly_df.columns:
            trend_df = weekly_df.set_index("week_label")[["adherence_pct"]].rename(
                columns={"adherence_pct": "Adherence %"}
            )
            st.line_chart(trend_df, color=["#0d9488"], use_container_width=True)
        else:
            st.info("Adherence trend not available.")


def render_tab_lecture_practice_exam(units_df: pd.DataFrame, sections: list[str]):
    """
    Renders unit-by-unit completion as card rows (Image #10 style).
    Section filter uses pill buttons top-right.
    When 'All' is selected, student counts are summed across sections.
    """
    if units_df.empty:
        st.info("No unit-level data available for this course.")
        return

    all_sections = sorted(units_df["section"].unique().tolist()) if "section" in units_df.columns else []
    section_options = ["All"] + all_sections

    # ── Section filter pill state ───────────────────────────────────────────────
    if "lpe_sec" not in st.session_state or st.session_state["lpe_sec"] not in section_options:
        st.session_state["lpe_sec"] = "All"
    cur_sec = st.session_state["lpe_sec"]

    # Compute total students for subtitle
    has_students = "total_students" in units_df.columns
    if has_students and cur_sec == "All":
        # Sum across sections: one row per (unit, section) → sum for all units in All view
        sec_students = units_df.groupby("section")["total_students"].max().sum()
        total_students_display = int(sec_students) if sec_students and not pd.isna(sec_students) else None
    elif has_students and cur_sec != "All":
        sec_df = units_df[units_df["section"] == cur_sec]
        ts_val = sec_df["total_students"].max() if not sec_df.empty else None
        total_students_display = int(ts_val) if ts_val and not pd.isna(ts_val) else None
    else:
        total_students_display = None

    # ── Header row: title left, section pills right ─────────────────────────────
    hcol_left, hcol_right = st.columns([2, 3])
    with hcol_left:
        sec_label = "All Sections" if cur_sec == "All" else cur_sec
        stu_label = f" · {total_students_display} students" if total_students_display else ""
        st.markdown(
            f"<div style='font-weight:700;font-size:1.05rem;margin-bottom:2px'>Unit-by-unit completion</div>"
            f"<div style='font-size:0.84rem;color:#64748b'>{escape_html(sec_label + stu_label)}</div>",
            unsafe_allow_html=True,
        )
    with hcol_right:
        pill_cols = st.columns(len(section_options))
        for j, sec in enumerate(section_options):
            with pill_cols[j]:
                is_active = (sec == cur_sec)
                btn_style = (
                    "background:#0f172a;color:#fff;border:1px solid #0f172a;" if is_active
                    else "background:#f1f5f9;color:#334155;border:1px solid #e2e8f0;"
                )
                st.markdown(
                    f"<style>div[data-testid='stButton'] #pill_{j}_{sec} button"
                    f"{{border-radius:999px;padding:4px 12px;font-size:0.82rem;font-weight:600;"
                    f"min-height:30px;{btn_style}}}</style>",
                    unsafe_allow_html=True,
                )
                if st.button(sec, key=f"lpe_pill_{sec}_{j}", use_container_width=True):
                    st.session_state["lpe_sec"] = sec
                    st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Filter / aggregate ──────────────────────────────────────────────────────
    filtered = units_df if cur_sec == "All" else units_df[units_df["section"] == cur_sec]

    if cur_sec == "All":
        agg_cols = {
            "total_sessions":     ("total_sessions",     "max"),   # curriculum-level, same across sections
            "delivered_sessions": ("delivered_sessions", "max"),
        }
        if "students_completed" in filtered.columns:
            agg_cols["students_completed"] = ("students_completed", "sum")   # sum across sections
        if "total_students" in filtered.columns:
            agg_cols["total_students"] = ("total_students", "sum")           # sum across sections
        filtered = filtered.groupby(["unit", "session_type"], as_index=False).agg(**agg_cols)
        filtered["completion_pct"] = (
            filtered["delivered_sessions"] / filtered["total_sessions"].replace(0, float("nan")) * 100
        ).round(1)
        # Fix: when All sections is selected, every row's denominator should be
        # the total university enrollment — not just the sections that happen to
        # have that unit in the session_adherence table.
        if total_students_display and "total_students" in filtered.columns:
            filtered["total_students"] = total_students_display

    type_order = {"LECTURE": 0, "PRACTICE": 1, "EXAM": 2, "QUIZ": 3}
    filtered = filtered.copy()
    filtered["_sort"] = filtered["session_type"].map(lambda t: type_order.get(str(t).upper(), 9))
    filtered = filtered.sort_values(["_sort", "unit"]).reset_index(drop=True)

    has_students = "students_completed" in filtered.columns and "total_students" in filtered.columns

    # Badge inline styles (avoids class nesting issues in Streamlit markdown)
    badge_style_map = {
        "LECTURE":  ("background:#f1f5f9;color:#475569",  "LECTURE"),
        "PRACTICE": ("background:#ccfbf1;color:#065f46",  "PRACTICE"),
        "EXAM":     ("background:#fee2e2;color:#991b1b",  "EXAM"),
        "QUIZ":     ("background:#fef9c3;color:#854d0e",  "QUIZ"),
    }

    # ── Build rows using <table> so Streamlit renders reliably ─────────────────
    rows_html = ""
    for i, row in filtered.iterrows():
        num       = f"{i+1:02d}"
        unit_name = escape_html(str(row.get("unit", "")))
        stype     = str(row.get("session_type", "")).upper()
        bstyle, blbl = badge_style_map.get(stype, ("background:#f1f5f9;color:#475569", stype))

        pct = row.get("completion_pct")
        try:
            pct = None if (pct is None or pd.isna(pct)) else float(pct)
        except (TypeError, ValueError):
            pct = None
        pct_cls = _pct_class(pct)
        bar_cls = _bar_class(pct)
        bar_w   = min(int(pct or 0), 100)
        pct_str = f"{pct:.1f}%" if pct is not None else "—"

        # Student counts
        sc = row.get("students_completed") if has_students else None
        tot = row.get("total_students") if has_students else None
        try:
            sc  = None if (sc  is None or pd.isna(sc))  else int(sc)
            tot = None if (tot is None or pd.isna(tot)) else int(tot)
        except (TypeError, ValueError):
            sc = tot = None

        if sc is not None and tot is not None:
            if cur_sec != "All":
                pending = max(0, tot - sc)
                pending_html = f' <span style="color:#ef4444;font-size:0.79rem">&middot; {pending} pending</span>' if pending > 0 else ""
            else:
                pending_html = ""
            stu_html = f'<b style="color:#0f172a">{sc}</b> <span style="color:#94a3b8">of {tot}</span>{pending_html}'
        elif tot is not None:
            stu_html = f'<span style="color:#64748b">{tot} students</span>'
        else:
            stu_html = '<span style="color:#94a3b8">—</span>'

        rows_html += f"""<tr>
          <td style="color:#94a3b8;font-size:0.82rem;padding:12px 6px 12px 16px;width:36px">{num}</td>
          <td style="font-weight:600;color:#0f172a;padding:12px 8px">{unit_name}</td>
          <td style="padding:12px 8px;width:100px"><span style="display:inline-block;padding:3px 10px;border-radius:6px;font-size:0.74rem;font-weight:700;{bstyle}">{blbl}</span></td>
          <td style="padding:12px 8px;font-size:0.85rem;white-space:nowrap;width:200px">{stu_html}</td>
          <td style="padding:12px 8px;font-weight:700;font-size:0.93rem;width:70px"><span class="{pct_cls}">{escape_html(pct_str)}</span></td>
          <td style="padding:12px 16px 12px 8px;width:130px">
            <div style="height:4px;background:#e2e8f0;border-radius:999px;width:110px;overflow:hidden">
              <div class="{bar_cls}" style="height:4px;border-radius:999px;width:{bar_w}%"></div>
            </div>
          </td>
        </tr>"""

    table_html = f"""<div style="overflow-x:auto;width:100%">
    <table style="width:100%;min-width:550px;border-collapse:collapse;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(15,23,42,0.06);font-size:0.9rem">
      <thead>
        <tr style="background:#f8fafc;border-bottom:1px solid #e2e8f0">
          <th style="padding:10px 6px 10px 16px;text-align:left;font-size:0.76rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">#</th>
          <th style="padding:10px 8px;text-align:left;font-size:0.76rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">Unit</th>
          <th style="padding:10px 8px;text-align:left;font-size:0.76rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">Type</th>
          <th style="padding:10px 8px;text-align:left;font-size:0.76rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">Students</th>
          <th style="padding:10px 8px;text-align:left;font-size:0.76rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">% Rate</th>
          <th style="padding:10px 16px 10px 8px;text-align:left;font-size:0.76rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em">Progress</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table></div>"""
    st.markdown(table_html, unsafe_allow_html=True)


def render_tab_quizzes(quiz_df: pd.DataFrame, quiz_metrics: dict, course_name: str, sections: list[str]):
    """Renders the quiz attempt funnel and per-quiz card rows (Image #13 style)."""
    # ── Section filter pills ───────────────────────────────────────────────────
    all_secs = sorted(quiz_df["section"].unique().tolist()) if not quiz_df.empty and "section" in quiz_df.columns else []
    section_options = ["All"] + all_secs

    if "quiz_sec" not in st.session_state or st.session_state["quiz_sec"] not in section_options:
        st.session_state["quiz_sec"] = "All"
    sel_sec = st.session_state["quiz_sec"]

    # Pills row
    pill_cols = st.columns(len(section_options))
    for j, sec in enumerate(section_options):
        with pill_cols[j]:
            is_active = (sec == sel_sec)
            if st.button(
                sec,
                key=f"qz_pill_{sec}_{j}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["quiz_sec"] = sec
                st.rerun()

    # ── Quiz type filter ───────────────────────────────────────────────────────
    _TYPE_LABELS = {
        "All Types":      None,
        "Classroom Quiz": "CLASSROOM_QUIZ",
        "Module Quiz":    "MODULE_QUIZ",
        "Course Quiz":    "COURSE_QUIZ",
        "Daily Quiz":     "DAILY_QUIZ",
    }
    # Only show types that actually exist in the data
    if not quiz_df.empty and "quiz_type" in quiz_df.columns:
        present_types = set(quiz_df["quiz_type"].dropna().str.upper().unique())
        _type_options = ["All Types"] + [
            label for label, val in _TYPE_LABELS.items()
            if val is not None and val in present_types
        ]
    else:
        _type_options = ["All Types"]

    if "quiz_type_filter" not in st.session_state or st.session_state["quiz_type_filter"] not in _type_options:
        st.session_state["quiz_type_filter"] = "All Types"

    type_filter_col, _ = st.columns([0.35, 0.65])
    with type_filter_col:
        sel_type_label = st.selectbox(
            "Quiz type",
            options=_type_options,
            key="quiz_type_filter",
            label_visibility="collapsed",
        )
    sel_type_val = _TYPE_LABELS.get(sel_type_label)

    scoped = quiz_df if quiz_df.empty or sel_sec == "All" else quiz_df[quiz_df["section"] == sel_sec]
    if sel_type_val is not None and not scoped.empty and "quiz_type" in scoped.columns:
        scoped = scoped[scoped["quiz_type"].str.upper() == sel_type_val]

    # ── Funnel summary ─────────────────────────────────────────────────────────
    if not scoped.empty:
        # total_students: sum of per-section max to avoid double-counting
        if "total_students" in scoped.columns and "section" in scoped.columns:
            total_students = int(scoped.groupby("section")["total_students"].max().sum() or 0)
        elif "total_students" in scoped.columns:
            total_students = int(scoped["total_students"].max() or 0)
        else:
            total_students = 0
        total_attempted = int(scoped.groupby("quiz_id")["attempted"].max().sum())
        total_passed    = int(scoped.groupby("quiz_id")["passed"].max().sum())
        total_failed    = int(scoped.groupby("quiz_id")["failed"].max().sum())
        not_attempted   = max(0, total_students - total_attempted) if total_students else None
        quiz_count      = scoped["quiz_id"].nunique()
        # Avg best attempt score
        avg_score: float | None = None
        if "avg_best_attempt_score" in scoped.columns:
            v = scoped["avg_best_attempt_score"].mean()
            try:
                avg_score = None if pd.isna(v) else round(float(v), 1)
            except (TypeError, ValueError):
                avg_score = None
        pass_of_enrolled_pct = round(total_passed / total_students * 100, 1) if total_students else None
    else:
        total_students = total_attempted = total_passed = total_failed = quiz_count = 0
        not_attempted = avg_score = pass_of_enrolled_pct = None

    drop_off_pct = (
        round(not_attempted / total_students * 100, 1)
        if not_attempted is not None and total_students
        else None
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.3, 1], gap="medium")
    with col1:
        not_att_str  = f"{not_attempted:,}" if not_attempted is not None else "—"
        drop_str     = f"<div style='font-size:0.8rem;color:#94a3b8'>{drop_off_pct:.1f}% drop-off</div>" if drop_off_pct is not None else ""
        enrolled_str = f"{total_students:,}" if total_students else "—"
        st.markdown(
            f"""
            <div style='background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:22px 24px;margin-bottom:12px'>
              <div style='font-weight:700;font-size:1rem;margin-bottom:4px'>Quiz attempt funnel</div>
              <div style='font-size:0.82rem;color:#64748b;margin-bottom:16px'>{escape_html(course_name)} · {'All sections' if sel_sec == 'All' else escape_html(sel_sec)} · {escape_html(sel_type_label)}</div>
              <div class='quiz-funnel-grid'>
                <div class='quiz-funnel-item'>
                  <div class='quiz-funnel-label'>Enrolled Students</div>
                  <div class='quiz-funnel-value'>{enrolled_str}</div>
                </div>
                <div class='quiz-funnel-item'>
                  <div class='quiz-funnel-label'>Not Attempted</div>
                  <div class='quiz-funnel-value red'>{not_att_str}</div>
                  {drop_str}
                </div>
                <div class='quiz-funnel-item'>
                  <div class='quiz-funnel-label'>Quizzes Passed</div>
                  <div class='quiz-funnel-value green'>{total_passed:,}</div>
                </div>
                <div class='quiz-funnel-item'>
                  <div class='quiz-funnel-label'>Quizzes Failed</div>
                  <div class='quiz-funnel-value orange'>{total_failed:,}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        score_str = f"{avg_score:.1f}" if avg_score is not None else "—"
        badge_html = (
            f"<div style='display:inline-block;background:#d1fae5;color:#065f46;border-radius:999px;"
            f"padding:5px 14px;font-size:0.84rem;font-weight:600;margin-top:12px'>"
            f"{pass_of_enrolled_pct:.1f}% of enrolled passed</div>"
            if pass_of_enrolled_pct is not None else ""
        )
        st.markdown(
            f"""
            <div style='background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:22px 24px;text-align:center;margin-bottom:12px'>
              <div style='font-weight:700;font-size:0.9rem;color:#64748b;margin-bottom:8px'>Avg Best Attempt</div>
              <div style='font-size:3.2rem;font-weight:800;color:#0d9488;line-height:1'>
                {escape_html(score_str)}<span style='font-size:1.3rem'>%</span>
              </div>
              <div style='font-size:0.82rem;color:#94a3b8;margin-top:6px'>across {total_attempted:,} attempts</div>
              {badge_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if scoped.empty:
        st.info("No quiz data found for this course.")
        return

    # ── Aggregate for display ──────────────────────────────────────────────────
    if sel_sec == "All":
        agg_kwargs: dict = dict(
            attempted=("attempted", "sum"),
            passed=("passed", "sum"),
            failed=("failed", "sum"),
            total_students=("total_students", "max"),
        )
        if "avg_best_attempt_number" in scoped.columns:
            agg_kwargs["avg_best_attempt_number"] = ("avg_best_attempt_number", "mean")
        if "avg_best_attempt_score" in scoped.columns:
            agg_kwargs["avg_best_attempt_score"] = ("avg_best_attempt_score", "mean")
        agg = scoped.groupby(["quiz_id", "quiz_name", "quiz_type"], as_index=False).agg(**agg_kwargs)
        agg["pass_pct"] = (agg["passed"] / agg["attempted"].replace(0, float("nan")) * 100).round(1)
    else:
        agg = scoped.copy()

    agg = agg.sort_values(["quiz_type", "quiz_name"]).reset_index(drop=True)

    # Type badge inline styles
    type_badge_style = {
        "CLASSROOM_QUIZ": ("background:#fef3c7;color:#92400e", "CLASSROOM_QUIZ"),
        "MODULE_QUIZ":    ("background:#dbeafe;color:#1e40af", "MODULE_QUIZ"),
        "DAILY_QUIZ":     ("background:#d1fae5;color:#065f46", "DAILY_QUIZ"),
        "COURSE_QUIZ":    ("background:#ede9fe;color:#5b21b6", "COURSE_QUIZ"),
    }

    has_score   = "avg_best_attempt_score"  in agg.columns
    has_att_num = "avg_best_attempt_number" in agg.columns
    has_topic   = "topic_title" in agg.columns
    has_quiz_no = "quiz_no"     in agg.columns

    type_suffix = f" · {escape_html(sel_type_label)}" if sel_type_label != "All Types" else ""
    st.markdown(
        f"<div style='font-weight:700;font-size:1rem;margin:14px 0 4px'>"
        f"{escape_html(course_name)} &middot; {quiz_count} quizzes</div>"
        f"<div style='font-size:0.82rem;color:#64748b;margin-bottom:10px'>"
        f"{'all sections' if sel_sec == 'All' else escape_html(sel_sec)}{type_suffix}</div>",
        unsafe_allow_html=True,
    )

    # ── Build table rows ───────────────────────────────────────────────────────
    rows_html = ""
    for idx, row in agg.iterrows():
        qname  = escape_html(str(row.get("quiz_name", row.get("quiz_id", ""))))
        qtype  = str(row.get("quiz_type", "")).upper()
        bstyle, blbl = type_badge_style.get(qtype, ("background:#f1f5f9;color:#475569", qtype))
        att = int(row.get("attempted", 0) or 0)
        pas = int(row.get("passed",    0) or 0)
        pct = row.get("pass_pct")
        try:
            pct = None if (pct is None or pd.isna(pct)) else float(pct)
        except (TypeError, ValueError):
            pct = None
        pct_str = f"{pct:.1f}%" if pct is not None else "—"
        pct_cls = _pct_class(pct)

        def _num_cell(col_name, fmt=None, color="#334155"):
            v = row.get(col_name)
            try:
                v = None if (v is None or pd.isna(v)) else float(v)
            except (TypeError, ValueError):
                v = None
            s = (fmt.format(v) if fmt and v is not None else (f"{v:.1f}" if v is not None else "—"))
            return f'<td style="padding:11px 10px;color:{color};font-size:0.87rem">{s}</td>'

        topic_cells = ""
        if has_topic:
            tt = escape_html(str(row.get("topic_title") or "—"))
            topic_cells = f'<td style="padding:11px 10px;color:#64748b;font-size:0.85rem">{tt}</td>'

        quiz_no_cell = ""
        if has_quiz_no:
            qno = row.get("quiz_no")
            qno_str = str(int(qno)) if qno is not None and not pd.isna(qno) else "—"
            quiz_no_cell = f'<td style="padding:11px 10px;color:#94a3b8;font-size:0.82rem;text-align:center">{qno_str}</td>'

        att_num_cell = _num_cell("avg_best_attempt_number") if has_att_num else ""
        score_cell   = _num_cell("avg_best_attempt_score", fmt="{:.1f}%", color="#0d9488") if has_score else ""

        rows_html += (
            f'<tr style="border-bottom:1px solid #f1f5f9">'
            f'<td style="padding:11px 6px 11px 16px;color:#94a3b8;font-size:0.8rem;width:32px">{idx+1:02d}</td>'
            + topic_cells
            + quiz_no_cell
            + f'<td style="padding:11px 10px;font-weight:600;color:#0f172a">{qname}</td>'
            f'<td style="padding:11px 10px"><span style="display:inline-block;padding:3px 9px;border-radius:6px;font-size:0.73rem;font-weight:700;{bstyle}">{blbl}</span></td>'
            f'<td style="padding:11px 10px;color:#334155;font-size:0.87rem">{att:,}</td>'
            f'<td style="padding:11px 10px;font-weight:600;color:#16a34a;font-size:0.87rem">{pas:,}</td>'
            + att_num_cell
            + score_cell
            + f'<td style="padding:11px 10px;font-weight:700"><span class="{pct_cls}">{pct_str}</span></td>'
            f'<td style="padding:11px 10px 11px 4px;color:#cbd5e1;text-align:right">›</td>'
            f'</tr>'
        )

    topic_th   = '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;text-align:left">Topic</th>' if has_topic else ""
    quiz_no_th = '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;text-align:center">Q#</th>' if has_quiz_no else ""
    att_num_th = '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Avg Attempts</th>' if has_att_num else ""
    score_th   = '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Avg Score</th>' if has_score else ""

    th_base = (
        '<th style="padding:10px 6px 10px 16px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">#</th>'
        + topic_th + quiz_no_th
        + '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Quiz Title</th>'
        '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Type</th>'
        '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Attempted</th>'
        '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Passed</th>'
        + att_num_th + score_th
        + '<th style="padding:10px 10px;color:#94a3b8;font-size:0.76rem;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">Pass %</th>'
        '<th style="padding:10px 10px;width:20px"></th>'
    )

    table_html = (
        '<div style="overflow-x:auto">'
        '<table style="width:100%;min-width:700px;border-collapse:collapse;background:#fff;'
        'border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(15,23,42,0.05);font-size:0.9rem">'
        f'<thead><tr style="background:#f8fafc;border-bottom:1px solid #e2e8f0">{th_base}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_tab_assessments(assessment_df: pd.DataFrame, course_name: str, sections: list[str]):
    """Renders assessment list and section-level performance for a course."""
    if assessment_df.empty:
        st.info("No assessment data available for this course.")
        return

    # Assessment summary table
    st.markdown("**Skill & Graded Assessments**")
    summary_rows = (
        assessment_df.groupby(["assessment_type"], as_index=False)
        .agg(
            assessed_sections=("section", "nunique"),
            avg_participation=("avg_participation", "mean"),
            avg_score=("avg_score", "mean"),
        )
    )
    for _, row in summary_rows.iterrows():
        atype = row["assessment_type"]
        badge_cls = "badge-practice" if "Skill" in atype else "badge-exam"
        st.markdown(
            f"<span class='unit-type-badge {badge_cls}' style='margin-right:8px'>{escape_html(atype)}</span>"
            f"Avg participation: <strong>{row['avg_participation']:.0f}</strong> &nbsp;|&nbsp; "
            f"Avg score: <strong>{row['avg_score']*100:.1f}%</strong>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Per-section, per-assessment-type breakdown
    st.markdown("**Section-level breakdown**")
    assessment_filter_options = ["All", "Skill only", "Graded only"]
    af_col, _ = st.columns([1, 2])
    with af_col:
        afilter = st.radio("Assessment filter", assessment_filter_options, horizontal=True, key="cd_assessment_filter", label_visibility="collapsed")

    scoped = assessment_df.copy()
    if afilter == "Skill only":
        scoped = scoped[scoped["assessment_type"] == "Skill Assessment"]
    elif afilter == "Graded only":
        scoped = scoped[scoped["assessment_type"] != "Skill Assessment"]

    if scoped.empty:
        st.info("No assessments match the selected filter.")
        return

    section_summary = (
        scoped.groupby("section", as_index=False)
        .agg(
            skill_avg=("avg_score", lambda x: x[scoped.loc[x.index, "assessment_type"] == "Skill Assessment"].mean() if (scoped.loc[x.index, "assessment_type"] == "Skill Assessment").any() else None),
            graded_avg=("avg_score", lambda x: x[scoped.loc[x.index, "assessment_type"] != "Skill Assessment"].mean() if (scoped.loc[x.index, "assessment_type"] != "Skill Assessment").any() else None),
            overall_avg=("avg_score", "mean"),
            students=("avg_participation", "mean"),
        )
    )

    rows_html = ""
    for i, row in section_summary.iterrows():
        def fmt(v): return f"{v*100:.1f}%" if v is not None and not pd.isna(v) else "—"
        overall_val = row["overall_avg"] * 100 if row["overall_avg"] is not None and not pd.isna(row["overall_avg"]) else None
        bar_w = min(int(overall_val or 0), 100)
        bar_cls = _bar_class(overall_val)
        rows_html += f"""
        <tr>
          <td class="cm-row-num">{i+1:02d}</td>
          <td><span style='background:#f1f5f9;border-radius:6px;padding:2px 8px;font-weight:600;font-size:0.85rem'>{escape_html(str(row['section']))}</span></td>
          <td>{fmt(row['skill_avg'])}</td>
          <td>{fmt(row['graded_avg'])}</td>
          <td><span class="cm-pct-val {_pct_class(overall_val)}">{fmt(row['overall_avg'])}</span></td>
          <td><div class="cm-bar-track" style="width:120px"><div class="cm-bar-fill {bar_cls}" style="width:{bar_w}%"></div></div></td>
        </tr>"""

    st.markdown(
        f"""<table class="unit-table">
          <thead><tr><th>#</th><th>Section</th><th>Skill Avg</th><th>Graded Avg</th><th>Overall %</th><th>Performance</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""",
        unsafe_allow_html=True,
    )


def render_tab_sections(semester_course_df: pd.DataFrame):
    """Renders per-section delivery breakdown for the selected course."""
    if semester_course_df.empty:
        st.info("No section data available.")
        return
    section_agg = (
        semester_course_df.groupby("section", as_index=False)
        .agg(sessions=("sessions", "sum"), completion=("completion", "mean"), students=("students", "first"))
        .sort_values("completion", ascending=False)
        .reset_index(drop=True)
    )
    rows_html = ""
    for i, row in section_agg.iterrows():
        pct = row.get("completion")
        bar_w = min(int(pct or 0), 100)
        bar_cls = _bar_class(pct)
        pct_str = f"{pct:.1f}%" if pct is not None else "—"
        rows_html += f"""
        <tr>
          <td class="cm-row-num">{i+1:02d}</td>
          <td><span style='background:#f1f5f9;border-radius:6px;padding:2px 8px;font-weight:600;font-size:0.85rem'>{escape_html(str(row['section']))}</span></td>
          <td>{int(row.get('students', 0))}</td>
          <td>{int(row.get('sessions', 0))}</td>
          <td><span class="cm-pct-val {_pct_class(pct)}">{pct_str}</span></td>
          <td><div class="cm-bar-track" style="width:120px"><div class="cm-bar-fill {bar_cls}" style="width:{bar_w}%"></div></div></td>
        </tr>"""
    st.markdown(
        f"""<table class="unit-table">
          <thead><tr><th>#</th><th>Section</th><th>Students</th><th>Sessions</th><th>Delivery %</th><th>Progress</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""",
        unsafe_allow_html=True,
    )


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
            /* ── Course Matrix ─────────────────────────── */
            .course-matrix-header {
                font-size: 1.15rem;
                font-weight: 700;
                color: #0f172a;
                margin-bottom: 2px;
            }
            .course-matrix-sub {
                font-size: 0.88rem;
                color: #64748b;
                margin-bottom: 14px;
            }
            /* New card-row matrix */
            .cm-card-container {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 24px rgba(15,23,42,0.07);
                font-size: 0.92rem;
            }
            .cm-card-header {
                display: flex;
                align-items: center;
                padding: 10px 16px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 0.78rem;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .cm-card-row {
                display: flex;
                align-items: center;
                padding: 13px 16px;
                border-bottom: 1px solid #f1f5f9;
                transition: background 0.12s;
            }
            .cm-card-row:last-child { border-bottom: none; }
            .cm-card-row:hover { background: #f8fafc; }
            /* Shared column widths for header and rows */
            .cm-th-num   { width: 36px;  min-width: 36px; }
            .cm-th-course{ flex: 1;      padding-right: 16px; }
            .cm-th-adh   { width: 140px; min-width: 110px; }
            .cm-th-comp  { width: 140px; min-width: 110px; }
            .cm-th-quiz  { width: 90px;  min-width: 80px; }
            .cm-th-skill { width: 80px;  min-width: 70px; }
            .cm-th-arrow { width: 24px;  min-width: 24px; text-align: right; }
            .cm-table {
                width: 100%;
                border-collapse: collapse;
                background: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 24px rgba(15,23,42,0.07);
                font-size: 0.92rem;
            }
            .cm-table thead tr {
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
            }
            .cm-table thead th {
                padding: 11px 14px;
                font-weight: 600;
                color: #64748b;
                font-size: 0.82rem;
                text-align: left;
                white-space: nowrap;
            }
            .cm-table thead th.right { text-align: right; }
            .cm-table tbody tr {
                border-bottom: 1px solid #f1f5f9;
                transition: background 0.15s;
            }
            .cm-table tbody tr:last-child { border-bottom: none; }
            .cm-table tbody tr:hover { background: #f8fafc; }
            .cm-table td {
                padding: 13px 14px;
                vertical-align: middle;
            }
            .cm-row-num {
                color: #94a3b8;
                font-size: 0.82rem;
                font-weight: 500;
                min-width: 28px;
            }
            .cm-course-name {
                font-weight: 600;
                color: #0f172a;
                font-size: 0.95rem;
            }
            .cm-sessions {
                font-size: 0.9rem;
                white-space: nowrap;
            }
            .cm-sessions .delivered { color: #0f172a; font-weight: 600; }
            .cm-sessions .planned   { color: #94a3b8; }
            .cm-pct-cell { min-width: 110px; }
            .cm-pct-val {
                font-weight: 700;
                font-size: 0.93rem;
                margin-bottom: 4px;
            }
            .cm-bar-track {
                height: 4px;
                background: #e2e8f0;
                border-radius: 999px;
                width: 90px;
                overflow: hidden;
            }
            .cm-bar-fill {
                height: 4px;
                border-radius: 999px;
            }
            .pct-green  { color: #16a34a; }
            .pct-orange { color: #d97706; }
            .pct-red    { color: #dc2626; }
            .bar-green  { background: #16a34a; }
            .bar-orange { background: #d97706; }
            .bar-red    { background: #dc2626; }
            .bar-black  { background: #0f172a; }
            .cm-arrow { color: #cbd5e1; font-size: 0.9rem; }
            /* ── Course Detail ─────────────────────────── */
            .cd-header-wrap {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 4px;
                flex-wrap: wrap;
            }
            .cd-title {
                font-size: 1.55rem;
                font-weight: 800;
                color: #0f172a;
                line-height: 1.15;
            }
            .cd-subtitle {
                font-size: 0.9rem;
                color: #64748b;
                margin-bottom: 14px;
            }
            .cd-stats-bar {
                display: flex;
                gap: 0;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 2px 12px rgba(15,23,42,0.05);
                margin-bottom: 18px;
                flex-wrap: wrap;
            }
            .cd-stat-item {
                flex: 1 1 120px;
                padding: 16px 20px;
                border-right: 1px solid #f1f5f9;
            }
            .cd-stat-item:last-child { border-right: none; }
            .cd-stat-label {
                font-size: 0.78rem;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 6px;
            }
            .cd-stat-value {
                font-size: 1.6rem;
                font-weight: 800;
                color: #0f172a;
                line-height: 1;
            }
            .cd-stat-sub {
                font-size: 0.78rem;
                color: #64748b;
                margin-top: 3px;
            }
            .cd-stat-value.accent-orange { color: #d97706; }
            .cd-stat-value.accent-green  { color: #16a34a; }
            /* ── Unit table (L/P/E tab) ────────────────── */
            .unit-table {
                width: 100%;
                border-collapse: collapse;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 12px rgba(15,23,42,0.05);
                font-size: 0.9rem;
            }
            .unit-table thead tr { background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
            .unit-table thead th { padding: 10px 14px; font-weight: 600; color: #64748b; font-size: 0.8rem; text-align: left; }
            .unit-table tbody tr { border-bottom: 1px solid #f1f5f9; }
            .unit-table tbody tr:last-child { border-bottom: none; }
            .unit-table td { padding: 11px 14px; vertical-align: middle; }
            .unit-type-badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.04em;
            }
            .badge-lecture  { background: #dbeafe; color: #1d4ed8; }
            .badge-practice { background: #d1fae5; color: #065f46; }
            .badge-exam     { background: #fef3c7; color: #92400e; }
            .badge-quiz     { background: #fef9c3; color: #854d0e; }
            /* ── Quiz card rows (Image #13 style) ───────*/
            .qz-card-container {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 2px 12px rgba(15,23,42,0.05);
                font-size: 0.9rem;
            }
            .qz-card-header {
                display: flex;
                align-items: center;
                padding: 10px 16px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 0.78rem;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .qz-card-row {
                display: flex;
                align-items: center;
                padding: 13px 16px;
                border-bottom: 1px solid #f1f5f9;
                transition: background 0.12s;
            }
            .qz-card-row:last-child { border-bottom: none; }
            .qz-card-row:hover { background: #f8fafc; }
            .qz-num      { width: 34px; min-width: 34px; color: #94a3b8; font-size: 0.82rem; }
            .qz-name     { flex: 1; font-weight: 600; color: #0f172a; padding-right: 12px; }
            .qz-badge    { width: 150px; min-width: 120px; display: inline-block;
                           padding: 3px 10px; border-radius: 6px; font-size: 0.75rem;
                           font-weight: 700; letter-spacing: 0.04em; text-align: center; }
            .qz-th-att   { width: 90px; min-width: 70px; font-size: 0.88rem; }
            .qz-th-pas   { width: 80px; min-width: 60px; font-size: 0.88rem; }
            .qz-th-score { width: 90px; min-width: 70px; font-size: 0.88rem; }
            .qz-th-pct   { width: 80px; min-width: 60px; font-weight: 700; }
            .qz-arrow    { width: 20px; min-width: 20px; color: #cbd5e1; text-align: right; }
            /* ── LPE Card rows (Image #10 style) ─────── */
            .lpe-card-container {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 2px 12px rgba(15,23,42,0.05);
                font-size: 0.9rem;
            }
            .lpe-card-header {
                display: flex;
                align-items: center;
                padding: 10px 16px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 0.78rem;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                gap: 0;
            }
            .lpe-card-row {
                display: flex;
                align-items: center;
                padding: 13px 16px;
                border-bottom: 1px solid #f1f5f9;
                gap: 0;
                transition: background 0.12s;
            }
            .lpe-card-row:last-child { border-bottom: none; }
            .lpe-card-row:hover { background: #f8fafc; }
            /* Column widths */
            .lpe-num,     .lpe-th-num     { width: 36px;  min-width: 36px;  color: #94a3b8; font-size: 0.82rem; }
            .lpe-name,    .lpe-th-name    { flex: 1;      font-weight: 600; color: #0f172a; padding-right: 12px; }
            .lpe-badge,   .lpe-th-badge   { width: 100px; min-width: 90px; }
            .lpe-students,.lpe-th-students { width: 200px; min-width: 160px; font-size: 0.85rem; }
            .lpe-pct,     .lpe-th-pct     { width: 72px;  min-width: 60px;  font-weight: 700; font-size: 0.93rem; text-align: right; }
            .lpe-bar-wrap,.lpe-th-bar     { width: 110px; min-width: 80px;  margin: 0 12px; }
            .lpe-arrow,   .lpe-th-arrow   { width: 20px;  min-width: 20px;  color: #cbd5e1; text-align: right; }
            /* Badge styles for LPE */
            .lpe-badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.04em;
            }
            .lpe-badge-lecture  { background: #f1f5f9; color: #475569; }
            .lpe-badge-practice { background: #ccfbf1; color: #065f46; }
            .lpe-badge-exam     { background: #fee2e2; color: #991b1b; }
            .lpe-badge-quiz     { background: #fef9c3; color: #854d0e; }
            /* Student count spans */
            .lpe-stu-count  { color: #0f172a; font-weight: 600; }
            .lpe-stu-of     { color: #64748b; }
            .lpe-stu-pending { color: #ef4444; font-size: 0.8rem; }
            /* LPE bar */
            .lpe-bar-wrap {
                height: 4px;
                background: #e2e8f0;
                border-radius: 999px;
                overflow: hidden;
            }
            .lpe-bar-fill {
                height: 4px;
                border-radius: 999px;
                transition: width 0.3s;
            }
            /* ── Section filter pills ──────────────────── */
            .section-pills {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-bottom: 14px;
            }
            /* ── Quiz funnel cards ─────────────────────── */
            .quiz-funnel-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 16px;
            }
            .quiz-funnel-item {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 14px 16px;
            }
            .quiz-funnel-label { font-size: 0.8rem; color: #64748b; margin-bottom: 4px; }
            .quiz-funnel-value { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
            .quiz-funnel-value.red    { color: #dc2626; }
            .quiz-funnel-value.green  { color: #16a34a; }
            .quiz-funnel-value.orange { color: #d97706; }
            .quiz-funnel-sub { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
            .quiz-pass-banner {
                display: flex;
                align-items: center;
                gap: 14px;
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-left: 4px solid #10b981;
                border-radius: 16px;
                padding: 14px 20px;
                margin-bottom: 14px;
                flex-wrap: wrap;
            }
            .quiz-pass-label {
                font-size: 0.88rem;
                font-weight: 700;
                color: #065f46;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                white-space: nowrap;
            }
            .quiz-pass-value {
                font-size: 1.6rem;
                font-weight: 800;
                color: #059669;
                line-height: 1;
                white-space: nowrap;
            }
            .quiz-pass-caption {
                font-size: 0.82rem;
                color: #047857;
                line-height: 1.4;
                opacity: 0.85;
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
        st.markdown(
            "<div style='padding:18px 4px 8px 4px'>"
            "<div style='font-size:1.25rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em'>NIAT Audit</div>"
            "<div style='font-size:0.75rem;color:#64748b;margin-top:2px'>Delivery &amp; Assessment Dashboard</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='margin:8px 0 16px 0;border:none;border-top:1px solid #e2e8f0'>", unsafe_allow_html=True)

        st.markdown("<div style='font-size:0.72rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px'>Filters</div>", unsafe_allow_html=True)
        batch = st.selectbox("Batch", ["NIAT 24", "NIAT 25", "NIAT 26"], index=1, label_visibility="collapsed" if False else "visible")
        available_semesters = get_available_semesters_for_batch(batch)
        if not available_semesters:
            st.warning(f"No semesters available yet for {batch}.")
            st.stop()
        default_semester = available_semesters[-1]
        previous_batch = st.session_state.get("batch")
        previous_semester = st.session_state.get("semester")
        if previous_batch == batch and previous_semester in available_semesters:
            default_semester = previous_semester
        semester = st.selectbox("Semester", available_semesters, index=available_semesters.index(default_semester))

        st.markdown("<hr style='margin:12px 0;border:none;border-top:1px solid #e2e8f0'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.72rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px'>View</div>", unsafe_allow_html=True)
        analysis_type = st.radio(
            "Grouping Logic",
            ["overview", "design", "delivered"],
            format_func=lambda v: {"overview": "Overview", "design": "Planned Bands", "delivered": "Delivered Bands"}[v],
            label_visibility="collapsed",
        )
        st.markdown(
            {
                "overview": "<div style='font-size:0.75rem;color:#64748b;line-height:1.5;padding:6px 0'>University timeline table — click a row to open its course breakdown.</div>",
                "design":   "<div style='font-size:0.75rem;color:#64748b;line-height:1.5;padding:6px 0'>Groups universities by <strong>planned</strong> session volume.</div>",
                "delivered":"<div style='font-size:0.75rem;color:#64748b;line-height:1.5;padding:6px 0'>Groups universities by <strong>delivered</strong> slot count.</div>",
            }[analysis_type],
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='margin:12px 0;border:none;border-top:1px solid #e2e8f0'>", unsafe_allow_html=True)
        load_clicked = st.button("Refresh data", type="primary", use_container_width=True)

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

    _quiz_pass_pct = (new_metrics.get("quiz", {}).get(selected_university) or {}).get("classroom_quiz_pass_pct")
    university_metrics = build_university_metrics(semester_df, assessment_df, selected_university, selected_section, semester, sem_course_titles, quiz_pass_pct=_quiz_pass_pct)
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
                    st.session_state.pop("selected_course_for_detail", None)
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
            _quiz_pass_pct = (new_metrics.get("quiz", {}).get(selected_university) or {}).get("classroom_quiz_pass_pct")
            university_metrics = build_university_metrics(semester_df, assessment_df, selected_university, selected_section, semester, sem_course_titles, quiz_pass_pct=_quiz_pass_pct)
            if university_metrics is None:
                st.warning("No university data available for the current selection.")
                st.stop()
            course_table, hidden_courses = filter_course_table(university_metrics["courseTable"], semester)

        # ── Semester window info ───────────────────────────────────────────────
        if dates:
            st.markdown(
                f"<div class='info-card'><strong>Semester window:</strong> {escape_html(dates['start'])} to {escape_html(dates['end'])}</div>",
                unsafe_allow_html=True,
            )

        # ── Fetch planned/delivered per course from session_adherence ──────────
        with st.spinner("Loading course delivery stats…"):
            delivery_stats_df = fetch_course_delivery_stats(batch, semester, selected_university)

        # ── Fetch per-course quiz pass rates ──────────────────────────────────
        with st.spinner("Loading quiz pass rates…"):
            quiz_pass_by_course_df = fetch_quiz_pass_by_course(batch, semester, selected_university)

        # Build lookups: by normalized title AND by portal_course_id
        _quiz_pass_course_lookup: dict[str, float | None] = {}
        _quiz_pass_by_portal_id: dict[str, float | None] = {}
        if not quiz_pass_by_course_df.empty and "course_title" in quiz_pass_by_course_df.columns:
            for _, _qr in quiz_pass_by_course_df.iterrows():
                _ct = str(_qr.get("course_title") or "").strip()
                _pid = str(_qr.get("portal_course_id") or "").strip()
                _pp = _qr.get("pass_pct")
                _pval: float | None
                try:
                    _pval = None if (_pp is None or pd.isna(_pp)) else float(_pp)
                except (TypeError, ValueError):
                    _pval = None
                if _ct:
                    _quiz_pass_course_lookup[normalize_text(_ct)] = _pval
                if _pid:
                    _quiz_pass_by_portal_id[_pid] = _pval

        # portal_course_id map: normalize_text(sem_course_title) → portal_course_id
        with st.spinner("Loading portal course ID map…"):
            _sem_course_portal_ids = fetch_portal_course_id_map(batch, semester)

        def _course_quiz_pass(course_name: str) -> float | None:
            """Return per-course quiz pass % — title match first, then portal_course_id fallback."""
            key = normalize_text(course_name)
            # 1. Exact title match
            if key in _quiz_pass_course_lookup:
                return _quiz_pass_course_lookup[key]
            # 2. Partial title match
            for k, v in _quiz_pass_course_lookup.items():
                if key in k or k in key:
                    return v
            # 3. Portal course ID fallback via sem_course_title → portal_course_id
            pid = _sem_course_portal_ids.get(key)
            if pid and pid in _quiz_pass_by_portal_id:
                return _quiz_pass_by_portal_id[pid]
            return None

        def _get_delivery_row(course_name: str) -> dict | None:
            if delivery_stats_df.empty:
                return None
            norm = normalize_text(course_name)
            # 1. Exact normalized match
            for _, r in delivery_stats_df.iterrows():
                if normalize_text(str(r.get("course", ""))) == norm:
                    return r.to_dict()
            # 2. Partial match
            for _, r in delivery_stats_df.iterrows():
                raw_norm = normalize_text(str(r.get("course", "")))
                if norm in raw_norm or raw_norm in norm:
                    return r.to_dict()
            # 3. Alias-group match: if both names normalize to the same canonical
            #    alias-group key they are the same subject regardless of how the
            #    title is stored in session_adherence.
            #    e.g. "Advanced Communicative English" and "Communicative English
            #    Advanced" both resolve to "Advanced Communicative English".
            norm_alias = normalize_text(normalize_course_name(course_name, semester))
            for _, r in delivery_stats_df.iterrows():
                raw = str(r.get("course", ""))
                if normalize_text(normalize_course_name(raw, semester)) == norm_alias:
                    return r.to_dict()
            return None

        # ── Build course_rows for the matrix ──────────────────────────────────
        course_rows = []
        for _, ct_row in course_table.iterrows():
            cname = ct_row["Course"]
            dr = _get_delivery_row(cname)
            delivered = dr["total_delivered"] if dr else ct_row.get("Total Slots")
            planned   = dr["total_planned"]   if dr else None
            adherence = dr["adherence_pct"]   if dr else None
            # avg completion across session types present
            comp_vals = [v for v in [ct_row.get("Lecture %"), ct_row.get("Practice %"), ct_row.get("Exam %")] if v is not None]
            completion = sum(comp_vals) / len(comp_vals) if comp_vals else None
            skill_val = ct_row.get("Skill Score %")
            course_rows.append({
                "course":         cname,
                "delivered":      delivered,
                "planned":        planned,
                "lecture_slots":  ct_row.get("Lecture Slots"),
                "practice_slots": ct_row.get("Practice Slots"),
                "exam_slots":     ct_row.get("Exam Slots"),
                "total_slots":    ct_row.get("Total Slots"),
                "lecture_pct":    ct_row.get("Lecture %"),
                "practice_pct":   ct_row.get("Practice %"),
                "exam_pct":       ct_row.get("Exam %"),
                "adherence_pct":  adherence if adherence is not None else completion,
                "completion_pct": completion,
                "quiz_pass_pct":  _course_quiz_pass(cname),
                "skill_pct":      skill_val,
            })

        # ── Course Matrix or Course Detail ─────────────────────────────────────
        selected_course_for_detail = st.session_state.get("selected_course_for_detail")

        if selected_course_for_detail is None:
            # ── MATRIX VIEW ───────────────────────────────────────────────────
            scope_label = selected_section if selected_section else "All sections"
            render_section_header(f"{selected_university} — {scope_label}", "Select a course row to drill into schedule adherence, unit completion, quizzes, and assessments.")
            if hidden_courses:
                st.markdown(
                    f"<div class='info-card'>Showing {escape_html(len(course_table))} core courses · {escape_html(hidden_courses)} support courses hidden.</div>",
                    unsafe_allow_html=True,
                )
            clicked = render_course_matrix(course_rows, selected_course_for_detail)
            if clicked:
                st.session_state["selected_course_for_detail"] = clicked
                st.session_state.pop("lpe_sec", None)
                st.session_state.pop("quiz_sec", None)
                st.rerun()

        else:
            # ── DETAIL VIEW ───────────────────────────────────────────────────
            back_col, _ = st.columns([0.15, 0.85])
            with back_col:
                if st.button("← Courses", key="back_to_matrix"):
                    st.session_state.pop("selected_course_for_detail", None)
                    st.session_state.pop("lpe_sec", None)
                    st.session_state.pop("quiz_sec", None)
                    st.session_state.pop("cm_course_select", None)
                    st.rerun()

            # Filter semester_df to selected course
            # Build a helper that maps a raw content course title to its display sem_course_title
            # using the same logic as build_university_metrics / _display_course
            def _raw_to_display(raw_course: str) -> str:
                normalized = normalize_course_name(str(raw_course), semester)
                return sem_course_titles.get(normalize_text(normalized), normalized)

            sem_course_df = semester_df[
                (semester_df["institute"] == selected_university) &
                (semester_df["course"].apply(lambda c: normalize_text(_raw_to_display(str(c)))) == normalize_text(selected_course_for_detail))
            ].copy()
            if selected_section:
                sem_course_df = sem_course_df[sem_course_df["section"] == selected_section]

            # Collect ALL raw session_adherence course titles that belong to the same
            # subject as selected_course_for_detail (e.g. "Communicative English Advanced"
            # + "English B1 Level Learner Program" both map to "Advanced Communicative English").
            _norm_alias = normalize_text(normalize_course_name(selected_course_for_detail, semester))
            _all_raw_titles: list[str] = []
            if not delivery_stats_df.empty:
                for _, _dr in delivery_stats_df.iterrows():
                    _raw = str(_dr.get("course", ""))
                    if normalize_text(normalize_course_name(_raw, semester)) == _norm_alias:
                        if _raw not in _all_raw_titles:
                            _all_raw_titles.append(_raw)
            raw_course_titles = tuple(_all_raw_titles) if _all_raw_titles else (selected_course_for_detail,)

            # Aggregate planned/delivered across all matching raw titles
            _sub_rows = [_get_delivery_row(t) for t in raw_course_titles]
            _sub_rows = [r for r in _sub_rows if r]
            if _sub_rows:
                _tot_planned   = sum(r.get("total_planned")   or 0 for r in _sub_rows)
                _tot_delivered = sum(r.get("total_delivered") or 0 for r in _sub_rows)
                sel_delivery = {
                    "course":          raw_course_titles[0],
                    "total_planned":   _tot_planned,
                    "total_delivered": _tot_delivered,
                    "adherence_pct":   round(_tot_delivered / _tot_planned * 100, 1) if _tot_planned else None,
                }
            else:
                sel_delivery = None

            # Pre-fetch units and quiz data for header stats (cached, so also reused in tabs)
            with st.spinner("Loading course data…"):
                _detail_units_df = fetch_course_session_units(batch, semester, selected_university, raw_course_titles)

            # Render header + stats bar
            _detail_quiz_pct = _course_quiz_pass(selected_course_for_detail)
            render_course_detail_header(selected_course_for_detail, sel_delivery, _detail_units_df, _detail_quiz_pct)

            # ── Tabs ──────────────────────────────────────────────────────────
            tab1, tab2, tab3 = st.tabs([
                "📅 Schedule Adherence",
                "📖 Lecture / Practice / Exam",
                "🎯 Assessments",
            ])

            with tab1:
                with st.spinner("Loading weekly delivery data…"):
                    weekly_df = fetch_course_weekly_delivery(batch, semester, selected_university, raw_course_titles)
                render_tab_schedule_adherence(weekly_df)

            with tab2:
                units_df = _detail_units_df
                sec_list = sorted(sem_course_df["section"].unique().tolist()) if not sem_course_df.empty else []
                render_tab_lecture_practice_exam(units_df, sec_list)

            with tab3:
                course_assessment_df = assessment_df[
                    (assessment_df["university"] == selected_university) &
                    (assessment_df["course_code"].apply(lambda c: normalize_text(_raw_to_display(str(c)))) == normalize_text(selected_course_for_detail))
                ].copy()
                if selected_section:
                    course_assessment_df = course_assessment_df[course_assessment_df["section"] == selected_section]
                sec_list_asmt = sorted(course_assessment_df["section"].unique().tolist()) if not course_assessment_df.empty else []
                render_tab_assessments(course_assessment_df, selected_course_for_detail, sec_list_asmt)





if __name__ == "__main__":
    main()
