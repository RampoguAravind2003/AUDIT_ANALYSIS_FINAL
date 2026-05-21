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
DEFAULT_SKILL_GRADED_SEM1_TABLE = "z_niat_key_metrics_dashboard_2025_batch_wise_skill_and_graded_assessments_scores"
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

PLANNED_CONTENT_SLOTS_OVERRIDES = {
    "Semester 1": {
        "Sanjay Ghodawat University":                  439,
        "Sanjay Godhawat University":                  439,
        "SGU":                                         439,
        "Vivekananda global University":               588,
        "VGU":                                         588,
        "Yenepoya University":                         514,
        "Yenapoya University":                         514,
        "Yenepoya":                                    514,
        "S-Vyasa":                                     593,
        "S-VYASA":                                     593,
        "A Dy Patil University":                       531,
        "A Dy Patil":                                  531,
        "Takshashila University":                      466,
        "Takshasila University":                       466,
        "Takshashila":                                 466,
        "Noida International":                         494,
        "Noida International University":              494,
        "NIU":                                         494,
        "Annamacharya University":                     512,
        "Annamacharya":                                512,
        "NRI Institute of Technology":                 425,
        "NRI":                                         425,
        "MRV University":                              540,
        "MRV":                                         540,
        "Malla Reddy Vishwavidyapeeth":                540,
        "CDU":                                         451,
        "Chaitanya Deemed-to-be University":           451,
        "Crescent University":                         492,
        "Crescent":                                    492,
        "Chalapathy":                                  366,
        "Chalapathy (CITY)":                           366,
        "Chalapathi":                                  366,
        "NSRIT":                                       603,
        "NSRIT University":                            603,
        "Aurora":                                      237,
        "Aurora University":                           237,
        "Academy of Maritime education & Technology":  339,
        "AMET":                                        339,
    },
}

SEMESTER_DATES_BY_SEMESTER = {
    "Semester 1": {
        "A Dy Patil University":                    {"start": "Aug 4, 2025",  "end": "Dec 15, 2025"},
        "Academy of Maritime education & Technology":{"start": "Sep 1, 2025",  "end": "Jan 27, 2026"},
        "AMET":                                      {"start": "Sep 1, 2025",  "end": "Jan 27, 2026"},
        "Annamacharya University":                   {"start": "Aug 11, 2025", "end": "Jan 6, 2026"},
        "Aurora University":                         {"start": "Sep 15, 2025", "end": "Jun 15, 2026"},
        "Chaitanya Deemed-to-be University":         {"start": "Aug 4, 2025",  "end": "Dec 24, 2025"},
        "Chalapathy":                                {"start": "Aug 25, 2025", "end": "Jan 24, 2026"},
        "Chalapathy (CITY)":                         {"start": "Aug 25, 2025", "end": "Jan 24, 2026"},
        "Crescent University":                       {"start": "Sep 8, 2025",  "end": "Dec 24, 2025"},
        "Malla Reddy Vishwavidyapeeth":              {"start": "Aug 4, 2025",  "end": "Dec 31, 2025"},
        "NIAT Chevella":                             {"start": "Aug 25, 2025", "end": "Jun 6, 2026"},
        "Noida International":                       {"start": "Aug 25, 2025", "end": "Dec 22, 2025"},
        "Noida International University":            {"start": "Aug 25, 2025", "end": "Dec 22, 2025"},
        "NRI":                                       {"start": "Aug 18, 2025", "end": "Dec 30, 2025"},
        "NRI Institute of Technology":               {"start": "Aug 18, 2025", "end": "Dec 30, 2025"},
        "NSRIT University":                          {"start": "Aug 18, 2025", "end": "Dec 30, 2025"},
        "NSRIT":                                     {"start": "Aug 18, 2025", "end": "Dec 30, 2025"},
        "S-VYASA":                                   {"start": "Aug 11, 2025", "end": "Jan 20, 2026"},
        "Sanjay Ghodawat University":                {"start": "Aug 11, 2025", "end": "Dec 15, 2025"},
        "Takshasila University":                     {"start": "Sep 15, 2025", "end": "Jan 21, 2026"},
        "Takshashila University":                    {"start": "Sep 15, 2025", "end": "Jan 21, 2026"},
        "Vivekananda global University":             {"start": "Aug 25, 2025", "end": "Dec 20, 2025"},
        "Yenapoya University":                       {"start": "Aug 4, 2025",  "end": "Dec 23, 2025"},
        "Yenepoya University":                       {"start": "Aug 4, 2025",  "end": "Dec 23, 2025"},
    },
    "Semester 2": {
        "A Dy Patil University":                    {"start": "Jan 5, 2026",  "end": "May 15, 2026"},
        "Academy of Maritime education & Technology":{"start": "Feb 2, 2026",  "end": "Jun 9, 2026"},
        "AMET":                                      {"start": "Feb 2, 2026",  "end": "Jun 9, 2026"},
        "Annamacharya University":                   {"start": "Jan 2, 2026",  "end": "Jun 4, 2026"},
        "Aurora University":                         {"start": "Aug 12, 2025", "end": "Feb 22, 2026"},
        "BITS":                                      {"start": "Jan 28, 2026", "end": "Aug 15, 2026"},
        "CDU":                                       {"start": "Jan 19, 2026", "end": "May 18, 2026"},
        "Chaitanya Deemed-to-be University":         {"start": "Jan 19, 2026", "end": "May 18, 2026"},
        "Chalapathy":                                {"start": "Jan 27, 2026", "end": "Jul 11, 2026"},
        "Chalapathy (CITY)":                         {"start": "Jan 27, 2026", "end": "Jul 11, 2026"},
        "Crescent University":                       {"start": "Jan 19, 2026", "end": "May 19, 2026"},
        "Malla Reddy Vishwavidyapeeth":              {"start": "Jan 2, 2026",  "end": "May 9, 2026"},
        "MRV University":                            {"start": "Jan 2, 2026",  "end": "May 9, 2026"},
        "Noida International":                       {"start": "Jan 12, 2026", "end": "Jun 6, 2026"},
        "Noida International University":            {"start": "Jan 12, 2026", "end": "Jun 6, 2026"},
        "NRI":                                       {"start": "Jan 16, 2026", "end": "Jun 20, 2026"},
        "NRI Institute of Technology":               {"start": "Jan 16, 2026", "end": "Jun 20, 2026"},
        "NSRIT":                                     {"start": "Feb 9, 2026",  "end": "Jul 13, 2026"},
        "NSRIT University":                          {"start": "Feb 9, 2026",  "end": "Jul 13, 2026"},
        "S-VYASA":                                   {"start": "Feb 16, 2026", "end": "Jul 7, 2026"},
        "Sanjay Ghodawat University":                {"start": "Jan 5, 2026",  "end": "Jun 13, 2026"},
        "Takshashila University":                    {"start": "Feb 9, 2026",  "end": "Jun 13, 2026"},
        "Takshasila University":                     {"start": "Feb 9, 2026",  "end": "Jun 13, 2026"},
        "Vivekananda global University":             {"start": "Jan 2, 2026",  "end": "May 30, 2026"},
        "Yenapoya University":                       {"start": "Jan 20, 2026", "end": "Jun 5, 2026"},
        "Yenepoya University":                       {"start": "Jan 20, 2026", "end": "Jun 5, 2026"},
    },
}


ASSESSMENT_SLOTS_BY_SEMESTER = {
    "Semester 1": 75,
    "Semester 2": 75,
}

DELIVERY_MODE_BY_SEMESTER = {
    "Semester 1": {
        "A Dy Patil University":            "Full Delivery",
        "AMET":                             "Full Delivery",
        "Annamacharya University":          "Co Delivery",
        "Aurora University":                "Full Delivery",
        "Chaitanya Deemed-to-be University":"Co Delivery",
        "Chalapathy (CITY)":               "Hybrid Delivery",
        "Crescent University":              "Co Delivery",
        "Malla Reddy Vishwavidyapeeth":     "Full Delivery",
        "NIAT Chevella":                    "Full Delivery",
        "Noida International University":   "Co Delivery",
        "NRI":                              "Co Delivery",
        "NSRIT University":                 "Hybrid Delivery",
        "S-VYASA":                          "Co Delivery",
        "Sanjay Ghodawat University":       "Co Delivery",
        "Takshasila University":            "Co Delivery",
        "Vivekananda global University":    "Full Delivery",
        "Yenapoya University":              "Co Delivery",
    },
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
        "Chalapathy (CITY)": "Hybrid Delivery",
        "Vivekananda global University": "Full Delivery",
        "NSRIT": "Hybrid Delivery",
        "MRV University": "Full Delivery",
        "Takshashila University": "Co Delivery",
        "Noida International": "Co Delivery",
        "Noida International University": "Co Delivery",
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
        "Chalapathy (CITY)": 83,
        "Vivekananda global University": 72,
        "NSRIT": 109,
        "MRV University": 75,
        "Takshashila University": 86,
        "Noida International": 86,
        "Noida International University": 86,
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
        "Chalapathy (CITY)": 72,
        "Vivekananda global University": 63,
        "NSRIT": 70,
        "MRV University": 64,
        "Takshashila University": 74,
        "Noida International": 74,
        "Noida International University": 74,
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
        "Chalapathy (CITY)": 12,
        "Vivekananda global University": 10.5,
        "NSRIT": 10,
        "MRV University": 10.66666667,
        "Takshashila University": 12.33333333,
        "Noida International": 12.33333333,
        "Noida International University": 12.33333333,
        "Crescent University": 10.8,
    },
}

