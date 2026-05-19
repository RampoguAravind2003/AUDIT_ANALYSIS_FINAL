import fs from 'fs';
import path from 'path';
import { BigQuery } from '@google-cloud/bigquery';
import { transformSemesterRow, transformAssessmentRow } from './transformers.js';
import { SEMESTER_DATES_BY_SEMESTER } from '../../src/constants/semesterDates.js';

const env = globalThis.process?.env ?? {};
const DEFAULT_PROJECT_ID = 'kossip-helpers';
const DEFAULT_DATASET = 'content_bases_metabase';
const DEFAULT_SEMESTER_TABLE = 'all_users_question_attempt_details_for_question_set_units';
const DEFAULT_ASSESSMENT_TABLE = 'all_users_question_attempt_details_for_question_set_units';
const DEFAULT_ASSESSMENT_TOPIC_TABLE = 'niat_learning_performance_semester_wise_topin_assessment_scores_for_curriculum_team';
const DEFAULT_USERS_TABLE = 'niat_and_intensive_offline_users_details';
const DEFAULT_CONTENT_TABLE = 'content_all_products_unit_wise_content_hierarchy_details';
const DEFAULT_SCHEDULE_TABLE = 'niat_and_intensive_offline_section_wise_daily_learning_schedule_details';

function getEnv(...keys) {
  for (const key of keys) {
    const value = env[key];
    if (typeof value === 'string' && value.trim()) return value.trim();
  }
  return '';
}

function parseTableReference(tableRef, defaultTable) {
  const fallback = {
    projectId: getEnv('BQ_PROJECT_ID', 'BQPROJECTID') || DEFAULT_PROJECT_ID,
    dataset: getEnv('BQ_DATASET', 'BQDATASET') || DEFAULT_DATASET,
    table: defaultTable,
  };

  if (!tableRef) return fallback;

  const parts = tableRef.split('.').map((part) => part.trim()).filter(Boolean);
  if (parts.length === 3) {
    return { projectId: parts[0], dataset: parts[1], table: parts[2] };
  }
  if (parts.length === 2) {
    return {
      projectId: fallback.projectId,
      dataset: parts[0],
      table: parts[1],
    };
  }
  if (parts.length === 1) {
    return {
      projectId: fallback.projectId,
      dataset: fallback.dataset,
      table: parts[0],
    };
  }

  throw new Error('Table reference must use table, dataset.table, or project.dataset.table format');
}

function resolveBigQueryOptions() {
  const credentialsJson = getEnv('BQ_CREDENTIALS_JSON', 'BQCREDENTIALSJSON');
  if (credentialsJson) return { credentials: JSON.parse(credentialsJson) };

  const credentialsFile = getEnv(
    'BQ_CREDENTIALS_FILE',
    'BQCREDENTIALSFILE',
    'GOOGLE_APPLICATION_CREDENTIALS',
    'GOOGLEAPPLICATIONCREDENTIALS',
  );
  if (!credentialsFile) return {};

  const resolvedPath = path.isAbsolute(credentialsFile)
    ? credentialsFile
    : path.resolve(process.cwd(), credentialsFile);

  if (!fs.existsSync(resolvedPath)) {
    throw new Error(`BigQuery credentials file not found: ${resolvedPath}`);
  }

  return { keyFilename: resolvedPath };
}

function formatTableReference({ projectId, dataset, table }) {
  return `\`${projectId}.${dataset}.${table}\``;
}

function toIsoDate(value) {
  if (!value) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '';
  return parsed.toISOString().split('T')[0];
}

