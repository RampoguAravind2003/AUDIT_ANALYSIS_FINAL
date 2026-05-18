"""Tool definitions (OpenAI/OpenRouter format) and execution for the NIAT Copilot."""

import json

from .thresholds import check_metrics
from .email_client import send_email as _send_email, build_escalation_email_html

# ── OpenAI-compatible tool definitions (used with OpenRouter) ─────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_bigquery_sql",
            "description": (
                "Execute a read-only SQL query against BigQuery and return results as JSON. "
                "Use this to fetch any operational or academic data. "
                "Only SELECT / WITH statements are allowed. Limit to ≤ 50 rows unless the user asks for more."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A valid BigQuery SQL SELECT statement.",
                    }
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all available BigQuery tables with their descriptions and key columns.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_schema",
            "description": "Retrieve the schema (column names and data types) of a specific BigQuery table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": (
                            "Logical name or full table ID. Logical names: "
                            "semester, assessment, schedule, quiz_attempts, skill_graded, "
                            "progress, session_adherence, portal_courses."
                        ),
                    }
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_kpi_thresholds",
            "description": (
                "Evaluate a set of KPI metric values against NIAT's defined operational thresholds. "
                "Returns per-metric status (good / warning / critical) and an overall escalation recommendation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "object",
                        "description": (
                            "Dict of metric_key → numeric value. "
                            "Valid keys: lecture_delivery_pct, practice_delivery_pct, exam_delivery_pct, "
                            "avg_delivery_pct, module_quiz_conduction_pct, module_quiz_pass_pct, "
                            "skill_assessment_conduction_pct, skill_assessment_pass_pct, "
                            "quiz_pass_pct, academic_pass_pct, deviation_pct."
                        ),
                    },
                    "university": {
                        "type": "string",
                        "description": "University name for context in the report.",
                    },
                },
                "required": ["metrics"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_escalation_email",
            "description": (
                "Send an escalation email via Outlook SMTP. "
                "Only use after confirming the recipient with the user. "
                "Operates in mock mode if email credentials are not configured."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to_emails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Recipient email addresses.",
                    },
                    "subject": {"type": "string"},
                    "body": {"type": "string", "description": "Plain text or HTML email body."},
                    "is_html": {"type": "boolean", "description": "True if body is HTML."},
                    "cc_emails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional CC recipients.",
                    },
                },
                "required": ["to_emails", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_escalation_report",
            "description": (
                "Build a styled HTML escalation report for a university. "
                "Returns the HTML body ready for use with send_escalation_email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "university": {"type": "string"},
                    "batch": {"type": "string"},
                    "semester": {"type": "string"},
                    "critical_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "warning_metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "metric_details": {
                        "type": "object",
                        "description": "Dict of metric_key → {label, value, status}.",
                    },
                    "notes": {"type": "string"},
                },
                "required": ["university", "batch", "semester", "critical_metrics", "warning_metrics", "metric_details"],
            },
        },
    },
]


# ── Table registry ─────────────────────────────────────────────────────────────

_TABLE_REGISTRY = {
    "semester": {
        "full_name": "kossip-helpers.content_bases_metabase.semester_section_metrics",
        "description": "Per-section delivery metrics (sessions planned vs delivered, lecture/practice/exam split)",
        "key_columns": ["batch", "semester", "institute", "section", "students",
                        "sessions_planned", "sessions_delivered",
                        "lecture_sessions_planned", "lecture_sessions_delivered",
                        "practice_sessions_planned", "practice_sessions_delivered",
                        "exam_sessions_planned", "exam_sessions_delivered"],
    },
    "assessment": {
        "full_name": "kossip-helpers.content_bases_metabase.assessment_results",
        "description": "Student assessment scores and pass/fail results",
        "key_columns": ["batch", "semester", "institute", "section", "student_id",
                        "course_title", "total_score", "score_percentage",
                        "assessment_date", "section_evaluation_result"],
    },
    "schedule": {
        "full_name": "kossip-helpers.content_bases_metabase.schedule",
        "description": "Content timetable — planned vs delivered sessions by resource type",
        "key_columns": ["batch", "semester", "institute", "section",
                        "resource_type", "resource_id", "semester_course_title",
                        "planned_date", "delivered_date", "derived_unit_type"],
    },
    "quiz_attempts": {
        "full_name": "kossip-helpers.content_bases_metabase.quiz_attempts",
        "description": "Student quiz attempt records with scores",
        "key_columns": ["quiz_id", "student_id", "score", "max_score", "attempt_date"],
    },
    "skill_graded": {
        "full_name": "kossip-helpers.content_bases_metabase.skill_graded",
        "description": "Skill assessment graded records",
        "key_columns": ["batch", "semester", "institute", "student_id",
                        "assessment_id", "score", "max_score", "assessment_start_datetime"],
    },
    "progress": {
        "full_name": "kossip-helpers.content_bases_metabase.progress",
        "description": "Content delivery progress tracker per resource",
        "key_columns": ["batch", "semester", "institute", "section",
                        "resource_type", "resource_id", "status", "completed_at"],
    },
    "session_adherence": {
        "full_name": "kossip-helpers.content_bases_metabase.session_adherence",
        "description": "Session attendance and adherence data",
        "key_columns": ["batch", "semester", "institute", "section",
                        "session_date", "attended", "total_students"],
    },
    "portal_courses": {
        "full_name": "kossip-helpers.content_bases_metabase.niat_portal_courses",
        "description": "NIAT course catalogue with subject mappings",
        "key_columns": ["batch", "semester", "course_title", "subject_name"],
    },
}