COURSE_MAPPING_BY_SEMESTER = {
    "Semester 1": {
        "GENERATIVE_AI": "Introduction to Generative AI",
        "MATHEMATICS": "Mathematics",
        "BUILD_YOUR_OWN_STATIC_WEBSITE": "Web Application Development 1",
        "COMMUNICATIVE_ENGLISH_FOUNDATION": "English Communication Foundation",
        "PROGRAMMING_FOUNDATIONS": "Computer Programming",
        "QUANTITATIVE_APTITUDE": "Quantitative Aptitude",
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
        "LINEAR_ALGEBRA": "Linear Algebra and Calculus",
        "LA_C": "Linear Algebra and Calculus",
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
        "MATHEMATICS": "Linear Algebra and Calculus",
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
            "calculus and differential equations",
        ],
        "Web Application Development 1": [
            "build your own static website",
            "build your own responsive website",
            "build your own dynamic application",
            "build your own dynamic web application",
            "modern responsive web design",
            "responsive web design using flexbox",
            "html css",
            "js programming",
            "web application development i",
            "web application development 1",
            "web application development 1 laboratory",
            "web application development-1",
            "web application development",
            "web development programmining",
            "frontend development 1",
            "frontend development fundamentals",
            "fundamentals of web development",
            "web technologies",
            "web technologies laboratory",
        ],
        "English Communication Foundation": [
            "communicative english foundation",
            "english communication foundation",
            "communication english foundation",
            "english foundation",
            "english course",
            "english - basic",
            "english basic",
            "introduction to english language and communication",
            "aec 1",
            "cambridge english b1",
            "writing practice",
            "professional skills for engineers",
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
            "more python concepts",
            "advanced programming",
        ],
        "Quantitative Aptitude": [
            "quantitative aptitude",
            "numerical aptitude",
            "numerical ability",
            "quantitative skills",
            "logical mathematics for software engineers i",
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
            "data base management systems",
            "data base management system",
            "database management systems laboratory",
            "database management systems lab",
            "database systems",
            "dbms",
            "dbms lab",
            "dbms laboratory",
            "dbms - database management systems",
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
        "Linear Algebra and Calculus": [
            "engineering mathematics 2",
            "mathematics 2",
            "linear algebra and calculus",
            "mathematics for problem solving",
            "logical mathematics for software engineers ii",
            "probability and statistics",
            "linear algebra",
            "linear algebra calculus",
            "calculus",
            "calculus and differential equations",
            "calculus & differential equations",
            "mathematics",
            "maths",
            "math",
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
        "Module Assessment 5",
        "Intro to Tech",
        "Intro to Software Development",
        "JS Essentials",
        "JavaScript Essentials",
        "NIAT-DSA",
        "NIAT - DSA",
        "Test Based Learning",
        "Text Based Learning",
    },
    "Semester 2": {
        "Assessment",
        "Module Quiz",
        "Module Assessment 5",
        "Intro to Tech",
        "Intro to Software Development",
        "Test Based Learning",
        "Text Based Learning",
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


def get_global_semester_date_range(semester: str, batch: str) -> tuple[str, str] | None:
    """
    Return (earliest_start_iso, latest_end_iso) across all institutes for a semester.
    Used as a fallback when the live DB query is unavailable.
    """
    windows = SEMESTER_DATES_BY_SEMESTER.get(semester)
    if not windows:
        return None
    year_shift = get_batch_year_shift(batch)
    starts, ends = [], []
    for window in windows.values():
        s = shift_iso_date(to_iso_date(window["start"]), year_shift)
        e = shift_iso_date(to_iso_date(window["end"]), year_shift)
        if s:
            starts.append(s)
        if e:
            ends.append(e)
    if not starts or not ends:
        return None
    return min(starts), max(ends)


def filter_df_by_semester_dates(
    df: pd.DataFrame,
    date_col: str,
    inst_col: str,
    semester: str,
    batch: str,
) -> pd.DataFrame:
    """
    Post-filter a DataFrame to only keep rows whose date falls within the
    semester window for that row's institute.

    Replaces the SQL get_semester_window_clause approach, which created an
    institute-name whitelist. Here we use fuzzy institute matching (exact →
    substring → acronym) so institutes with differing name formats are still
    matched correctly. Rows whose institute has no defined window are kept.
    """
    if df.empty:
        return df
    windows = SEMESTER_DATES_BY_SEMESTER.get(semester)
    if not windows:
        return df

    year_shift = get_batch_year_shift(batch)
    stop_words = {"of", "the", "and", "to", "for", "a", "an", "at", "in", "&"}

    # Build lookup: normalize_text(institute_name) → (start_date, end_date)
    date_ranges: dict[str, tuple] = {}
    for inst_name, window in windows.items():
        start = datetime.strptime(
            shift_iso_date(to_iso_date(window["start"]), year_shift), "%Y-%m-%d"
        ).date()
        end = datetime.strptime(
            shift_iso_date(to_iso_date(window["end"]), year_shift), "%Y-%m-%d"
        ).date()
        date_ranges[normalize_text(inst_name)] = (start, end)

    all_keys = list(date_ranges.keys())

    def _get_range(inst_name: str):
        norm = normalize_text(inst_name)
        if norm in date_ranges:
            return date_ranges[norm]
        for key in all_keys:
            if (norm and key) and (norm in key or key in norm):
                return date_ranges[key]
        # Acronym: first letter of each significant word
        words = [w for w in norm.split() if w and w not in stop_words]
        if words:
            acronym = "".join(w[0] for w in words)
            if acronym in date_ranges:
                return date_ranges[acronym]
        return None  # unknown institute — no filtering

    # Cache range per unique institute name to avoid repeated lookups
    _range_cache: dict[str, tuple | None] = {}

    def _in_range(row) -> bool:
        inst_name = str(row.get(inst_col) or "").strip()
        if inst_name not in _range_cache:
            _range_cache[inst_name] = _get_range(inst_name)
        range_ = _range_cache[inst_name]
        if range_ is None:
            return True  # no window defined — keep row
        date_val = row.get(date_col)
        if date_val is None or str(date_val) in ("None", "NaT", "nan", ""):
            return True
        try:
            if hasattr(date_val, "date"):
                row_date = date_val.date()
            else:
                row_date = datetime.strptime(str(date_val)[:10], "%Y-%m-%d").date()
        except Exception:
            return True
        return range_[0] <= row_date <= range_[1]

    mask = df.apply(_in_range, axis=1)
    return df[mask]


def should_apply_batch_filter(batch: str) -> bool:
    return bool(batch and batch.strip())


def batch_sql_filter(batch: str, col_expr: str) -> str:
    """
    Return a SQL WHERE snippet that filters col_expr to the given batch.

    Handles two naming conventions used across tables:
      - 'NIAT 25' style  → LIKE '%niat 25%'
      - 'VGU Batch-1' style → REGEXP 'batch[-_ ]?1\\b'  (NIAT 25 → batch number 1)

    Always returns a non-empty string when batch is non-empty.
    """
    if not batch or not batch.strip():
        return ""
    like_pat = sql_escape(batch.strip().lower())
    conditions = [f"LOWER(TRIM(CAST({col_expr} AS STRING))) LIKE '%{like_pat}%'"]
    batch_num = get_niat_batch_number(batch)
    if batch_num is not None:
        conditions.append(
            f"REGEXP_CONTAINS(LOWER(TRIM(CAST({col_expr} AS STRING))), r'batch[-_ ]?{batch_num}\\b')"
        )
    return f"({' OR '.join(conditions)})"


def get_batch_year_shift(batch: str) -> int:
    match = re.match(r"^niat\s+(\d{2})$", batch.strip(), re.IGNORECASE) if batch else None
    return int(match.group(1)) - 25 if match else 0


def get_niat_batch_number(batch: str) -> int | None:
    """
    Convert NIAT batch name to sequential batch number used in table batch_name column.
    Table stores batches as '<Institute> Batch-1', '<Institute> Batch-2', etc.
    NIAT 25 → Batch 1  (25 - 24 = 1)
    NIAT 26 → Batch 2  (26 - 24 = 2)
    Returns None if the batch name doesn't match the NIAT XX pattern.
    """
    m = re.match(r"^niat\s+(\d{2})$", batch.strip(), re.IGNORECASE) if batch else None
    if m:
        return int(m.group(1)) - 24
    return None


def match_batch_names_from_table(all_names: list[str], batch: str) -> list[str]:
    """
    Given a list of batch_name values from the table (e.g. 'VGU Batch-1',
    'SGU Batch-1 CSE', 'NIAT Chevella Batch-1') and a UI batch selection
    (e.g. 'NIAT 25'), return the subset that corresponds to that batch.

    Mapping: NIAT 25 → Batch-1/Batch 1, NIAT 26 → Batch-2/Batch 2, etc.
    """
    batch_num = get_niat_batch_number(batch)
    if batch_num is not None:
        # Match table names containing 'Batch-N' or 'Batch N' or 'Batch_N'
        pattern = re.compile(
            rf"\bbatch[-_ ]?{batch_num}\b", re.IGNORECASE
        )
        matched = [str(n) for n in all_names if pattern.search(str(n))]
        return matched
    # Fallback: match on raw digit string from batch name
    digits = re.sub(r"[^\d]", "", batch.strip()) if batch else ""
    if digits:
        return [str(n) for n in all_names if digits in re.sub(r"[^\d]", "", str(n))]
    return [str(n) for n in all_names]


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
        if batch and batch.strip():
            where_clauses.append(batch_sql_filter(batch, "s.batch_name"))
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


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_semester_actual_date_range(batch: str, semester: str) -> tuple[str, str] | None:
    """
    Query portal_courses + session_adherence to get the actual MIN/MAX session
    dates for this batch + semester combination.

    This is the source-of-truth date range used to filter skill/graded
    assessment records — no hardcoded dates, no institute-name whitelist.
    Falls back to get_global_semester_date_range if the DB query fails.
    """
    refs = get_table_refs()
    sem_num = "1" if "1" in semester else ("2" if "2" in semester else "")

    portal_where = [
        "TRIM(COALESCE(p.institute_name, '')) != ''",
        "TRIM(COALESCE(p.sem_course_id, '')) != ''",
    ]
    if sem_num:
        portal_where.append(f"LOWER(COALESCE(p.semester_title, '')) LIKE '%semester {sem_num}%'")
    if batch and batch.strip():
        portal_where.append(batch_sql_filter(batch, "p.batch_name"))

    sa_where = [
        "TRIM(COALESCE(sa.semester_course_id, '')) != ''",
        "sa.session_date IS NOT NULL",
    ]
    if batch and batch.strip():
        sa_where.append(batch_sql_filter(batch, "sa.batch_name"))

    sql = f"""
        SELECT
          CAST(MIN(DATE(sa.session_date)) AS STRING) AS sem_start,
          CAST(MAX(DATE(sa.session_date)) AS STRING) AS sem_end
        FROM {refs["portal_courses"]} p
        JOIN {refs["session_adherence"]} sa
          ON REPLACE(p.sem_course_id, '-', '') = TRIM(CAST(sa.semester_course_id AS STRING))
        WHERE {' AND '.join(portal_where)}
          AND {' AND '.join(sa_where)}
    """
    try:
        df = run_query(sql)
        if not df.empty:
            start = str(df.iloc[0].get("sem_start") or "").strip()
            end   = str(df.iloc[0].get("sem_end")   or "").strip()
            if start and end and start not in ("None", "NaT", "nan"):
                return start[:10], end[:10]
    except Exception:
        pass
    # Fallback to hardcoded ranges
    return get_global_semester_date_range(semester, batch)


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


DBMS_ALIAS_NAMES = {
    normalize_text("Database Management Systems"),
    normalize_text("Database Management System"),
    normalize_text("Data Base Management Systems"),
    normalize_text("Data Base Management System"),
    normalize_text("Introduction to Database"),
    normalize_text("Introduction to Databases"),
    normalize_text("Introduction to Database Management Systems"),
    normalize_text("Introduction to Database Management Systems Lab"),
    normalize_text("Introduction to DBMS"),
    normalize_text("DBMS"),
    normalize_text("DBMS Fundamentals"),
    normalize_text("Database Systems"),
    normalize_text("MongoDB"),
    normalize_text("SQL"),
    normalize_text("SQL Basics"),
    normalize_text("SQL Fundamentals"),
    normalize_text("Structured Query Language"),
    normalize_text("MySQL"),
    normalize_text("SQL Programming"),
    normalize_text("DBMS - Database management systems"),
    normalize_text("Introduction to DataBase"),
}


def canonicalize_course_label(name: str, semester: str) -> str:
    normalized = normalize_text(name)
    if not normalized:
        return name
    if normalized in DBMS_ALIAS_NAMES:
        return "Database Management Systems"
    canonical = normalize_course_name(name, semester)
    if normalize_text(canonical) in DBMS_ALIAS_NAMES:
        return "Database Management Systems"
    return canonical


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
    planned_slots_df: pd.DataFrame | None = None,
    progress_slots_df: pd.DataFrame | None = None,
    new_metrics: dict | None = None,
    assessment_df: pd.DataFrame | None = None,
):
    """
    Builds the University Overview table with all 20 requested fields.

    New metrics dict structure (keyed by institute name):
      new_metrics["quiz"][institute]         â†' classroom_quiz_attempt_pct, classroom_quiz_pass_pct,
                                               module_quiz_conducted, module_quiz_participation_pct, module_quiz_pass_pct
      new_metrics["practice"][institute]    â†' practice_completion_pct
      new_metrics["delivery"][institute]    â†' practice_delivery_pct, module_quiz_conduction_pct, skill_conduction_pct
      new_metrics["skill_graded"][institute]â†' skill_conducted, skill_participation_pct, skill_pass_pct, academic_attempt_pct, academic_pass_pct

    Metric formulas:
      Deviation %            = (Actual - Expected Till Date) / Expected Till Date Ã— 100  (negative = behind)
      Session Delivery %     = (Actual Slots Delivered Till Date / Expected Slots Till Date) Ã— 100
      Practice Delivery %    = (practice_delivered_count / planned_practice_sessions) Ã— 100
      Module Quiz Conduction %  = (module_quiz_conducted / planned_module_quizzes) Ã— 100
      Skill Assessment Conduction % = (COUNT DISTINCT assessment dates in skill_graded) / 5 Ã— 100

    Pass threshold: â‰¥80% score throughout.
    """
    timeline_df = build_university_timeline_rows(universities, semester, batch)
    content_slot_counts = {}
    if planned_slots_df is not None and not planned_slots_df.empty and {"institute", "planned_content_slots"}.issubset(planned_slots_df.columns):
        content_slot_counts = planned_slots_df.set_index("institute")["planned_content_slots"].fillna(0).to_dict()

    # â€â€ progress slots (existing) â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
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

    # â€â€ new metrics lookups â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    nm = new_metrics or {}
    quiz_data: dict         = nm.get("quiz", {})
    practice_data: dict     = nm.get("practice", {})
    delivery_data: dict     = nm.get("delivery", {})   # from session_adherence
    skill_graded_data: dict = nm.get("skill_graded", {})

    # ── Assessment-df based pass % (same source as course overview) ──────────
    # Pre-build a normalised lookup so we can do case-insensitive institute match.
    _adf = assessment_df if (assessment_df is not None and not assessment_df.empty) else pd.DataFrame()
    _adf_by_inst: dict[str, pd.DataFrame] = {}
    if not _adf.empty and "university" in _adf.columns:
        for _inst_key, _grp in _adf.groupby(_adf["university"].str.strip().str.lower()):
            _adf_by_inst[_inst_key] = _grp

    def _assessment_pass_pct(univ_name: str, atype: str) -> float | None:
        """
        Compute pass % from assessment_df using the same per-course averaging
        logic as the course overview (mirrors build_university_metrics).
        Falls back to None so callers can use skill_graded_data as backup.
        """
        rows = _adf_by_inst.get(univ_name.strip().lower())
        if rows is None or rows.empty:
            return None
        typed = rows[rows["assessment_type"] == atype]
        if typed.empty:
            return None
        rates = []
        for _, r in typed.iterrows():
            part  = pd.to_numeric(r.get("avg_participation"), errors="coerce")
            passed = pd.to_numeric(r.get("avg_pass_count"), errors="coerce")
            if pd.notna(part) and part > 0 and pd.notna(passed):
                rates.append(float(passed) / float(part) * 100)
        return round(sum(rates) / len(rates), 1) if rates else None

    def _get(d: dict, institute: str, key: str):
        # Normalize to lowercase+trimmed to match to_dict keys
        norm = str(institute).strip().lower()
        row = d.get(norm)
        if row is None:
            # Partial-match fallback: handles cases where portal_courses name differs
            # from session_adherence/schedule name (e.g. 'Chalapathy (CITY)' vs 'Chalapathy',
            # 'Noida International University' vs 'Noida International').
            for k in d:
                if k and (k in norm or norm in k):
                    row = d[k]
                    break
        if row is None:
            return None
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

        # â€â€ Actual slots delivered till date â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        allotted = item.get("allottedHours")
        delivery_capacity_slots = round(float(allotted), 1) if allotted is not None else None
        delivered = _get(progress_slots, name, "delivered_slots")
        if delivered is None:
            delivered = item.get("avgLecturePracticeSessions", 0)
        if allotted is not None:
            delivered = min(delivered, float(allotted))
        actual_slots = round(delivered, 1)

        planned_content_slots = float(content_slot_counts.get(name, 0) or 0)
        dates = get_semester_dates_for_institute(name, semester, batch)
        planned_content_slots_till_date = calculate_expected_slots_to_date(dates, planned_content_slots)

        # â€â€ Expected slots till date (from timeline) â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        # Will be filled after merging with timeline_df; placeholder here.
        # We store actual_slots per university and compute derivations post-merge.

        metric_rows.append({
            "University": name,
            "Delivery capacity slots": delivery_capacity_slots,
            "Planned content slots": round(planned_content_slots, 1),
            "Planned content slots till date": round(float(planned_content_slots_till_date), 1) if planned_content_slots_till_date is not None else None,
            "Planned slots delivered till date": actual_slots,
            # â€â€ Session Delivery % replaces old Session completion % â€â€â€â€â€â€â€â€â€â€â€
            # Computed post-merge once Expected Slots Till Date is available.
            # â€â€ Practice Completion % (from unlocked_units; fallback to progress table) â€â€
            "Practice Completion %": round(v, 1) if (v := _get(practice_data, name, "practice_completion_pct")) is not None
                else (round(v2, 1) if (v2 := _get(progress_slots, name, "practice_completion_pct")) is not None else None),
            # â€â€ Classroom Quizzes â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
            "Class Room Quizzes Attempt %":    round(v, 1) if (v := _get(quiz_data, name, "classroom_quiz_attempt_pct"))    is not None else None,
            "Class Room Quizzes Pass %":       round(v, 1) if (v := _get(quiz_data, name, "classroom_quiz_pass_pct"))       is not None else None,
            "CR Quiz Pass % (â‰¥60)":            round(v, 1) if (v := _get(quiz_data, name, "classroom_quiz_pass_60_pct"))    is not None else None,
            "CR Quiz Pass % (>80)":            round(v, 1) if (v := _get(quiz_data, name, "classroom_quiz_pass_80_pct"))    is not None else None,
            "Lecture Delivery %":           round(v, 1) if (v := _get(delivery_data, name, "lecture_delivery_pct")) is not None else None,
            # â€â€ Practice Delivery % (from session_adherence) â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
            "Practice Delivery %":          round(v, 1) if (v := _get(delivery_data, name, "practice_delivery_pct")) is not None else None,
            # â€â€ Module Quiz â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
            "Module Quiz Conduction %":     round(v, 1) if (v := _get(delivery_data, name, "module_quiz_conduction_pct")) is not None else None,
            "Module Quiz Student Participation %": round(v, 1) if (v := _get(quiz_data, name, "module_quiz_participation_pct")) is not None else None,
            "Module Quiz Pass %":            round(v, 1) if (v := _get(quiz_data, name, "module_quiz_pass_pct"))          is not None else None,
            "Module Quiz Pass % (â‰¥60)":      round(v, 1) if (v := _get(quiz_data, name, "module_quiz_pass_60_pct"))       is not None else None,
            "Module Quiz Pass % (>80)":      round(v, 1) if (v := _get(quiz_data, name, "module_quiz_pass_80_pct"))       is not None else None,
            # ── Skill Assessment ──────────────────────────────────────────────
            "Skill Assessment Conduction %":    round(min((v / 5) * 100, 100.0), 1) if (v := _get(skill_graded_data, name, "skill_conducted")) is not None else None,
            "Skill Assessment Student Participation %": round(v, 1) if (v := _get(skill_graded_data, name, "skill_participation_pct")) is not None else None,
            # Skill pass %: use same assessment_df source as the course overview;
            # fall back to skill_graded_data if assessment_df has no data for this university.
            "Skill Assessment Pass %": (
                _assessment_pass_pct(name, "Skill Assessment")
                or (round(v, 1) if (v := _get(skill_graded_data, name, "skill_pass_pct")) is not None else None)
            ),
            # ── Academic Assessments ──────────────────────────────────────────
            "Academic Assessments Attempt %": round(v, 1) if (v := _get(skill_graded_data, name, "academic_attempt_pct")) is not None else None,
            # Academic pass %: same pattern — assessment_df first, then skill_graded fallback.
            "Academic Assessments Pass %": (
                _assessment_pass_pct(name, "Graded Assessment")
                or (round(v, 1) if (v := _get(skill_graded_data, name, "academic_pass_pct")) is not None else None)
            ),
        })

    if not metric_rows:
        return timeline_df

    metric_df = pd.DataFrame(metric_rows)
    overview_df = timeline_df.merge(metric_df, on="University", how="left").reset_index(drop=True)

    # â€â€ Derived columns that need Expected Slots Till Date â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    # timeline_df already has "Expected Slots" = paced value (slots expected till today).
    # We rename that to "Expected Slots Till Date", then set "Expected Slots" = full-semester total.
    overview_df["Deviation %"] = overview_df.apply(
        lambda r: round(
            (float(r["Planned slots delivered till date"]) - float(r["Planned content slots till date"]))
            / float(r["Planned content slots till date"]) * 100, 1
        )
        if pd.notna(r.get("Planned content slots till date")) and float(r.get("Planned content slots till date", 0) or 0) != 0
        else None,
        axis=1,
    )
    # Practice Delivery %, Module Quiz Conduction %, Skill Assessment Conduction %
    # are already computed per-institute in fetch_session_delivery_metrics and
    # stored directly in metric_rows -- no post-merge calculation needed.

    # â€â€ Rename and filter â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
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
            "Delivery capacity slots",
            "Planned content slots",
            "Planned content slots till date",
            "Planned slots delivered till date",
            "Deviation %",
            "Class Room Quizzes Attempt %",
            "Class Room Quizzes Pass %",
            "Lecture Delivery %",
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
        "skill_graded_sem1": format_table_ref(get_config("BQ_SKILL_GRADED_SEM1_TABLE", DEFAULT_SKILL_GRADED_SEM1_TABLE), DEFAULT_SKILL_GRADED_SEM1_TABLE),
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


@st.cache_data(ttl=600, show_spinner=False)
def fetch_matching_batch_names(table_ref: str, batch_hint: str) -> list[str]:
    """
    Query distinct batch_name values from a table and return those that
    loosely match the selected batch (e.g. 'NIAT 25' matches 'NIAT 25',
    'NIAT25', 'Batch NIAT 25', etc.).
    Returns a list of exact values found in the table.
    """
    if not batch_hint or not batch_hint.strip():
        return []
    hint = batch_hint.strip().lower().replace(" ", "")
    try:
        sql = f"SELECT DISTINCT TRIM(CAST(batch_name AS STRING)) AS batch_name FROM {table_ref} WHERE batch_name IS NOT NULL"
        df = run_query(sql)
        if df.empty or "batch_name" not in df.columns:
            return []
        matches = [
            str(v) for v in df["batch_name"].dropna()
            if hint in str(v).lower().replace(" ", "")
        ]
        return matches
    except Exception:
        return []


def build_batch_filter_sql(table_ref: str, batch: str, alias_col: str) -> str:
    """
    Returns a SQL snippet filtering alias_col by the actual batch names found
    in the table, e.g.: TRIM(CAST(q.batch_name AS STRING)) IN ('NIAT 25', 'niat25')
    Falls back to a LIKE pattern if no exact matches found.
    """
    if not batch or not batch.strip():
        return ""
    exact = fetch_matching_batch_names(table_ref, batch)
    if exact:
        quoted = ", ".join(f"'{sql_escape(v)}'" for v in exact)
        return f"TRIM(CAST({alias_col} AS STRING)) IN ({quoted})"
    # Fallback: LIKE pattern
    return f"LOWER(TRIM(CAST({alias_col} AS STRING))) LIKE '%{sql_escape(batch.strip().lower())}%'"


def module_quiz_name_filter_sql(expr: str) -> str:
    """
    Match module quiz labels from schedule-like columns.
    Rule: starts with quiz or contains module anywhere.
    """
    lowered = f"LOWER(COALESCE({expr}, ''))"
    return f"({lowered} LIKE 'quiz%' OR {lowered} LIKE '%module%')"


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
    """
    Build the per-course delivery DataFrame using portal_courses as the canonical
    course list and session_adherence as the session source, joined via
    session_adherence.semester_course_id = REPLACE(portal_courses.sem_course_id, '-', '').
    Returns an extra 'sem_course_id' column (UUID without dashes) for ID-based drill-downs.
    """
    refs = get_table_refs()
    sem_num = "1" if "1" in semester else ("2" if "2" in semester else "")

    # portal_courses filters
    portal_where = [
        "TRIM(COALESCE(p.institute_name, '')) != ''",
        "TRIM(COALESCE(p.sem_course_title, '')) != ''",
        "TRIM(COALESCE(p.sem_course_id, '')) != ''",
    ]
    if sem_num:
        portal_where.append(f"LOWER(COALESCE(p.semester_title, '')) LIKE '%semester {sem_num}%'")
    if batch and batch.strip():
        portal_where.append(batch_sql_filter(batch, "p.batch_name"))

    # session_adherence filters (primary)
    # NOTE: do NOT apply get_semester_window_clause here — it creates a strict institute-name
    # whitelist that excludes universities whose DB name differs from the hardcoded key.
    sa_where = [
        "TRIM(COALESCE(sa.semester_course_id, '')) != ''",
        "TRIM(COALESCE(sa.session_name_enum, '')) != ''",
    ]
    if batch and batch.strip():
        sa_where.append(batch_sql_filter(batch, "sa.batch_name"))

    # Targeted supplement: date range for scoping SA data to this semester
    _sem_range = fetch_semester_actual_date_range(batch, semester)
    _sa_supp_date = f"AND DATE(sa2.session_date) BETWEEN '{_sem_range[0]}' AND '{_sem_range[1]}'" if _sem_range else ""
    _sa_supp_batch = f"AND {batch_sql_filter(batch, 'sa2.batch_name')}" if (batch and batch.strip()) else ""

    sql = f"""
        WITH portal AS (
          SELECT DISTINCT
            TRIM(p.institute_name)                        AS institute,
            REPLACE(p.sem_course_id, '-', '')             AS sem_course_id,
            TRIM(p.sem_course_title)                      AS course
          FROM {refs["portal_courses"]} p
          WHERE {' AND '.join(portal_where)}
        ),
        sa_units AS (
          SELECT
            TRIM(COALESCE(sa.semester_course_id, ''))              AS sem_course_id,
            TRIM(sa.session_type)                                   AS session_type,
            TRIM(sa.session_name_enum)                             AS session_name_enum,
            COALESCE(NULLIF(TRIM(sa.section_name), ''), 'Unknown') AS section,
            MAX(sa.total_sessions_planned)                         AS max_planned,
            MAX(sa.total_sessions_delivered)                       AS max_delivered,
            MAX(DATE(sa.session_date))                             AS last_date
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(sa_where)}
          GROUP BY sa.semester_course_id, session_type, session_name_enum, section
        ),
        joined AS (
          -- portal_courses drives the institute+course list; LEFT JOIN gets session data.
          -- Universities in portal_courses but missing from session_adherence still appear (sessions=0).
          SELECT
            p.course,
            p.institute,
            COALESCE(su.section, 'Unknown')         AS section,
            p.sem_course_id,
            COALESCE(su.session_type, '')            AS session_type,
            COALESCE(su.session_name_enum, '')       AS session_name_enum,
            COALESCE(su.max_planned, 0)              AS max_planned,
            COALESCE(su.max_delivered, 0)            AS max_delivered,
            su.last_date
          FROM portal p
          LEFT JOIN sa_units su ON su.sem_course_id = p.sem_course_id
        ),
        sa_targeted AS (
          -- Targeted fallback for universities that may be in session_adherence but not portal_courses.
          -- Uses keyword matching on institute_name mapped to canonical names.
          -- Scoped to semester date range to avoid pulling other semesters' data.
          SELECT DISTINCT
            CASE
              WHEN LOWER(TRIM(sa2.institute_name)) LIKE '%annamacharya%'
                THEN 'Annamacharya University'
              WHEN LOWER(TRIM(sa2.institute_name)) LIKE '%chalapathy%'
                OR  LOWER(TRIM(sa2.institute_name)) LIKE '%chalapathi%'
                THEN 'Chalapathy (CITY)'
              WHEN LOWER(TRIM(sa2.institute_name)) LIKE '%noida international%'
                THEN 'Noida International University'
              WHEN LOWER(TRIM(sa2.institute_name)) LIKE '%maritime%'
                OR  LOWER(TRIM(sa2.institute_name)) LIKE '%amet%'
                THEN 'AMET'
            END AS institute,
            TRIM(COALESCE(sa2.semester_course_id, '')) AS sem_course_id
          FROM {refs["session_adherence"]} sa2
          WHERE (
               LOWER(TRIM(sa2.institute_name)) LIKE '%annamacharya%'
            OR LOWER(TRIM(sa2.institute_name)) LIKE '%chalapathy%'
            OR LOWER(TRIM(sa2.institute_name)) LIKE '%chalapathi%'
            OR LOWER(TRIM(sa2.institute_name)) LIKE '%noida international%'
            OR LOWER(TRIM(sa2.institute_name)) LIKE '%maritime%'
            OR LOWER(TRIM(sa2.institute_name)) LIKE '%amet%'
          )
          AND TRIM(COALESCE(sa2.semester_course_id, '')) != ''
          AND TRIM(COALESCE(sa2.session_name_enum, '')) != ''
          {_sa_supp_batch}
          {_sa_supp_date}
          AND TRIM(COALESCE(sa2.semester_course_id, '')) NOT IN (SELECT sem_course_id FROM portal)
        ),
        joined_targeted AS (
          SELECT
            ''                                 AS course,
            st.institute,
            COALESCE(su.section, 'Unknown')    AS section,
            st.sem_course_id,
            COALESCE(su.session_type, '')      AS session_type,
            COALESCE(su.session_name_enum, '') AS session_name_enum,
            COALESCE(su.max_planned, 0)        AS max_planned,
            COALESCE(su.max_delivered, 0)      AS max_delivered,
            su.last_date
          FROM sa_targeted st
          LEFT JOIN sa_units su ON su.sem_course_id = st.sem_course_id
          WHERE st.institute IS NOT NULL
        ),
        all_joined AS (
          SELECT * FROM joined
          UNION ALL
          SELECT * FROM joined_targeted
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
          j.course,
          j.institute,
          j.section,
          j.session_type,
          COUNT(DISTINCT NULLIF(j.session_name_enum, '')) AS sessions,
          COALESCE(r.students, 0) AS students,
          ROUND(
            100 * SAFE_DIVIDE(
              COUNT(DISTINCT IF(j.max_delivered > 0, NULLIF(j.session_name_enum, ''), NULL)),
              NULLIF(COUNT(DISTINCT NULLIF(j.session_name_enum, '')), 0)
            ), 2
          ) AS completion,
          0 AS avg_time,
          0 AS p80_time,
          COALESCE(rc.section_count, 0) AS section_count,
          '{sql_escape(batch)}' AS batch,
          '{sql_escape(semester)}' AS semester,
          CAST(MAX(j.last_date) AS STRING) AS report_date,
          j.sem_course_id
        FROM all_joined j
        LEFT JOIN roster r
          ON r.institute = j.institute
          AND r.section = j.section
        LEFT JOIN roster_counts rc
          ON rc.institute = j.institute
        GROUP BY course, institute, section, session_type, students, section_count, sem_course_id
        ORDER BY institute, section, course
    """
    return run_query(sql)


@st.cache_data(ttl=600, show_spinner=False)
def fetch_planned_content_slots(batch: str, semester: str) -> pd.DataFrame:
    # If hardcoded overrides exist for this semester, use them directly
    overrides = PLANNED_CONTENT_SLOTS_OVERRIDES.get(semester)
    if overrides:
        rows = [
            {"institute": inst, "planned_content_slots": slots}
            for inst, slots in overrides.items()
        ]
        return pd.DataFrame(rows)

    refs = get_table_refs()
    where_clauses = ["TRIM(COALESCE(s.institute_name, '')) != ''"]
    window_clause = get_semester_window_clause(semester, batch, "s.institute_name", "DATE(s.session_date)")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "s.batch_name"))

    sql = f"""
        SELECT
          s.institute_name AS institute,
          COUNT(DISTINCT s.session_id) AS planned_content_slots
        FROM {refs["schedule"]} s
        WHERE {' AND '.join(where_clauses)}
          AND UPPER(CAST(s.session_type AS STRING)) IN ('LECTURE', 'PRACTICE', 'EXAM')
        GROUP BY institute
        HAVING planned_content_slots > 0
        ORDER BY institute
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
    if batch and batch.strip() and batch_col:
        where_clauses.append(batch_sql_filter(batch, f"p.{bq_column(batch_col)}"))

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
      derived_unit_type, best_attempt_percentage_score, session_date

    Classification via derived_unit_type:
      CLASSROOM_QUIZ                            â†' classroom category
      MODULE_QUIZ | COURSE_QUIZ                 â†' module category

    Module Quiz Pass %: passed student-quiz pairs / attempted student-quiz pairs
    across module/course quizzes at the university.
    """
    refs = get_table_refs()
    where_clauses = ["TRIM(COALESCE(q.institute_name, '')) != ''"]
    window_clause = get_semester_window_clause(semester, batch, "q.institute_name", "q.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "q.batch_name"))

    where_str = ' AND '.join(where_clauses)

    sql = f"""
        WITH institute_roster AS (
          SELECT
            u.institute_name AS institute,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY institute
        ),
        quiz_totals AS (
          -- All quiz attempt counts grouped by institute.
          --
          -- Classroom Quiz Attempt %:
          --   numerator   = COUNT(DISTINCT user_id || quiz_id) -- studentÃ—quiz pairs actually attempted
          --   denominator = total_students Ã— COUNT(DISTINCT classroom quiz_id)
          --   e.g. 100 students, 3 quizzes â†' max 300 pairs; 150 attempted â†' 50%
          --
          -- Classroom Quiz Pass %:
          --   numerator   = pairs where best_attempt_percentage_score >= 80
          --   denominator = total attempted pairs (classroom_pairs_attempted)
          --
          -- Module Quiz Participation %:
          --   numerator   = COUNT(DISTINCT user_id || quiz_id) for module quiz types
          --   denominator = total_students Ã— COUNT(DISTINCT module quiz_id)
          SELECT
            q.institute_name AS institute,
            -- Classroom: unique students who attempted at least one classroom quiz
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ',
              q.user_id, NULL))
              AS classroom_students_attempted,
            -- Classroom: unique studentÃ—quiz pairs attempted
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ',
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS classroom_pairs_attempted,
            -- Classroom: unique quiz IDs (needed for denominator)
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ',
              q.quiz_id, NULL))
              AS classroom_quiz_count,
            -- Classroom: pairs PASSED -- use platform result if available, else score >= 80
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ'
              AND (
                UPPER(TRIM(CAST(q.best_attempt_evaluation_result AS STRING))) IN ('PASS', 'PASSED')
                OR (
                  (q.best_attempt_evaluation_result IS NULL
                    OR TRIM(CAST(q.best_attempt_evaluation_result AS STRING)) = '')
                  AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                )
              ),
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS classroom_passed,
            -- Classroom: pairs with score >= 60
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ'
              AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 60,
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS classroom_passed_60,
            -- Classroom: pairs with score > 80
            COUNT(DISTINCT IF(q.derived_unit_type = 'CLASSROOM_QUIZ'
              AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) > 80,
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS classroom_passed_80,
            -- Module: unique quiz IDs (for denominator and conducted count)
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ'),
              q.quiz_id, NULL))
              AS module_quiz_count,
            -- Module: unique students who attempted at least one module/course quiz
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ'),
              q.user_id, NULL))
              AS module_students_attempted,
            -- Module: unique studentÃ—quiz pairs attempted
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ'),
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS module_pairs_attempted,
            -- Module: pairs PASSED -- use platform result if available, else score >= 80
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ')
              AND (
                UPPER(TRIM(CAST(q.best_attempt_evaluation_result AS STRING))) IN ('PASS', 'PASSED')
                OR (
                  (q.best_attempt_evaluation_result IS NULL
                    OR TRIM(CAST(q.best_attempt_evaluation_result AS STRING)) = '')
                  AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                )
              ),
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS module_passed,
            -- Module: pairs with score >= 60
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ')
              AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 60,
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS module_passed_60,
            -- Module: pairs with score > 80
            COUNT(DISTINCT IF(q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ')
              AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) > 80,
              CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)), NULL))
              AS module_passed_80
          FROM {refs["quiz_attempts"]} q
          WHERE {where_str}
            AND q.derived_unit_type IN ('CLASSROOM_QUIZ', 'MODULE_QUIZ', 'COURSE_QUIZ')
          GROUP BY q.institute_name
        )
        SELECT
          qt.institute,
          -- Classroom Attendance % = (student×quiz pairs attempted) / (students × total quizzes)
          ROUND(SAFE_DIVIDE(qt.classroom_pairs_attempted,
                            NULLIF(ir.total_students * qt.classroom_quiz_count, 0)) * 100, 1) AS classroom_quiz_attempt_pct,
          -- Classroom Pass % (platform best_attempt_evaluation_result = 'PASS')
          ROUND(SAFE_DIVIDE(qt.classroom_passed,
                            NULLIF(qt.classroom_pairs_attempted, 0)) * 100, 1)                AS classroom_quiz_pass_pct,
          -- Classroom Pass % at >= 60 threshold
          ROUND(SAFE_DIVIDE(qt.classroom_passed_60,
                            NULLIF(qt.classroom_pairs_attempted, 0)) * 100, 1)                AS classroom_quiz_pass_60_pct,
          -- Classroom Pass % at > 80 threshold
          ROUND(SAFE_DIVIDE(qt.classroom_passed_80,
                            NULLIF(qt.classroom_pairs_attempted, 0)) * 100, 1)                AS classroom_quiz_pass_80_pct,
          qt.module_quiz_count                                                                 AS module_quiz_conducted,
          -- Module Attendance % = (student×quiz pairs attempted) / (students × total module quizzes)
          ROUND(SAFE_DIVIDE(qt.module_pairs_attempted,
                            NULLIF(ir.total_students * qt.module_quiz_count, 0)) * 100, 1)    AS module_quiz_participation_pct,
          -- Module Pass % (platform best_attempt_evaluation_result = 'PASS')
          ROUND(SAFE_DIVIDE(qt.module_passed,
                            NULLIF(qt.module_pairs_attempted, 0)) * 100, 1)                   AS module_quiz_pass_pct,
          -- Module Pass % at >= 60 threshold
          ROUND(SAFE_DIVIDE(qt.module_passed_60,
                            NULLIF(qt.module_pairs_attempted, 0)) * 100, 1)                   AS module_quiz_pass_60_pct,
          -- Module Pass % at > 80 threshold
          ROUND(SAFE_DIVIDE(qt.module_passed_80,
                            NULLIF(qt.module_pairs_attempted, 0)) * 100, 1)                   AS module_quiz_pass_80_pct
        FROM quiz_totals qt
        LEFT JOIN institute_roster ir ON ir.institute = qt.institute
        ORDER BY qt.institute
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_quiz_metrics error: {e}")
        return pd.DataFrame(columns=["institute", "classroom_quiz_attempt_pct",
                                     "classroom_quiz_pass_pct", "classroom_quiz_pass_60_pct", "classroom_quiz_pass_80_pct",
                                     "module_quiz_conducted", "module_quiz_participation_pct",
                                     "module_quiz_pass_pct", "module_quiz_pass_60_pct", "module_quiz_pass_80_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_practice_completion(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute practice completion metrics from unlocked_units_completion_details.

    Actual schema used:
      institute_name, section_name, batch_name, user_id, unit_id,
      unit_type ('PRACTICE'), derived_unit_type ('MCQ_PRACTICE'),
      unit_completion_status ('COMPLETED' | 'IN_PROGRESS' | 'YET_TO_START'), session_date

    Practice Completion % = completed student-practice-unit pairs /
    all available student-practice-unit pairs.
    """
    refs = get_table_refs()
    where_clauses = [
        "TRIM(COALESCE(uu.institute_name, '')) != ''",
        "uu.unit_type = 'PRACTICE'",
    ]
    window_clause = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "uu.batch_name"))

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
          -- StudentÃ—practice-unit pairs completed and available, per institute.
          SELECT
            uu.institute_name AS institute,
            COUNT(DISTINCT IF(uu.unit_completion_status = 'COMPLETED',
              CONCAT(CAST(uu.user_id AS STRING), '||', CAST(uu.unit_id AS STRING)), NULL)) AS completed_practice_pairs,
            COUNT(DISTINCT uu.unit_id) AS practice_unit_count
          FROM {refs["unlocked_units"]} uu
          WHERE {' AND '.join(where_clauses)}
          GROUP BY uu.institute_name
        )
        SELECT
          pc.institute,
          -- Practice Completion %: completed studentÃ—practice sessions / available studentÃ—practice sessions
          ROUND(SAFE_DIVIDE(pc.completed_practice_pairs, NULLIF(ir.total_students * pc.practice_unit_count, 0)) * 100, 1) AS practice_completion_pct
        FROM practice_completed pc
        LEFT JOIN institute_roster ir ON ir.institute = pc.institute
        ORDER BY pc.institute
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["institute", "practice_completion_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_completion_by_course(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-course student content completion from unlocked_units.
    Completion % = completed studentÃ—unit pairs / available studentÃ—unit pairs.
    """
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(uu.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    window_clause = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "uu.batch_name"))
    if section:
        where_clauses.append(f"LOWER(TRIM(COALESCE(uu.section_name, ''))) = LOWER('{sql_escape(section)}')")

    content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
    content_cols      = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
    content_cid_col   = first_existing_column(content_cols, ["portal_course_id", "course_id"])

    if content_cid_col:
        content_cte = build_content_subquery_with_course_id(refs["content"], content_cid_col)
        extra_select = "MAX(c.portal_course_id) AS portal_course_id,"
    else:
        content_cte = build_content_subquery(refs["content"])
        extra_select = "CAST(NULL AS STRING) AS portal_course_id,"

    roster_where = [f"LOWER(TRIM(COALESCE(u.institute_name, ''))) = LOWER('{sql_escape(institute)}')"]
    if batch and batch.strip():
        roster_where.append(batch_sql_filter(batch, "u.batch_name"))
    if section:
        roster_where.append(f"LOWER(TRIM(COALESCE(u.section_name, ''))) = LOWER('{sql_escape(section)}')")

    sql = f"""
        WITH
        content AS (
          {content_cte}
        ),
        roster AS (
          SELECT COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE {' AND '.join(roster_where)}
        ),
        course_units AS (
          SELECT
            c.course_title,
            {extra_select}
            COUNT(DISTINCT uu.unit_id) AS unit_count,
            COUNT(DISTINCT IF(uu.unit_completion_status = 'COMPLETED',
              CONCAT(CAST(uu.user_id AS STRING), '||', CAST(uu.unit_id AS STRING)), NULL)) AS completed_pairs
          FROM {refs["unlocked_units"]} uu
          INNER JOIN content c ON uu.unit_id = c.unit_id
          WHERE {' AND '.join(where_clauses)}
            AND TRIM(COALESCE(c.course_title, '')) != ''
          GROUP BY c.course_title
        )
        SELECT
          cu.course_title,
          cu.portal_course_id,
          cu.completed_pairs,
          cu.unit_count,
          r.total_students,
          ROUND(SAFE_DIVIDE(cu.completed_pairs, NULLIF(cu.unit_count * r.total_students, 0)) * 100, 1) AS completion_pct
        FROM course_units cu
        CROSS JOIN roster r
        ORDER BY cu.course_title
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_course_completion_by_course error: {e}")
        return pd.DataFrame(columns=["course_title", "portal_course_id", "completed_pairs", "unit_count", "total_students", "completion_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_practice_completion_by_course(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-course practice completion % from unlocked_units (unit_type='PRACTICE').

    Practice Completion % = completed studentÃ—PRACTICE-unit pairs /
                            (total_students Ã— distinct PRACTICE unit count per course)

    Mirrors fetch_practice_completion() but scoped to course level via content join.
    Columns returned: course_title, practice_completion_pct
    """
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(uu.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "uu.unit_type = 'PRACTICE'",
    ]
    window_clause = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "uu.batch_name"))
    if section:
        where_clauses.append(f"LOWER(TRIM(COALESCE(uu.section_name, ''))) = LOWER('{sql_escape(section)}')")

    content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
    content_cols      = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
    content_cid_col   = first_existing_column(content_cols, ["portal_course_id", "course_id"])
    content_cte       = (build_content_subquery_with_course_id(refs["content"], content_cid_col)
                         if content_cid_col else build_content_subquery(refs["content"]))

    roster_where = [f"LOWER(TRIM(COALESCE(u.institute_name, ''))) = LOWER('{sql_escape(institute)}')"]
    if batch and batch.strip():
        roster_where.append(batch_sql_filter(batch, "u.batch_name"))
    if section:
        roster_where.append(f"LOWER(TRIM(COALESCE(u.section_name, ''))) = LOWER('{sql_escape(section)}')")

    sql = f"""
        WITH
        content AS ( {content_cte} ),
        roster AS (
          SELECT COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE {' AND '.join(roster_where)}
        ),
        practice_units AS (
          SELECT
            c.course_title,
            COUNT(DISTINCT uu.unit_id) AS practice_unit_count,
            COUNT(DISTINCT IF(uu.unit_completion_status = 'COMPLETED',
              CONCAT(CAST(uu.user_id AS STRING), '||', CAST(uu.unit_id AS STRING)), NULL))
              AS completed_practice_pairs
          FROM {refs["unlocked_units"]} uu
          INNER JOIN content c ON uu.unit_id = c.unit_id
          WHERE {' AND '.join(where_clauses)}
            AND TRIM(COALESCE(c.course_title, '')) != ''
          GROUP BY c.course_title
        )
        SELECT
          pu.course_title,
          ROUND(SAFE_DIVIDE(
            pu.completed_practice_pairs,
            NULLIF(r.total_students * pu.practice_unit_count, 0)
          ) * 100, 1) AS practice_completion_pct
        FROM practice_units pu
        CROSS JOIN roster r
        ORDER BY pu.course_title
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["course_title", "practice_completion_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_delivery_stats(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-course planned/delivered totals and LPE-style unit counts for a single institute.

    Designed (lecture_slots, practice_slots, exam_slots):
      Source: session_adherence joined via sem_course_id — COUNT(DISTINCT session_name_enum)
      No date filter so all designed units are counted regardless of conduction status.

    Scheduled (lec_scheduled, prac_scheduled, mq_scheduled):
      Source: schedule table — COUNT(DISTINCT session_id WHERE session_status IN
              COMPLETED / DELIVERED / CONDUCTED) averaged across sections.
      This is a direct count, NOT a derived Designed × Delivery% formula.
    """
    refs = get_table_refs()
    sem_num = "1" if "1" in semester else ("2" if "2" in semester else "")
    _empty = pd.DataFrame(columns=[
        "course", "sem_course_id", "total_planned", "total_delivered",
        "lecture_slots", "practice_slots", "exam_slots", "adherence_pct",
        "lec_scheduled", "prac_scheduled", "mq_scheduled",
    ])

    # ── Portal WHERE ──────────────────────────────────────────────────────────
    portal_where = [
        f"LOWER(TRIM(COALESCE(p.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "TRIM(COALESCE(p.sem_course_title, '')) != ''",
    ]
    if sem_num:
        portal_where.append(f"LOWER(COALESCE(p.semester_title, '')) LIKE '%semester {sem_num}%'")
    if batch and batch.strip():
        portal_where.append(batch_sql_filter(batch, "p.batch_name"))

    # ── Session adherence WHERE (Designed counts — no date filter) ────────────
    # NOTE: no get_semester_window_clause here — the sem_course_id JOIN with
    # portal_courses already scopes to the correct semester. A date filter would
    # exclude quizzes designed but not yet conducted.
    sa_where = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "TRIM(COALESCE(sa.semester_course_id, '')) != ''",
    ]
    if batch and batch.strip():
        sa_where.append(batch_sql_filter(batch, "sa.batch_name"))
    if section:
        sa_where.append(f"LOWER(TRIM(COALESCE(sa.section_name, ''))) = LOWER('{sql_escape(section)}')")

    # ── Part 1: Designed counts from session_adherence ────────────────────────
    sa_sql = f"""
        WITH portal AS (
          SELECT DISTINCT
            REPLACE(p.sem_course_id, '-', '') AS sem_course_id,
            TRIM(p.sem_course_title)          AS course
          FROM {refs["portal_courses"]} p
          WHERE {' AND '.join(portal_where)}
        ),
        slots AS (
          SELECT
            TRIM(COALESCE(sa.semester_course_id, '')) AS sem_course_id,
            sa.section_name                           AS section,
            sa.session_type,
            sa.session_name_enum,
            MAX(sa.total_sessions_planned)            AS planned,
            MAX(sa.total_sessions_delivered)          AS delivered
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(sa_where)}
          GROUP BY sem_course_id, section, session_type, session_name_enum
        ),
        joined AS (
          SELECT p.course, p.sem_course_id, s.section, s.session_type,
                 s.session_name_enum, s.planned, s.delivered
          FROM portal p
          JOIN slots s ON s.sem_course_id = p.sem_course_id
        ),
        section_stats AS (
          SELECT
            course, sem_course_id, section,
            SUM(planned)                                                              AS total_planned,
            COUNT(DISTINCT IF(COALESCE(delivered, 0) > 0, session_name_enum, NULL))  AS total_delivered,
            COUNT(DISTINCT IF(session_type = 'LECTURE',  session_name_enum, NULL))   AS lecture_slots,
            COUNT(DISTINCT IF(session_type = 'PRACTICE', session_name_enum, NULL))   AS practice_slots,
            -- All EXAM sessions = module quizzes (consistent with institute level)
            COUNT(DISTINCT IF(session_type = 'EXAM',     session_name_enum, NULL))   AS exam_slots
          FROM joined
          GROUP BY course, sem_course_id, section
        )
        SELECT
          course, sem_course_id,
          AVG(total_planned)   AS total_planned,
          AVG(total_delivered) AS total_delivered,
          AVG(lecture_slots)   AS lecture_slots,
          AVG(practice_slots)  AS practice_slots,
          AVG(exam_slots)      AS exam_slots,
          ROUND(SAFE_DIVIDE(AVG(total_delivered), NULLIF(AVG(total_planned), 0)) * 100, 1) AS adherence_pct
        FROM section_stats
        GROUP BY course, sem_course_id
        ORDER BY course
    """
    try:
        designed_df = run_query(sa_sql)
    except Exception as e:
        st.error(f"fetch_course_delivery_stats error: {e}")
        return _empty

    if designed_df.empty:
        return _empty

    return designed_df


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_weekly_delivery(batch: str, semester: str, institute: str, course_title, section: str = "", sem_course_id: str = "") -> pd.DataFrame:
    """
    Returns week-by-week planned/delivered/adherence for a single institute+course.
    course_title may be a str or tuple[str, ...] (multi-title subjects).
    Derives weekly delta from the cumulative totals in session_adherence.
    When sem_course_id is provided, filters by semester_course_id (ID-based, no text matching).
    """
    if isinstance(course_title, str):
        course_title = (course_title,)
    refs = get_table_refs()
    where_clauses = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    if sem_course_id:
        clean_id = sem_course_id.replace("-", "")
        where_clauses.append(f"TRIM(COALESCE(sa.semester_course_id, '')) = '{sql_escape(clean_id)}'")
    else:
        titles_in = ", ".join(f"LOWER('{sql_escape(t)}')" for t in course_title)
        where_clauses.append(f"LOWER(TRIM(COALESCE(sa.course_title, ''))) IN ({titles_in})")
    window_clause = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "sa.batch_name"))
    if section:
        where_clauses.append(f"LOWER(TRIM(COALESCE(sa.section_name, ''))) = LOWER('{sql_escape(section)}')")
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
def fetch_course_session_units(batch: str, semester: str, institute: str, course_title, section: str = "", sem_course_id: str = "") -> pd.DataFrame:
    """
    Returns per-unit delivery stats using session_adherence.session_name_enum as the unit name.
    Also enriches PRACTICE units with student-level completion from unlocked_units.

    course_title may be a single str or a tuple[str, ...] — used for unlocked_units filtering.
    When sem_course_id is provided, session_adherence is filtered by semester_course_id (ID-based).

    session_adherence gives:  unit name (session_name_enum), session_type, planned, delivered
    unlocked_units gives:     student completion count per unit_id (PRACTICE units)
    content bridges:          unit_id — course_title for filtering unlocked_units by course

    Columns: unit, session_type, section, total_sessions, delivered_sessions, completion_pct,
             total_students, students_completed  (NaN for non-PRACTICE types)
    """
    if isinstance(course_title, str):
        course_title = (course_title,)
    titles_in = ", ".join(f"LOWER('{sql_escape(t)}')" for t in course_title)
    refs = get_table_refs()
    sa_where = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "TRIM(COALESCE(sa.session_name_enum, '')) != ''",
    ]
    if sem_course_id:
        clean_id = sem_course_id.replace("-", "")
        sa_where.append(f"TRIM(COALESCE(sa.semester_course_id, '')) = '{sql_escape(clean_id)}'")
    else:
        sa_where.append(f"LOWER(TRIM(COALESCE(sa.course_title, ''))) IN ({titles_in})")
    sa_window = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if sa_window:
        sa_where.append(sa_window)
    if batch and batch.strip():
        sa_where.append(batch_sql_filter(batch, "sa.batch_name"))
    if section:
        sa_where.append(f"LOWER(TRIM(COALESCE(sa.section_name, ''))) = LOWER('{sql_escape(section)}')")

    uu_where = [
        f"LOWER(TRIM(COALESCE(uu.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    uu_window = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if uu_window:
        uu_where.append(uu_window)
    if batch and batch.strip():
        uu_where.append(batch_sql_filter(batch, "uu.batch_name"))
    if section:
        uu_where.append(f"LOWER(TRIM(COALESCE(uu.section_name, ''))) = LOWER('{sql_escape(section)}')")

    sql = f"""
        WITH
        -- â€â€ Session delivery (all unit types) from session_adherence â€â€â€â€â€â€â€â€â€â€
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
        -- â€â€ Student-level practice completion from unlocked_units â€â€â€â€â€â€â€â€â€â€â€â€â€
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
        -- â€â€ Final: delivery stats joined with student completion where available
        SELECT
          su.unit,
          su.session_type,
          su.section,
          su.total_sessions,
          su.delivered_sessions,
          ROUND(LEAST(SAFE_DIVIDE(su.delivered_sessions, NULLIF(su.total_sessions, 0)) * 100, 100.0), 1) AS completion_pct,
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
def fetch_course_session_units_schedule(
    batch: str,
    semester: str,
    institute: str,
    course_title,
    section: str = "",
    sem_course_id: str = "",
) -> pd.DataFrame:
    """
    Fetches per-unit delivery data for the LPE tab from the SCHEDULE table.

    Path: institute_name → subject (course_title / sem_course_id) → session_id
          session_id carries session_type (LECTURE / PRACTICE / EXAM) and
          session_status (COMPLETED / DELIVERED / CONDUCTED).

    This avoids the session_adherence name-filter problem where EXAM sessions
    whose session_name_enum doesn't match 'quiz%' or '%module%' are silently
    dropped.

    Planned  = COUNT(DISTINCT session_id)
    Delivered = COUNT(DISTINCT session_id WHERE status IN completed statuses)

    Also enriches PRACTICE units with student completion from unlocked_units
    (same as fetch_course_session_units).

    Returns columns: unit, session_type, section, total_sessions,
                     delivered_sessions, completion_pct,
                     total_students, students_completed
    """
    if isinstance(course_title, str):
        course_title = (course_title,)

    refs = get_table_refs()

    # ── Detect course-title and status columns in schedule table ─────────────
    sched_table_ref = get_config("BQ_SCHEDULE_TABLE", DEFAULT_SCHEDULE_TABLE)
    sched_cols = fetch_table_columns(sched_table_ref, DEFAULT_SCHEDULE_TABLE)
    status_col = first_existing_column(sched_cols, ["session_status", "session_delivery_status", "delivery_status", "status"]) or "session_status"
    course_col = first_existing_column(
        sched_cols,
        ["semester_course_title", "course_title", "subject_name", "course_name", "sem_course_title"],
    )
    if not course_col:
        # schedule table has no recognisable course column — fall back gracefully
        return pd.DataFrame(columns=["unit", "session_type", "section", "total_sessions",
                                     "delivered_sessions", "completion_pct",
                                     "total_students", "students_completed"])

    # ── Schedule WHERE clauses ────────────────────────────────────────────────
    sched_where = [
        f"LOWER(TRIM(COALESCE(s.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "TRIM(COALESCE(s.session_name_enum, '')) != ''",
        "UPPER(CAST(s.session_type AS STRING)) IN ('LECTURE', 'PRACTICE', 'EXAM')",
    ]

    # Course filter: prefer sem_course_id join through portal_courses for exact match
    if sem_course_id:
        clean_id = sem_course_id.replace("-", "")
        # Join portal_courses to get the canonical course title, then match schedule
        sched_where.append(
            f"LOWER(TRIM(COALESCE(CAST(s.{course_col} AS STRING), ''))) IN ("
            f"  SELECT LOWER(TRIM(COALESCE(p.sem_course_title, ''))) "
            f"  FROM {refs['portal_courses']} p "
            f"  WHERE REPLACE(p.sem_course_id, '-', '') = '{sql_escape(clean_id)}'"
            f")"
        )
    else:
        titles_in = ", ".join(f"LOWER('{sql_escape(t)}')" for t in course_title)
        sched_where.append(
            f"LOWER(TRIM(COALESCE(CAST(s.{course_col} AS STRING), ''))) IN ({titles_in})"
        )

    sched_window = get_semester_window_clause(semester, batch, "s.institute_name", "DATE(s.session_date)")
    if sched_window:
        sched_where.append(sched_window)
    if batch and batch.strip():
        sched_where.append(batch_sql_filter(batch, "s.batch_name"))
    if section:
        sched_where.append(f"LOWER(TRIM(COALESCE(s.section_name, ''))) = LOWER('{sql_escape(section)}')")

    # ── unlocked_units WHERE (PRACTICE student completion) ────────────────────
    titles_in_uu = ", ".join(f"LOWER('{sql_escape(t)}')" for t in course_title)
    uu_where = [
        f"LOWER(TRIM(COALESCE(uu.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    uu_window = get_semester_window_clause(semester, batch, "uu.institute_name", "uu.session_date")
    if uu_window:
        uu_where.append(uu_window)
    if batch and batch.strip():
        uu_where.append(batch_sql_filter(batch, "uu.batch_name"))
    if section:
        uu_where.append(f"LOWER(TRIM(COALESCE(uu.section_name, ''))) = LOWER('{sql_escape(section)}')")

    sql = f"""
        WITH
        -- ── Schedule-based unit delivery (all types via session_id) ──────────
        schedule_units AS (
          SELECT
            TRIM(s.session_name_enum)                                       AS unit,
            UPPER(CAST(s.session_type AS STRING))                           AS session_type,
            COALESCE(NULLIF(TRIM(s.section_name), ''), 'Unknown')           AS section,
            COUNT(DISTINCT s.session_id)                                    AS total_sessions,
            COUNT(DISTINCT IF(
              UPPER(COALESCE(s.{status_col}, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              s.session_id, NULL
            ))                                                               AS delivered_sessions
          FROM {refs["schedule"]} s
          WHERE {' AND '.join(sched_where)}
          GROUP BY unit, session_type, section
        ),
        -- ── Student roster ────────────────────────────────────────────────────
        roster AS (
          SELECT
            u.institute_name,
            COALESCE(NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
            COUNT(DISTINCT u.user_id) AS total_students
          FROM {refs["users"]} u
          WHERE TRIM(COALESCE(u.institute_name, '')) != ''
          GROUP BY u.institute_name, section
        ),
        -- ── PRACTICE student completion from unlocked_units ───────────────────
        content AS (
          {build_content_subquery(refs["content"])}
        ),
        practice_completion AS (
          SELECT
            COALESCE(NULLIF(TRIM(uu.section_name), ''), 'Unknown') AS section,
            MAX(r.total_students)                                   AS total_students,
            COUNT(DISTINCT CASE WHEN uu.unit_completion_status = 'COMPLETED'
                                THEN uu.user_id END)               AS students_completed
          FROM {refs["unlocked_units"]} uu
          INNER JOIN content c ON uu.unit_id = c.unit_id
          LEFT JOIN roster r
            ON r.institute_name = uu.institute_name
           AND r.section = COALESCE(NULLIF(TRIM(uu.section_name), ''), 'Unknown')
          WHERE {' AND '.join(uu_where)}
            AND LOWER(TRIM(COALESCE(c.course_title, ''))) IN ({titles_in_uu})
          GROUP BY section
        )
        -- ── Final join ────────────────────────────────────────────────────────
        SELECT
          su.unit,
          su.session_type,
          su.section,
          su.total_sessions,
          su.delivered_sessions,
          ROUND(LEAST(SAFE_DIVIDE(su.delivered_sessions,
                NULLIF(su.total_sessions, 0)) * 100, 100.0), 1)  AS completion_pct,
          r.total_students,
          CASE WHEN su.session_type = 'PRACTICE'
               THEN pc.students_completed ELSE NULL END            AS students_completed
        FROM schedule_units su
        LEFT JOIN roster r
          ON LOWER(TRIM(r.institute_name)) = LOWER('{sql_escape(institute)}')
         AND r.section = su.section
        LEFT JOIN practice_completion pc
          ON pc.section = su.section
        ORDER BY su.session_type, su.unit
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_course_session_units_schedule error: {e}")
        return pd.DataFrame(columns=["unit", "session_type", "section", "total_sessions",
                                     "delivered_sessions", "completion_pct",
                                     "total_students", "students_completed"])



@st.cache_data(ttl=600, show_spinner=False)
def fetch_quiz_pass_by_course(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-subject quiz pass % using the schedule table LP_QUIZ approach.

    Path:
      schedule.semester_course_title (or best available course column)
      â†' resource_type = 'LP_QUIZ'
      â†' resource_id (= quiz_id in quiz_attempts)
      â†' pass % = studentÃ—quiz pairs with best_attempt_percentage_score >= 80 /
                 total attempted studentÃ—quiz pairs

    Columns returned: course_title, attempted, passed, quiz_pass_pct
    """
    refs = get_table_refs()

    # â€â€ Detect the course-title column in the schedule table â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    sched_table_ref = get_config("BQ_SCHEDULE_TABLE", DEFAULT_SCHEDULE_TABLE)
    sched_cols = fetch_table_columns(sched_table_ref, DEFAULT_SCHEDULE_TABLE)
    course_col = first_existing_column(
        sched_cols,
        ["semester_course_title", "course_title", "subject_name", "course_name", "sem_course_title"],
    )

    # â€â€ quiz_attempts WHERE clauses (institute-scoped) â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    q_where = [
        f"LOWER(TRIM(COALESCE(q.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    window_clause = get_semester_window_clause(semester, batch, "q.institute_name", "q.session_date")
    if window_clause:
        q_where.append(window_clause)
    if batch and batch.strip():
        q_where.append(batch_sql_filter(batch, "q.batch_name"))
    if section:
        q_where.append(f"LOWER(TRIM(COALESCE(q.section_name, ''))) = LOWER('{sql_escape(section)}')")

    if course_col:
        # â€â€ Primary path: schedule.{course_col} + resource_type='LP_QUIZ' â€â€â€â€â€â€
        sql = f"""
            WITH lp_quiz_ids AS (
              SELECT
                TRIM(CAST(s.{course_col} AS STRING)) AS course_title,
                CAST(s.resource_id AS STRING)         AS quiz_id
              FROM {refs["schedule"]} s
              WHERE UPPER(TRIM(CAST(s.resource_type AS STRING))) = 'LP_QUIZ'
                AND TRIM(COALESCE(CAST(s.resource_id AS STRING),    '')) != ''
                AND TRIM(COALESCE(CAST(s.{course_col} AS STRING), '')) != ''
            )
            SELECT
              r.course_title,
              COUNT(DISTINCT CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)))
                AS attempted,
              COUNT(DISTINCT CASE WHEN SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                THEN CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))
              END) AS passed,
              ROUND(SAFE_DIVIDE(
                COUNT(DISTINCT CASE WHEN SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                  THEN CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))
                END),
                NULLIF(COUNT(DISTINCT CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))), 0)
              ) * 100, 1) AS quiz_pass_pct
            FROM {refs["quiz_attempts"]} q
            JOIN lp_quiz_ids r ON CAST(q.quiz_id AS STRING) = r.quiz_id
            WHERE {' AND '.join(q_where)}
            GROUP BY r.course_title
            ORDER BY r.course_title
        """
    else:
        # â€â€ Fallback: derived_unit_type='CLASSROOM_QUIZ' + content join â€â€â€â€â€â€â€â€
        content_table_ref = get_config("BQ_CONTENT_TABLE", DEFAULT_CONTENT_TABLE)
        content_cols    = fetch_table_columns(content_table_ref, DEFAULT_CONTENT_TABLE)
        content_cid_col = first_existing_column(content_cols, ["portal_course_id", "course_id"])
        if content_cid_col:
            content_cte = build_content_subquery_with_course_id(refs["content"], content_cid_col)
        else:
            content_cte = build_content_subquery(refs["content"])
        q_where_fallback = [*q_where, "q.derived_unit_type = 'CLASSROOM_QUIZ'"]
        sql = f"""
            WITH content AS ( {content_cte} )
            SELECT
              c.course_title,
              COUNT(DISTINCT CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)))
                AS attempted,
              COUNT(DISTINCT CASE WHEN SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                THEN CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))
              END) AS passed,
              ROUND(SAFE_DIVIDE(
                COUNT(DISTINCT CASE WHEN SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                  THEN CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))
                END),
                NULLIF(COUNT(DISTINCT CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))), 0)
              ) * 100, 1) AS quiz_pass_pct
            FROM {refs["quiz_attempts"]} q
            INNER JOIN content c ON CAST(q.quiz_id AS STRING) = c.unit_id
            WHERE {' AND '.join(q_where_fallback)}
              AND TRIM(COALESCE(c.course_title, '')) != ''
            GROUP BY c.course_title
            ORDER BY c.course_title
        """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["course_title", "attempted", "passed", "quiz_pass_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_exam_delivery_by_course(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-course EXAM session conduction % from session_adherence.

    Conducted = delivery_status_vs_plan IN ('ON_TIME', 'DELIVERED_DELAYED')
    Columns returned: course_title, exam_conducted, exam_planned, exam_conduction_pct
    """
    refs = get_table_refs()

    where_clauses = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'",
        "TRIM(COALESCE(sa.course_title, '')) != ''",
        "TRIM(COALESCE(sa.session_id, '')) != ''",
    ]
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "sa.batch_name"))
    if section:
        where_clauses.append(f"LOWER(TRIM(COALESCE(sa.section_name, ''))) = LOWER('{sql_escape(section)}')")

    sql = f"""
        WITH per_section AS (
          SELECT
            TRIM(sa.course_title)                                                   AS course_title,
            COALESCE(NULLIF(TRIM(sa.section_name), ''), 'Unknown')                  AS section,
            COUNT(DISTINCT IF(
              UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                                  AS exam_conducted,
            COUNT(DISTINCT sa.session_id)                                            AS exam_planned
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(where_clauses)}
          GROUP BY course_title, section
        )
        SELECT
          course_title,
          ROUND(AVG(exam_conducted), 1) AS exam_conducted,
          ROUND(AVG(exam_planned),   1) AS exam_planned,
          ROUND(SAFE_DIVIDE(AVG(exam_conducted), NULLIF(AVG(exam_planned), 0)) * 100, 1) AS exam_conduction_pct
        FROM per_section
        GROUP BY course_title
        ORDER BY course_title
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["course_title", "exam_conducted", "exam_planned", "exam_conduction_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_course_scheduled_counts(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-course scheduled session counts directly from session_adherence.

    Scheduled = COUNT(DISTINCT session_id WHERE delivery_status_vs_plan IN ('ON_TIME', 'DELIVERED_DELAYED'))
    grouped by course_title, averaged across sections.

    Source: session_adherence table (has course_title + delivery_status_vs_plan + session_id).
    Columns: course_title, lec_scheduled, prac_scheduled, mq_scheduled
    """
    refs = get_table_refs()
    _empty = pd.DataFrame(columns=["course_title", "lec_scheduled", "prac_scheduled", "mq_scheduled"])

    where_clauses = [
        f"LOWER(TRIM(COALESCE(sa.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
        "UPPER(CAST(sa.session_type AS STRING)) IN ('LECTURE', 'PRACTICE', 'EXAM')",
        "TRIM(COALESCE(sa.course_title, '')) != ''",
        "TRIM(COALESCE(sa.session_id, '')) != ''",
    ]
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "sa.batch_name"))
    if section:
        where_clauses.append(f"LOWER(TRIM(COALESCE(sa.section_name, ''))) = LOWER('{sql_escape(section)}')")

    sql = f"""
        WITH per_section AS (
          SELECT
            TRIM(sa.course_title)                                          AS course_title,
            COALESCE(NULLIF(TRIM(sa.section_name), ''), 'Unknown')         AS section,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'LECTURE'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                         AS lec_scheduled,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'PRACTICE'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                         AS prac_scheduled,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                         AS mq_scheduled
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(where_clauses)}
          GROUP BY course_title, section
        )
        SELECT
          course_title,
          ROUND(AVG(lec_scheduled),  1) AS lec_scheduled,
          ROUND(AVG(prac_scheduled), 1) AS prac_scheduled,
          ROUND(AVG(mq_scheduled),   1) AS mq_scheduled
        FROM per_section
        GROUP BY course_title
        ORDER BY course_title
    """
    try:
        return run_query(sql)
    except Exception:
        return _empty


@st.cache_data(ttl=600, show_spinner=False)
def fetch_module_quiz_pass_by_course(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns per-subject module quiz pass % and attempt counts.

    Strategy: filter quiz_attempts where derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ'),
    then join to the content table on quiz_id = unit_id to get course_title.

    Pass logic:
      best_attempt_evaluation_result IN ('PASS', 'PASSED')
      OR (result blank/null AND best_attempt_percentage_score >= 80)

    Columns returned: course_title, attempted, passed, quiz_count, module_quiz_pass_pct
    """
    refs = get_table_refs()

    # WHERE filters for quiz_attempts (alias q)
    q_where = [
        f"q.derived_unit_type IN ('MODULE_QUIZ', 'COURSE_QUIZ', 'OTHERS')",
        f"LOWER(TRIM(COALESCE(q.institute_name, ''))) = LOWER('{sql_escape(institute)}')",
    ]
    window_clause = get_semester_window_clause(semester, batch, "q.institute_name", "q.session_date")
    if window_clause:
        q_where.append(window_clause)
    if batch and batch.strip():
        q_where.append(batch_sql_filter(batch, "q.batch_name"))
    if section:
        q_where.append(f"LOWER(TRIM(COALESCE(q.section_name, ''))) = LOWER('{sql_escape(section)}')")

    _pass_expr = """(
                UPPER(TRIM(CAST(q.best_attempt_evaluation_result AS STRING))) IN ('PASS', 'PASSED')
                OR (
                  (q.best_attempt_evaluation_result IS NULL
                    OR TRIM(CAST(q.best_attempt_evaluation_result AS STRING)) = '')
                  AND SAFE_CAST(q.best_attempt_percentage_score AS FLOAT64) >= 80
                )
              )"""

    sql = f"""
        WITH content AS (
          {build_content_subquery(refs["content"])}
        )
        SELECT
          c.course_title,
          COUNT(DISTINCT CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING)))
            AS attempted,
          COUNT(DISTINCT CASE WHEN {_pass_expr}
            THEN CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))
          END) AS passed,
          COUNT(DISTINCT q.quiz_id) AS quiz_count,
          ROUND(SAFE_DIVIDE(
            COUNT(DISTINCT CASE WHEN {_pass_expr}
              THEN CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))
            END),
            NULLIF(COUNT(DISTINCT CONCAT(CAST(q.user_id AS STRING), '||', CAST(q.quiz_id AS STRING))), 0)
          ) * 100, 1) AS module_quiz_pass_pct
        FROM {refs["quiz_attempts"]} q
        JOIN content c
          ON COALESCE(
               CAST(SAFE_CAST(q.quiz_id AS INT64) AS STRING),
               TRIM(CAST(q.quiz_id AS STRING))
             ) = TRIM(CAST(c.unit_id AS STRING))
        WHERE {' AND '.join(q_where)}
          AND TRIM(COALESCE(c.course_title, '')) != ''
        GROUP BY c.course_title
        ORDER BY c.course_title
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["course_title", "attempted", "passed", "quiz_count", "module_quiz_pass_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_session_delivery_metrics(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute delivery metrics entirely from session_adherence.

    Delivered  = delivery_status_vs_plan IN ('ON_TIME', 'DELIVERED_DELAYED')
    Planned    = all distinct session_ids (regardless of status)
    Module Quiz = EXAM sessions whose session_name_enum LIKE 'quiz%' OR '%module%'
    Skill Assess = EXAM sessions whose session_name_enum contains 'skill'
    """
    refs = get_table_refs()

    where_clauses = [
        "TRIM(COALESCE(sa.institute_name, '')) != ''",
        "TRIM(COALESCE(sa.session_id, '')) != ''",
    ]
    window_clause = get_semester_window_clause(semester, batch, "sa.institute_name", "sa.session_date")
    if window_clause:
        where_clauses.append(window_clause)
    if batch and batch.strip():
        where_clauses.append(batch_sql_filter(batch, "sa.batch_name"))

    sql = f"""
        WITH per_section AS (
          SELECT
            TRIM(sa.institute_name)                                              AS institute,
            COALESCE(NULLIF(TRIM(sa.section_name), ''), 'Unknown')               AS section,
            -- Lecture
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'LECTURE'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                               AS lecture_delivered,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'LECTURE',
              sa.session_id, NULL))                                               AS lecture_planned,
            -- Practice
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'PRACTICE'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                               AS practice_delivered,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'PRACTICE',
              sa.session_id, NULL))                                               AS practice_planned,
            -- Exam (all)
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED'),
              sa.session_id, NULL))                                               AS exam_delivered,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM',
              sa.session_id, NULL))                                               AS exam_planned,
            -- Module Quiz (EXAM whose name starts with QUIZ or contains MODULE)
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED')
              AND (LOWER(COALESCE(sa.session_name_enum, '')) LIKE 'quiz%'
                   OR LOWER(COALESCE(sa.session_name_enum, '')) LIKE '%module%'),
              sa.session_id, NULL))                                               AS mq_delivered,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'
              AND (LOWER(COALESCE(sa.session_name_enum, '')) LIKE 'quiz%'
                   OR LOWER(COALESCE(sa.session_name_enum, '')) LIKE '%module%'),
              sa.session_id, NULL))                                               AS mq_planned,
            -- Skill Assessment (EXAM whose name contains 'skill')
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'
              AND UPPER(COALESCE(sa.delivery_status_vs_plan, '')) IN ('ON_TIME', 'DELIVERED_DELAYED')
              AND REGEXP_CONTAINS(LOWER(COALESCE(sa.session_name_enum, '')), r'skill'),
              sa.session_id, NULL))                                               AS sa_delivered,
            COUNT(DISTINCT IF(
              UPPER(CAST(sa.session_type AS STRING)) = 'EXAM'
              AND REGEXP_CONTAINS(LOWER(COALESCE(sa.session_name_enum, '')), r'skill'),
              sa.session_id, NULL))                                               AS sa_planned
          FROM {refs["session_adherence"]} sa
          WHERE {' AND '.join(where_clauses)}
          GROUP BY institute, section
        ),
        per_institute AS (
          SELECT
            institute,
            SUM(lecture_delivered)  AS lecture_delivered,
            SUM(lecture_planned)    AS lecture_planned,
            SUM(practice_delivered) AS practice_delivered,
            SUM(practice_planned)   AS practice_planned,
            SUM(exam_delivered)     AS exam_delivered,
            SUM(exam_planned)       AS exam_planned,
            SUM(mq_delivered)       AS mq_delivered,
            SUM(mq_planned)         AS mq_planned,
            SUM(sa_delivered)       AS sa_delivered,
            SUM(sa_planned)         AS sa_planned
          FROM per_section
          GROUP BY institute
        )
        SELECT
          institute,
          ROUND(SAFE_DIVIDE(lecture_delivered,  NULLIF(lecture_planned,  0)) * 100, 1) AS lecture_delivery_pct,
          ROUND(SAFE_DIVIDE(practice_delivered, NULLIF(practice_planned, 0)) * 100, 1) AS practice_delivery_pct,
          ROUND(SAFE_DIVIDE(exam_delivered,     NULLIF(exam_planned,     0)) * 100, 1) AS exam_delivery_pct,
          ROUND(SAFE_DIVIDE(mq_delivered,       NULLIF(mq_planned,       0)) * 100, 1) AS module_quiz_conduction_pct,
          ROUND(SAFE_DIVIDE(sa_delivered,       NULLIF(sa_planned,       0)) * 100, 1) AS skill_conduction_pct
        FROM per_institute
        ORDER BY institute
    """
    try:
        return run_query(sql)
    except Exception:
        return pd.DataFrame(columns=["institute", "lecture_delivery_pct", "practice_delivery_pct", "exam_delivery_pct", "module_quiz_conduction_pct", "skill_conduction_pct"])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_skill_graded_metrics(batch: str, semester: str) -> pd.DataFrame:
    """
    Returns per-institute skill and academic assessment metrics.

    Table selection: dynamically discovers columns in the Sem 1 table; falls back to the
    Sem 2 (curriculum_ops) table when required columns are absent or the Sem 1 table is missing.

    Skill:    assessment_type = 'SKILL_ASSESSMENT'
    Academic: assessment_type = 'GRADED_ASSESSMENT'
    Pass:     user_section_score_percentage >= 0.80
    """
    refs = get_table_refs()
    _empty = pd.DataFrame(columns=["institute", "skill_conducted", "skill_participation_pct",
                                    "skill_pass_pct", "academic_attempt_pct", "academic_pass_pct"])

    is_sem1 = "1" in semester

    # ── Resolve table + column names dynamically ────────────────────────────────
    def _resolve_table_and_cols():
        """Returns (table_ref, date_col_expr, score_col, assessment_id_col, assessment_type_col)
           or None if we cannot resolve required columns."""
        candidates = []
        if is_sem1:
            candidates.append((refs["skill_graded_sem1"], DEFAULT_SKILL_GRADED_SEM1_TABLE))
        candidates.append((refs["skill_graded"], DEFAULT_SKILL_GRADED_TABLE))

        for tref, tdefault in candidates:
            cols = fetch_table_columns(tref, tdefault)
            if not cols:
                continue

            # Date column
            date_raw = first_existing_column(
                cols,
                ["assessment_start_date", "assessment_start_datetime",
                 "assessment_date", "start_date", "date"],
            )
            if not date_raw:
                continue
            # Wrap datetime columns with DATE()
            if "datetime" in date_raw or date_raw in ("assessment_start_datetime",):
                date_col_expr = f"DATE(sg.{date_raw})"
            else:
                date_col_expr = f"sg.{date_raw}"

            # Score percentage column
            score_col = first_existing_column(
                cols,
                ["user_section_score_percentage", "score_percentage",
                 "user_score_percentage", "percentage_score", "score_pct"],
            )
            if not score_col:
                continue

            # Assessment ID column
            asmt_id_col = first_existing_column(
                cols,
                ["assessment_id", "id", "quiz_id", "assessment_key"],
            )
            if not asmt_id_col:
                continue

            # Assessment type column
            asmt_type_col = first_existing_column(
                cols,
                ["assessment_type", "type", "session_type"],
            )
            if not asmt_type_col:
                continue

            return tref, date_col_expr, score_col, asmt_id_col, asmt_type_col

        return None

    resolved = _resolve_table_and_cols()
    if resolved is None:
        st.warning("fetch_skill_graded_metrics: could not resolve required columns in skill/graded table.")
        return _empty

    skill_table, date_col, score_col, asmt_id_col, asmt_type_col = resolved

    # ── Lookup actual batch names from the skill/graded table ──────────────────
    # Query the table itself to find what batch_name values actually exist.
    # These may be formatted differently from the UI selection (e.g. "NIAT 2025"
    # vs "NIAT 25"). We do a loose match on the batch number digit and use the
    # exact values found — no hardcoded patterns.
    _actual_batch_names: list[str] = []
    try:
        _lookup_sql = f"""
            SELECT DISTINCT
              TRIM(CAST(sg.batch_name AS STRING))       AS batch_name,
              TRIM(CAST(sg.institute_name AS STRING))   AS institute_name,
              TRIM(CAST(sg.{asmt_type_col} AS STRING))  AS assessment_type
            FROM {skill_table} sg
            WHERE sg.batch_name IS NOT NULL
              AND TRIM(CAST(sg.batch_name AS STRING)) != ''
            LIMIT 500
        """
        _lookup_df = run_query(_lookup_sql)
        if not _lookup_df.empty and "batch_name" in _lookup_df.columns:
            all_names = _lookup_df["batch_name"].dropna().unique().tolist()
            _actual_batch_names = match_batch_names_from_table(all_names, batch)
            if not _actual_batch_names:
                _actual_batch_names = [str(n) for n in all_names]
    except Exception:
        pass

    # ── Build WHERE clauses ─────────────────────────────────────────────────────
    base_where = [
        "TRIM(COALESCE(sg.institute_name, '')) != ''",
        f"sg.{score_col} IS NOT NULL",
    ]
    if _actual_batch_names:
        _quoted = ", ".join(f"'{sql_escape(n)}'" for n in _actual_batch_names)
        base_where.append(f"TRIM(CAST(sg.batch_name AS STRING)) IN ({_quoted})")
    # Scope to the correct semester using a global date range (no institute-name whitelist)
    _sg_sem_range = fetch_semester_actual_date_range(batch, semester)
    if _sg_sem_range:
        base_where.append(f"{date_col} BETWEEN '{_sg_sem_range[0]}' AND '{_sg_sem_range[1]}'")

    base_where_sql = ' AND '.join(base_where)

    # ── Lookup institute names from skill table and users table ────────────────
    # Build a Python-level mapping: skill_institute → users_institute
    # This handles cases where the same university has different name formats
    # in different tables (e.g. "AMET" in skill table vs "Academy of Maritime
    # Education & Technology" in users table).

    _skill_institutes: list[str] = []
    try:
        _si_filter = f"AND TRIM(CAST(sg.batch_name AS STRING)) IN ({', '.join(repr(n) for n in _actual_batch_names)})" if _actual_batch_names else ""
        _si_sql = f"""
            SELECT DISTINCT LOWER(TRIM(CAST(sg.institute_name AS STRING))) AS institute
            FROM {skill_table} sg
            WHERE sg.institute_name IS NOT NULL
              AND TRIM(CAST(sg.institute_name AS STRING)) != ''
              {_si_filter}
            LIMIT 500
        """
        _si_df = run_query(_si_sql)
        if not _si_df.empty:
            _skill_institutes = _si_df["institute"].dropna().tolist()
    except Exception:
        pass

    # Also build a batch filter for the users/roster table so the student
    # count denominator is scoped to the same batch as the skill data.
    _users_batch_names_for_roster: list[str] = []
    _user_institutes: list[str] = []
    try:
        _ur_sql = f"""
            SELECT DISTINCT
              TRIM(CAST(batch_name AS STRING))                  AS batch_name,
              LOWER(TRIM(CAST(institute_name AS STRING)))        AS institute
            FROM {refs["users"]}
            WHERE batch_name IS NOT NULL AND TRIM(CAST(batch_name AS STRING)) != ''
              AND institute_name IS NOT NULL AND TRIM(CAST(institute_name AS STRING)) != ''
            LIMIT 500
        """
        _ur_df = run_query(_ur_sql)
        if not _ur_df.empty:
            _all_ur = _ur_df["batch_name"].dropna().unique().tolist()
            _users_batch_names_for_roster = match_batch_names_from_table(_all_ur, batch)
            _user_institutes = _ur_df["institute"].dropna().unique().tolist()
    except Exception:
        pass

    # Build mapping: skill_institute_name → users_institute_name
    def _match_institute(skill_inst: str, user_insts: list[str]) -> str:
        """Return the users-table institute name that best matches skill_inst."""
        if skill_inst in user_insts:
            return skill_inst  # exact (case-normalized) match
        # Substring: skill name contained in user name or vice versa
        for ui in user_insts:
            if skill_inst in ui or ui in skill_inst:
                return ui
        # Acronym: first letters of significant words in user name = skill_inst
        stop = {"of", "the", "and", "to", "for", "a", "an", "at", "in", "&"}
        for ui in user_insts:
            words = [w for w in ui.split() if w and w not in stop]
            if words:
                acronym = "".join(w[0] for w in words)
                if acronym == skill_inst:
                    return ui
        return skill_inst  # no match found — use as-is

    _institute_mapping: dict[str, str] = {}
    for si in _skill_institutes:
        matched = _match_institute(si, _user_institutes)
        if matched != si:
            _institute_mapping[si] = matched

    # Build a SQL CASE WHEN expression that maps skill institute names → users institute names
    # so the JOIN with institute_roster (keyed by users institute names) works correctly.
    if _institute_mapping:
        _map_cases = " ".join(
            f"WHEN LOWER(TRIM(CAST(sg.institute_name AS STRING))) = '{sql_escape(k)}' THEN '{sql_escape(v)}'"
            for k, v in _institute_mapping.items()
        )
        _inst_expr = f"CASE {_map_cases} ELSE LOWER(TRIM(CAST(sg.institute_name AS STRING))) END"
    else:
        _inst_expr = "LOWER(TRIM(CAST(sg.institute_name AS STRING)))"

    roster_where = ["TRIM(COALESCE(u.institute_name, '')) != ''"]
    if _users_batch_names_for_roster:
        _ur_quoted = ", ".join(f"'{sql_escape(n)}'" for n in _users_batch_names_for_roster)
        roster_where.append(f"TRIM(CAST(u.batch_name AS STRING)) IN ({_ur_quoted})")
    roster_where_sql = ' AND '.join(roster_where)

    sql = f"""
        WITH institute_roster AS (
          -- Only count students from the same batch so the denominator is correct
          SELECT
            LOWER(TRIM(u.institute_name)) AS institute,
            COUNT(DISTINCT u.user_id)     AS total_students
          FROM {refs["users"]} u
          WHERE {roster_where_sql}
          GROUP BY LOWER(TRIM(u.institute_name))
        ),
        sg_skill AS (
          SELECT
            -- Map skill-table institute name to the canonical users-table institute name
            {_inst_expr}                                                                               AS institute,
            COUNT(DISTINCT {date_col})                                                                 AS skill_conducted,
            COUNT(DISTINCT sg.user_id)                                                                 AS skill_students_attempted,
            COUNT(DISTINCT IF(sg.{score_col} >= 0.80, sg.user_id, NULL))                              AS skill_students_passed,
            COUNT(DISTINCT CONCAT(CAST(sg.user_id AS STRING), '||', CAST(sg.{asmt_id_col} AS STRING)))
                                                                                                       AS skill_pairs_attempted,
            COUNT(DISTINCT sg.{asmt_id_col})                                                           AS skill_assessment_count
          FROM {skill_table} sg
          WHERE {base_where_sql}
            AND UPPER(TRIM(CAST(sg.{asmt_type_col} AS STRING))) = 'SKILL_ASSESSMENT'
          GROUP BY {_inst_expr}
        ),
        sg_graded AS (
          SELECT
            {_inst_expr}                                                                               AS institute,
            COUNT(DISTINCT sg.user_id)                                                                 AS graded_students_attempted,
            COUNT(DISTINCT IF(sg.{score_col} >= 0.80, sg.user_id, NULL))                              AS graded_students_passed,
            COUNT(DISTINCT CONCAT(CAST(sg.user_id AS STRING), '||', CAST(sg.{asmt_id_col} AS STRING)))
                                                                                                       AS graded_pairs_attempted,
            COUNT(DISTINCT sg.{asmt_id_col})                                                           AS graded_assessment_count
          FROM {skill_table} sg
          WHERE {base_where_sql}
            AND UPPER(TRIM(CAST(sg.{asmt_type_col} AS STRING))) = 'GRADED_ASSESSMENT'
          GROUP BY {_inst_expr}
        )
        SELECT
          COALESCE(sk.institute, gr.institute) AS institute,
          sk.skill_conducted,
          ROUND(
            SAFE_DIVIDE(sk.skill_pairs_attempted,
                        NULLIF(ir.total_students * sk.skill_assessment_count, 0)) * 100,
          1) AS skill_participation_pct,
          ROUND(
            IF(sk.skill_students_attempted > 0,
               SAFE_DIVIDE(sk.skill_students_passed, NULLIF(sk.skill_students_attempted, 0)),
               NULL) * 100,
          1) AS skill_pass_pct,
          ROUND(
            SAFE_DIVIDE(gr.graded_pairs_attempted,
                        NULLIF(ir.total_students * gr.graded_assessment_count, 0)) * 100,
          1) AS academic_attempt_pct,
          ROUND(
            IF(gr.graded_students_attempted > 0,
               SAFE_DIVIDE(gr.graded_students_passed, NULLIF(gr.graded_students_attempted, 0)),
               NULL) * 100,
          1) AS academic_pass_pct
        FROM (
          SELECT institute FROM sg_skill
          UNION DISTINCT
          SELECT institute FROM sg_graded
        ) institutes
        LEFT JOIN sg_skill  sk ON sk.institute = institutes.institute
        LEFT JOIN sg_graded gr ON gr.institute = institutes.institute
        LEFT JOIN institute_roster ir ON ir.institute = institutes.institute
        ORDER BY institutes.institute
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_skill_graded_metrics error: {e}")
        return _empty


@st.cache_data(ttl=600, show_spinner=False)
def fetch_skill_assessment_detail(batch: str, semester: str, institute: str, section: str = "") -> pd.DataFrame:
    """
    Returns raw skill assessment detail from assessment_topic for a given institute.
    Used for the three-level assessment tab view.
    Returns columns:
      institute, section_name, user_id, assessment_id, assessment_title, section_tech_stack,
      assessment_date, assessment_type, exam_section, user_section_score, section_actual_score,
      score_pct
    """
    refs = get_table_refs()
    # Include both skill and graded assessments; exclude mocks
    where_clauses = [
        f"LOWER(TRIM(COALESCE(COALESCE(NULLIF(TRIM(t.institute_name),''), u.institute_name), ''))) = LOWER('{sql_escape(institute)}')",
        "(REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'skill assessment') OR REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'graded assessment'))",
        "NOT REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'mock')",
        "COALESCE(t.section_actual_score, 0) > 0",
    ]
    institute_expr = "COALESCE(NULLIF(TRIM(t.institute_name), ''), u.institute_name)"
    date_expr = "DATE(t.assessment_start_datetime)"
    # Use global semester date range (no per-institute name matching) to scope to the
    # correct semester without creating a whitelist that excludes unknown institute names.
    _sem_range = fetch_semester_actual_date_range(batch, semester)
    if _sem_range:
        where_clauses.append(f"{date_expr} BETWEEN '{_sem_range[0]}' AND '{_sem_range[1]}'")
    if section:
        where_clauses.append(f"LOWER(TRIM(COALESCE(t.section_name, u.section_name, ''))) = LOWER('{sql_escape(section)}')")

    users_batch_filter = ""
    if batch and batch.strip():
        users_batch_filter = f"AND {batch_sql_filter(batch, 'batch_name')}"

    sql = f"""
        WITH users AS (
          SELECT DISTINCT user_id, institute_name, section_name, batch_name
          FROM {refs["users"]}
          WHERE TRIM(COALESCE(institute_name, '')) != ''
          {users_batch_filter}
        )
        SELECT
          {institute_expr}                                               AS institute,
          COALESCE(NULLIF(TRIM(t.section_name), ''), NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section_name,
          t.user_id,
          t.assessment_id,
          t.assessment_title,
          COALESCE(NULLIF(TRIM(t.section_tech_stack), ''), 'Unknown')    AS section_tech_stack,
          {date_expr}                                                    AS assessment_date,
          CASE
            WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.assessment_title, '')), r'graded assessment') THEN 'Graded Assessment'
            ELSE 'Skill Assessment'
          END                                                            AS assessment_type,
          t.user_section_score,
          t.section_actual_score,
          ROUND(SAFE_DIVIDE(t.user_section_score, NULLIF(t.section_actual_score, 0)) * 100, 2) AS score_pct
        FROM {refs["assessment_topic"]} t
        LEFT JOIN users u ON u.user_id = t.user_id
        WHERE {' AND '.join(where_clauses)}
        ORDER BY assessment_date, assessment_title, section_name, t.user_id
    """
    try:
        return run_query(sql)
    except Exception as e:
        st.error(f"fetch_skill_assessment_detail error: {e}")
        return pd.DataFrame(columns=["institute","section_name","user_id","assessment_id","assessment_title",
                                     "section_tech_stack","assessment_date","assessment_type",
                                     "user_section_score","section_actual_score","score_pct"])


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
        # Normalize key to lowercase+trimmed so lookups are case-insensitive
        return {str(row[key]).strip().lower(): row.to_dict() for _, row in df.iterrows()}

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
    if batch and batch.strip():
        batch_filter_q = f"AND {batch_sql_filter(batch, 'batch_name')}"
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
    Returns {normalized_key â†' sem_course_title} by joining content â†' portal_courses
    via portal_course_id so that content-level course titles map to the official
    semester subject names.

    Keys added per row (so any lookup form hits the right sem_course_title):
      â€¢ normalize_text(content.course_title)
      â€¢ normalize_text(normalize_course_name(content.course_title, semester))
      â€¢ normalize_text(sem_course_title)          â† direct match fallback
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
    if batch and batch.strip():
        portal_where.append(batch_sql_filter(batch, "pc.batch_name"))
    sem_num = ""
    if "1" in semester:
        sem_num = "1"
    elif "2" in semester:
        sem_num = "2"
    if sem_num and portal_sem_col:
        portal_where.append(f"LOWER(COALESCE(pc.{bq_column(portal_sem_col)}, '')) LIKE '%semester {sem_num}%'")

    result: dict[str, str] = {}

    # â€â€ Primary path: join content â†' portal_courses via portal_course_id â€â€â€â€â€
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

    # â€â€ Fallback path: sem_course_title â†' sem_course_title (if join fails) â€â€
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
def fetch_portal_subject_map(batch: str, semester: str) -> dict:
    """
    Returns {normalize_text(sem_course_title): subject_name} from the portal table.
    This is the primary subject-name source for the semester across all universities.
    """
    portal_table_ref = get_config("BQ_PORTAL_COURSES_TABLE", DEFAULT_PORTAL_COURSES_TABLE)
    portal_cols      = fetch_table_columns(portal_table_ref, DEFAULT_PORTAL_COURSES_TABLE)

    subject_col     = first_existing_column(portal_cols, ["subject_name", "subject_title", "subject"])
    portal_sem_col  = first_existing_column(portal_cols, ["semester_title", "semester_name", "semester"])

    if not subject_col:
        return {}

    where = [f"TRIM(COALESCE(pc.sem_course_title, '')) != ''", f"TRIM(COALESCE(pc.{bq_column(subject_col)}, '')) != ''"]
    sem_num = "1" if "1" in semester else ("2" if "2" in semester else "")
    if sem_num and portal_sem_col:
        where.append(f"LOWER(COALESCE(pc.{bq_column(portal_sem_col)}, '')) LIKE '%semester {sem_num}%'")
    if batch and batch.strip():
        where.append(batch_sql_filter(batch, "pc.batch_name"))

    sql = f"""
        SELECT DISTINCT
          TRIM(pc.sem_course_title)                 AS sem_course_title,
          TRIM(pc.{bq_column(subject_col)})         AS subject_name
        FROM {format_table_ref(portal_table_ref, DEFAULT_PORTAL_COURSES_TABLE)} pc
        WHERE {' AND '.join(where)}
        ORDER BY sem_course_title
    """
    try:
        df = run_query(sql)
        result: dict[str, str] = {}
        for _, row in df.iterrows():
            course_title = str(row.get("sem_course_title") or "").strip()
            subject_name = str(row.get("subject_name") or "").strip()
            if course_title and subject_name:
                result[normalize_text(course_title)] = subject_name
        return result
    except Exception:
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_university_subject_map(batch: str, semester: str, institute: str) -> dict:
    """
    Queries curriculum_ops_semester_subject_wise_portal_course_details to get the
    exact subject â†' course mapping for a specific university and semester.

    Primary source: portal subject names across all universities.
    Fallback: university-specific subject rows, then alias mapping in normalize_course_name.

    Falls back gracefully if subject_name or institute_name columns don't exist.
    """
    result = dict(fetch_portal_subject_map(batch, semester))
    if result:
        return result

    portal_table_ref = get_config("BQ_PORTAL_COURSES_TABLE", DEFAULT_PORTAL_COURSES_TABLE)
    portal_cols      = fetch_table_columns(portal_table_ref, DEFAULT_PORTAL_COURSES_TABLE)
    subject_col     = first_existing_column(portal_cols, ["subject_name", "subject_title", "subject"])
    inst_col        = first_existing_column(portal_cols, ["institute_name", "university_name", "college_name", "institute"])
    portal_sem_col  = first_existing_column(portal_cols, ["semester_title", "semester_name", "semester"])
    if not subject_col:
        return {}

    sem_num = "1" if "1" in semester else ("2" if "2" in semester else "")
    where = [f"TRIM(COALESCE(pc.sem_course_title, '')) != ''", f"TRIM(COALESCE(pc.{bq_column(subject_col)}, '')) != ''"]
    if inst_col:
        where.append(f"LOWER(TRIM(COALESCE(pc.{bq_column(inst_col)}, ''))) = LOWER('{sql_escape(institute)}')")
    if sem_num and portal_sem_col:
        where.append(f"LOWER(COALESCE(pc.{bq_column(portal_sem_col)}, '')) LIKE '%semester {sem_num}%'")
    if batch and batch.strip():
        where.append(batch_sql_filter(batch, "pc.batch_name"))

    sql = f"""
        SELECT DISTINCT
          TRIM(pc.sem_course_title)                 AS sem_course_title,
          TRIM(pc.{bq_column(subject_col)})         AS subject_name
        FROM {format_table_ref(portal_table_ref, DEFAULT_PORTAL_COURSES_TABLE)} pc
        WHERE {' AND '.join(where)}
        ORDER BY sem_course_title
    """
    try:
        df = run_query(sql)
        for _, row in df.iterrows():
            course_title = str(row.get("sem_course_title") or "").strip()
            subject_name = str(row.get("subject_name") or "").strip()
            if course_title and subject_name:
                result[normalize_text(course_title)] = subject_name
        return result
    except Exception:
        return result


@st.cache_data(ttl=600, show_spinner=False)
def fetch_portal_course_id_map(batch: str, semester: str) -> dict:
    """
    Returns two-way lookup dict for quiz pass fallback matching:
      {normalize_text(sem_course_title) â†' portal_course_id}
      {normalize_text(content_course_title) â†' portal_course_id}   (if join possible)

    Used when quiz data can't be found by title -- match via portal_course_id instead.
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
    if batch and batch.strip():
        portal_where.append(batch_sql_filter(batch, "pc.batch_name"))
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

    # ── Lookup actual batch names from the assessment_topic table ──────────────
    # The topic table may store batch names differently from the UI selection.
    # Query it directly and match on the batch number digits only.
    _topic_batch_names: list[str] = []
    try:
        _batch_lookup_sql = f"""
            SELECT DISTINCT
              TRIM(CAST(t.batch_name AS STRING)) AS batch_name,
              TRIM(CAST(t.institute_name AS STRING)) AS institute_name,
              DATE(t.assessment_start_datetime) AS assessment_date,
              CAST(t.assessment_id AS STRING) AS assessment_id,
              TRIM(LOWER(COALESCE(t.assessment_title, ''))) AS assessment_type
            FROM {refs["assessment_topic"]} t
            WHERE t.batch_name IS NOT NULL
              AND TRIM(CAST(t.batch_name AS STRING)) != ''
            LIMIT 500
        """
        _blookup_df = run_query(_batch_lookup_sql)
        if not _blookup_df.empty and "batch_name" in _blookup_df.columns:
            _all_names = _blookup_df["batch_name"].dropna().unique().tolist()
            _topic_batch_names = match_batch_names_from_table(_all_names, batch)
            if not _topic_batch_names:
                _topic_batch_names = [str(n) for n in _all_names]
    except Exception:
        pass

    # Same lookup from users table for legacy path
    _users_batch_names: list[str] = []
    try:
        _u_lookup_sql = f"""
            SELECT DISTINCT TRIM(CAST(batch_name AS STRING)) AS batch_name
            FROM {refs["users"]}
            WHERE batch_name IS NOT NULL AND TRIM(CAST(batch_name AS STRING)) != ''
            LIMIT 500
        """
        _u_df = run_query(_u_lookup_sql)
        if not _u_df.empty and "batch_name" in _u_df.columns:
            _all_u = _u_df["batch_name"].dropna().unique().tolist()
            _users_batch_names = match_batch_names_from_table(_all_u, batch)
            if not _users_batch_names:
                _users_batch_names = [str(n) for n in _all_u]
    except Exception:
        pass

    # Semester date range filter — use a global (non-institute-specific) range so we don't
    # create an institute-name whitelist. This ensures Sem 1 and Sem 2 return distinct data.
    _sem_date_range = fetch_semester_actual_date_range(batch, semester)

    legacy_where_clauses = [
        "u.user_id IS NOT NULL",
        "TRIM(COALESCE(u.institute_name, '')) != ''",
    ]
    if _users_batch_names:
        _u_quoted = ", ".join(f"'{sql_escape(n)}'" for n in _users_batch_names)
        legacy_where_clauses.append(f"TRIM(CAST(u.batch_name AS STRING)) IN ({_u_quoted})")
    if _sem_date_range:
        legacy_where_clauses.append(f"{legacy_date_expr} BETWEEN '{_sem_date_range[0]}' AND '{_sem_date_range[1]}'")

    topic_institute_expr = "COALESCE(NULLIF(TRIM(t.institute_name), ''), u.institute_name)"
    topic_where_clauses = [
        f"TRIM(COALESCE({topic_institute_expr}, '')) != ''",
    ]
    if _topic_batch_names:
        _t_quoted = ", ".join(f"'{sql_escape(n)}'" for n in _topic_batch_names)
        topic_where_clauses.append(f"TRIM(CAST(t.batch_name AS STRING)) IN ({_t_quoted})")
    if _sem_date_range:
        topic_where_clauses.append(f"{topic_date_expr} BETWEEN '{_sem_date_range[0]}' AND '{_sem_date_range[1]}'")

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
            {legacy_date_expr} AS report_date,
            CAST(a.question_set_id AS STRING) AS assessment_id
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
            {topic_date_expr} AS report_date,
            CAST(t.assessment_id AS STRING) AS assessment_id
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
              COALESCE(SAFE_DIVIDE(user_score, NULLIF(actual_score, 0)), 0) >= 0.8,
              user_id,
              NULL
            )
          ) AS avg_pass_count,
          ROUND(AVG(COALESCE(SAFE_DIVIDE(user_score, NULLIF(actual_score, 0)), 0)), 4) AS avg_score,
          -- Attendance numerator: distinct (student, assessment) pairs attempted
          COUNT(DISTINCT IF(COALESCE(user_score, actual_score) IS NOT NULL,
            CONCAT(CAST(user_id AS STRING), '||', CAST(assessment_id AS STRING)), NULL)) AS pair_count,
          -- Attendance denominator component: distinct assessments in this course+type
          COUNT(DISTINCT IF(COALESCE(user_score, actual_score) IS NOT NULL, assessment_id, NULL)) AS assessment_count,
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
    skill_section_avgs = []
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
        skill_data = univ_data[(univ_data["section"] == section) & (univ_data["assessment_type"] == "Skill Assessment")]
        skill_only = summarize_assessment_subset(skill_data, "Skill Assessment")
        if any(skill_only.get(key) is not None for key in ("score", "participation", "pass_count")):
            skill_section_avgs.append(
                {
                    "skill_score": skill_only["score"],
                    "skill_participation": skill_only["participation"],
                    "skill_pass_count": skill_only["pass_count"],
                }
            )

    def average_metric(key: str):
        values = [item[key] for item in section_avgs if item[key] is not None]
        return sum(values) / len(values) if values else None

    def average_skill_metric(key: str):
        values = [item[key] for item in skill_section_avgs if item[key] is not None]
        return sum(values) / len(values) if values else None

    return {
        "avgScore": average_metric("score"),
        "avgParticipation": average_metric("participation"),
        "avgAcademicScore": average_metric("academic_score"),
        "avgAcademicParticipation": average_metric("academic_participation"),
        "avgAcademicPassCount": average_metric("academic_pass_count"),
        "avgSkillScore": average_skill_metric("skill_score"),
        "avgSkillParticipation": average_skill_metric("skill_participation"),
        "avgSkillPassCount": average_skill_metric("skill_pass_count"),
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


def build_university_metrics(data_df: pd.DataFrame, assessment_df: pd.DataFrame, institute: str, section: str, semester: str, sem_course_titles: dict | None = None, quiz_pass_pct: float | None = None, subject_map: dict | None = None):
    filtered = data_df[data_df["institute"] == institute].copy()
    if section:
        filtered = filtered[filtered["section"] == section]
    if filtered.empty:
        return None
    # subject_map: {normalize_text(sem_course_title): subject_name} from portal_courses table.
    # Used as primary normalization -- maps raw schedule titles to canonical subject names
    # before alias-based fallback.
    _subject_map = subject_map or {}

    # Map normalized course names to official sem_course_title where available
    # Defined before _normalize_course so it can be used as a dynamic BQ-based alias lookup.
    sem_titles = sem_course_titles or {}

    def _normalize_course(course: str) -> str:
        key = normalize_text(course)
        # 1. subject_map (portal_courses): normalize_text(sem_course_title) â†' subject_name
        if key in _subject_map:
            return canonicalize_course_label(_subject_map[key], semester)
        # 2. static alias groups should canonicalize raw title variants first.
        canonical = canonicalize_course_label(course, semester)
        # 3. sem_titles (BQ contentâ†'sem_course_title): use as a display fallback,
        #    but collapse the resolved title back through the same canonicalizer so
        #    portal-title variants like "Introduction to DataBase" still merge into
        #    the DBMS family instead of staying split as separate rows.
        if key in sem_titles:
            resolved = sem_titles[key]
            return canonicalize_course_label(resolved, semester)
        return canonical

    filtered["normalized_course"] = filtered["course"].apply(_normalize_course)

    # Collect all canonical course names known from the schedule for fallback matching
    _schedule_courses: set[str] = set(filtered["normalized_course"].unique())

    # Build a reverse lookup: normalize_text(subject_name) → canonical course label
    # _subject_map is {normalize_text(sem_course_title): subject_name}
    _subj_name_to_canonical: dict[str, str] = {}
    for _sct_key, _subj_name in _subject_map.items():
        _canonical = canonicalize_course_label(_subj_name, semester)
        _subj_name_to_canonical[normalize_text(_subj_name)] = _canonical
        # Also map the sem_course_title key itself to the canonical
        _subj_name_to_canonical[_sct_key] = _canonical

    def _normalize_course_extended(course: str) -> str:
        """
        Like _normalize_course but with extra fallback:
        if the standard normalization doesn't yield a known schedule course,
        try matching the raw course_code against portal subject names directly.
        """
        result = _normalize_course(course)
        if result in _schedule_courses:
            return result
        key = normalize_text(course)
        # Direct subject-name lookup (course_code IS a subject_name or sem_course_title)
        if key in _subj_name_to_canonical:
            candidate = _subj_name_to_canonical[key]
            if candidate in _schedule_courses:
                return candidate
        # Partial/substring fallback: course_code is a meaningful substring of a subject name
        for subj_key, canonical in _subj_name_to_canonical.items():
            if canonical not in _schedule_courses:
                continue
            if len(key) >= 4 and (key in subj_key or subj_key in key):
                return canonical
        return result

    def _display_course(name: str) -> str:
        return canonicalize_course_label(sem_titles.get(normalize_text(name), name), semester)
    lecture_df = filtered[filtered["session_type"] == "LECTURE"]
    practice_df = filtered[filtered["session_type"] == "PRACTICE"]
    exam_df = filtered[filtered["session_type"] == "EXAM"]
    section_names = [
        section_name
        for section_name in sorted(filtered["section"].dropna().astype(str).unique().tolist())
        if section_name and section_name.strip().lower() != "unknown"
    ]
    if not section_names:
        section_names = sorted(filtered["section"].dropna().astype(str).unique().tolist())

    def _planned_slots(course_df: pd.DataFrame, session_type: str) -> float:
        scoped = course_df[course_df["session_type"] == session_type]
        if scoped.empty:
            return 0.0
        if section:
            return float(scoped["sessions"].sum())
        per_section = scoped.groupby("section")["sessions"].sum()
        values = [float(per_section.get(sec, 0.0)) for sec in section_names]
        return float(sum(values) / len(values)) if values else 0.0

    course_records = []
    assessment_filtered = assessment_df[assessment_df["university"] == institute].copy()
    if section:
        assessment_filtered = assessment_filtered[assessment_filtered["section"] == section]
    # Use extended normalization so assessment course_code values that don't directly
    # resolve to a known schedule course are matched via portal subject names.
    assessment_filtered["normalized_course"] = assessment_filtered["course_code"].apply(_normalize_course_extended) if not assessment_filtered.empty else []

    # Pre-compute roster size so per-course attendance % can be derived inside the loop
    roster_size = get_roster_size_for_scope(filtered, section)

    for course_name in sorted(filtered["normalized_course"].unique().tolist()):
        course_df = filtered[filtered["normalized_course"] == course_name]
        lecture = summarize_type(course_df, "LECTURE")
        practice = summarize_type(course_df, "PRACTICE")
        exam = summarize_type(course_df, "EXAM")
        lecture_slots = _planned_slots(course_df, "LECTURE")
        practice_slots = _planned_slots(course_df, "PRACTICE")
        exam_slots = _planned_slots(course_df, "EXAM")
        assessment_row = assessment_filtered[assessment_filtered["normalized_course"] == course_name]
        overall_assessment_row = summarize_assessment_subset(assessment_row)
        skill_assessment_row = summarize_assessment_subset(assessment_row, "Skill Assessment")
        graded_assessment_row = summarize_assessment_subset(assessment_row, "Graded Assessment")

        # Skill pass % — average of per-raw-course pass rates (not pooled counts).
        # Fixes mismatch when multiple raw course codes roll up into the same subject label.
        skill_pass_pct = None
        _skill_rows = assessment_row[assessment_row["assessment_type"] == "Skill Assessment"] if not assessment_row.empty else pd.DataFrame()
        if not _skill_rows.empty and "avg_pass_count" in _skill_rows.columns and "avg_participation" in _skill_rows.columns:
            _rates = []
            for _, _r in _skill_rows.iterrows():
                _part = pd.to_numeric(_r.get("avg_participation"), errors="coerce")
                _pass = pd.to_numeric(_r.get("avg_pass_count"), errors="coerce")
                if pd.notna(_part) and _part > 0 and pd.notna(_pass):
                    _rates.append(float(_pass) / float(_part) * 100)
            if _rates:
                skill_pass_pct = round(sum(_rates) / len(_rates), 1)

        # Academic (graded) pass % — same aggregation pattern as skill
        academic_pass_pct = None
        _graded_rows = assessment_row[assessment_row["assessment_type"] == "Graded Assessment"] if not assessment_row.empty else pd.DataFrame()
        if not _graded_rows.empty and "avg_pass_count" in _graded_rows.columns and "avg_participation" in _graded_rows.columns:
            _rates = []
            for _, _r in _graded_rows.iterrows():
                _part = pd.to_numeric(_r.get("avg_participation"), errors="coerce")
                _pass = pd.to_numeric(_r.get("avg_pass_count"), errors="coerce")
                if pd.notna(_part) and _part > 0 and pd.notna(_pass):
                    _rates.append(float(_pass) / float(_part) * 100)
            if _rates:
                academic_pass_pct = round(sum(_rates) / len(_rates), 1)

        # Attendance % = SUM(student×assessment pairs attempted) / (roster_size × SUM(assessment_count))
        _skill_pairs = float(_skill_rows["pair_count"].sum()) if (not _skill_rows.empty and "pair_count" in _skill_rows.columns) else None
        _skill_asmt_cnt = float(_skill_rows["assessment_count"].sum()) if (not _skill_rows.empty and "assessment_count" in _skill_rows.columns) else None
        if roster_size > 0 and _skill_pairs and _skill_asmt_cnt and _skill_asmt_cnt > 0:
            skill_attendance_pct = round(min(_skill_pairs / (roster_size * _skill_asmt_cnt) * 100, 100.0), 1)
        else:
            skill_attendance_pct = None

        _graded_pairs = float(_graded_rows["pair_count"].sum()) if (not _graded_rows.empty and "pair_count" in _graded_rows.columns) else None
        _graded_asmt_cnt = float(_graded_rows["assessment_count"].sum()) if (not _graded_rows.empty and "assessment_count" in _graded_rows.columns) else None
        if roster_size > 0 and _graded_pairs and _graded_asmt_cnt and _graded_asmt_cnt > 0:
            academic_attendance_pct = round(min(_graded_pairs / (roster_size * _graded_asmt_cnt) * 100, 100.0), 1)
        else:
            academic_attendance_pct = None

        # Extract sem_course_id for ID-based drill-down (present when semester_df comes from portal_courses)
        _sem_cid = ""
        if "sem_course_id" in course_df.columns:
            _cid_vals = course_df["sem_course_id"].dropna()
            if not _cid_vals.empty:
                _sem_cid = str(_cid_vals.iloc[0])
        course_records.append(
            {
                "Course": _display_course(course_name),
                "sem_course_id": _sem_cid,
                "Lecture Slots": round(lecture_slots, 2),
                "Practice Slots": round(practice_slots, 2),
                "Exam Slots": round(exam_slots, 2),
                "Total Slots": round(lecture_slots + practice_slots + exam_slots, 2),
                "Lecture Delivery %": round(lecture["completion"], 1) if lecture else None,
                "Practice Delivery %": round(practice["completion"], 1) if practice else None,
                "Exam Delivery %": round(exam["completion"], 1) if exam else None,
                "Score %": round(overall_assessment_row["score"] * 100, 1) if overall_assessment_row["score"] is not None else None,
                "Participation #": round(overall_assessment_row["participation"], 1) if overall_assessment_row["participation"] is not None else None,
                "Skill Pass %": skill_pass_pct,
                "Skill Participation #": round(skill_assessment_row["participation"], 1) if skill_assessment_row["participation"] is not None else None,
                "Skill Attendance %": skill_attendance_pct,
                "Academic Assessment Score %": round(graded_assessment_row["score"] * 100, 1) if graded_assessment_row["score"] is not None else None,
                "Academic Assessment Participation #": round(graded_assessment_row["participation"], 1) if graded_assessment_row["participation"] is not None else None,
                "Academic Attendance %": academic_attendance_pct,
                "Academic Pass %": academic_pass_pct,
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


def filter_course_table(course_table: pd.DataFrame, semester: str, institute: str = ""):
    if course_table.empty:
        return course_table.copy(), 0
    filtered = course_table.copy()
    excluded_courses = {
        normalize_text(course)
        for course in (NON_CORE_COURSES_BY_SEMESTER.get(semester)
                       or NON_CORE_COURSES_BY_SEMESTER.get("Semester 2", set()))
    }
    if excluded_courses:
        filtered = filtered[~filtered["Course"].map(lambda value: normalize_text(value) in excluded_courses)].copy()
    institute_norm = normalize_text(institute)
    if semester == "Semester 2" and institute_norm in {normalize_text("A Dy Patil University"), normalize_text("A Dy Patil")}:
        dsml_norm = normalize_text("DSML(L2)")
        filtered = filtered[filtered["Course"].map(lambda value: normalize_text(value) != dsml_norm)].copy()
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


def render_institute_overview_table(
    institute: str,
    course_rows: list[dict],
    overview_df: pd.DataFrame,
    semester: str,
) -> None:
    """
    Renders a single-row HTML institute-level summary above the course matrix.
    Uses the exact same 8 color-groups as render_course_overview_table with all
    the same columns, plus Mode / Start Date / End Date in the Subject Info group.
    """
    if not course_rows:
        return

    import html as _html_mod

    # ── Shared color-group palette (identical to course overview) ────────────
    _G = {
        1: ("#EEF2FF", "#C7D2FE", "#4338CA", "#6366F1"),
        2: ("#F0FDF4", "#BBF7D0", "#15803D", "#16A34A"),
        3: ("#F8FAFC", "#E2E8F0", "#94A3B8", "#CBD5E1"),
        4: ("#FFF7ED", "#FED7AA", "#C2410C", "#D97706"),
        5: ("#F0FDFA", "#99F6E4", "#0F766E", "#0D9488"),
        6: ("#FAF5FF", "#E9D5FF", "#6D28D9", "#7C3AED"),
        7: ("#FFFBEB", "#FDE68A", "#92400E", "#B45309"),
        8: ("#FFF1F2", "#FECDD3", "#BE123C", "#E11D48"),
    }

    # ── Value helpers ────────────────────────────────────────────────────────
    def _v(val, decimals=1, suffix="", empty="--"):
        if val is None:
            return empty
        try:
            f = float(val)
            if f != f:
                return empty
            return f"{int(round(f))}{suffix}" if decimals == 0 else f"{f:.{decimals}f}{suffix}"
        except (TypeError, ValueError):
            return str(val) if val else empty

    def _pct_color(val, green=75, orange=50):
        if val is None: return "#94A3B8"
        try: f = float(val)
        except Exception: return "#94A3B8"
        return "#16A34A" if f >= green else ("#D97706" if f >= orange else "#DC2626")

    def _dev_color(val):
        if val is None: return "#94A3B8"
        try: f = float(val)
        except Exception: return "#94A3B8"
        return "#16A34A" if f >= 0 else ("#D97706" if f >= -25 else "#DC2626")

    # ── Pull mode / dates from overview_df ───────────────────────────────────
    _mode = _start = _end = "--"
    if overview_df is not None and not overview_df.empty and "Universities" in overview_df.columns:
        _ov_match = overview_df[overview_df["Universities"].str.strip().str.lower() == institute.strip().lower()]
        if not _ov_match.empty:
            _r = _ov_match.iloc[0]
            _mode  = str(_r.get("Delivery Mode") or "--")
            _start = str(_r.get("Start Date")    or "--")
            _end   = str(_r.get("End Date")      or "--")

    # ── Aggregate from course_rows ───────────────────────────────────────────
    def _fsum(key):
        vals = [float(r[key]) for r in course_rows
                if r.get(key) is not None and not (isinstance(r.get(key), float) and r[key] != r[key])]
        return round(sum(vals), 1) if vals else None

    def _favg(key):
        vals = [float(r[key]) for r in course_rows
                if r.get(key) is not None and not (isinstance(r.get(key), float) and r[key] != r[key])]
        return round(sum(vals) / len(vals), 1) if vals else None

    _total_designed    = _fsum("total_slots")
    _lec_designed      = _fsum("lecture_slots")
    _lec_till          = _fsum("lec_till_date")
    _lec_sched         = _fsum("lec_scheduled")
    _lec_dev           = _favg("lec_deviation")
    _prac_designed     = _fsum("practice_slots")
    _prac_till         = _fsum("prac_till_date")
    _prac_sched        = _fsum("prac_scheduled")
    _prac_dev          = _favg("prac_deviation")
    _prac_completion   = _favg("practice_completion_pct")
    _mq_designed       = _fsum("exam_slots")
    _mq_till           = _fsum("mq_till_date")
    _mq_sched          = _fsum("mq_scheduled")
    _mq_dev            = _favg("mq_deviation")
    _mq_attend         = _favg("mq_attendance_pct")
    _mq_pass           = _favg("module_quiz_pass_pct")
    _skill_designed    = _fsum("skill_designed")
    _skill_till        = _fsum("skill_till_date")
    _skill_attend      = _favg("skill_attendance_pct")
    _skill_pass        = _favg("skill_pass_pct")
    _acad_attend       = _favg("academic_attendance_pct")
    _acad_pass         = _favg("academic_pass_pct")

    # ── Cell builders ────────────────────────────────────────────────────────
    _ROW_BG = "#F8FAFF"
    _TD = (f"padding:5px 10px;text-align:center;font-size:0.78rem;"
           f"border-bottom:1px solid #E2E8F0;white-space:nowrap;"
           f"background:{_ROW_BG};font-weight:700;color:#1E293B;")

    def _cell(val, decimals=1, suffix="", color=None):
        txt = _v(val, decimals, suffix)
        col = f"color:{color};" if color else ""
        return f'<td style="{_TD}{col}">{txt}</td>'

    def _pct_cell(val, green=75, orange=50):
        return _cell(val, 1, "%", color=_pct_color(val, green, orange))

    def _dev_cell(val):
        return _cell(val, 1, "%", color=_dev_color(val))

    def _na_cell():
        return f'<td style="{_TD}color:#CBD5E1;">--</td>'

    # ── Header helpers ────────────────────────────────────────────────────────
    def _grp_th(label, colspan, g):
        bg, border, text, _ = _G[g]
        return (
            f'<th colspan="{colspan}" style="background:{bg};color:{text};'
            f'padding:7px 10px;text-align:center;font-weight:700;font-size:0.69rem;'
            f'letter-spacing:0.06em;text-transform:uppercase;'
            f'border-bottom:2px solid {border};white-space:nowrap;">{label}</th>'
        )

    def _col_th(label, g):
        bg, _, _, sub = _G[g]
        return (
            f'<th style="background:{bg};color:{sub};padding:6px 8px;'
            f'text-align:center;font-weight:600;font-size:0.69rem;'
            f'border-bottom:2px solid #E2E8F0;white-space:nowrap;min-width:72px;">{label}</th>'
        )

    # ── Group header row (Subject Info = 5 cols; rest identical to course table) ──
    grp_row = (
        _grp_th("Institute Info", 5, 1)
        + _grp_th("Lectures", 4, 2)
        + _grp_th("Classroom Quiz", 3, 3)
        + _grp_th("Practice", 4, 4)
        + _grp_th("Practice Completion", 1, 5)
        + _grp_th("Module Quiz", 6, 6)
        + _grp_th("Skill Assessment", 5, 7)
        + _grp_th("Academic", 2, 8)
    )

    col_row = (
        _col_th("Institute", 1) + _col_th("Mode", 1) + _col_th("Start Date", 1)
        + _col_th("End Date", 1) + _col_th("Total Designed", 1)
        + _col_th("Designed", 2) + _col_th("Designed Till Date", 2)
        + _col_th("Scheduled", 2) + _col_th("Deviation %", 2)
        + _col_th("Attend %", 3) + _col_th("Q Attempt", 3) + _col_th("Q Correct", 3)
        + _col_th("Designed", 4) + _col_th("Designed Till Date", 4)
        + _col_th("Scheduled", 4) + _col_th("Deviation %", 4)
        + _col_th("Completion %", 5)
        + _col_th("Designed", 6) + _col_th("Designed Till Date", 6)
        + _col_th("Scheduled", 6) + _col_th("Deviation %", 6)
        + _col_th("Attend %", 6) + _col_th("Pass %", 6)
        + _col_th("Designed", 7) + _col_th("Designed Till Date", 7)
        + _col_th("Scheduled", 7) + _col_th("Attend %", 7) + _col_th("Pass %", 7)
        + _col_th("Attend %", 8) + _col_th("Pass %", 8)
    )

    # ── Data row ──────────────────────────────────────────────────────────────
    _bg1, _, _text1, _ = _G[1]
    _inst_td = (
        f"padding:5px 12px;text-align:left;font-size:0.78rem;"
        f"border-bottom:1px solid #E2E8F0;white-space:nowrap;"
        f"background:{_ROW_BG};font-weight:700;color:{_text1};min-width:150px;"
    )
    _plain_td = (
        f"padding:5px 10px;text-align:center;font-size:0.78rem;"
        f"border-bottom:1px solid #E2E8F0;white-space:nowrap;"
        f"background:{_ROW_BG};color:#475569;"
    )

    data_row = (
        f'<td style="{_inst_td}">{_html_mod.escape(institute)}</td>'
        + f'<td style="{_plain_td}">{_html_mod.escape(_mode)}</td>'
        + f'<td style="{_plain_td}">{_html_mod.escape(_start)}</td>'
        + f'<td style="{_plain_td}">{_html_mod.escape(_end)}</td>'
        + _cell(_total_designed, decimals=0)
        # Lectures
        + _cell(_lec_designed, 0)
        + _cell(_lec_till, 1)
        + _cell(_lec_sched, 1)
        + _dev_cell(_lec_dev)
        # Classroom Quiz (no per-institute counts available)
        + _na_cell() + _na_cell() + _na_cell()
        # Practice
        + _cell(_prac_designed, 0)
        + _cell(_prac_till, 1)
        + _cell(_prac_sched, 1)
        + _dev_cell(_prac_dev)
        # Practice Completion
        + _pct_cell(_prac_completion)
        # Module Quiz
        + _cell(_mq_designed, 0)
        + _cell(_mq_till, 1)
        + _cell(_mq_sched, 1)
        + _dev_cell(_mq_dev)
        + _pct_cell(_mq_attend)
        + _pct_cell(_mq_pass)
        # Skill Assessment
        + _cell(_skill_designed, 0)
        + _cell(_skill_till, 1)
        + _na_cell()   # Skill Scheduled — not tracked at course level
        + _pct_cell(_skill_attend)
        + _pct_cell(_skill_pass)
        # Academic
        + _pct_cell(_acad_attend)
        + _pct_cell(_acad_pass)
    )

    html_out = f"""
    <div style="margin-bottom:16px;border-radius:10px;overflow:auto;
                border:1px solid #C7D2FE;box-shadow:0 1px 6px rgba(99,102,241,.12);">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr>{grp_row}</tr>
          <tr>{col_row}</tr>
        </thead>
        <tbody>
          <tr>{data_row}</tr>
        </tbody>
      </table>
    </div>
    """
    st.markdown(html_out, unsafe_allow_html=True)


def render_all_institutes_html_table(
    all_universities: list[dict],
    semester_df: pd.DataFrame,
    overview_df: pd.DataFrame,
    new_metrics: dict,
    semester: str,
    batch: str,
) -> str | None:
    """Renders all universities as rows in the institute overview HTML table format."""
    import html as _html_mod

    if not all_universities:
        return None

    # ── Value helpers ─────────────────────────────────────────────────────────
    def _safe_f(v):
        try:
            f = float(v)
            return None if f != f else f
        except Exception:
            return None

    def _v(val, decimals=1, suffix="", empty="--"):
        if val is None:
            return empty
        try:
            f = float(val)
            if f != f:
                return empty
            return f"{int(round(f))}{suffix}" if decimals == 0 else f"{f:.{decimals}f}{suffix}"
        except (TypeError, ValueError):
            return str(val) if val else empty

    def _pct_color(val, green=75, orange=50):
        if val is None:
            return "#94A3B8"
        try:
            f = float(val)
        except Exception:
            return "#94A3B8"
        return "#16A34A" if f >= green else ("#D97706" if f >= orange else "#DC2626")

    def _dev_color(val):
        if val is None:
            return "#94A3B8"
        try:
            f = float(val)
        except Exception:
            return "#94A3B8"
        return "#16A34A" if f >= 0 else ("#D97706" if f >= -25 else "#DC2626")

    def _deviation(till, sched):
        if till is not None and till > 0 and sched is not None:
            return round(((sched - till) / till) * 100, 1)
        return None

    # ── Color group palette ───────────────────────────────────────────────────
    _G = {
        1: ("#EEF2FF", "#C7D2FE", "#4338CA", "#6366F1"),
        2: ("#F0FDF4", "#BBF7D0", "#15803D", "#16A34A"),
        3: ("#F8FAFC", "#E2E8F0", "#94A3B8", "#CBD5E1"),
        4: ("#FFF7ED", "#FED7AA", "#C2410C", "#D97706"),
        5: ("#F0FDFA", "#99F6E4", "#0F766E", "#0D9488"),
        6: ("#FAF5FF", "#E9D5FF", "#6D28D9", "#7C3AED"),
        7: ("#FFFBEB", "#FDE68A", "#92400E", "#B45309"),
        8: ("#FFF1F2", "#FECDD3", "#BE123C", "#E11D48"),
    }

    # ── Cell / header builders ────────────────────────────────────────────────
    _TD_BASE = "padding:5px 10px;text-align:center;font-size:0.78rem;border-bottom:1px solid #E2E8F0;white-space:nowrap;"

    def _cell(val, decimals=1, suffix="", color=None, bg="#FFFFFF"):
        txt = _v(val, decimals, suffix)
        col_s = f"color:{color};" if color else "color:#1E293B;"
        return f'<td style="{_TD_BASE}background:{bg};font-weight:700;{col_s}">{txt}</td>'

    def _pct_cell(val, green=75, orange=50, bg="#FFFFFF"):
        return _cell(val, 1, "%", color=_pct_color(val, green, orange), bg=bg)

    def _dev_cell(val, bg="#FFFFFF"):
        return _cell(val, 1, "%", color=_dev_color(val), bg=bg)

    def _na_cell(bg="#FFFFFF"):
        return f'<td style="{_TD_BASE}background:{bg};color:#CBD5E1;">--</td>'

    def _grp_th(label, colspan, g):
        bg, border, text, _ = _G[g]
        return (
            f'<th colspan="{colspan}" style="background:{bg};color:{text};'
            f'padding:7px 10px;text-align:center;font-weight:700;font-size:0.69rem;'
            f'letter-spacing:0.06em;text-transform:uppercase;'
            f'border-bottom:2px solid {border};white-space:nowrap;">{label}</th>'
        )

    def _col_th(label, g):
        bg, _, _, sub = _G[g]
        return (
            f'<th style="background:{bg};color:{sub};padding:6px 8px;'
            f'text-align:center;font-weight:600;font-size:0.69rem;'
            f'border-bottom:2px solid #E2E8F0;white-space:nowrap;min-width:72px;">{label}</th>'
        )

    grp_row = (
        _grp_th("Institute Info", 5, 1)
        + _grp_th("Lectures", 4, 2)
        + _grp_th("Classroom Quiz", 3, 3)
        + _grp_th("Practice", 4, 4)
        + _grp_th("Practice Completion", 1, 5)
        + _grp_th("Module Quiz", 6, 6)
        + _grp_th("Skill Assessment", 5, 7)
        + _grp_th("Academic", 2, 8)
    )

    col_row = (
        _col_th("Institute", 1) + _col_th("Mode", 1) + _col_th("Start Date", 1)
        + _col_th("End Date", 1) + _col_th("Total Designed", 1)
        + _col_th("Designed", 2) + _col_th("Designed Till Date", 2)
        + _col_th("Scheduled", 2) + _col_th("Deviation %", 2)
        + _col_th("Attend %", 3) + _col_th("Q Attempt", 3) + _col_th("Q Correct", 3)
        + _col_th("Designed", 4) + _col_th("Designed Till Date", 4)
        + _col_th("Scheduled", 4) + _col_th("Deviation %", 4)
        + _col_th("Completion %", 5)
        + _col_th("Designed", 6) + _col_th("Designed Till Date", 6)
        + _col_th("Scheduled", 6) + _col_th("Deviation %", 6)
        + _col_th("Attend %", 6) + _col_th("Pass %", 6)
        + _col_th("Designed", 7) + _col_th("Designed Till Date", 7)
        + _col_th("Scheduled", 7) + _col_th("Attend %", 7) + _col_th("Pass %", 7)
        + _col_th("Attend %", 8) + _col_th("Pass %", 8)
    )

    # ── Build overview lookup (keyed by lowercased university name) ───────────
    ov_lookup: dict = {}
    if overview_df is not None and not overview_df.empty and "Universities" in overview_df.columns:
        for _, row in overview_df.iterrows():
            ov_lookup[str(row["Universities"]).strip().lower()] = row.to_dict()

    nm = new_metrics or {}
    skill_graded_data: dict = nm.get("skill_graded", {})

    # ── Pacing ratio ──────────────────────────────────────────────────────────
    def _pacing(start_str: str, end_str: str) -> float:
        try:
            s_iso = datetime.strptime(start_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            e_iso = datetime.strptime(end_str,   "%d/%m/%Y").strftime("%Y-%m-%d")
            total_wd = count_weekdays_between(s_iso, e_iso)
            if not total_wd:
                return 0.0
            today_str = datetime.now().strftime("%Y-%m-%d")
            end_eff   = e_iso if e_iso <= today_str else today_str
            elapsed   = count_weekdays_between(s_iso, end_eff) or 0
            return min(1.0, float(elapsed) / float(total_wd))
        except Exception:
            return 0.0

    # ── Per-type slot count from semester_df ──────────────────────────────────
    def _slot_count(inst_name: str, stype: str):
        if semester_df is None or semester_df.empty:
            return None
        if "session_type" not in semester_df.columns:
            return None
        norm = inst_name.strip().lower()
        mask = (
            semester_df["institute"].str.strip().str.lower() == norm
        ) & (
            semester_df["session_type"].str.upper() == stype
        )
        df_t = semester_df[mask]
        if df_t.empty:
            return None
        # sum sessions across courses per section, then average sections
        per_section = df_t.groupby("section")["sessions"].sum()
        return float(per_section.mean())

    # ── Build rows ────────────────────────────────────────────────────────────
    _, _, _text1, _ = _G[1]
    body_rows = []
    nav_names = []

    for idx, univ in enumerate(all_universities):
        name = univ["name"]
        norm = name.strip().lower()
        bg = "#F8FAFF" if idx % 2 == 0 else "#FFFFFF"

        # Overview row lookup with partial-match fallback
        ov_row = ov_lookup.get(norm)
        if ov_row is None:
            for k, v in ov_lookup.items():
                if norm in k or k in norm:
                    ov_row = v
                    break

        def _ov(col, _row=ov_row):
            if _row is None:
                return None
            return _safe_f(_row.get(col))

        _mode  = str(ov_row.get("Delivery Mode") or "--") if ov_row is not None else "--"
        _start = str(ov_row.get("Start Date")    or "--") if ov_row is not None else "--"
        _end   = str(ov_row.get("End Date")      or "--") if ov_row is not None else "--"

        ratio = _pacing(_start, _end) if (_start != "--" and _end != "--") else 0.0

        # Slot counts from semester_df
        _lec  = _slot_count(name, "LECTURE")
        _prac = _slot_count(name, "PRACTICE")
        _exam = _slot_count(name, "EXAM")
        _total_slots = ((_lec or 0) + (_prac or 0) + (_exam or 0)) or None

        # Delivery pcts from overview_df
        _lec_pct  = _ov("Lecture Delivery %")
        _prac_pct = _ov("Practice Delivery %")
        _exam_pct = _ov("Module Quiz Conduction %")

        _lec_till  = round((_lec  or 0) * ratio, 1) if _lec  is not None else None
        _prac_till = round((_prac or 0) * ratio, 1) if _prac is not None else None
        _exam_till = round((_exam or 0) * ratio, 1) if _exam is not None else None

        _lec_sched  = round((_lec  or 0) * ((_lec_pct  or 0) / 100), 1) if _lec  is not None else None
        _prac_sched = round((_prac or 0) * ((_prac_pct or 0) / 100), 1) if _prac is not None else None
        _exam_sched = round((_exam or 0) * ((_exam_pct or 0) / 100), 1) if _exam is not None else None

        _lec_dev  = _deviation(_lec_till,  _lec_sched)
        _prac_dev = _deviation(_prac_till, _prac_sched)
        _exam_dev = _deviation(_exam_till, _exam_sched)

        _cr_attend = _ov("Class Room Quizzes Attempt %")
        _prac_comp = _ov("Practice Completion %")
        _mq_attend = _ov("Module Quiz Student Participation %")
        _mq_pass   = _ov("Module Quiz Pass %")

        # Skill assessment (5 designed per semester)
        _sg = skill_graded_data.get(norm, {})
        _skill_cond = None
        try:
            _raw = _sg.get("skill_conducted")
            if _raw is not None:
                _skill_cond = float(_raw)
        except Exception:
            pass
        _skill_till  = round(5 * ratio, 1)
        _skill_sched = round(min(_skill_cond or 0, 5), 0) if _skill_cond is not None else None
        _skill_attend = _ov("Skill Assessment Student Participation %")
        _skill_pass   = _ov("Skill Assessment Pass %")
        _acad_attend  = _ov("Academic Assessments Attempt %")
        _acad_pass    = _ov("Academic Assessments Pass %")

        # Cell styles
        _inst_td = (
            f"padding:5px 12px;text-align:left;font-size:0.78rem;"
            f"border-bottom:1px solid #E2E8F0;white-space:nowrap;"
            f"background:{bg};font-weight:700;color:{_text1};min-width:180px;"
        )
        _txt_td = (
            f"padding:5px 10px;text-align:center;font-size:0.78rem;"
            f"border-bottom:1px solid #E2E8F0;white-space:nowrap;"
            f"background:{bg};color:#475569;"
        )

        row_html = (
            f'<td style="{_inst_td}">{_html_mod.escape(name)}</td>'
            + f'<td style="{_txt_td}">{_html_mod.escape(_mode)}</td>'
            + f'<td style="{_txt_td}">{_html_mod.escape(_start)}</td>'
            + f'<td style="{_txt_td}">{_html_mod.escape(_end)}</td>'
            + _cell(_total_slots, 0, bg=bg)
            # Lectures
            + _cell(_lec,      0, bg=bg)
            + _cell(_lec_till, 1, bg=bg)
            + _cell(_lec_sched, 1, bg=bg)
            + _dev_cell(_lec_dev, bg=bg)
            # Classroom Quiz (Q Attempt / Q Correct not available at institute level)
            + _pct_cell(_cr_attend, green=70, orange=50, bg=bg)
            + _na_cell(bg=bg)
            + _na_cell(bg=bg)
            # Practice
            + _cell(_prac,      0, bg=bg)
            + _cell(_prac_till, 1, bg=bg)
            + _cell(_prac_sched, 1, bg=bg)
            + _dev_cell(_prac_dev, bg=bg)
            # Practice Completion
            + _pct_cell(_prac_comp, green=75, orange=50, bg=bg)
            # Module Quiz
            + _cell(_exam,      0, bg=bg)
            + _cell(_exam_till, 1, bg=bg)
            + _cell(_exam_sched, 1, bg=bg)
            + _dev_cell(_exam_dev, bg=bg)
            + _pct_cell(_mq_attend, green=70, orange=50, bg=bg)
            + _pct_cell(_mq_pass,   green=70, orange=50, bg=bg)
            # Skill Assessment
            + _cell(5, 0, bg=bg)
            + _cell(_skill_till,  1, bg=bg)
            + _cell(_skill_sched, 0, bg=bg)
            + _pct_cell(_skill_attend, green=70, orange=50, bg=bg)
            + _pct_cell(_skill_pass,   green=70, orange=50, bg=bg)
            # Academic
            + _pct_cell(_acad_attend, green=70, orange=50, bg=bg)
            + _pct_cell(_acad_pass,   green=70, orange=50, bg=bg)
        )
        body_rows.append(f"<tr>{row_html}</tr>")
        nav_names.append(name)

    all_html = f"""
    <div style="margin-bottom:16px;border-radius:10px;overflow:auto;
                border:1px solid #C7D2FE;box-shadow:0 1px 6px rgba(99,102,241,.12);">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr>{grp_row}</tr>
          <tr>{col_row}</tr>
        </thead>
        <tbody>
          {"".join(body_rows)}
        </tbody>
      </table>
    </div>
    """
    sel = None
    if nav_names:
        sel = st.selectbox(
            "Navigate to university course breakdown \u2192",
            options=["(Select a university)"] + nav_names,
            key="all_institutes_nav_select",
        )

    st.markdown(all_html, unsafe_allow_html=True)

    if sel and sel != "(Select a university)":
        return sel
    return None


def render_course_overview_table(course_rows: list[dict], section: str = "") -> str | None:
    """
    Renders the 8-color-group course overview as a custom HTML table.
    Returns the selected course name for drill-down (via selectbox), or None.
    When section is provided (single-section view), deviation % shows as integers.
    """
    if not course_rows:
        st.warning("No course data to display.")
        return None

    def _v(val, decimals=1, suffix="", empty="--"):
        if val is None:
            return empty
        try:
            f = float(val)
            if f != f:
                return empty
            return f"{int(round(f))}{suffix}" if decimals == 0 else f"{f:.{decimals}f}{suffix}"
        except (TypeError, ValueError):
            return str(val) if val else empty

    def _pct_color(val, green=75, orange=50):
        if val is None:
            return "#94A3B8"
        try:
            f = float(val)
        except Exception:
            return "#94A3B8"
        if f >= green:
            return "#16A34A"
        if f >= orange:
            return "#D97706"
        return "#DC2626"

    def _dev_color(val):
        # Positive = forward/ahead (good), Negative = behind schedule (bad)
        if val is None:
            return "#94A3B8"
        try:
            f = float(val)
        except Exception:
            return "#94A3B8"
        if f >= 0:
            return "#16A34A"
        if f >= -25:
            return "#D97706"
        return "#DC2626"

    _TD = "padding:5px 10px;text-align:center;font-size:0.78rem;border-bottom:1px solid #F1F5F9;white-space:nowrap;"

    def _cell(val, decimals=1, suffix="", color=None, bold=False):
        txt = _v(val, decimals, suffix)
        s = _TD
        if color:
            s += f"color:{color};"
        if bold:
            s += "font-weight:600;"
        return f'<td style="{s}">{txt}</td>'

    def _pct_cell(val, green=75, orange=50):
        return _cell(val, 1, "%", color=_pct_color(val, green, orange), bold=True)

    def _dev_cell(val):
        # Single section → integer %; all sections → 1 decimal
        decimals = 0 if section else 1
        return _cell(val, decimals, "%", color=_dev_color(val), bold=True)

    def _na_cell():
        return f'<td style="{_TD}color:#CBD5E1;">--</td>'

    # Color group palette
    _G = {
        1: ("#EEF2FF", "#C7D2FE", "#4338CA", "#6366F1"),
        2: ("#F0FDF4", "#BBF7D0", "#15803D", "#16A34A"),
        3: ("#F8FAFC", "#E2E8F0", "#94A3B8", "#CBD5E1"),
        4: ("#FFF7ED", "#FED7AA", "#C2410C", "#D97706"),
        5: ("#F0FDFA", "#99F6E4", "#0F766E", "#0D9488"),
        6: ("#FAF5FF", "#E9D5FF", "#6D28D9", "#7C3AED"),
        7: ("#FFFBEB", "#FDE68A", "#92400E", "#B45309"),
        8: ("#FFF1F2", "#FECDD3", "#BE123C", "#E11D48"),
    }

    def _grp_th(label, colspan, g):
        bg, border, text, _ = _G[g]
        return (
            f'<th colspan="{colspan}" style="background:{bg};color:{text};'
            f'padding:7px 10px;text-align:center;font-weight:700;font-size:0.69rem;'
            f'letter-spacing:0.06em;text-transform:uppercase;'
            f'border-bottom:2px solid {border};white-space:nowrap;">{label}</th>'
        )

    def _col_th(label, g):
        bg, _, _, sub = _G[g]
        return (
            f'<th style="background:{bg};color:{sub};padding:6px 8px;'
            f'text-align:center;font-weight:600;font-size:0.69rem;'
            f'border-bottom:2px solid #E2E8F0;white-space:nowrap;min-width:72px;">{label}</th>'
        )

    grp_row = (
        _grp_th("Subject Info", 3, 1)
        + _grp_th("Lectures", 4, 2)
        + _grp_th("Classroom Quiz", 3, 3)
        + _grp_th("Practice", 4, 4)
        + _grp_th("Practice Completion", 1, 5)
        + _grp_th("Module Quiz", 6, 6)
        + _grp_th("Skill Assessment", 5, 7)
        + _grp_th("Academic", 2, 8)
    )

    col_row = (
        _col_th("Subject", 1) + _col_th("Mode", 1) + _col_th("Total Designed", 1)
        + _col_th("Designed", 2) + _col_th("Designed Till Date", 2) + _col_th("Scheduled", 2) + _col_th("Deviation %", 2)
        + _col_th("Attend %", 3) + _col_th("Q Attempt", 3) + _col_th("Q Correct", 3)
        + _col_th("Designed", 4) + _col_th("Designed Till Date", 4) + _col_th("Scheduled", 4) + _col_th("Deviation %", 4)
        + _col_th("Completion %", 5)
        + _col_th("Designed", 6) + _col_th("Designed Till Date", 6) + _col_th("Scheduled", 6)
        + _col_th("Deviation %", 6) + _col_th("Attend %", 6) + _col_th("Pass %", 6)
        + _col_th("Designed", 7) + _col_th("Designed Till Date", 7) + _col_th("Scheduled", 7)
        + _col_th("Attend %", 7) + _col_th("Pass %", 7)
        + _col_th("Attend %", 8) + _col_th("Pass %", 8)
    )

    # ── Summary row (averages / sums across all courses) ──────────────────────
    def _s_avg(key):
        vals = [float(r[key]) for r in course_rows
                if r.get(key) is not None and not (isinstance(r.get(key), float) and r[key] != r[key])]
        return round(sum(vals) / len(vals), 1) if vals else None

    def _s_sum(key):
        vals = [float(r[key]) for r in course_rows if r.get(key) is not None]
        return round(sum(vals), 1) if vals else None

    _SUM_BG = "#F1F5F9"
    _SUM_TD = (
        f"padding:5px 10px;text-align:center;font-size:0.78rem;"
        f"border-bottom:2px solid #CBD5E1;white-space:nowrap;background:{_SUM_BG};"
        f"font-weight:700;color:#1E293B;"
    )
    _SUM_SUBJ = (
        f"padding:5px 12px;text-align:left;font-size:0.78rem;"
        f"border-bottom:2px solid #CBD5E1;white-space:nowrap;background:{_SUM_BG};"
        f"font-weight:700;color:#4338CA;min-width:150px;"
    )

    def _sc(val, decimals=1, suffix="", color=None):
        txt = _v(val, decimals, suffix)
        s = _SUM_TD + (f"color:{color};" if color else "")
        return f'<td style="{s}">{txt}</td>'

    def _sc_pct(val, green=75, orange=50):
        return _sc(val, 1, "%", color=_pct_color(val, green, orange))

    def _sc_dev(val):
        decimals = 0 if section else 1
        return _sc(val, decimals, "%", color=_dev_color(val))

    def _sc_na():
        return f'<td style="{_SUM_TD}color:#CBD5E1;">--</td>'

    _total_designed = _s_sum("total_slots")
    summary_row = (
        f'<tr>'
        f'<td style="{_SUM_SUBJ}">Summary (Avg / Total)</td>'
        f'<td style="{_SUM_TD}color:#94A3B8;">--</td>'
        + _sc(_total_designed, 1)
        # Lectures
        + _sc(_s_sum("lecture_slots"), 1)
        + _sc(_s_sum("lec_till_date"), 1)
        + _sc(_s_sum("lec_scheduled"), 1)
        + _sc_dev(_s_avg("lec_deviation"))
        # Classroom Quiz (all --)
        + _sc_na() + _sc_na() + _sc_na()
        # Practice
        + _sc(_s_sum("practice_slots"), 1)
        + _sc(_s_sum("prac_till_date"), 1)
        + _sc(_s_sum("prac_scheduled"), 1)
        + _sc_dev(_s_avg("prac_deviation"))
        # Practice Completion
        + _sc_pct(_s_avg("practice_completion_pct"))
        # Module Quiz
        + _sc(_s_sum("exam_slots"), 1)
        + _sc(_s_sum("mq_till_date"), 1)
        + _sc(_s_sum("mq_scheduled"), 1)
        + _sc_dev(_s_avg("mq_deviation"))
        + _sc_pct(_s_avg("mq_attendance_pct"))
        + _sc_pct(_s_avg("module_quiz_pass_pct"))
        # Skill Assessment
        + _sc(_s_sum("skill_designed"), 1)
        + _sc(_s_sum("skill_till_date"), 1)
        + _sc_na()  # Skill Scheduled
        + _sc_pct(_s_avg("skill_attendance_pct"))
        + _sc_pct(_s_avg("skill_pass_pct"))
        # Academic
        + _sc_pct(_s_avg("academic_attendance_pct"))
        + _sc_pct(_s_avg("academic_pass_pct"))
        + '</tr>'
    )

    data_rows_html = []
    for i, row in enumerate(course_rows):
        bg = "#FAFBFF" if i % 2 == 0 else "#FFFFFF"
        subj_s = (
            f"padding:5px 12px;text-align:left;font-weight:600;font-size:0.78rem;"
            f"border-bottom:1px solid #F1F5F9;white-space:nowrap;background:{bg};"
            f"color:#1E293B;min-width:150px;"
        )
        plain_s = f"padding:5px 10px;text-align:center;font-size:0.78rem;border-bottom:1px solid #F1F5F9;white-space:nowrap;background:{bg};color:#334155;"

        total = (row.get("lecture_slots") or 0) + (row.get("practice_slots") or 0) + (row.get("exam_slots") or 0)

        tr = f'<tr style="background:{bg};">'
        # Color 1
        tr += f'<td style="{subj_s}">{html.escape(str(row.get("course", "")))}</td>'
        tr += f'<td style="{plain_s}">{html.escape(str(row.get("delivery_mode") or "--"))}</td>'
        tr += f'<td style="{plain_s}">{_v(total, 0)}</td>'
        # Color 2 — Lectures
        tr += f'<td style="{plain_s}">{_v(row.get("lecture_slots"), 0)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("lec_till_date"), 1)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("lec_scheduled"), 1)}</td>'
        tr += _dev_cell(row.get("lec_deviation"))
        # Color 3 — Classroom Quiz (all --)
        tr += _na_cell(); tr += _na_cell(); tr += _na_cell()
        # Color 4 — Practice
        tr += f'<td style="{plain_s}">{_v(row.get("practice_slots"), 0)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("prac_till_date"), 1)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("prac_scheduled"), 1)}</td>'
        tr += _dev_cell(row.get("prac_deviation"))
        # Color 5 — Practice Completion
        tr += _pct_cell(row.get("practice_completion_pct"))
        # Color 6 — Module Quiz
        tr += f'<td style="{plain_s}">{_v(row.get("exam_slots"), 0)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("mq_till_date"), 1)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("mq_scheduled"), 1)}</td>'
        tr += _dev_cell(row.get("mq_deviation"))
        tr += _pct_cell(row.get("mq_attendance_pct"))
        tr += _pct_cell(row.get("module_quiz_pass_pct"))
        # Color 7 — Skill Assessment
        tr += f'<td style="{plain_s}">{_v(row.get("skill_designed"), 0)}</td>'
        tr += f'<td style="{plain_s}">{_v(row.get("skill_till_date"), 1)}</td>'
        tr += _na_cell()  # Skill Scheduled — subject mapping unclear
        tr += _pct_cell(row.get("skill_attendance_pct"))
        tr += _pct_cell(row.get("skill_pass_pct"))
        # Color 8 — Academic
        tr += _pct_cell(row.get("academic_attendance_pct"))
        tr += _pct_cell(row.get("academic_pass_pct"))
        tr += "</tr>"
        data_rows_html.append(tr)
    data_rows_html.append(summary_row)

    table_html = (
        '<div style="overflow-x:auto;border:1px solid #E2E8F0;border-radius:12px;'
        'box-shadow:0 1px 4px rgba(0,0,0,.06);margin-bottom:10px;">'
        '<table style="border-collapse:collapse;white-space:nowrap;width:100%;'
        'font-family:Inter,ui-sans-serif,sans-serif;">'
        f"<thead><tr>{grp_row}</tr><tr>{col_row}</tr></thead>"
        f"<tbody>{''.join(data_rows_html)}</tbody>"
        "</table></div>"
    )

    course_names = [r["course"] for r in course_rows]
    selected = st.selectbox(
        "Select a course to open the detail view",
        ["-- Select course --"] + course_names,
        key="cm_course_select",
    )

    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px'>"
        "<div style='width:4px;height:1.1em;background:linear-gradient(180deg,#6366f1,#4f46e5);"
        "border-radius:999px;flex-shrink:0'></div>"
        "<div style='font-size:1rem;font-weight:700;color:#0F172A;letter-spacing:-0.01em'>Course Overview</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(table_html, unsafe_allow_html=True)

    if selected and selected != "-- Select course --":
        return selected
    return None


def render_course_matrix(course_rows: list[dict], selected_course: str | None) -> str | None:
    """
    Renders the course matrix as a compact st.dataframe with color-coded % values.
    Clicking any row navigates to the course detail view.
    Returns the clicked course name or None.
    """
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin-bottom:3px'>"
        "<div style='width:4px;height:1.1em;background:linear-gradient(180deg,#6366f1,#4f46e5);border-radius:999px;flex-shrink:0'></div>"
        "<div class='course-matrix-header'>Course Matrix</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='course-matrix-sub' style='padding-left:14px;margin-bottom:8px'>"
        "Click any row to open the course detail view Â· Planned slots Â· delivery rates Â· completion Â· quiz pass Â· skill pass"
        "</div>",
        unsafe_allow_html=True,
    )

    def _s(v):
        try:
            return None if (v is None or pd.isna(v)) else float(v)
        except (TypeError, ValueError):
            return None

    # Build flat DataFrame for st.dataframe
    display_rows = []
    course_index = []  # original course names indexed by row position
    for i, row in enumerate(course_rows):
        cname = row.get("course", "")
        course_index.append(cname)
        display_rows.append({
            "#":                        i + 1,
            "Course":                   cname,
            "Planned Lecture":          round(_s(row.get("lecture_slots")) or 0),
            "Planned Practice":         round(_s(row.get("practice_slots")) or 0),
            "Planned Module Quiz":      round(_s(row.get("exam_slots")) or 0),
            "Planned Content Slots":    round(_s(row.get("total_slots")) or 0),
            "Delivered Content Slots Till Date (Avg)": round(_s(row.get("delivered")) or 0),
            "Lecture Delivery %":       _s(row.get("lecture_pct")),
            "Practice Delivery %":      _s(row.get("practice_pct")),
            "Module Quiz Conduction %": _s(row.get("exam_pct")),
            "Student Completion %":      _s(row.get("completion_pct")),
            "Practice Completion %":    _s(row.get("practice_completion_pct")),
            "CR Quiz Pass %":           _s(row.get("quiz_pass_pct")),
            "Module Quiz Pass %":       _s(row.get("module_quiz_pass_pct")),
            "Skill Pass %":             _s(row.get("skill_pass_pct")),
        })

    cm_df = pd.DataFrame(display_rows)
    _cm_pct_cols = ["Lecture Delivery %", "Practice Delivery %", "Module Quiz Conduction %",
                    "Student Completion %", "Practice Completion %", "CR Quiz Pass %", "Module Quiz Pass %", "Skill Pass %"]
    _cm_styled = _apply_pct_colors(cm_df, _cm_pct_cols)

    cm_key = f"course_matrix_table_{st.session_state.get('cm_table_nonce', 0)}"
    st.markdown(
        "<div style='background:var(--surface,#fff);border:1px solid var(--border,#e2e8f0);"
        "border-radius:12px;padding:4px 0 0 0;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden;'>",
        unsafe_allow_html=True,
    )
    cm_selection = st.dataframe(
        _cm_styled,
        use_container_width=True,
        hide_index=True,
        key=cm_key,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "#":                        st.column_config.NumberColumn("#", format="%d", width=40),
            "Course":                   st.column_config.TextColumn("Course", width="large"),
            "Planned Lecture":          st.column_config.NumberColumn("Planned Lecture", format="%.0f", width=100),
            "Planned Practice":         st.column_config.NumberColumn("Planned Practice", format="%.0f", width=100),
            "Planned Module Quiz":      st.column_config.NumberColumn("Planned Module Quiz", format="%.0f", width=110),
            "Planned Content Slots":    st.column_config.NumberColumn("Planned Content Slots", format="%.0f", width=60),
            "Delivered Content Slots Till Date (Avg)": st.column_config.NumberColumn("Delivered Content Slots Till Date (Avg)", format="%.0f", width=140),
            "Lecture Delivery %":       st.column_config.NumberColumn("Lecture Delivery %", format="%.1f%%", width=110),
            "Practice Delivery %":      st.column_config.NumberColumn("Practice Delivery %", format="%.1f%%", width=115),
            "Module Quiz Conduction %": st.column_config.NumberColumn("Module Quiz Conduction %", format="%.1f%%", width=130),
            "Student Completion %":     st.column_config.NumberColumn("Student Completion %", format="%.1f%%", width=120),
            "Practice Completion %":    st.column_config.NumberColumn("Practice Completion %", format="%.1f%%", width=125),
            "CR Quiz Pass %":           st.column_config.NumberColumn("CR Quiz Pass %", format="%.1f%%", width=105),
            "Module Quiz Pass %":       st.column_config.NumberColumn("Module Quiz Pass %", format="%.1f%%", width=115),
            "Skill Pass %":             st.column_config.NumberColumn("Skill Pass %", format="%.1f%%", width=95),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Handle row click â†' return course name
    sel_rows = []
    if cm_selection is not None:
        sel_state = getattr(cm_selection, "selection", None)
        if sel_state is not None:
            sel_rows = list(getattr(sel_state, "rows", []) or [])
        elif isinstance(cm_selection, dict):
            sel_rows = cm_selection.get("selection", {}).get("rows", []) or []
    if sel_rows:
        st.session_state["cm_table_nonce"] = st.session_state.get("cm_table_nonce", 0) + 1
        return course_index[sel_rows[0]]
    return None


def render_course_detail_header(course_name: str, delivery_row: dict | None, units_df: pd.DataFrame):
    """Renders the course title, subtitle, and stats bar."""
    delivered_total = round(float(delivery_row["total_delivered"])) if delivery_row and delivery_row.get("total_delivered") is not None else None
    planned_total   = round(float(delivery_row["total_planned"]))   if delivery_row and delivery_row.get("total_planned")   is not None else None
    adherence_pct   = delivery_row["adherence_pct"]        if delivery_row else None

    # Unit counts from units_df (fetch_course_session_units)
    # Each unit appears once per section -- deduplicate by unit name for totals
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
            return "N/A", "no units"
        return f"{done}/{total}", "delivered"

    lec_val,  lec_sub  = _unit_stat(lec_done,  lec_total)
    prac_val, prac_sub = _unit_stat(prac_done, prac_total)
    exam_val, exam_sub = _unit_stat(exam_done, exam_total)

    adh_sub = f"{adherence_pct:.1f}% adherence" if adherence_pct is not None else ""
    delivered_str = f"{delivered_total:d}" if delivered_total is not None else "N/A"
    planned_str = f"{planned_total:d}" if planned_total is not None else "N/A"

    adh_accent = "accent-green" if adherence_pct is not None and adherence_pct >= 75 else ("accent-orange" if adherence_pct is not None and adherence_pct >= 50 else "")
    st.markdown(
        f"""
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>
          <div style='width:4px;height:1.4em;background:linear-gradient(180deg,#6366f1,#4f46e5);border-radius:999px;flex-shrink:0'></div>
          <span class='cd-title'>{escape_html(course_name)}</span>
        </div>
        <div class='cd-subtitle' style='padding-left:14px'>{escape_html(delivered_str)}/{escape_html(planned_str)} content slots delivered till date on average</div>
        <div class='cd-stats-bar'>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>&#128203; Planned Content Slots</div>
            <div class='cd-stat-value'>{escape_html(planned_str)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>&#9989; Delivered Content Slots Till Date</div>
            <div class='cd-stat-value {adh_accent}'>{escape_html(delivered_str)}</div>
            <div class='cd-stat-sub'>{escape_html(adh_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>&#128218; Lecture Units</div>
            <div class='cd-stat-value'>{escape_html(lec_val)}</div>
            <div class='cd-stat-sub'>{escape_html(lec_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>&#128295; Practice Units</div>
            <div class='cd-stat-value'>{escape_html(prac_val)}</div>
            <div class='cd-stat-sub'>{escape_html(prac_sub)}</div>
          </div>
          <div class='cd-stat-item'>
            <div class='cd-stat-label'>&#128221; Exam Units</div>
            <div class='cd-stat-value'>{escape_html(exam_val)}</div>
            <div class='cd-stat-sub'>{escape_html(exam_sub)}</div>
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

    # â€â€ Section filter pill state â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if "lpe_sec" not in st.session_state or st.session_state["lpe_sec"] not in section_options:
        st.session_state["lpe_sec"] = "All"
    cur_sec = st.session_state["lpe_sec"]

    # Compute total students for subtitle
    has_students = "total_students" in units_df.columns
    if has_students and cur_sec == "All":
        # Sum across sections: one row per (unit, section) â†' sum for all units in All view
        sec_students = units_df.groupby("section")["total_students"].max().sum()
        total_students_display = int(sec_students) if sec_students and not pd.isna(sec_students) else None
    elif has_students and cur_sec != "All":
        sec_df = units_df[units_df["section"] == cur_sec]
        ts_val = sec_df["total_students"].max() if not sec_df.empty else None
        total_students_display = int(ts_val) if ts_val and not pd.isna(ts_val) else None
    else:
        total_students_display = None

    # â€â€ Header row: title left, section pills right â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    hcol_left, hcol_right = st.columns([2, 3])
    with hcol_left:
        sec_label = "All Sections" if cur_sec == "All" else cur_sec
        stu_label = f" Â· {total_students_display} students" if total_students_display else ""
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

    # â€â€ Type filter â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    type_options = ["All Types", "LECTURE", "PRACTICE", "EXAM"]
    if "lpe_type" not in st.session_state:
        st.session_state["lpe_type"] = "All Types"
    type_cols = st.columns(len(type_options))
    for k, topt in enumerate(type_options):
        with type_cols[k]:
            if st.button(topt, key=f"lpe_type_{topt}_{k}", use_container_width=True):
                st.session_state["lpe_type"] = topt
                st.rerun()
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # â€â€ Filter / aggregate â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    filtered = units_df if cur_sec == "All" else units_df[units_df["section"] == cur_sec]

    # Apply type filter
    cur_type = st.session_state.get("lpe_type", "All Types")
    if cur_type != "All Types":
        filtered = filtered[filtered["session_type"].str.upper() == cur_type]

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
        # the total university enrollment -- not just the sections that happen to
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

    # â€â€ Build rows using <table> so Streamlit renders reliably â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
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
        pct_str = f"{pct:.1f}%" if pct is not None else "N/A"

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
            stu_html = '<span style="color:#94a3b8">N/A</span>'

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


def render_tab_assessments(
    assessment_df: pd.DataFrame,
    course_name: str,
    sections: list[str],
    institute: str = "",
    batch: str = "",
    semester: str = "",
    selected_section: str = "",
):
    """Renders assessment tab with All Sections / Section Level / Subject Level views."""
    # â€â€ Existing course-level summary â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if not assessment_df.empty:
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

    # â€â€ Skill Assessment Detail (university-level, three views) â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if not institute:
        if assessment_df.empty:
            st.info("No assessment data available for this course.")
        return

    st.markdown("---")
    st.markdown("**Skill & Graded Assessment Analysis**")

    view_options = ["All Sections", "Section Level", "Subject Level"]
    view_col, _ = st.columns([2, 3])
    with view_col:
        sa_view = st.radio(
            "View",
            view_options,
            horizontal=True,
            key="sa_detail_view",
            label_visibility="collapsed",
        )

    with st.spinner("Loading assessment data..."):
        sa_df = fetch_skill_assessment_detail(batch, semester, institute, selected_section)

    if sa_df.empty:
        st.info("No skill/graded assessment data available for this university.")
        return

    if sa_view == "All Sections":
        # â€â€ Date Ã— Type summary â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        summary = (
            sa_df.groupby(["assessment_date", "assessment_type"], as_index=False)
            .agg(
                total_users=("user_id", "nunique"),
                avg_score=("score_pct", "mean"),
                median_score=("score_pct", "median"),
            )
            .sort_values("assessment_date")
        )
        rows_html = ""
        for _, row in summary.iterrows():
            rows_html += f"""
            <tr>
              <td>{escape_html(str(row['assessment_date']))}</td>
              <td><span class='unit-type-badge badge-exam'>{escape_html(str(row['assessment_type']))}</span></td>
              <td style='text-align:right'>{int(row['total_users'])}</td>
              <td style='text-align:right'>{row['avg_score']:.2f}%</td>
              <td style='text-align:right'>{row['median_score']:.2f}%</td>
            </tr>"""
        st.markdown(
            f"""<table class="unit-table">
              <thead><tr>
                <th>Assessment Date</th><th>Assessment Type</th>
                <th style='text-align:right'>Total Users - Attempted</th>
                <th style='text-align:right'>AVG % Score</th>
                <th style='text-align:right'>Median % Score</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>""",
            unsafe_allow_html=True,
        )

    elif sa_view == "Section Level":
        # â€â€ Assessment Wise Users & Section Scores â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        st.markdown("<div style='color:#0e7490;font-weight:700;font-size:1.05rem;text-align:center;margin-bottom:8px'>Assessment Wise Users & Section Scores</div>", unsafe_allow_html=True)
        section_detail = (
            sa_df.groupby(["assessment_date", "assessment_type", "assessment_title", "section_tech_stack"], as_index=False)
            .agg(
                total_students=("user_id", "nunique"),
                avg_score=("score_pct", "mean"),
            )
            .sort_values(["assessment_date", "assessment_title"])
        )
        rows_html = ""
        prev_date = prev_type = prev_title = None
        for _, row in section_detail.iterrows():
            date_str  = str(row["assessment_date"]) if row["assessment_date"] != prev_date else ""
            type_str  = row["assessment_type"] if row["assessment_type"] != prev_type or row["assessment_date"] != prev_date else ""
            title_str = row["assessment_title"] if row["assessment_title"] != prev_title or row["assessment_date"] != prev_date else ""
            score_cls = "accent-green" if row["avg_score"] >= 80 else ("accent-orange" if row["avg_score"] >= 50 else "accent-red")
            rows_html += f"""
            <tr>
              <td>{escape_html(date_str)}</td>
              <td><span class='unit-type-badge badge-exam'>{escape_html(type_str)}</span></td>
              <td>{escape_html(title_str)}</td>
              <td style='color:#0284c7'>{escape_html(str(row['section_tech_stack']))}</td>
              <td style='text-align:right'>{int(row['total_students'])}</td>
              <td style='text-align:right'><span class='{score_cls}'>{row['avg_score']:.2f}%</span></td>
            </tr>"""
            prev_date = row["assessment_date"]
            prev_type = row["assessment_type"]
            prev_title = row["assessment_title"]
        st.markdown(
            f"""<table class="unit-table">
              <thead><tr>
                <th>Assessment Date</th><th>Assessment Type</th><th>Assessment Title</th>
                <th>Subject (Tech Stack)</th>
                <th style='text-align:right'>Total Unique Students</th>
                <th style='text-align:right'>AVG % Section Score</th>
              </tr></thead>
              <tbody>{rows_html}</tbody>
            </table>""",
            unsafe_allow_html=True,
        )

        # â€â€ Section Ã— Tech Stack Pivot â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        st.markdown("<div style='color:#0e7490;font-weight:700;font-size:1.05rem;text-align:center;margin:16px 0 8px'>Section Tech Stack Wise Performance</div>", unsafe_allow_html=True)
        pivot = (
            sa_df.groupby(["section_name", "section_tech_stack"], as_index=False)
            .agg(avg_score=("score_pct", "mean"))
        )
        if not pivot.empty:
            pivot_wide = pivot.pivot_table(index="section_name", columns="section_tech_stack", values="avg_score", aggfunc="mean")
            pivot_wide = pivot_wide.reset_index().rename(columns={"section_name": "Section"})
            pivot_wide.columns.name = None
            # Format % columns
            subject_cols = [c for c in pivot_wide.columns if c != "Section"]
            for col in subject_cols:
                pivot_wide[col] = pivot_wide[col].apply(lambda v: f"{v:.1f}%" if pd.notna(v) else "--")
            st.dataframe(pivot_wide, hide_index=True, use_container_width=True)

    else:  # Subject Level
        # â€â€ User Ã— Tech Stack Performance â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        st.markdown("<div style='color:#0e7490;font-weight:700;font-size:1.05rem;text-align:center;margin-bottom:8px'>User - Tech Stack Wise Assessment Performance</div>", unsafe_allow_html=True)
        user_pivot = (
            sa_df.groupby(["user_id", "section_name", "section_tech_stack"], as_index=False)
            .agg(best_score=("score_pct", "max"))
        )
        if not user_pivot.empty:
            user_wide = user_pivot.pivot_table(
                index=["user_id", "section_name"],
                columns="section_tech_stack",
                values="best_score",
                aggfunc="max",
            ).reset_index()
            user_wide.columns.name = None
            subject_cols = [c for c in user_wide.columns if c not in ("user_id", "section_name")]
            for col in subject_cols:
                user_wide[col] = user_wide[col].apply(lambda v: f"{v:.1f}%" if pd.notna(v) else "--")
            st.dataframe(user_wide, hide_index=True, use_container_width=True)

        # â€â€ Detailed per-student table â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        st.markdown("<div style='color:#0e7490;font-weight:700;font-size:1.05rem;text-align:center;margin:16px 0 8px'>Assessment Performance Summary</div>", unsafe_allow_html=True)
        detail = sa_df[["assessment_date","section_name","user_id","assessment_type","section_tech_stack",
                         "assessment_title","user_section_score","section_actual_score","score_pct"]].copy()
        detail = detail.rename(columns={
            "assessment_date": "Assessment Date",
            "section_name": "Section Name",
            "user_id": "User ID",
            "assessment_type": "Assessment Type",
            "section_tech_stack": "Tech Stack",
            "assessment_title": "Assessment Title",
            "user_section_score": "User Score",
            "section_actual_score": "Max Score",
            "score_pct": "Score %",
        })
        detail["Score %"] = detail["Score %"].apply(lambda v: f"{v:.2f}%" if pd.notna(v) else "--")
        st.dataframe(detail.sort_values(["Assessment Date","Section Name","User ID"]), hide_index=True, use_container_width=True)


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
        pct_str = f"{pct:.1f}%" if pct is not None else "--"
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
            /* â€â€ Design tokens â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            :root {
                --primary:       #4f46e5;
                --primary-dark:  #3730a3;
                --primary-light: #ede9fe;
                --accent:        #0ea5e9;
                --bg:            #f1f5f9;
                --surface:       #ffffff;
                --border:        #e2e8f0;
                --border-light:  #f1f5f9;
                --txt-primary:   #0f172a;
                --txt-secondary: #475569;
                --txt-muted:     #94a3b8;
                --green:         #059669;
                --orange:        #d97706;
                --red:           #dc2626;
                --green-bg:      #ecfdf5;
                --orange-bg:     #fffbeb;
                --red-bg:        #fef2f2;
                --shadow-sm:     0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.04);
                --shadow-md:     0 4px 12px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.04);
                --shadow-lg:     0 10px 32px rgba(15,23,42,0.10), 0 4px 8px rgba(15,23,42,0.05);
                --radius-sm:     8px;
                --radius-md:     12px;
                --radius-lg:     16px;
                --radius-xl:     20px;
            }

            /* â€â€ Base â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .stApp {
                background: var(--bg);
                color: var(--txt-primary);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            }
            .block-container {
                max-width: 1380px;
                padding-top: 1.5rem;
                padding-left: 2.5rem;
                padding-right: 2.5rem;
                padding-bottom: 3rem;
            }
            * { box-sizing: border-box; }
            div[data-testid="column"] { min-width: 0; }
            div[data-testid="column"] > div { width: 100%; }

            /* â€â€ Topbar â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            [data-testid="stHeader"] {
                background: rgba(241, 245, 249, 0.92);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-bottom: 1px solid var(--border);
            }
            [data-testid="stToolbar"] { right: 1rem; }

            /* â€â€ Sidebar â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            [data-testid="stSidebar"] {
                background: #1e1b4b;
                border-right: none;
                box-shadow: 2px 0 20px rgba(15,23,42,0.15);
            }
            [data-testid="stSidebar"]::before {
                content: '';
                display: block;
                height: 3px;
                background: linear-gradient(90deg, #6366f1 0%, #0ea5e9 100%);
                position: absolute;
                top: 0; left: 0; right: 0;
            }
            [data-testid="stSidebar"] * { color: #ffffff !important; }
            [data-testid="stSidebar"] label p { color: #ffffff !important; font-size: 0.82rem; }
            [data-testid="stSidebar"] .stRadio label p { color: #ffffff !important; }
            [data-testid="stSidebar"] .stRadio label span { color: #ffffff !important; }
            [data-testid="stSidebar"] p { color: #ffffff !important; }
            [data-testid="stSidebar"] span { color: #ffffff !important; }
            [data-testid="stSidebar"] [data-baseweb="select"] > div {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(165,180,252,0.2);
                border-radius: var(--radius-md);
                color: #ffffff;
            }
            [data-testid="stSidebar"] .stRadio > div {
                background: transparent;
                border: none;
            }
            [data-testid="stSidebar"] .stRadio label {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(165,180,252,0.15);
                border-radius: var(--radius-sm);
                padding: 6px 12px;
                margin-bottom: 4px;
                transition: all 0.15s;
            }
            [data-testid="stSidebar"] .stButton button {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                border: none;
                color: white;
                font-weight: 700;
                letter-spacing: 0.02em;
                border-radius: var(--radius-md);
                box-shadow: 0 4px 12px rgba(99,102,241,0.4);
                transition: all 0.2s;
            }
            [data-testid="stSidebar"] .stButton button:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(99,102,241,0.5);
            }
            [data-testid="stSidebar"] hr { border-color: rgba(165,180,252,0.15); }

            /* â€â€ Main controls â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            [data-baseweb="select"] > div {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                min-height: 44px;
                box-shadow: var(--shadow-sm);
                transition: border-color 0.15s, box-shadow 0.15s;
            }
            [data-baseweb="select"] > div:focus-within {
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
            }
            [data-testid="stButton"] button {
                min-height: 40px;
                white-space: normal;
                line-height: 1.2;
                border-radius: var(--radius-md);
                font-weight: 600;
                transition: all 0.15s;
            }
            [data-testid="stButton"] button p { line-height: 1.2; }
            [data-testid="stButton"] button[kind="primary"] {
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                border: none;
                box-shadow: 0 2px 8px rgba(99,102,241,0.3);
            }
            [data-testid="stButton"] button[kind="primary"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(99,102,241,0.4);
            }
            .stSelectbox label p,
            .stRadio label p { font-weight: 600; color: var(--txt-secondary); }

            /* â€â€ Hero card â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .hero-card {
                position: relative;
                background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 75%, #6366f1 100%);
                border-radius: var(--radius-xl);
                color: white;
                padding: 32px 36px;
                box-shadow: 0 20px 60px rgba(67,56,202,0.35), 0 4px 16px rgba(15,23,42,0.1);
                margin-bottom: 24px;
                width: 100%;
                overflow: hidden;
            }
            .hero-card::before {
                content: '';
                position: absolute;
                top: -60px; right: -60px;
                width: 300px; height: 300px;
                background: radial-gradient(circle, rgba(165,180,252,0.18) 0%, transparent 70%);
                border-radius: 50%;
                pointer-events: none;
            }
            .hero-card::after {
                content: '';
                position: absolute;
                bottom: -40px; left: 30%;
                width: 200px; height: 200px;
                background: radial-gradient(circle, rgba(14,165,233,0.12) 0%, transparent 70%);
                border-radius: 50%;
                pointer-events: none;
            }
            .hero-eyebrow {
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.14em;
                color: #a5b4fc;
                text-transform: uppercase;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .hero-eyebrow::before {
                content: '';
                display: inline-block;
                width: 20px; height: 2px;
                background: #6366f1;
                border-radius: 999px;
            }
            .hero-title {
                font-size: 2.1rem;
                font-weight: 800;
                margin: 0;
                letter-spacing: -0.03em;
                line-height: 1.1;
            }
            .hero-subtitle {
                margin-top: 12px;
                font-size: 0.96rem;
                line-height: 1.65;
                max-width: 820px;
                color: rgba(199,210,254,0.85);
            }
            .hero-meta {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 8px;
                margin-top: 20px;
            }
            .hero-pill {
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(165,180,252,0.25);
                border-radius: 999px;
                padding: 5px 14px;
                font-size: 0.82rem;
                font-weight: 600;
                color: #e0e7ff;
                backdrop-filter: blur(4px);
                overflow-wrap: anywhere;
            }

            /* â€â€ Section headings â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .section-heading {
                margin: 8px 0 3px 0;
                font-size: 1.15rem;
                font-weight: 700;
                color: var(--txt-primary);
                letter-spacing: -0.02em;
                overflow-wrap: anywhere;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .section-heading::before {
                content: '';
                display: inline-block;
                width: 4px;
                height: 1.1em;
                background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
                border-radius: 999px;
                flex-shrink: 0;
            }
            .section-caption {
                color: var(--txt-secondary);
                margin-bottom: 14px;
                font-size: 0.9rem;
                overflow-wrap: anywhere;
                padding-left: 14px;
            }

            /* â€â€ Metric cards â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .metric-row-gap { height: 0.75rem; }
            .metric-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-left: 3px solid var(--primary);
                border-radius: var(--radius-lg);
                padding: 18px 20px 16px 20px;
                box-shadow: var(--shadow-md);
                min-height: 130px;
                height: 100%;
                display: flex;
                flex-direction: column;
                transition: transform 0.15s, box-shadow 0.15s;
                position: relative;
                overflow: hidden;
            }
            .metric-card::after {
                content: '';
                position: absolute;
                top: 0; right: 0;
                width: 80px; height: 80px;
                background: radial-gradient(circle at top right, rgba(99,102,241,0.06) 0%, transparent 70%);
                pointer-events: none;
            }
            .metric-label {
                color: var(--txt-secondary);
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 10px;
                min-height: 2.2em;
                line-height: 1.3;
                overflow-wrap: anywhere;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .metric-value {
                color: var(--txt-primary);
                font-size: 1.75rem;
                font-weight: 800;
                line-height: 1;
                margin-bottom: 6px;
                overflow-wrap: anywhere;
                letter-spacing: -0.02em;
            }
            .metric-help {
                color: var(--txt-muted);
                font-size: 0.76rem;
                line-height: 1.5;
                margin-top: auto;
                overflow-wrap: anywhere;
            }

            /* â€â€ Info cards â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .info-card {
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-left: 3px solid #3b82f6;
                border-radius: var(--radius-md);
                padding: 12px 16px;
                color: #1e40af;
                font-size: 0.88rem;
                margin-bottom: 14px;
                overflow-wrap: anywhere;
            }

            /* â€â€ Course Matrix â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .course-matrix-header {
                font-size: 1.1rem;
                font-weight: 700;
                color: var(--txt-primary);
                margin-bottom: 2px;
                letter-spacing: -0.02em;
            }
            .course-matrix-sub {
                font-size: 0.84rem;
                color: var(--txt-muted);
                margin-bottom: 16px;
            }
            .cm-card-container {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-md);
                font-size: 0.92rem;
            }
            .cm-card-header {
                display: flex;
                align-items: center;
                padding: 11px 18px;
                background: #f8fafc;
                border-bottom: 1px solid var(--border);
                font-size: 0.72rem;
                font-weight: 700;
                color: var(--txt-muted);
                text-transform: uppercase;
                letter-spacing: 0.07em;
            }
            .cm-card-row {
                display: flex;
                align-items: center;
                padding: 14px 18px;
                border-bottom: 1px solid var(--border-light);
                transition: background 0.12s;
            }
            .cm-card-row:last-child { border-bottom: none; }
            .cm-card-row:hover { background: #f8fafc; }
            /* Shared column widths */
            .cm-th-num   { width: 36px;  min-width: 36px; }
            .cm-th-course{ flex: 1;      padding-right: 16px; }
            .cm-th-adh   { width: 140px; min-width: 110px; }
            .cm-th-comp  { width: 140px; min-width: 110px; }
            .cm-th-quiz  { width: 90px;  min-width: 80px; }
            .cm-th-skill { width: 80px;  min-width: 70px; }
            .cm-th-arrow { width: 24px;  min-width: 24px; text-align: right; }
            .cm-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                background: var(--surface);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-md);
                font-size: 0.91rem;
            }
            .cm-table thead tr {
                background: #f8fafc;
                border-bottom: 2px solid var(--border);
            }
            .cm-table thead th {
                padding: 12px 14px;
                font-weight: 700;
                color: var(--txt-muted);
                font-size: 0.72rem;
                text-align: left;
                white-space: nowrap;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }
            .cm-table thead th.right { text-align: right; }
            .cm-table tbody tr {
                border-bottom: 1px solid var(--border-light);
                transition: background 0.12s;
            }
            .cm-table tbody tr:last-child { border-bottom: none; }
            .cm-table tbody tr:nth-child(even) { background: #fafafa; }
            .cm-table tbody tr:hover { background: #f0f4ff !important; }
            .cm-table td {
                padding: 13px 14px;
                vertical-align: middle;
            }
            .cm-row-num {
                color: var(--txt-muted);
                font-size: 0.78rem;
                font-weight: 500;
                min-width: 28px;
            }
            .cm-course-name {
                font-weight: 600;
                color: var(--txt-primary);
                font-size: 0.92rem;
            }
            .cm-sessions { font-size: 0.9rem; white-space: nowrap; }
            .cm-sessions .delivered { color: var(--txt-primary); font-weight: 600; }
            .cm-sessions .planned   { color: var(--txt-muted); }
            .cm-pct-cell { min-width: 110px; }
            .cm-pct-val {
                font-weight: 700;
                font-size: 0.92rem;
                margin-bottom: 5px;
            }
            .cm-bar-track {
                height: 5px;
                background: #e2e8f0;
                border-radius: 999px;
                width: 90px;
                overflow: hidden;
            }
            .cm-bar-fill {
                height: 5px;
                border-radius: 999px;
                transition: width 0.4s cubic-bezier(0.4,0,0.2,1);
            }
            .pct-green  { color: #059669; }
            .pct-orange { color: #d97706; }
            .pct-red    { color: #dc2626; }
            .bar-green  { background: linear-gradient(90deg, #059669, #10b981); }
            .bar-orange { background: linear-gradient(90deg, #d97706, #f59e0b); }
            .bar-red    { background: linear-gradient(90deg, #dc2626, #ef4444); }
            .bar-black  { background: linear-gradient(90deg, #4f46e5, #6366f1); }
            .cm-arrow { color: #cbd5e1; font-size: 0.9rem; }

            /* â€â€ Course Detail â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .cd-header-wrap {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 4px;
                flex-wrap: wrap;
            }
            .cd-title {
                font-size: 1.6rem;
                font-weight: 800;
                color: var(--txt-primary);
                line-height: 1.15;
                letter-spacing: -0.03em;
            }
            .cd-subtitle {
                font-size: 0.88rem;
                color: var(--txt-secondary);
                margin-bottom: 16px;
            }
            .cd-stats-bar {
                display: flex;
                gap: 0;
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-sm);
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            .cd-stat-item {
                flex: 1 1 120px;
                padding: 18px 22px;
                border-right: 1px solid var(--border-light);
                position: relative;
            }
            .cd-stat-item:first-child { border-left: 3px solid var(--primary); }
            .cd-stat-item:last-child { border-right: none; }
            .cd-stat-label {
                font-size: 0.72rem;
                font-weight: 700;
                color: var(--txt-muted);
                text-transform: uppercase;
                letter-spacing: 0.07em;
                margin-bottom: 8px;
            }
            .cd-stat-value {
                font-size: 1.65rem;
                font-weight: 800;
                color: var(--txt-primary);
                line-height: 1;
                letter-spacing: -0.02em;
            }
            .cd-stat-sub {
                font-size: 0.76rem;
                color: var(--txt-secondary);
                margin-top: 4px;
            }
            .cd-stat-value.accent-orange { color: var(--orange); }
            .cd-stat-value.accent-green  { color: var(--green); }

            /* â€â€ Unit table â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .unit-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                background: var(--surface);
                border-radius: var(--radius-md);
                overflow: hidden;
                box-shadow: var(--shadow-sm);
                font-size: 0.9rem;
            }
            .unit-table thead tr { background: #f8fafc; border-bottom: 2px solid var(--border); }
            .unit-table thead th {
                padding: 10px 14px;
                font-weight: 700;
                color: var(--txt-muted);
                font-size: 0.72rem;
                text-align: left;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }
            .unit-table tbody tr { border-bottom: 1px solid var(--border-light); }
            .unit-table tbody tr:nth-child(even) { background: #fafafa; }
            .unit-table tbody tr:last-child { border-bottom: none; }
            .unit-table tbody tr:hover { background: #f0f4ff; }
            .unit-table td { padding: 11px 14px; vertical-align: middle; }
            .unit-type-badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }
            .badge-lecture  { background: #e0e7ff; color: #3730a3; }
            .badge-practice { background: #d1fae5; color: #065f46; }
            .badge-exam     { background: #fef3c7; color: #92400e; }
            .badge-quiz     { background: #ede9fe; color: #5b21b6; }

            /* â€â€ Quiz card rows â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€*/
            .qz-card-container {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-sm);
                font-size: 0.9rem;
            }
            .qz-card-header {
                display: flex;
                align-items: center;
                padding: 11px 18px;
                background: #f8fafc;
                border-bottom: 1px solid var(--border);
                font-size: 0.72rem;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .qz-card-row {
                display: flex;
                align-items: center;
                padding: 13px 18px;
                border-bottom: 1px solid var(--border-light);
                transition: background 0.12s;
            }
            .qz-card-row:last-child { border-bottom: none; }
            .qz-card-row:hover { background: #f0f4ff; }
            .qz-num      { width: 34px; min-width: 34px; color: var(--txt-muted); font-size: 0.78rem; }
            .qz-name     { flex: 1; font-weight: 600; color: var(--txt-primary); padding-right: 12px; }
            .qz-badge    { width: 150px; min-width: 120px; display: inline-block;
                           padding: 3px 12px; border-radius: 999px; font-size: 0.72rem;
                           font-weight: 700; letter-spacing: 0.05em; text-align: center; text-transform: uppercase; }
            .qz-th-att   { width: 90px; min-width: 70px; font-size: 0.88rem; }
            .qz-th-pas   { width: 80px; min-width: 60px; font-size: 0.88rem; }
            .qz-th-score { width: 90px; min-width: 70px; font-size: 0.88rem; }
            .qz-th-pct   { width: 80px; min-width: 60px; font-weight: 700; }
            .qz-arrow    { width: 20px; min-width: 20px; color: #cbd5e1; text-align: right; }

            /* â€â€ LPE Card rows â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€*/
            .lpe-card-container {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-sm);
                font-size: 0.9rem;
            }
            .lpe-card-header {
                display: flex;
                align-items: center;
                padding: 11px 18px;
                background: #f8fafc;
                border-bottom: 1px solid var(--border);
                font-size: 0.72rem;
                font-weight: 700;
                color: var(--txt-muted);
                text-transform: uppercase;
                letter-spacing: 0.07em;
                gap: 0;
            }
            .lpe-card-row {
                display: flex;
                align-items: center;
                padding: 14px 18px;
                border-bottom: 1px solid var(--border-light);
                gap: 0;
                transition: background 0.12s;
            }
            .lpe-card-row:nth-child(even) { background: #fafafa; }
            .lpe-card-row:last-child { border-bottom: none; }
            .lpe-card-row:hover { background: #f0f4ff !important; }
            /* Column widths */
            .lpe-num,     .lpe-th-num     { width: 36px;  min-width: 36px;  color: var(--txt-muted); font-size: 0.78rem; }
            .lpe-name,    .lpe-th-name    { flex: 1;      font-weight: 600; color: var(--txt-primary); padding-right: 12px; }
            .lpe-badge,   .lpe-th-badge   { width: 100px; min-width: 90px; }
            .lpe-students,.lpe-th-students { width: 200px; min-width: 160px; font-size: 0.85rem; }
            .lpe-pct,     .lpe-th-pct     { width: 72px;  min-width: 60px;  font-weight: 700; font-size: 0.93rem; text-align: right; }
            .lpe-bar-wrap,.lpe-th-bar     { width: 110px; min-width: 80px;  margin: 0 12px; }
            .lpe-arrow,   .lpe-th-arrow   { width: 20px;  min-width: 20px;  color: #cbd5e1; text-align: right; }
            /* Badge styles for LPE */
            .lpe-badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }
            .lpe-badge-lecture  { background: #e0e7ff; color: #3730a3; }
            .lpe-badge-practice { background: #d1fae5; color: #065f46; }
            .lpe-badge-exam     { background: #fef3c7; color: #92400e; }
            .lpe-badge-quiz     { background: #ede9fe; color: #5b21b6; }
            /* Student count spans */
            .lpe-stu-count  { color: var(--txt-primary); font-weight: 600; }
            .lpe-stu-of     { color: var(--txt-secondary); }
            .lpe-stu-pending { color: #ef4444; font-size: 0.8rem; }
            /* LPE bar */
            .lpe-bar-wrap {
                height: 5px;
                background: var(--border);
                border-radius: 999px;
                overflow: hidden;
            }
            .lpe-bar-fill {
                height: 5px;
                border-radius: 999px;
                transition: width 0.4s cubic-bezier(0.4,0,0.2,1);
            }

            /* â€â€ Section filter pills â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .section-pills {
                display: flex;
                gap: 6px;
                flex-wrap: wrap;
                margin-bottom: 14px;
            }

            /* â€â€ Quiz funnel cards â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            .quiz-funnel-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-bottom: 18px;
            }
            .quiz-funnel-item {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 16px 18px;
                box-shadow: var(--shadow-sm);
            }
            .quiz-funnel-label { font-size: 0.76rem; font-weight: 600; color: var(--txt-muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em; }
            .quiz-funnel-value { font-size: 1.6rem; font-weight: 800; color: var(--txt-primary); letter-spacing: -0.02em; }
            .quiz-funnel-value.red    { color: var(--red); }
            .quiz-funnel-value.green  { color: var(--green); }
            .quiz-funnel-value.orange { color: var(--orange); }
            .quiz-funnel-sub { font-size: 0.76rem; color: var(--txt-muted); margin-top: 4px; }
            .quiz-pass-banner {
                display: flex;
                align-items: center;
                gap: 16px;
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                border: 1px solid rgba(16, 185, 129, 0.25);
                border-left: 4px solid #10b981;
                border-radius: var(--radius-lg);
                padding: 16px 22px;
                margin-bottom: 16px;
                flex-wrap: wrap;
            }
            .quiz-pass-label {
                font-size: 0.76rem;
                font-weight: 700;
                color: #065f46;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                white-space: nowrap;
            }
            .quiz-pass-value {
                font-size: 1.75rem;
                font-weight: 800;
                color: #059669;
                line-height: 1;
                white-space: nowrap;
                letter-spacing: -0.02em;
            }
            .quiz-pass-caption {
                font-size: 0.8rem;
                color: #047857;
                line-height: 1.5;
                opacity: 0.9;
            }

            /* â€â€ Data tables â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            div[data-testid="stDataFrame"] {
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-md);
                background: var(--surface);
            }

            /* â€â€ Tabs â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            div[data-testid="stTabs"] [data-baseweb="tab-list"] {
                gap: 6px;
                margin-bottom: 1.25rem;
                background: var(--bg);
                padding: 4px;
                border-radius: var(--radius-md);
                border: 1px solid var(--border);
                width: fit-content;
            }
            div[data-testid="stTabs"] button {
                font-weight: 600;
                font-size: 0.86rem;
                border: none;
                border-radius: var(--radius-sm);
                padding: 0.45rem 1rem;
                background: transparent;
                color: var(--txt-secondary);
                transition: all 0.15s;
            }
            div[data-testid="stTabs"] button:hover {
                background: var(--surface);
                color: var(--txt-primary);
            }
            div[data-testid="stTabs"] button[aria-selected="true"] {
                background: var(--surface);
                color: var(--primary);
                font-weight: 700;
                box-shadow: var(--shadow-sm);
            }
            div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
                display: none;
            }

            /* â€â€ Alerts / warnings â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            div[data-testid="stAlert"] {
                border-radius: var(--radius-md);
            }

            /* â€â€ Scrollbar â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
            ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

            /* â€â€ Responsive â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€ */
            @media (max-width: 900px) {
                .block-container { padding-left: 1rem; padding-right: 1rem; }
                .hero-card { padding: 24px 22px; border-radius: var(--radius-lg); }
                .hero-title { font-size: 1.6rem; }
                .metric-card { min-height: auto; }
                .metric-label { min-height: 0; }
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


_METRIC_ACCENT_COLORS = ["#4f46e5", "#0ea5e9", "#059669", "#d97706", "#8b5cf6", "#f43f5e", "#14b8a6", "#f59e0b"]


def _apply_pct_colors(df: "pd.DataFrame", pct_cols: list[str], deviation_cols: list[str] | None = None) -> "pd.DataFrame.style":
    """Return a pandas Styler that colours numeric % columns by value.

    Standard %:  â‰¥75 â†' green   50--75 â†' orange   <50 â†' red
    Deviation %: â‰¥0  â†' green   âˆ'25--0 â†' orange   <âˆ'25 â†' red
    """
    import pandas as _pd

    def _std_color(val):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return ""
        if v >= 75:
            return "color:#059669;font-weight:600"
        if v >= 50:
            return "color:#d97706;font-weight:600"
        return "color:#dc2626;font-weight:600"

    def _dev_color(val):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return ""
        if v >= 0:
            return "color:#059669;font-weight:600"
        if v >= -25:
            return "color:#d97706;font-weight:600"
        return "color:#dc2626;font-weight:600"

    styler = df.style
    valid_std = [c for c in pct_cols if c in df.columns]
    if valid_std:
        styler = styler.map(_std_color, subset=valid_std)
    if deviation_cols:
        valid_dev = [c for c in deviation_cols if c in df.columns]
        if valid_dev:
            styler = styler.map(_dev_color, subset=valid_dev)
    return styler


def render_metric_row(items):
    metric_rows = chunk_metric_items(items)
    global_idx = 0
    for row_index, row_items in enumerate(metric_rows):
        columns = st.columns(len(row_items), gap="medium")
        for column, item in zip(columns, row_items):
            accent = _METRIC_ACCENT_COLORS[global_idx % len(_METRIC_ACCENT_COLORS)]
            help_text = f"<div class='metric-help'>{escape_html(item.get('help', ''))}</div>" if item.get("help") else ""
            column.markdown(
                f"""
                <div class="metric-card" style="border-left-color:{accent}">
                    <div class="metric-label">{escape_html(item['label'])}</div>
                    <div class="metric-value" style="color:{accent}">{escape_html(item['value'])}</div>
                    {help_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
            global_idx += 1
        if row_index < len(metric_rows) - 1:
            st.markdown("<div class='metric-row-gap'></div>", unsafe_allow_html=True)


def render_copilot(batch: str, semester: str) -> None:
    """Render the AI Copilot chat interface."""
    from copilot.agent import run_agent_streaming

    api_key = get_config("OPENROUTER_API_KEY", "")

    # â€â€ Header â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    st.markdown(
        """
        <div class="hero-card" style="margin-bottom:20px">
            <div class="hero-eyebrow">AI-Powered</div>
            <h1 class="hero-title" style="font-size:1.6rem">NIAT Academic Operations Copilot</h1>
            <div class="hero-subtitle">Ask anything about delivery metrics, quiz performance, skill assessments,
            deviations, or trigger escalation workflows -- all via natural language.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # â€â€ API key gate â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if not api_key:
        st.error("**OPENROUTER_API_KEY not configured.** Add the following to `.streamlit/secrets.toml`:")
        st.code('OPENROUTER_API_KEY = "sk-or-v1-..."', language="toml")
        st.info("Get your free API key from openrouter.ai/keys -- the Copilot uses Claude Sonnet via OpenRouter.")
        return

    # â€â€ Capability chips â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    st.markdown(
        """
        <div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px'>
          <span style='background:#ede9fe;color:#4f46e5;padding:4px 12px;border-radius:999px;font-size:0.8rem;font-weight:600'>Query Metrics</span>
          <span style='background:#dcfce7;color:#15803d;padding:4px 12px;border-radius:999px;font-size:0.8rem;font-weight:600'>Detect Deviations</span>
          <span style='background:#fef3c7;color:#92400e;padding:4px 12px;border-radius:999px;font-size:0.8rem;font-weight:600'>Escalation Emails</span>
          <span style='background:#e0f2fe;color:#0369a1;padding:4px 12px;border-radius:999px;font-size:0.8rem;font-weight:600'>KPI Threshold Check</span>
          <span style='background:#fce7f3;color:#9d174d;padding:4px 12px;border-radius:999px;font-size:0.8rem;font-weight:600'>Generate Reports</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # â€â€ Session state â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if "copilot_display" not in st.session_state:
        st.session_state["copilot_display"] = []

    # â€â€ Quick-start suggestions (shown only when chat is empty) â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if not st.session_state["copilot_display"]:
        st.markdown("<div style='font-size:0.78rem;color:#64748b;margin-bottom:8px;font-weight:600'>Try asking:</div>", unsafe_allow_html=True)
        suggestions = [
            f"Which universities in {batch} {semester} have lecture delivery below 75%?",
            f"Show me the top 10 universities by avg delivery % for {semester}",
            f"Which universities have skill assessment conduction below 60% in {semester}?",
            f"Show deviation % for all universities in {batch} {semester}",
            "Check KPI thresholds for a university and draft an escalation email",
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            col = cols[i % 2]
            if col.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                st.session_state["copilot_pending"] = suggestion
                st.rerun()

    # â€â€ Render existing messages â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    for msg in st.session_state["copilot_display"]:
        with st.chat_message(msg["role"], avatar=None):
            st.markdown(msg["content"])
            # Show tool call log if present
            if msg["role"] == "assistant" and msg.get("tool_log"):
                with st.expander(f"🔧 {len(msg['tool_log'])} tool call(s) made", expanded=False):
                    for tc in msg["tool_log"]:
                        st.markdown(f"**`{tc['tool']}`**")
                        if tc["input"]:
                            st.json(tc["input"])
                        result = tc.get("result", {})
                        if "error" in result:
                            st.error(result["error"])
                        elif "data" in result:
                            import pandas as _pd
                            try:
                                _df = _pd.DataFrame(result["data"])
                                st.dataframe(_df, use_container_width=True, hide_index=True)
                                if result.get("truncated"):
                                    st.caption("Results truncated to 100 rows.")
                            except Exception:
                                st.json(result)
                        else:
                            st.json(result)

    # â€â€ Handle pending suggestion click â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    pending = st.session_state.pop("copilot_pending", None)

    # â€â€ Chat input â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    user_input = st.chat_input("Ask about operations, KPIs, deviations, or request an escalation email...")

    prompt = pending or user_input
    if not prompt:
        # Clear chat button
        if st.session_state["copilot_display"]:
            if st.button("Clear conversation", key="clear_copilot"):
                st.session_state["copilot_display"] = []
                st.rerun()
        return

    # Add user message to display
    st.session_state["copilot_display"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # â€â€ Run agent (streaming events) â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    bq_client = get_bigquery_client()
    history_for_agent = [
        m for m in st.session_state["copilot_display"][:-1]
        if m["role"] in ("user", "assistant") and isinstance(m.get("content"), str)
    ]

    tool_log: list[dict] = []
    final_text = ""

    with st.chat_message("assistant", avatar=None):
        status_placeholder = st.empty()
        response_placeholder = st.empty()
        accumulated_text = ""

        try:
            for event in run_agent_streaming(
                display_history=history_for_agent,
                user_prompt=prompt,
                bq_client=bq_client,
                api_key=api_key,
                batch=batch,
                semester=semester,
            ):
                etype = event.get("type")

                if etype == "tool_start":
                    tool_name = event["tool"]
                    nice = {
                        "run_bigquery_sql": "Querying BigQuery...",
                        "list_tables": "Listing tables...",
                        "get_table_schema": "Fetching schema...",
                        "check_kpi_thresholds": "Checking KPI thresholds...",
                        "send_escalation_email": "Sending escalation email...",
                        "build_escalation_report": "Building escalation report...",
                    }.get(tool_name, f"Running {tool_name}...")

                    status_placeholder.info(nice)
                    tool_log.append({"tool": tool_name, "input": event.get("input", {}), "result": {}})

                elif etype == "tool_result":
                    # Update the last log entry with the result
                    tool_name = event["tool"]
                    if tool_log and tool_log[-1]["tool"] == tool_name:
                        tool_log[-1]["result"] = event.get("result", {})
                    status_placeholder.empty()

                elif etype == "done":
                    final_text = event.get("text", "")
                    status_placeholder.empty()
                    response_placeholder.markdown(final_text)

                elif etype == "error":
                    status_placeholder.empty()
                    response_placeholder.error(f"Error: {event.get('message')}")
                    final_text = f"âš ï¸ Error: {event.get('message')}"

        except Exception as exc:
            status_placeholder.empty()
            response_placeholder.error(f"Copilot error: {exc}")
            final_text = f"âš ï¸ Copilot encountered an error: {exc}"

        # Show tool call summary inline
        if tool_log:
            with st.expander(f"🔧 {len(tool_log)} tool call(s) made", expanded=False):
                for tc in tool_log:
                    st.markdown(f"**`{tc['tool']}`**")
                    result = tc.get("result", {})
                    if "data" in result:
                        import pandas as _pd2
                        try:
                            _df2 = _pd2.DataFrame(result["data"])
                            st.dataframe(_df2, use_container_width=True, hide_index=True)
                        except Exception:
                            st.json(result)
                    elif result:
                        st.json(result)

    # Persist assistant response
    st.session_state["copilot_display"].append({
        "role": "assistant",
        "content": final_text,
        "tool_log": tool_log,
    })


def main():
    st.set_page_config(page_title="NIAT Analytics Streamlit", layout="wide")
    inject_custom_css()

    with st.sidebar:
        st.markdown(
            "<div style='padding:22px 6px 14px 6px'>"
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>"
            "<div style='width:34px;height:34px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:10px;"
            "display:flex;align-items:center;justify-content:center;font-size:1.05rem;font-weight:900;color:white;"
            "box-shadow:0 4px 12px rgba(99,102,241,0.45);flex-shrink:0'>N</div>"
            "<div>"
            "<div style='font-size:1.05rem;font-weight:800;color:#e0e7ff;letter-spacing:-0.01em;line-height:1.1'>NIAT Audit</div>"
            "<div style='font-size:0.7rem;color:#a5b4fc;margin-top:1px;letter-spacing:0.02em'>Delivery &amp; Assessment</div>"
            "</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='margin:0 0 16px 0;border:none;border-top:1px solid rgba(165,180,252,0.15)'>", unsafe_allow_html=True)

        # â€â€ Mode toggle â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        _mode = st.session_state.get("app_mode", "dashboard")
        _copilot_active = _mode == "copilot"
        _mode_label = "Back to Dashboard" if _copilot_active else "AI Copilot"
        if st.button(_mode_label, use_container_width=True, key="mode_toggle"):
            st.session_state["app_mode"] = "dashboard" if _copilot_active else "copilot"
            st.rerun()
        st.markdown("<hr style='margin:12px 0 16px 0;border:none;border-top:1px solid rgba(165,180,252,0.15)'>", unsafe_allow_html=True)

        st.markdown("<div style='font-size:0.67rem;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px'>Filters</div>", unsafe_allow_html=True)
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

        st.markdown("<hr style='margin:14px 0;border:none;border-top:1px solid rgba(165,180,252,0.15)'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.67rem;font-weight:700;color:#6366f1;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px'>View</div>", unsafe_allow_html=True)
        analysis_type = st.radio(
            "Grouping Logic",
            ["overview", "design", "delivered"],
            format_func=lambda v: {"overview": "Overview", "design": "Planned Bands", "delivered": "Delivered Bands"}[v],
            label_visibility="collapsed",
        )
        st.markdown(
            {
                "overview": "<div style='font-size:0.73rem;color:#a5b4fc;line-height:1.5;padding:6px 4px'>University table -- click a row to open course breakdown.</div>",
                "design":   "<div style='font-size:0.73rem;color:#a5b4fc;line-height:1.5;padding:6px 4px'>Groups universities by <strong style=\"color:#c7d2fe\">planned</strong> session volume.</div>",
                "delivered":"<div style='font-size:0.73rem;color:#a5b4fc;line-height:1.5;padding:6px 4px'>Groups universities by <strong style=\"color:#c7d2fe\">delivered</strong> slot count.</div>",
            }[analysis_type],
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='margin:14px 0;border:none;border-top:1px solid rgba(165,180,252,0.15)'>", unsafe_allow_html=True)
        load_clicked = st.button("Refresh Data", type="primary", use_container_width=True)

    # â€â€ Copilot mode -- skip dashboard entirely â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
    if st.session_state.get("app_mode") == "copilot":
        render_copilot(batch, semester)
        return

    if load_clicked or "semester_df" not in st.session_state or "planned_slots_df" not in st.session_state or st.session_state.get("batch") != batch or st.session_state.get("semester") != semester:
        with st.spinner("Fetching data from BigQuery..."):
            semester_df = fetch_semester_data(batch, semester)
            planned_slots_df = fetch_planned_content_slots(batch, semester)
            progress_slots_df = fetch_progress_delivered_slots(batch, semester)
            assessment_df = fetch_assessment_data(batch, semester)
            new_metrics = fetch_all_new_metrics(batch, semester)
            sem_course_titles = fetch_sem_course_titles(batch, semester)
            portal_subject_map = fetch_portal_subject_map(batch, semester)
            st.session_state["semester_df"] = semester_df
            st.session_state["planned_slots_df"] = planned_slots_df
            st.session_state["progress_slots_df"] = progress_slots_df
            st.session_state["assessment_df"] = assessment_df
            st.session_state["new_metrics"] = new_metrics
            st.session_state["sem_course_titles"] = sem_course_titles
            st.session_state["portal_subject_map"] = portal_subject_map
            st.session_state["batch"] = batch
            st.session_state["semester"] = semester

    semester_df = st.session_state.get("semester_df", pd.DataFrame())
    planned_slots_df = st.session_state.get("planned_slots_df", pd.DataFrame())
    progress_slots_df = st.session_state.get("progress_slots_df", pd.DataFrame())
    assessment_df = st.session_state.get("assessment_df", pd.DataFrame())
    new_metrics = st.session_state.get("new_metrics", {})
    sem_course_titles = st.session_state.get("sem_course_titles", {})
    portal_subject_map = st.session_state.get("portal_subject_map", {})

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
            <h1 class="hero-title">NIAT Delivery &amp; Assessment</h1>
            <div class="hero-subtitle">University-level delivery tracking, course completion rates, and assessment performance - across lectures, practice, exams, quizzes, and skill assessments.</div>
            <div class="hero-meta">
                <div class="hero-pill">&#127979; {escape_html(batch)}</div>
                <div class="hero-pill">&#128197; {escape_html(semester)}</div>
                <div class="hero-pill">&#128202; {escape_html(analysis_label)}</div>
                <div class="hero-pill">&#128337; {escape_html(last_updated)}</div>
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
                "Lecture Delivery %": round(item["avgLectureCompletion"], 1),
                "Practice Delivery %": round(item["avgPracticeCompletion"], 1),
                "Exam Delivery %": round(item["avgExamCompletion"], 1),
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
    _subject_map   = dict(portal_subject_map)
    _subject_map.update(fetch_university_subject_map(batch, semester, selected_university))
    university_metrics = build_university_metrics(semester_df, assessment_df, selected_university, selected_section, semester, sem_course_titles, quiz_pass_pct=_quiz_pass_pct, subject_map=_subject_map)
    if university_metrics is None:
        st.warning("No university data available for the current selection.")
        st.stop()
    course_table, hidden_courses = filter_course_table(university_metrics["courseTable"], semester, selected_university)
    dates = get_semester_dates_for_institute(selected_university, semester, batch)

    timeline_df = build_university_timeline_rows(all_universities, semester, batch)
    overview_df = build_university_overview_rows(all_universities, semester, batch, planned_slots_df, progress_slots_df, new_metrics, assessment_df=assessment_df)
    top_metrics = [
        {"label": "Universities", "value": format_metric_value(len(overview_df), decimals=0), "help": "Institutions with schedule data in the current view."},
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
        st.caption(f"Planned content slots till date is calculated as of {format_today_display_date()}.")

        with st.expander("Metric definitions", expanded=False):
            _ov_metrics = [
                # Institute Info
                ("Institute",                               "University / institute name."),
                ("Mode",                                    "Delivery mode: Full Delivery, Co Delivery, or Hybrid Delivery."),
                ("Start Date",                              "Configured semester start date for this institute."),
                ("End Date",                                "Configured semester end date for this institute."),
                ("Total Designed",                          "Total planned sessions = Lecture + Practice + Module Quiz slots."),
                # Lectures
                ("Lectures - Designed",                     "Total lecture sessions planned for the full semester."),
                ("Lectures - Designed Till Date",           "Pro-rated lecture sessions expected by today based on semester pacing (Designed × elapsed days / total days)."),
                ("Lectures - Scheduled",                    "COUNT of distinct lecture session IDs where delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED' (source: session_adherence table), averaged across sections."),
                ("Lectures - Deviation %",                  "Positive = ahead of schedule. Negative = behind schedule. Formula: (Scheduled − Designed Till Date) / Designed Till Date × 100."),
                # Classroom Quiz
                ("Classroom Quiz - Attend %",               "% of enrolled students who attempted classroom (LP_QUIZ) quizzes."),
                # Practice
                ("Practice - Designed",                     "Total practice sessions planned for the full semester."),
                ("Practice - Designed Till Date",           "Pro-rated practice sessions expected by today based on semester pacing."),
                ("Practice - Scheduled",                    "COUNT of distinct practice session IDs where delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED' (source: session_adherence table), averaged across sections."),
                ("Practice - Deviation %",                  "Positive = ahead of schedule. Negative = behind schedule."),
                # Practice Completion
                ("Practice Completion %",                   "% of assigned practice content units completed by students."),
                # Module Quiz
                ("Module Quiz - Designed",                  "Total module quiz (EXAM-type) sessions planned for the full semester."),
                ("Module Quiz - Designed Till Date",        "Pro-rated module quizzes expected by today based on semester pacing."),
                ("Module Quiz - Scheduled",                 "COUNT of distinct EXAM session IDs where delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED' (source: session_adherence table), averaged across sections."),
                ("Module Quiz - Deviation %",               "Positive = ahead of schedule. Negative = behind schedule."),
                ("Module Quiz - Attend %",                  "% of enrolled students who participated in module quizzes."),
                ("Module Quiz - Pass %",                    "% of module quiz participants who passed (score ≥ 80%)."),
                # Skill Assessment
                ("Skill - Designed",                        "Number of skill assessments planned per semester (fixed at 5)."),
                ("Skill - Designed Till Date",              "Pro-rated skill assessments expected by today (5 × pacing ratio)."),
                ("Skill - Scheduled",                       "COUNT of distinct EXAM session IDs whose session_name_enum contains 'skill' and delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED' (source: session_adherence table)."),
                ("Skill - Attend %",                        "% of enrolled students who participated in skill assessments."),
                ("Skill - Pass %",                          "% of skill assessment participants who passed (score ≥ 80%)."),
                # Academic
                ("Academic - Attend %",                     "% of students who attempted the academic (semester-end) assessment."),
                ("Academic - Pass %",                       "% of academic assessment participants who passed based on university criteria."),
            ]
            _metric_items = "".join(
                f'<li style="margin-bottom:10px;">'
                f'<code style="color:#059669;background:rgba(5,150,105,.08);'
                f'padding:2px 8px;border-radius:4px;font-size:0.85em;">{m}</code>'
                f' : {d}'
                f'</li>'
                for m, d in _ov_metrics
            )
            st.markdown(
                f'<ul style="list-style:disc;padding-left:20px;line-height:1.8;">{_metric_items}</ul>',
                unsafe_allow_html=True,
            )
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
        filter_columns = st.columns([5, 1, 1, 1, 1], gap="small")
        selected_delivery_mode = st.session_state.get("overview_delivery_mode", "All")
        for column, label in zip(filter_columns[1:], filter_labels):
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
            # Filter all_universities to match the mode-filtered overview
            _filtered_names = set(filtered_overview_df["Universities"].str.strip().str.lower())
            _filtered_univs = [u for u in all_universities if u["name"].strip().lower() in _filtered_names]
            _nav_university = render_all_institutes_html_table(
                _filtered_univs, semester_df, filtered_overview_df, new_metrics, semester, batch
            )
            if _nav_university:
                queue_course_breakdown_navigation(_nav_university)
                st.rerun()
            # Keep legacy dataframe hidden but available (used by other views that reference filtered_overview_df)
            if False:  # pragma: no cover — kept for reference only
                overview_table_key = f"overview_university_table_{st.session_state.get('overview_table_nonce', 0)}"
                st.markdown(
                    "<div style='background:var(--surface,#fff);border:1px solid var(--border,#e2e8f0);"
                    "border-radius:12px;padding:4px 0 0 0;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden;margin-bottom:8px;'>",
                    unsafe_allow_html=True,
                )
                _overview_pct_cols = [
                    "Class Room Quizzes Attempt %", "Class Room Quizzes Pass %",
                    "CR Quiz Pass % (â‰¥60)", "CR Quiz Pass % (>80)",
                    "Lecture Delivery %", "Practice Delivery %", "Practice Completion %",
                    "Module Quiz Conduction %", "Module Quiz Student Participation %",
                    "Module Quiz Pass %", "Module Quiz Pass % (â‰¥60)", "Module Quiz Pass % (>80)",
                    "Skill Assessment Conduction %", "Skill Assessment Student Participation %", "Skill Assessment Pass %",
                    "Academic Assessments Attempt %", "Academic Assessments Pass %",
                ]
                _overview_styled = _apply_pct_colors(filtered_overview_df, _overview_pct_cols, deviation_cols=["Deviation %"])
                overview_selection = st.dataframe(
                    _overview_styled,
                    use_container_width=True,
                    hide_index=True,
                    key=overview_table_key,
                    on_select="rerun",
                    selection_mode="single-row",
                    column_config={
                        "Universities":                          st.column_config.TextColumn("Universities", width="medium"),
                        "Delivery Mode":                         st.column_config.TextColumn("Delivery Mode", width="small"),
                        "Start Date":                            st.column_config.TextColumn("Start Date", width="small"),
                        "End Date":                             st.column_config.TextColumn("End Date", width="small"),
                        "Delivery capacity slots":               st.column_config.NumberColumn("Capacity Slots", format="%.0f", width="small"),
                        "Planned content slots":                 st.column_config.NumberColumn("Planned Slots", format="%.0f", width="small"),
                        "Planned content slots till date":       st.column_config.NumberColumn("Planned Till Date", format="%.0f", width="small"),
                    "Planned slots delivered till date":     st.column_config.NumberColumn("Delivered Till Date", format="%.0f", width="small"),
                    "Deviation %":                           st.column_config.NumberColumn("Deviation %", format="%.1f%%", help="(Planned slots delivered till date âˆ' Planned content slots till date) / Planned content slots till date Ã— 100. Negative = behind schedule."),
                    "Class Room Quizzes Attempt %":          st.column_config.NumberColumn("CR Quiz Attempt %", format="%.1f%%", help="Students who attempted classroom quizzes / total enrolled Ã— 100"),
                    "Class Room Quizzes Pass %":             st.column_config.NumberColumn("CR Quiz Pass %", format="%.1f%%", help="Pairs where best_attempt_evaluation_result = 'PASS' / total attempted pairs Ã— 100"),
                    "CR Quiz Pass % (â‰¥60)":                  st.column_config.NumberColumn("CR Quiz Pass % (â‰¥60)", format="%.1f%%", help="Classroom quiz pairs with score â‰¥ 60% / total attempted pairs Ã— 100"),
                    "CR Quiz Pass % (>80)":                  st.column_config.NumberColumn("CR Quiz Pass % (>80)", format="%.1f%%", help="Classroom quiz pairs with score > 80% / total attempted pairs Ã— 100"),
                    "Lecture Delivery %":                    st.column_config.NumberColumn("Lecture Delivery %", format="%.1f%%", help="COUNT DISTINCT lecture session_ids with delivery_status_vs_plan IN ('ON_TIME','DELIVERED_DELAYED') / COUNT DISTINCT planned lecture session_ids x 100  (source: session_adherence)"),
                    "Practice Delivery %":                   st.column_config.NumberColumn("Practice Delivery %", format="%.1f%%", help="COUNT DISTINCT practice session_ids with delivery_status_vs_plan IN ('ON_TIME','DELIVERED_DELAYED') / COUNT DISTINCT planned practice session_ids x 100  (source: session_adherence)"),
                    "Practice Completion %":                 st.column_config.NumberColumn("Practice Completion %", format="%.1f%%", help="Completed student x practice sessions / available student x practice sessions x 100"),
                    "Module Quiz Conduction %":              st.column_config.NumberColumn("Module Quiz Conduction %", format="%.1f%%", help="COUNT DISTINCT EXAM session_ids (session_name_enum LIKE 'quiz%' or '%module%') with delivery_status_vs_plan IN ('ON_TIME','DELIVERED_DELAYED') / planned x 100  (source: session_adherence)"),
                    "Module Quiz Student Participation %":   st.column_config.NumberColumn("Module Quiz Participation %", format="%.1f%%", help="Students who attempted module quiz / total enrolled Ã— 100"),
                    "Module Quiz Pass %":                    st.column_config.NumberColumn("Module Quiz Pass %", format="%.1f%%", help="Pairs where best_attempt_evaluation_result = 'PASS' / total attempted pairs Ã— 100"),
                    "Module Quiz Pass % (â‰¥60)":              st.column_config.NumberColumn("Module Quiz Pass % (â‰¥60)", format="%.1f%%", help="Module quiz pairs with score â‰¥ 60% / total attempted pairs Ã— 100"),
                    "Module Quiz Pass % (>80)":              st.column_config.NumberColumn("Module Quiz Pass % (>80)", format="%.1f%%", help="Module quiz pairs with score > 80% / total attempted pairs Ã— 100"),
                    "Skill Assessment Conduction %":         st.column_config.NumberColumn("Skill Conduction %", format="%.1f%%", help="COUNT DISTINCT EXAM session_ids (session_name_enum contains 'skill') with delivery_status_vs_plan IN ('ON_TIME','DELIVERED_DELAYED') / planned x 100  (source: session_adherence)"),
                    "Skill Assessment Student Participation %": st.column_config.NumberColumn("Skill Participation %", format="%.1f%%", help="Students attempted skill assessment / total enrolled Ã— 100"),
                    "Skill Assessment Pass %":               st.column_config.NumberColumn("Skill Pass %", format="%.1f%%", help="Average of per-course Skill Pass % from course matrix (avg pass_count / participation per course, averaged across all courses)"),
                    "Academic Assessments Attempt %":        st.column_config.NumberColumn("Academic Attempt %", format="%.1f%%", help="Students who attempted graded assessments / total enrolled Ã— 100"),
                    "Academic Assessments Pass %":           st.column_config.NumberColumn("Academic Pass %", format="%.1f%%", help="Students passed (section_evaluation_result=PASSED) / students attempted academic assessments Ã— 100"),
                },
            )
                st.markdown("</div>", unsafe_allow_html=True)
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
        st.markdown(
            "<div style='background:var(--surface,#fff);border:1px solid var(--border,#e2e8f0);"
            "border-radius:12px;padding:4px 0 0 0;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden;margin-bottom:8px;'>",
            unsafe_allow_html=True,
        )
        _series_styled = _apply_pct_colors(series_df, ["Avg Delivery %", "Avg Score %", "Skill Score %", "Academic Assessment Score %"])
        st.dataframe(
            _series_styled,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Series":                        st.column_config.TextColumn("Series", width="small"),
                "Universities":                  st.column_config.NumberColumn("Universities", format="%d", width="small"),
                "Students":                      st.column_config.NumberColumn("Students", format="%d", width="small"),
                "Avg Slots":                     st.column_config.NumberColumn("Avg Slots", format="%.1f", width="small"),
                "Avg Delivery %":                st.column_config.NumberColumn("Avg Delivery %", format="%.1f%%"),
                "Avg Score %":                   st.column_config.NumberColumn("Avg Score %", format="%.1f%%"),
                "Skill Score %":                 st.column_config.NumberColumn("Skill Score %", format="%.1f%%"),
                "Academic Assessment Score %":   st.column_config.NumberColumn("Academic Score %", format="%.1f%%"),
                "Avg Allotted Hours":            st.column_config.NumberColumn("Avg Hours", format="%.1f", width="small"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif current_view == "University Comparison":
        render_section_header("University benchmark", "Lecture, practice, and exam delivery percentages are shown by university. Avg Delivery % is the overall university delivery view.")
        st.markdown(
            "<div style='background:var(--surface,#fff);border:1px solid var(--border,#e2e8f0);"
            "border-radius:12px;padding:4px 0 0 0;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow:hidden;margin-bottom:8px;'>",
            unsafe_allow_html=True,
        )
        _univ_pct_cols = ["Lecture Delivery %", "Practice Delivery %", "Exam Delivery %", "Avg Delivery %", "Avg Score %", "Skill Score %", "Academic Assessment Score %"]
        _univ_styled = _apply_pct_colors(university_rows, _univ_pct_cols)
        st.dataframe(
            _univ_styled,
            use_container_width=True,
            hide_index=True,
            column_config={
                "University":                          st.column_config.TextColumn("University", width="medium"),
                "Sections":                            st.column_config.NumberColumn("Sections", format="%d", width="small"),
                "Allotted Hours":                      st.column_config.NumberColumn("Allotted Hours", format="%.1f", width="small"),
                "Avg Slots":                           st.column_config.NumberColumn("Avg Slots", format="%.1f", width="small"),
                "Lecture Delivery %":                  st.column_config.NumberColumn("Lecture Delivery %", format="%.1f%%"),
                "Practice Delivery %":                 st.column_config.NumberColumn("Practice Delivery %", format="%.1f%%"),
                "Exam Delivery %":                     st.column_config.NumberColumn("Exam Delivery %", format="%.1f%%"),
                "Avg Delivery %":                      st.column_config.NumberColumn("Avg Delivery %", format="%.1f%%"),
                "Avg Score %":                         st.column_config.NumberColumn("Avg Score %", format="%.1f%%"),
                "Participation #":                     st.column_config.NumberColumn("Participation #", format="%.1f", width="small"),
                "Skill Score %":                       st.column_config.NumberColumn("Skill Score %", format="%.1f%%"),
                "Skill Participation #":               st.column_config.NumberColumn("Skill Participation #", format="%.1f", width="small"),
                "Academic Assessment Score %":         st.column_config.NumberColumn("Academic Score %", format="%.1f%%"),
                "Academic Assessment Participation #": st.column_config.NumberColumn("Academic Participation #", format="%.1f", width="small"),
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)

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
                if st.button("Back", key="overview_back_arrow", type="primary", use_container_width=True):
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
            _subject_map   = dict(portal_subject_map)
            _subject_map.update(fetch_university_subject_map(batch, semester, selected_university))
            university_metrics = build_university_metrics(semester_df, assessment_df, selected_university, selected_section, semester, sem_course_titles, quiz_pass_pct=_quiz_pass_pct, subject_map=_subject_map)
            if university_metrics is None:
                st.warning("No university data available for the current selection.")
                st.stop()
            course_table, hidden_courses = filter_course_table(university_metrics["courseTable"], semester, selected_university)

        # â€â€ Semester window info â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        if dates:
            st.markdown(
                f"<div class='info-card'><strong>Semester window:</strong> {escape_html(dates['start'])} to {escape_html(dates['end'])}</div>",
                unsafe_allow_html=True,
            )

        # â€â€ Fetch planned/delivered per course from session_adherence â€â€â€â€â€â€â€â€â€â€
        with st.spinner("Loading course delivery stats..."):
            delivery_stats_df = fetch_course_delivery_stats(batch, semester, selected_university, selected_section)

        with st.spinner("Loading course completion rates..."):
            completion_by_course_df = fetch_course_completion_by_course(batch, semester, selected_university, selected_section)

        _completion_course_lookup: dict[str, float | None] = {}
        _completion_by_portal_id: dict[str, float | None] = {}
        _completion_by_canonical: dict[str, list[float]] = {}
        if not completion_by_course_df.empty and "course_title" in completion_by_course_df.columns:
            for _, _cr in completion_by_course_df.iterrows():
                _ct = str(_cr.get("course_title") or "").strip()
                _pid = str(_cr.get("portal_course_id") or "").strip()
                _cp = _cr.get("completion_pct")
                try:
                    _cval = None if (_cp is None or pd.isna(_cp)) else float(_cp)
                except (TypeError, ValueError):
                    _cval = None
                if _ct:
                    _completion_course_lookup[normalize_text(_ct)] = _cval
                    # Use BQ sem_course_titles first for dynamic resolution, fallback to static aliases
                    _canonical_key = normalize_text(
                        sem_course_titles.get(normalize_text(_ct))
                        or sem_course_titles.get(normalize_text(normalize_course_name(_ct, semester)))
                        or normalize_course_name(_ct, semester)
                    )
                    if _cval is not None:
                        _completion_by_canonical.setdefault(_canonical_key, []).append(_cval)
                if _pid:
                    _completion_by_portal_id[_pid] = _cval

        # â€â€ Module quiz conduction % per course from schedule EXAM sessions â€â€â€
        with st.spinner("Loading module quiz conduction rates..."):
            exam_delivery_by_course_df = fetch_exam_delivery_by_course(batch, semester, selected_university, selected_section)

        _exam_conduction_lookup: dict[str, float | None] = {}
        if not exam_delivery_by_course_df.empty and "course_title" in exam_delivery_by_course_df.columns:
            for _, _er in exam_delivery_by_course_df.iterrows():
                _et = str(_er.get("course_title") or "").strip()
                _ev = _er.get("exam_conduction_pct")
                try:
                    _eval = None if (_ev is None or pd.isna(_ev)) else float(_ev)
                except (TypeError, ValueError):
                    _eval = None
                if _et:
                    _exam_conduction_lookup[normalize_text(_et)] = _eval

        def _course_exam_conduction(course_name: str) -> float | None:
            key = normalize_text(course_name)
            if key in _exam_conduction_lookup:
                return _exam_conduction_lookup[key]
            for k, v in _exam_conduction_lookup.items():
                if key in k or k in key:
                    return v
            canonical_key = normalize_text(normalize_course_name(course_name, semester))
            for k, v in _exam_conduction_lookup.items():
                if normalize_text(normalize_course_name(k, semester)) == canonical_key:
                    return v
            return None

        # â€â€ Quiz pass % per course via schedule LP_QUIZ â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        with st.spinner("Loading quiz pass rates..."):
            quiz_pass_by_course_df = fetch_quiz_pass_by_course(batch, semester, selected_university, selected_section)

        _quiz_pass_course_lookup: dict[str, float | None] = {}
        _quiz_pass_by_canonical: dict[str, list[float]] = {}
        if not quiz_pass_by_course_df.empty and "course_title" in quiz_pass_by_course_df.columns:
            for _, _qr in quiz_pass_by_course_df.iterrows():
                _qt = str(_qr.get("course_title") or "").strip()
                _qv = _qr.get("quiz_pass_pct")
                try:
                    _qval = None if (_qv is None or pd.isna(_qv)) else float(_qv)
                except (TypeError, ValueError):
                    _qval = None
                if _qt:
                    _quiz_pass_course_lookup[normalize_text(_qt)] = _qval
                    _qcanon = normalize_text(
                        canonicalize_course_label(
                            sem_course_titles.get(normalize_text(_qt))
                            or sem_course_titles.get(normalize_text(normalize_course_name(_qt, semester)))
                            or _qt,
                            semester,
                        )
                    )
                    if _qval is not None:
                        _quiz_pass_by_canonical.setdefault(_qcanon, []).append(_qval)

        def _course_quiz_pass(course_name: str) -> float | None:
            key = normalize_text(course_name)
            if key in _quiz_pass_course_lookup:
                return _quiz_pass_course_lookup[key]
            for k, v in _quiz_pass_course_lookup.items():
                if key in k or k in key:
                    return v
            canonical_key = normalize_text(canonicalize_course_label(course_name, semester))
            if canonical_key in _quiz_pass_by_canonical:
                vals = _quiz_pass_by_canonical[canonical_key]
                return round(sum(vals) / len(vals), 1) if vals else None
            return None

        # â€â€ Module quiz pass % per course via schedule MODULE_QUIZ/COURSE_QUIZ â€â€
        with st.spinner("Loading module quiz pass rates..."):
            module_quiz_pass_by_course_df = fetch_module_quiz_pass_by_course(batch, semester, selected_university, selected_section)

        _mq_pass_course_lookup: dict[str, float | None] = {}
        _mq_pass_by_canonical: dict[str, list[float]] = {}
        if not module_quiz_pass_by_course_df.empty and "course_title" in module_quiz_pass_by_course_df.columns:
            for _, _mqr in module_quiz_pass_by_course_df.iterrows():
                _mqt = str(_mqr.get("course_title") or "").strip()
                _mqv = _mqr.get("module_quiz_pass_pct")
                try:
                    _mqval = None if (_mqv is None or pd.isna(_mqv)) else float(_mqv)
                except (TypeError, ValueError):
                    _mqval = None
                if _mqt:
                    _mq_pass_course_lookup[normalize_text(_mqt)] = _mqval
                    _mqcanon = normalize_text(canonicalize_course_label(
                        sem_course_titles.get(normalize_text(_mqt))
                        or sem_course_titles.get(normalize_text(normalize_course_name(_mqt, semester)))
                        or _mqt,
                        semester,
                    ))
                    if _mqval is not None:
                        _mq_pass_by_canonical.setdefault(_mqcanon, []).append(_mqval)

        def _course_module_quiz_pass(course_name: str) -> float | None:
            key = normalize_text(course_name)
            if key in _mq_pass_course_lookup:
                return _mq_pass_course_lookup[key]
            for k, v in _mq_pass_course_lookup.items():
                if key in k or k in key:
                    return v
            canonical_key = normalize_text(canonicalize_course_label(course_name, semester))
            if canonical_key in _mq_pass_by_canonical:
                vals = _mq_pass_by_canonical[canonical_key]
                return round(sum(vals) / len(vals), 1) if vals else None
            return None

        # Module quiz attendance % per course:
        # attempted = COUNT(DISTINCT student×quiz pairs), quiz_count = COUNT(DISTINCT quiz_id)
        # attendance_pct = attempted / (roster_size × quiz_count) × 100
        _mq_roster = university_metrics.get("classSize") or 0
        _mq_attend_course_lookup: dict[str, float | None] = {}
        _mq_attend_by_canonical: dict[str, list[float]] = {}
        if not module_quiz_pass_by_course_df.empty and "course_title" in module_quiz_pass_by_course_df.columns and "quiz_count" in module_quiz_pass_by_course_df.columns:
            for _, _mqr in module_quiz_pass_by_course_df.iterrows():
                _mqt = str(_mqr.get("course_title") or "").strip()
                _mq_att = _mqr.get("attempted")
                _mq_qc  = _mqr.get("quiz_count")
                try:
                    _mq_att = float(_mq_att) if (_mq_att is not None and not pd.isna(_mq_att)) else None
                    _mq_qc  = float(_mq_qc)  if (_mq_qc  is not None and not pd.isna(_mq_qc))  else None
                except (TypeError, ValueError):
                    _mq_att = _mq_qc = None
                _mq_att_pct = None
                if _mq_roster > 0 and _mq_att is not None and _mq_qc and _mq_qc > 0:
                    _mq_att_pct = round(min(_mq_att / (_mq_roster * _mq_qc) * 100, 100.0), 1)
                if _mqt:
                    _mq_attend_course_lookup[normalize_text(_mqt)] = _mq_att_pct
                    _mqacanon = normalize_text(canonicalize_course_label(
                        sem_course_titles.get(normalize_text(_mqt))
                        or sem_course_titles.get(normalize_text(normalize_course_name(_mqt, semester)))
                        or _mqt, semester,
                    ))
                    if _mq_att_pct is not None:
                        _mq_attend_by_canonical.setdefault(_mqacanon, []).append(_mq_att_pct)

        def _course_module_quiz_attendance(course_name: str) -> float | None:
            key = normalize_text(course_name)
            if key in _mq_attend_course_lookup:
                return _mq_attend_course_lookup[key]
            for k, v in _mq_attend_course_lookup.items():
                if key in k or k in key:
                    return v
            canonical_key = normalize_text(canonicalize_course_label(course_name, semester))
            if canonical_key in _mq_attend_by_canonical:
                vals = _mq_attend_by_canonical[canonical_key]
                return round(sum(vals) / len(vals), 1) if vals else None
            return None

        # â€â€ Practice completion % per course â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        with st.spinner("Loading practice completion rates..."):
            practice_completion_by_course_df = fetch_practice_completion_by_course(batch, semester, selected_university, selected_section)

        _prac_completion_lookup: dict[str, float | None] = {}
        _prac_completion_by_canonical: dict[str, list[float]] = {}
        if not practice_completion_by_course_df.empty and "course_title" in practice_completion_by_course_df.columns:
            for _, _pr in practice_completion_by_course_df.iterrows():
                _pt = str(_pr.get("course_title") or "").strip()
                _pv = _pr.get("practice_completion_pct")
                try:
                    _pval = None if (_pv is None or pd.isna(_pv)) else float(_pv)
                except (TypeError, ValueError):
                    _pval = None
                if _pt:
                    _prac_completion_lookup[normalize_text(_pt)] = _pval
                    _pcanon = normalize_text(
                        sem_course_titles.get(normalize_text(_pt))
                        or sem_course_titles.get(normalize_text(normalize_course_name(_pt, semester)))
                        or normalize_course_name(_pt, semester)
                    )
                    if _pval is not None:
                        _prac_completion_by_canonical.setdefault(_pcanon, []).append(_pval)

        def _course_practice_completion(course_name: str) -> float | None:
            key = normalize_text(course_name)
            if key in _prac_completion_lookup:
                return _prac_completion_lookup[key]
            for k, v in _prac_completion_lookup.items():
                if key in k or k in key:
                    return v
            canonical_key = normalize_text(normalize_course_name(course_name, semester))
            if canonical_key in _prac_completion_by_canonical:
                vals = _prac_completion_by_canonical[canonical_key]
                return round(sum(vals) / len(vals), 1) if vals else None
            return None

        # portal_course_id map: normalize_text(sem_course_title) â†' portal_course_id
        with st.spinner("Loading portal course ID map..."):
            _sem_course_portal_ids = fetch_portal_course_id_map(batch, semester)

        def _course_completion(course_name: str) -> float | None:
            key = normalize_text(course_name)
            if key in _completion_course_lookup:
                return _completion_course_lookup[key]
            for k, v in _completion_course_lookup.items():
                if key in k or k in key:
                    return v
            pid = _sem_course_portal_ids.get(key)
            if pid and pid in _completion_by_portal_id:
                return _completion_by_portal_id[pid]
            canonical_key = normalize_text(normalize_course_name(course_name, semester))
            if canonical_key in _completion_by_canonical:
                vals = _completion_by_canonical[canonical_key]
                return round(sum(vals) / len(vals), 1) if vals else None
            return None

        def _get_delivery_row(course_name: str, sem_course_id: str = "") -> dict | None:
            if delivery_stats_df.empty:
                return None
            # 1. ID-based match (preferred — works even when titles differ)
            if sem_course_id and "sem_course_id" in delivery_stats_df.columns:
                clean_id = sem_course_id.replace("-", "")
                for _, r in delivery_stats_df.iterrows():
                    r_id = str(r.get("sem_course_id", "") or "").replace("-", "")
                    if r_id and r_id == clean_id:
                        return r.to_dict()
            # 2. Exact normalized title match
            norm = normalize_text(course_name)
            for _, r in delivery_stats_df.iterrows():
                if normalize_text(str(r.get("course", ""))) == norm:
                    return r.to_dict()
            # 3. Partial match
            for _, r in delivery_stats_df.iterrows():
                raw_norm = normalize_text(str(r.get("course", "")))
                if norm in raw_norm or raw_norm in norm:
                    return r.to_dict()
            # 4. Alias-group match
            norm_alias = normalize_text(normalize_course_name(course_name, semester))
            for _, r in delivery_stats_df.iterrows():
                raw = str(r.get("course", ""))
                if normalize_text(normalize_course_name(raw, semester)) == norm_alias:
                    return r.to_dict()
            return None

        # â€â€ Build course_rows for the matrix â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        # Pacing ratio: elapsed working days / total semester working days
        _pacing_ratio = 0.0
        if dates and dates.get("start") and dates.get("end"):
            _total_wd = count_weekdays_between(dates["start"], dates["end"])
            if _total_wd:
                _today_str = datetime.now().strftime("%Y-%m-%d")
                _end_eff = dates["end"] if dates["end"] <= _today_str else _today_str
                _elapsed_wd = count_weekdays_between(dates["start"], _end_eff) or 0
                _pacing_ratio = min(1.0, float(_elapsed_wd) / float(_total_wd))

        _delivery_mode = "NxtWave"

        def _safe_f(v):
            try:
                f = float(v)
                return 0.0 if f != f else f
            except (TypeError, ValueError):
                return 0.0

        def _deviation(till_date, scheduled):
            # Positive = forward / ahead of schedule (scheduled > till_date)
            # Negative = behind schedule (scheduled < till_date)
            if till_date and till_date > 0 and scheduled is not None:
                return round(((scheduled - till_date) / till_date) * 100, 1)
            return None

        # ── Scheduled counts from schedule table (session_id + session_status) ──
        with st.spinner("Loading scheduled session counts..."):
            scheduled_counts_df = fetch_course_scheduled_counts(batch, semester, selected_university, selected_section)

        _sched_lookup: dict[str, dict] = {}
        if not scheduled_counts_df.empty and "course_title" in scheduled_counts_df.columns:
            for _, _sr in scheduled_counts_df.iterrows():
                _st = str(_sr.get("course_title") or "").strip()
                if _st:
                    _sched_lookup[normalize_text(_st)] = _sr.to_dict()

        def _course_scheduled(course_name: str) -> dict | None:
            key = normalize_text(course_name)
            if key in _sched_lookup:
                return _sched_lookup[key]
            for k, v in _sched_lookup.items():
                if key in k or k in key:
                    return v
            canonical_key = normalize_text(normalize_course_name(course_name, semester))
            for k, v in _sched_lookup.items():
                if normalize_text(normalize_course_name(k, semester)) == canonical_key:
                    return v
            return None

        course_rows = []
        for _, ct_row in course_table.iterrows():
            cname = ct_row["Course"]
            cid = str(ct_row.get("sem_course_id", "") or "")
            dr = _get_delivery_row(cname, cid)
            delivered = dr["total_delivered"] if dr else ct_row.get("Total Slots")
            planned   = dr["total_planned"]   if dr else None
            completion = _course_completion(cname)
            lecture_pct = ct_row.get("Lecture Delivery %")
            practice_pct = ct_row.get("Practice Delivery %")
            exam_pct = ct_row.get("Exam Delivery %")
            if exam_pct is None:
                exam_pct = _course_exam_conduction(cname)
            lecture_slots = dr.get("lecture_slots") if dr and dr.get("lecture_slots") is not None else ct_row.get("Lecture Slots")
            practice_slots = dr.get("practice_slots") if dr and dr.get("practice_slots") is not None else ct_row.get("Practice Slots")
            exam_slots = dr.get("exam_slots") if dr and dr.get("exam_slots") is not None else ct_row.get("Exam Slots")

            _lec  = _safe_f(lecture_slots)
            _prac = _safe_f(practice_slots)
            _exam = _safe_f(exam_slots)
            lec_till  = round(_lec  * _pacing_ratio, 1)
            prac_till = round(_prac * _pacing_ratio, 1)
            mq_till   = round(_exam * _pacing_ratio, 1)

            # Scheduled = COUNT(DISTINCT session_id WHERE session_status IN ('ON_TIME', 'DELIVERED_DELAYED'))
            # Direct from schedule table only — no fallback formula.
            _sched_row = _course_scheduled(cname)
            def _sched_val(key):
                if _sched_row is not None:
                    v = _sched_row.get(key)
                    if v is not None:
                        try:
                            return float(v)
                        except (TypeError, ValueError):
                            pass
                return None
            lec_sched  = _sched_val("lec_scheduled")
            prac_sched = _sched_val("prac_scheduled")
            mq_sched   = _sched_val("mq_scheduled")

            course_rows.append({
                "course":         cname,
                "sem_course_id":  cid,
                "delivery_mode":  _delivery_mode,
                "delivered":      delivered,
                "planned":        planned,
                "lecture_slots":  lecture_slots,
                "practice_slots": practice_slots,
                "exam_slots":     exam_slots,
                "total_slots":    (_lec + _prac + _exam),
                "lecture_pct":    lecture_pct,
                "practice_pct":   practice_pct,
                "exam_pct":       exam_pct,
                "lec_till_date":  lec_till,
                "lec_scheduled":  lec_sched,
                "lec_deviation":  _deviation(lec_till, lec_sched),
                "prac_till_date": prac_till,
                "prac_scheduled": prac_sched,
                "prac_deviation": _deviation(prac_till, prac_sched),
                "mq_till_date":   mq_till,
                "mq_scheduled":   mq_sched,
                "mq_deviation":   _deviation(mq_till, mq_sched),
                "skill_designed":       5,
                "skill_till_date":      round(5 * _pacing_ratio, 1),
                "skill_attendance_pct": ct_row.get("Skill Attendance %"),
                "skill_pass_pct":       ct_row.get("Skill Pass %"),
                "academic_attendance_pct": ct_row.get("Academic Attendance %"),
                "academic_pass_pct":       ct_row.get("Academic Pass %"),
                "completion_pct":          completion,
                "practice_completion_pct": _course_practice_completion(cname),
                "quiz_pass_pct":           _course_quiz_pass(cname),
                "module_quiz_pass_pct":    _course_module_quiz_pass(cname),
                "mq_attendance_pct":       _course_module_quiz_attendance(cname),
            })

        # â€â€ Course Matrix or Course Detail â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
        selected_course_for_detail = st.session_state.get("selected_course_for_detail")

        if selected_course_for_detail is None:
            # â€â€ MATRIX VIEW â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
            scope_label = selected_section if selected_section else "All sections"
            render_section_header(f"{selected_university} -- {scope_label}", "Select a course row to drill into schedule adherence, unit completion, quizzes, and assessments.")
            if hidden_courses:
                st.markdown(
                    f"<div class='info-card'>Showing {escape_html(len(course_table))} core courses Â· {escape_html(hidden_courses)} support courses hidden.</div>",
                    unsafe_allow_html=True,
                )

            if not selected_section:
                st.caption("In All Sections view, Planned Lecture, Planned Practice, and Planned Module Quiz are averaged per section for each course.")

            with st.expander("Metric definitions", expanded=False):
                _cm_metrics = [
                    # Subject Info
                    ("Subject",                   "Course name for the semester."),
                    ("Mode",                      "Indicates whether the subject is taught by NxtWave or the University."),
                    ("Total Designed",            "Total planned sessions = lecture + practice + module quiz slots."),
                    # Lectures
                    ("Lectures - Designed",             "Total lecture sessions planned for the full semester."),
                    ("Lectures - Designed Till Date",   "Pro-rated lecture sessions expected by today based on semester pacing."),
                    ("Lectures - Scheduled",            "COUNT DISTINCT lecture session_ids with delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED', averaged across sections (source: session_adherence)."),
                    ("Lectures - Deviation %",          "Positive = ahead of schedule (forward). Negative = behind schedule. Formula: (Scheduled - Designed Till Date) / Designed Till Date x 100."),
                    # Classroom Quiz
                    ("CR Quiz - Attend %",   "% of expected student-quiz pairs that attempted classroom (LP_QUIZ) quizzes."),
                    ("CR Quiz - Q Attempt",  "Count of distinct student-quiz attempt pairs for classroom quizzes."),
                    ("CR Quiz - Q Correct",  "Count of student-quiz pairs that passed (score >= 80%) in classroom quizzes."),
                    # Practice
                    ("Practice - Designed",             "Total practice sessions planned for the full semester."),
                    ("Practice - Designed Till Date",   "Pro-rated practice sessions expected by today."),
                    ("Practice - Scheduled",            "COUNT DISTINCT practice session_ids with delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED', averaged across sections (source: session_adherence)."),
                    ("Practice - Deviation %",          "Positive = ahead of schedule (forward). Negative = behind schedule."),
                    # Practice Completion
                    ("Completion %",  "% of assigned practice content units completed by students."),
                    # Module Quiz
                    ("Module Quiz - Designed",            "Total module quiz (EXAM-type) sessions planned for the full semester."),
                    ("Module Quiz - Designed Till Date",  "Pro-rated module quizzes expected by today based on semester pacing."),
                    ("Module Quiz - Scheduled",           "COUNT DISTINCT EXAM session_ids with delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED', averaged across sections (source: session_adherence)."),
                    ("Module Quiz - Deviation %",         "Positive = ahead of schedule (forward). Negative = behind schedule."),
                    ("Module Quiz - Attend %",            "% of expected student-quiz pairs that attempted module quizzes = attempts / (roster x quiz count) x 100."),
                    ("Module Quiz - Pass %",              "% of module quiz participants who passed (result = PASS or score >= 80%)."),
                    # Skill Assessment
                    ("Skill - Designed",            "Number of skill assessments planned (5 per semester)."),
                    ("Skill - Designed Till Date",  "Pro-rated skill assessments expected by today."),
                    ("Skill - Scheduled",           "COUNT DISTINCT EXAM session_ids whose session_name_enum contains 'skill' and delivery_status_vs_plan = 'ON_TIME' or 'DELIVERED_DELAYED', averaged across sections (source: session_adherence)."),
                    ("Skill - Attend %",            "% of expected student-assessment pairs that attempted skill assessments = pairs / (roster x assessment count) x 100."),
                    ("Skill - Pass %",              "% of skill assessment participants who passed (score >= 80%)."),
                    # Academic
                    ("Academic - Attend %",  "% of students who attempted the academic (semester-end) assessment."),
                    ("Academic - Pass %",    "% of academic assessment participants who passed (score >= 80%)."),
                ]
                _cm_items = "".join(
                    f'<li style="margin-bottom:10px;">'
                    f'<code style="color:#059669;background:rgba(5,150,105,.08);'
                    f'padding:2px 8px;border-radius:4px;font-size:0.85em;">{m}</code>'
                    f' : {d}'
                    f'</li>'
                    for m, d in _cm_metrics
                )
                st.markdown(
                    f'<ul style="list-style:disc;padding-left:20px;line-height:1.8;">{_cm_items}</ul>',
                    unsafe_allow_html=True,
                )

            render_institute_overview_table(selected_university, course_rows, overview_df, semester)
            clicked = render_course_overview_table(course_rows, section=selected_section)
            if clicked:
                st.session_state["selected_course_for_detail"] = clicked
                _clicked_id = next(
                    (r.get("sem_course_id", "") for r in course_rows if r.get("course") == clicked),
                    ""
                )
                st.session_state["selected_course_sem_id"] = _clicked_id
                st.session_state.pop("lpe_sec", None)
                st.session_state.pop("quiz_sec", None)
                st.rerun()

        else:
            # â€â€ DETAIL VIEW â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€â€
            back_col, _ = st.columns([0.15, 0.85])
            with back_col:
                if st.button("Courses", key="back_to_matrix"):
                    st.session_state.pop("selected_course_for_detail", None)
                    st.session_state.pop("selected_course_sem_id", None)
                    st.session_state.pop("lpe_sec", None)
                    st.session_state.pop("quiz_sec", None)
                    st.session_state.pop("cm_course_select", None)
                    st.rerun()

            # Build a helper that maps a raw course title to its display name
            def _raw_to_display(raw_course: str) -> str:
                normalized = normalize_course_name(str(raw_course), semester)
                return sem_course_titles.get(normalize_text(normalized), normalized)

            # ── ID-based course lookup ────────────────────────────────────────────
            # Retrieve the sem_course_id stored when this course was clicked.
            # This eliminates text-based alias matching for session_adherence queries.
            _drill_sem_course_id = st.session_state.get("selected_course_sem_id", "")

            # Fallback: derive sem_course_id from semester_df if not in session state
            if not _drill_sem_course_id and "sem_course_id" in semester_df.columns:
                _sc_rows = semester_df[
                    (semester_df["institute"] == selected_university) &
                    (semester_df["course"] == selected_course_for_detail)
                ]
                if _sc_rows.empty:
                    _sc_rows = semester_df[
                        (semester_df["institute"] == selected_university) &
                        (semester_df["course"].apply(lambda c: normalize_text(str(c))) == normalize_text(selected_course_for_detail))
                    ]
                if not _sc_rows.empty:
                    _drill_sem_course_id = str(_sc_rows["sem_course_id"].iloc[0] or "")

            # Filter semester_df to selected course — prefer ID match, fall back to title match
            if _drill_sem_course_id and "sem_course_id" in semester_df.columns:
                sem_course_df = semester_df[
                    (semester_df["institute"] == selected_university) &
                    (semester_df["sem_course_id"] == _drill_sem_course_id)
                ].copy()
            else:
                sem_course_df = semester_df[
                    (semester_df["institute"] == selected_university) &
                    (semester_df["course"].apply(lambda c: normalize_text(_raw_to_display(str(c)))) == normalize_text(selected_course_for_detail))
                ].copy()
            if selected_section:
                sem_course_df = sem_course_df[sem_course_df["section"] == selected_section]

            # course_title tuple for unlocked_units fallback (practice completion)
            raw_course_titles = (selected_course_for_detail,)

            # Delivery stats lookup using ID then title fallback
            _dr = _get_delivery_row(selected_course_for_detail, _drill_sem_course_id)
            if _dr:
                sel_delivery = {
                    "course":          selected_course_for_detail,
                    "total_planned":   _dr.get("total_planned"),
                    "total_delivered": _dr.get("total_delivered"),
                    "adherence_pct":   _dr.get("adherence_pct"),
                }
            else:
                sel_delivery = None

            # Pre-fetch units and quiz data for header stats (cached, so also reused in tabs)
            with st.spinner("Loading course data…"):
                _detail_units_df = fetch_course_session_units(
                    batch, semester, selected_university,
                    raw_course_titles, selected_section, _drill_sem_course_id
                )

            # Render header + stats bar
            render_course_detail_header(selected_course_for_detail, sel_delivery, _detail_units_df)

            # ── Tabs ─────────────────────────────────────────────────────────────
            tab1, tab2, tab3 = st.tabs([
                "📅 Schedule Adherence",
                "📖 Lecture / Practice / Exam",
                "🎯 Assessments",
            ])

            with tab1:
                with st.spinner("Loading weekly delivery data…"):
                    weekly_df = fetch_course_weekly_delivery(
                        batch, semester, selected_university,
                        raw_course_titles, selected_section, _drill_sem_course_id
                    )
                render_tab_schedule_adherence(weekly_df)

            with tab2:
                with st.spinner("Loading unit data…"):
                    _lpe_units_df = fetch_course_session_units_schedule(
                        batch, semester, selected_university,
                        raw_course_titles, selected_section, _drill_sem_course_id
                    )
                    # Fall back to session_adherence source if schedule returned nothing
                    if _lpe_units_df.empty:
                        _lpe_units_df = _detail_units_df
                sec_list = sorted(sem_course_df["section"].unique().tolist()) if not sem_course_df.empty else []
                render_tab_lecture_practice_exam(_lpe_units_df, sec_list)

            with tab3:
                _sel_norm = normalize_text(selected_course_for_detail)
                def _course_code_matches(c: str) -> bool:
                    # Primary: match after _raw_to_display transform
                    if normalize_text(_raw_to_display(str(c))) == _sel_norm:
                        return True
                    # Fallback 1: direct normalization match (course_code IS the subject name)
                    c_direct = normalize_text(str(c))
                    if c_direct == _sel_norm:
                        return True
                    # Fallback 2: substring / contained match (handles tech-stack names like "Python"
                    # matching a portal course title like "Python Programming")
                    if len(c_direct) >= 4 and len(_sel_norm) >= 4:
                        if c_direct in _sel_norm or _sel_norm in c_direct:
                            return True
                    return False
                course_assessment_df = assessment_df[
                    (assessment_df["university"] == selected_university) &
                    (assessment_df["course_code"].apply(_course_code_matches))
                ].copy()
                if selected_section:
                    course_assessment_df = course_assessment_df[course_assessment_df["section"] == selected_section]
                sec_list_asmt = sorted(course_assessment_df["section"].unique().tolist()) if not course_assessment_df.empty else []
                render_tab_assessments(
                    course_assessment_df,
                    selected_course_for_detail,
                    sec_list_asmt,
                    institute=selected_university,
                    batch=batch,
                    semester=semester,
                    selected_section=selected_section,
                )





if __name__ == "__main__":
    main()

