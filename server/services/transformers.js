/**
 * Transform a BigQuery semester row to match parseSemesterCSV output shape.
 * Column name fallbacks handle different naming conventions.
 */
export function transformSemesterRow(row) {
  return {
    course:       String(row.course || row.course_name || ''),
    institute:    String(row.institute_name || row.institute || row.university || ''),
    section:      String(row.section_name || row.section_na || row.section || ''),
    session_type: String(row.session_type || '').toUpperCase(),
    sessions:     parseFloat(row.distinct_sessions_delivered || row.distinct_sessions || row.sessions_delivered || row.sessions || 0),
    students:     parseFloat(row.total_students || row.students || 0),
    completion:   parseFloat(String(row.average_of_pct_completed || row['average_of_%_completed'] || row.pct_completed || row.completion || 0).replace('%', '')),
    avg_time:     parseFloat(row.sum_of_avg_time_spent_to_complete || row.avg_time_spent_to_complete || row.avg_time_spent || row.avg_time || 0),
    p80_time:     parseFloat(row.sum_of_p80_time_to_completed || row.p80_time_to_completed || row.p80_time || 0),
    section_count: parseFloat(row.section_count || row.sections_count || 0),
    batch:        String(row.batch || ''),
    semester:     String(row.semester || ''),
    report_date:  row.report_date ? formatDate(row.report_date) : '',
  };
}

/**
 * Transform a BigQuery assessment row to match parseAssessmentCSV output shape.
 */
export function transformAssessmentRow(row) {
  return {
    university:        String(row.institute_name || row.university || row.institute || ''),
    section:           String(row.section_name || row.section || ''),
    course_code:       String(row.section_tech_stack || row.section_tech || row.tech_stack || row.course_code || ''),
    assessment_type:   String(row.assessment_type || row.assessmentType || 'Assessment'),
    avg_participation: parseFloat(row.avg_user || row.avg_participation || row.participation || row.users || 0),
    avg_score:         parseFloat(row.avg_score || row.score || 0),
    pass_rate:         row.pass_rate === null || row.pass_rate === undefined ? null : parseFloat(row.pass_rate),
    batch:             String(row.batch || ''),
    semester:          String(row.semester || ''),
    report_date:       row.report_date ? formatDate(row.report_date) : '',
  };
}

/**
 * Format BigQuery date/timestamp values to string
 */
function formatDate(val) {
  if (!val) return '';
  if (typeof val === 'string') return val;
  if (val.value) return val.value; // BigQuery date object
  if (val instanceof Date) return val.toISOString().split('T')[0];
  return String(val);
}
