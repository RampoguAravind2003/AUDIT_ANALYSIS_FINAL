export const parseAssessmentCSV = (text) => {
  const lines = text.split('\n').filter(l => l.trim());
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, '').toLowerCase());
  const findCol = (...patterns) => { for (const p of patterns) { const i = headers.findIndex(h => h.includes(p.toLowerCase())); if (i !== -1) return i; } return -1; };

  // Detect if this is a raw per-user file (has user_id + user_section_score)
  const isRawUserFile = findCol('user_id') !== -1 && findCol('user_section_score') !== -1;

  if (isRawUserFile) {
    // Raw per-user file — aggregate to section level
    const cols = {
      userId: findCol('user_id'),
      university: findCol('institute_name', 'institute', 'university'),
      section: findCol('section_name', 'section'),
      courseCode: findCol('section_tech_stack', 'section_tech', 'tech_stack', 'course_code'),
      score: findCol('user_section_score'),
      result: findCol('section_evaluation_result', 'evaluation_result', 'result'),
      assessmentId: findCol('assessment_id'),
      assessmentType: findCol('assessment_type'),
      batch: findCol('batch'),
      semester: findCol('semester'),
      reportDate: findCol('report_date', 'date'),
    };

    // Parse all rows into a map keyed by institute|section|course
    const groupMap = {};
    for (let i = 1; i < lines.length; i++) {
      const vals = []; let curr = '', inQ = false;
      for (const c of lines[i]) { if (c === '"') inQ = !inQ; else if (c === ',' && !inQ) { vals.push(curr.trim()); curr = ''; } else curr += c; }
      vals.push(curr.trim());
      const get = (idx) => idx >= 0 && idx < vals.length ? vals[idx].replace(/"/g, '').trim() : '';
      const getNum = (idx) => parseFloat(get(idx)) || 0;

      const university = get(cols.university);
      const section = get(cols.section);
      const courseCode = get(cols.courseCode);
      const userId = get(cols.userId);
      const score = getNum(cols.score);
      const result = get(cols.result);
      const assessmentId = get(cols.assessmentId) || courseCode;
      const assessmentType = get(cols.assessmentType);
      const batch = get(cols.batch);
      const semester = get(cols.semester);
      const reportDate = get(cols.reportDate);

      if (!university || !courseCode || !userId) continue;

      const key = `${university}|||${section}|||${courseCode}`;
      if (!groupMap[key]) {
        groupMap[key] = {
          university, section, course_code: courseCode,
          scores: [], userIds: new Set(),
          attempts: new Set(), passed: new Set(), assessmentType,
          batch, semester, report_date: reportDate,
        };
      }
      groupMap[key].scores.push(score);
      groupMap[key].userIds.add(userId);
      const attemptKey = `${userId}|||${assessmentId}`;
      groupMap[key].attempts.add(attemptKey);
      if (String(result).toUpperCase().includes('PASS')) groupMap[key].passed.add(attemptKey);
    }

    // Convert groups to aggregated rows
    return Object.values(groupMap).map(g => ({
      university: g.university,
      section: g.section,
      course_code: g.course_code,
      assessment_type: g.assessmentType || 'Assessment',
      // average score normalised to 0-1
      avg_score: g.scores.length ? (g.scores.reduce((s, v) => s + v, 0) / g.scores.length) / 100 : 0,
      pass_rate: g.attempts.size ? g.passed.size / g.attempts.size : null,
      // distinct user count as participation
      avg_participation: g.userIds.size,
      batch: g.batch,
      semester: g.semester,
      report_date: g.report_date,
    }));
  }

  // Already-aggregated file — original parser path
  const cols = {
    university: findCol('university', 'institute'), section: findCol('section'), courseCode: findCol('section_tech', 'tech_stack', 'course_code'),
    participation: findCol('avg_user', 'participation', 'users'), score: findCol('avg_score', 'score'),
    passRate: findCol('pass_rate', 'pass %', 'pass_percentage'), assessmentType: findCol('assessment_type'),
    batch: findCol('batch'), semester: findCol('semester'), reportDate: findCol('report_date', 'date'),
  };
  const result = [];
  for (let i = 1; i < lines.length; i++) {
    const vals = []; let curr = '', inQ = false;
    for (const c of lines[i]) { if (c === '"') inQ = !inQ; else if (c === ',' && !inQ) { vals.push(curr.trim()); curr = ''; } else curr += c; }
    vals.push(curr.trim());
    const get = (idx) => idx >= 0 && idx < vals.length ? vals[idx].replace(/"/g, '').trim() : '';
    const getNum = (idx) => parseFloat(get(idx)) || 0;
    const university = get(cols.university), section = get(cols.section), courseCode = get(cols.courseCode);
    if (!university || !courseCode) continue;
    result.push({ university, section, course_code: courseCode, assessment_type: get(cols.assessmentType) || 'Assessment', avg_participation: getNum(cols.participation), avg_score: getNum(cols.score), pass_rate: cols.passRate >= 0 ? getNum(cols.passRate) : null, batch: get(cols.batch), semester: get(cols.semester), report_date: get(cols.reportDate) });
  }
  return result;
};