function shiftIsoDate(isoDate, yearDelta = 0) {
  if (!isoDate || yearDelta === 0) return isoDate;
  const [year, month, day] = isoDate.split('-').map(Number);
  return `${String(year + yearDelta).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function shouldApplyBatchFilter(batch) {
  if (!batch?.trim()) return false;
  return !/^niat\s+\d+$/i.test(batch.trim());
}

function getBatchYearShift(batch) {
  const match = batch?.trim().match(/^niat\s+(\d{2})$/i);
  if (!match) return 0;
  return Number(match[1]) - 25;
}

function buildSemesterWindowClause(semester, batch, instituteExpr, dateExpr, params) {
  const windows = SEMESTER_DATES_BY_SEMESTER[semester];
  if (!windows) return '';
  const yearShift = getBatchYearShift(batch);

  const clauses = Object.entries(windows)
    .map(([instituteName, { start, end }], index) => {
      const startDate = shiftIsoDate(toIsoDate(start), yearShift);
      const endDate = shiftIsoDate(toIsoDate(end), yearShift);
      if (!startDate || !endDate) return null;

      const instituteKey = `semesterInstitute${index}`;
      const startKey = `semesterStart${index}`;
      const endKey = `semesterEnd${index}`;

      params[instituteKey] = instituteName.toLowerCase();
      params[startKey] = startDate;
      params[endKey] = endDate;

      return `(LOWER(${instituteExpr}) = @${instituteKey} AND ${dateExpr} BETWEEN @${startKey} AND @${endKey})`;
    })
    .filter(Boolean);

  return clauses.length ? `(${clauses.join(' OR ')})` : '';
}

function buildFilters(filters = {}, { attemptAlias = 'a', userAlias = 'u' } = {}) {
  const dateExpr = `DATE(COALESCE(${attemptAlias}.submission_datetime, ${attemptAlias}.question_start_datetime))`;
  const instituteExpr = `${userAlias}.institute_name`;
  const conditions = [
    `${userAlias}.user_id IS NOT NULL`,
    `TRIM(COALESCE(${instituteExpr}, '')) != ''`,
  ];
  const params = {};

  const semesterWindowClause = buildSemesterWindowClause(filters.semester, filters.batch, instituteExpr, dateExpr, params);
  if (semesterWindowClause) conditions.push(semesterWindowClause);

  if (filters.startDate) {
    conditions.push(`${dateExpr} >= @startDate`);
    params.startDate = filters.startDate;
  }

  if (filters.endDate) {
    conditions.push(`${dateExpr} <= @endDate`);
    params.endDate = filters.endDate;
  }

  if (shouldApplyBatchFilter(filters.batch)) {
    conditions.push(`LOWER(COALESCE(${userAlias}.batch_name, '')) LIKE @batchPattern`);
    params.batchPattern = `%${filters.batch.trim().toLowerCase()}%`;
  }

  return {
    whereClause: conditions.join(' AND '),
    params,
    dateExpr,
  };
}

function getSessionTypeExpression(titleExpr = 'a.question_set_title') {
  return `CASE
    WHEN REGEXP_CONTAINS(LOWER(COALESCE(${titleExpr}, '')), r'assignment|assessment|exam|quiz') THEN 'EXAM'
    WHEN REGEXP_CONTAINS(LOWER(COALESCE(${titleExpr}, '')), r'session|lecture') THEN 'LECTURE'
    ELSE 'PRACTICE'
  END`;
}

function getCourseExpression(attemptAlias = 'a') {
  return `COALESCE(
    NULLIF(TRIM(${attemptAlias}.question_set_title), ''),
    CONCAT('Question Set ', CAST(${attemptAlias}.question_set_id AS STRING))
  )`;
}

function getSectionExpression(userAlias = 'u') {
  return `COALESCE(NULLIF(TRIM(${userAlias}.section_name), ''), 'Unknown')`;
}

const semesterTableRef = parseTableReference(
  getEnv('BQ_SEMESTER_TABLE', 'BQSEMESTERTABLE', 'BQ_TABLE', 'BQTABLE'),
  DEFAULT_SEMESTER_TABLE,
);
const assessmentTableRef = parseTableReference(
  getEnv('BQ_ASSESSMENT_TABLE', 'BQASSESSMENTTABLE', 'BQ_TABLE', 'BQTABLE'),
  DEFAULT_ASSESSMENT_TABLE,
);
const assessmentTopicTableRef = parseTableReference(
  getEnv('BQ_ASSESSMENT_TOPIC_TABLE', 'BQASSESSMENTTOPICTABLE'),
  DEFAULT_ASSESSMENT_TOPIC_TABLE,
);
const usersTableRef = parseTableReference(
  getEnv('BQ_USERS_TABLE', 'BQUSERSTABLE'),
  DEFAULT_USERS_TABLE,
);
const contentTableRef = parseTableReference(
  getEnv('BQ_CONTENT_TABLE', 'BQCONTENTTABLE'),
  DEFAULT_CONTENT_TABLE,
);
const scheduleTableRef = parseTableReference(
  getEnv('BQ_SCHEDULE_TABLE', 'BQSCHEDULETABLE'),
  DEFAULT_SCHEDULE_TABLE,
);

const projectId = getEnv('BQ_PROJECT_ID', 'BQPROJECTID') || semesterTableRef.projectId;
const dataset = getEnv('BQ_DATASET', 'BQDATASET') || semesterTableRef.dataset;

const semesterTable = formatTableReference(semesterTableRef);
const assessmentTable = formatTableReference(assessmentTableRef);
const assessmentTopicTable = formatTableReference(assessmentTopicTableRef);
const usersTable = formatTableReference(usersTableRef);
const contentTable = formatTableReference(contentTableRef);
const scheduleTable = formatTableReference(scheduleTableRef);

const bigquery = new BigQuery({
  projectId,
  ...resolveBigQueryOptions(),
});

function buildUsersSubquery() {
  return `
    SELECT DISTINCT
      user_id,
      institute_name,
      section_name,
      batch_name
    FROM ${usersTable}
  `;
}

function buildContentSubquery() {
  return `
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
      FROM ${contentTable}
    )
    GROUP BY unit_id
  `;
}

function buildScheduleFilters(filters = {}) {
  const dateExpr = 'DATE(s.session_date)';
  const instituteExpr = 's.institute_name';
  const conditions = [`TRIM(COALESCE(${instituteExpr}, '')) != ''`];
  const params = {};

  const semesterWindowClause = buildSemesterWindowClause(filters.semester, filters.batch, instituteExpr, dateExpr, params);
  if (semesterWindowClause) conditions.push(semesterWindowClause);

  if (filters.startDate) {
    conditions.push(`${dateExpr} >= @startDate`);
    params.startDate = filters.startDate;
  }

  if (filters.endDate) {
    conditions.push(`${dateExpr} <= @endDate`);
    params.endDate = filters.endDate;
  }

  if (shouldApplyBatchFilter(filters.batch)) {
    conditions.push(`LOWER(COALESCE(s.batch_name, '')) LIKE @batchPattern`);
    params.batchPattern = `%${filters.batch.trim().toLowerCase()}%`;
  }

  return {
    whereClause: conditions.join(' AND '),
    params,
    dateExpr,
  };
}

export async function testConnection() {
  await Promise.all([
    bigquery.query(`SELECT 1 AS test FROM ${semesterTable} LIMIT 1`),
    bigquery.query(`SELECT 1 AS test FROM ${usersTable} LIMIT 1`),
  ]);

  return {
    connected: true,
    projectId,
    dataset,
    semesterTable: semesterTableRef.table,
    assessmentTable: assessmentTableRef.table,
    usersTable: usersTableRef.table,
    contentTable: contentTableRef.table,
    scheduleTable: scheduleTableRef.table,
  };
}

export async function fetchSemesterData(filters = {}) {
  const { whereClause, params, dateExpr } = buildScheduleFilters(filters);

  const sql = `
    WITH content AS (
      ${buildContentSubquery()}
    ),
    schedule_base AS (
      SELECT
        s.institute_name AS institute,
        COALESCE(NULLIF(TRIM(s.section_name), ''), 'Unknown') AS section,
        s.session_type,
        s.session_status,
        ${dateExpr} AS report_date,
        s.session_id,
        COALESCE(content.course_title, s.session_name) AS course_candidate
      FROM ${scheduleTable} s
      LEFT JOIN content ON s.resource_id = content.unit_id
      WHERE ${whereClause}
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
        ${getSectionExpression('u')} AS section,
        COUNT(DISTINCT user_id) AS students
      FROM ${usersTable} u
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
      COUNT(DISTINCT sc.session_id) AS sessions,
      COALESCE(r.students, 0) AS students,
      ROUND(
        100 * SAFE_DIVIDE(
          COUNT(DISTINCT IF(UPPER(COALESCE(sc.session_status, '')) IN ('COMPLETED', 'DELIVERED', 'CONDUCTED'), sc.session_id, NULL)),
          COUNT(DISTINCT sc.session_id)
        ),
        2
      ) AS completion,
      0 AS avg_time,
      0 AS p80_time,
      COALESCE(rc.section_count, 0) AS section_count,
      @selectedBatch AS batch,
      @selectedSemester AS semester,
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
  `;

  const [rows] = await bigquery.query({
    query: sql,
    params: {
      ...params,
      selectedBatch: filters.batch || '',
      selectedSemester: filters.semester || '',
    },
  });

  return rows.map(transformSemesterRow);
}

export async function fetchAssessmentData(filters = {}) {
  const legacyDateExpr = `DATE(COALESCE(a.submission_datetime, a.question_start_datetime))`;
  const topicDateExpr = 'DATE(t.assessment_start_datetime)';
  const topicInstituteExpr = `COALESCE(NULLIF(TRIM(t.institute_name), ''), u.institute_name)`;
  const params = {
    selectedBatch: filters.batch || '',
    selectedSemester: filters.semester || '',
  };

  const legacyConditions = [
    `u.user_id IS NOT NULL`,
    `TRIM(COALESCE(u.institute_name, '')) != ''`,
  ];
  const legacySemesterClause = buildSemesterWindowClause(filters.semester, filters.batch, 'u.institute_name', legacyDateExpr, params);
  if (legacySemesterClause) legacyConditions.push(legacySemesterClause);

  const topicConditions = [
    `TRIM(COALESCE(${topicInstituteExpr}, '')) != ''`,
  ];
  const topicSemesterClause = buildSemesterWindowClause(filters.semester, filters.batch, topicInstituteExpr, topicDateExpr, params);
  if (topicSemesterClause) topicConditions.push(topicSemesterClause);

  if (filters.startDate) {
    legacyConditions.push(`${legacyDateExpr} >= @startDate`);
    topicConditions.push(`${topicDateExpr} >= @startDate`);
    params.startDate = filters.startDate;
  }

  if (filters.endDate) {
    legacyConditions.push(`${legacyDateExpr} <= @endDate`);
    topicConditions.push(`${topicDateExpr} <= @endDate`);
    params.endDate = filters.endDate;
  }

  if (shouldApplyBatchFilter(filters.batch)) {
    legacyConditions.push(`LOWER(COALESCE(u.batch_name, '')) LIKE @batchPattern`);
    topicConditions.push(`LOWER(COALESCE(u.batch_name, '')) LIKE @batchPattern`);
    params.batchPattern = `%${filters.batch.trim().toLowerCase()}%`;
  }

  const sql = `
    WITH users AS (
      ${buildUsersSubquery()}
    ),
    content AS (
      ${buildContentSubquery()}
    ),
    legacy_attempts AS (
      SELECT
        u.institute_name AS university,
        COALESCE(NULLIF(TRIM(u.section_name), ''), 'Unknown') AS section,
        COALESCE(content.course_title, ${getCourseExpression()}) AS course_code,
        'Assessment' AS assessment_type,
        CAST(a.question_set_id AS STRING) AS assessment_id,
        a.user_id AS user_id,
        COALESCE(a.user_score, a.actual_score) AS user_score,
        a.actual_score AS actual_score,
        NULL AS section_evaluation_result,
        ${legacyDateExpr} AS report_date
      FROM ${assessmentTable} a
      JOIN users u USING (user_id)
      LEFT JOIN content ON CAST(a.question_set_id AS STRING) = content.unit_id
      WHERE ${legacyConditions.join(' AND ')}
        AND COALESCE(a.actual_score, 0) > 0
        AND NOT REGEXP_CONTAINS(LOWER(COALESCE(a.question_set_title, '')), r'skill assessment|graded assessment')
    ),
    topic_attempts AS (
      SELECT
        ${topicInstituteExpr} AS university,
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
        CAST(t.assessment_id AS STRING) AS assessment_id,
        t.user_id AS user_id,
        t.user_section_score AS user_score,
        t.section_actual_score AS actual_score,
        t.section_evaluation_result AS section_evaluation_result,
        ${topicDateExpr} AS report_date
      FROM ${assessmentTopicTable} t
      LEFT JOIN users u USING (user_id)
      LEFT JOIN content ON CAST(t.unit_id AS STRING) = content.unit_id
      WHERE ${topicConditions.join(' AND ')}
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
      ROUND(AVG(COALESCE(SAFE_DIVIDE(user_score, NULLIF(actual_score, 0)), 0)), 4) AS avg_score,
      ROUND(
        SAFE_DIVIDE(
          COUNT(DISTINCT IF(
            assessment_type IN ('Skill Assessment', 'Graded Assessment')
              AND REGEXP_CONTAINS(UPPER(COALESCE(section_evaluation_result, '')), r'PASS'),
            CONCAT(CAST(user_id AS STRING), '||', CAST(assessment_id AS STRING)),
            NULL
          )),
          COUNT(DISTINCT IF(
            assessment_type IN ('Skill Assessment', 'Graded Assessment'),
            CONCAT(CAST(user_id AS STRING), '||', CAST(assessment_id AS STRING)),
            NULL
          ))
        ),
        4
      ) AS pass_rate,
      @selectedBatch AS batch,
      @selectedSemester AS semester,
      CAST(MAX(report_date) AS STRING) AS report_date
    FROM all_attempts
    GROUP BY university, section, course_code, assessment_type
    ORDER BY university, section, course_code, assessment_type
  `;

  const [rows] = await bigquery.query({
    query: sql,
    params,
  });

  return rows.map(transformAssessmentRow);
}

export async function executeCustomQuery(sql, params = {}) {
  const trimmed = sql.trim().toUpperCase();
  if (!trimmed.startsWith('SELECT')) {
    throw new Error('Only SELECT queries are allowed');
  }
  const [rows] = await bigquery.query({ query: sql, params });
  return rows;
}

export async function listTables() {
  const [tables] = await bigquery.dataset(dataset).getTables();
  return tables.map((table) => ({
    id: table.id,
    metadata: {
      type: table.metadata.type,
      numRows: table.metadata.numRows,
      numBytes: table.metadata.numBytes,
    },
  }));
}