# ── Tool executor ──────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, bq_client) -> dict:
    """Dispatch a tool call and return a JSON-serialisable result dict."""
    try:
        if tool_name == "run_bigquery_sql":
            return _run_bq_sql(tool_input["sql"], bq_client)

        elif tool_name == "list_tables":
            return {
                "tables": [
                    {"name": k, "full_name": v["full_name"], "description": v["description"]}
                    for k, v in _TABLE_REGISTRY.items()
                ]
            }

        elif tool_name == "get_table_schema":
            return _get_table_schema(tool_input["table_name"], bq_client)

        elif tool_name == "check_kpi_thresholds":
            return check_metrics(
                tool_input["metrics"],
                university=tool_input.get("university", ""),
            )

        elif tool_name == "send_escalation_email":
            return _send_email(
                to_emails=tool_input["to_emails"],
                subject=tool_input["subject"],
                body=tool_input["body"],
                is_html=tool_input.get("is_html", False),
                cc_emails=tool_input.get("cc_emails"),
            )

        elif tool_name == "build_escalation_report":
            html = build_escalation_email_html(
                university=tool_input["university"],
                batch=tool_input["batch"],
                semester=tool_input["semester"],
                critical_metrics=tool_input.get("critical_metrics", []),
                warning_metrics=tool_input.get("warning_metrics", []),
                metric_details=tool_input.get("metric_details", {}),
                notes=tool_input.get("notes", ""),
            )
            return {"html_body": html, "status": "ready"}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as exc:
        return {"error": str(exc)}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run_bq_sql(sql: str, bq_client) -> dict:
    sql_stripped = sql.strip()
    first_word = sql_stripped.split()[0].upper() if sql_stripped else ""
    if first_word not in ("SELECT", "WITH"):
        return {"error": "Only SELECT / WITH queries are allowed."}
    try:
        result = bq_client.query(sql_stripped).result()
        import pandas as pd
        df = result.to_dataframe(create_bqstorage_client=False)
        truncated = len(df) > 100
        if truncated:
            df = df.head(100)
        records = json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))
        return {
            "rows": len(records),
            "columns": list(df.columns),
            "data": records,
            "truncated": truncated,
            "truncated_note": "Results capped at 100 rows." if truncated else None,
        }
    except Exception as exc:
        return {"error": str(exc)}


def _get_table_schema(table_name: str, bq_client) -> dict:
    entry = _TABLE_REGISTRY.get(table_name.lower())
    full_name = entry["full_name"] if entry else table_name
    full_name = full_name.replace("`", "")
    parts = full_name.split(".")
    if len(parts) != 3:
        return {"error": f"Could not resolve table: {table_name}"}
    project, dataset, table = parts
    try:
        table_ref = bq_client.dataset(dataset, project=project).table(table)
        bq_table = bq_client.get_table(table_ref)
        schema = [{"name": f.name, "type": f.field_type, "mode": f.mode} for f in bq_table.schema]
        return {
            "table": full_name,
            "description": entry["description"] if entry else "",
            "schema": schema,
            "row_count_estimate": bq_table.num_rows,
        }
    except Exception as exc:
        return {"error": str(exc)}
