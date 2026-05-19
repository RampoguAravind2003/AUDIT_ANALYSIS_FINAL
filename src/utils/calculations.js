import { SERIES_RANGES } from '../constants';
import { getAllottedHours, getSeriesForAllottedHours, getSeriesForValue } from './semesterHelpers';

const normalizeSection = (section) => String(section || '').trim();
const isValidSection = (section) => {
  const value = normalizeSection(section);
  return value && value.toLowerCase() !== 'unknown';
};

const getRosterSectionCount = (rows) => {
  const counts = rows
    .map(d => Number(d.section_count ?? d.sectionCount ?? 0))
    .filter(count => Number.isFinite(count) && count > 0);
  return counts.length ? Math.max(...counts) : 0;
};

const average = (values) => {
  const nums = values.filter(v => Number.isFinite(v));
  return nums.length ? nums.reduce((sum, value) => sum + value, 0) / nums.length : null;
};

const normalizeAssessmentType = (type) => String(type || '').trim().toLowerCase();
const isSkillAssessment = (row) => normalizeAssessmentType(row.assessment_type).includes('skill');
const isGradedAssessment = (row) => normalizeAssessmentType(row.assessment_type).includes('graded');
const passValue = (row) => {
  const value = row.pass_rate ?? row.avg_score;
  return Number.isFinite(value) ? value : null;
};

const calcRowsAssessment = (rows) => ({
  avgScore: average(rows.map(d => Number(d.avg_score))),
  avgParticipation: average(rows.map(d => Number(d.avg_participation))),
  avgSkillPassRate: average(rows.filter(isSkillAssessment).map(passValue)),
  avgGradedPassRate: average(rows.filter(isGradedAssessment).map(passValue)),
});

export const calcUnivAssessment = (assessmentData, univName) => {
  if (!assessmentData) return { avgScore: null, avgParticipation: null, avgSkillPassRate: null, avgGradedPassRate: null };
  const univData = assessmentData.filter(d => d.university === univName);
  if (!univData.length) return { avgScore: null, avgParticipation: null, avgSkillPassRate: null, avgGradedPassRate: null };
  const sections = [...new Set(univData.map(d => normalizeSection(d.section)).filter(isValidSection))];
  if (sections.length <= 1) {
    return calcRowsAssessment(univData);
  }
  const sectionAvgs = sections.map(sec => {
    const secData = univData.filter(d => d.section === sec);
    return calcRowsAssessment(secData);
  });
  return {
    avgScore: average(sectionAvgs.map(a => a.avgScore)),
    avgParticipation: average(sectionAvgs.map(a => a.avgParticipation)),
    avgSkillPassRate: average(sectionAvgs.map(a => a.avgSkillPassRate)),
    avgGradedPassRate: average(sectionAvgs.map(a => a.avgGradedPassRate)),
  };
};

export const calculateSeriesData = (data, assessmentData, analysisType = 'design', semester) => {
  const institutes = [...new Set(data.map(d => d.institute))];
  const univMetrics = institutes.map(inst => {
    const instData = data.filter(d => d.institute === inst);
    const sections = [...new Set(instData.map(d => normalizeSection(d.section)).filter(isValidSection))];
    const rosterSectionCount = getRosterSectionCount(instData);
    const calcSectionMetric = (secData) => {
      const lec = secData.filter(d => d.session_type === 'LECTURE');
      const prac = secData.filter(d => d.session_type === 'PRACTICE');
      const exam = secData.filter(d => d.session_type === 'EXAM');
      const sum = (a, k) => a.reduce((s, d) => s + (d[k] || 0), 0);
      const avg = (a, k) => a.length ? sum(a, k) / a.length : 0;
      // Get max sessions value per session type (representative delivered count)
      const lecSessions = lec.length ? Math.max(...lec.map(d => d.sessions || 0)) : 0;
      const pracSessions = prac.length ? Math.max(...prac.map(d => d.sessions || 0)) : 0;
      const examSessions = exam.length ? Math.max(...exam.map(d => d.sessions || 0)) : 0;
      const totalSessions = lecSessions + pracSessions + examSessions;
      return {
        totalSessions,
        classSize: Math.max(...secData.map(d => d.students || 0), 0),
        lectureCompletion: avg(lec, 'completion'),
        practiceCompletion: avg(prac, 'completion'),
        examCompletion: avg(exam, 'completion'),
        avgTime: sum(secData, 'avg_time'),
        p80Time: sum(secData, 'p80_time'),
        practiceAvgTime: sum(prac, 'avg_time'),
        practiceP80Time: sum(prac, 'p80_time'),
      };
    };
    const sectionMetrics = sections.length > 0
      ? sections.map(sec => ({ section: sec, ...calcSectionMetric(instData.filter(d => d.section === sec)) }))
      : [{ section: 'All', ...calcSectionMetric(instData) }];
    const n = sectionMetrics.length;
    const avg = (k) => sectionMetrics.reduce((s, m) => s + m[k], 0) / n;
    const { avgScore, avgParticipation, avgSkillPassRate, avgGradedPassRate } = calcUnivAssessment(assessmentData, inst);
    const allottedHours = getAllottedHours(inst, semester);
    let seriesName;
    if (analysisType === 'design') {
      const seriesInfo = getSeriesForAllottedHours(inst, semester);
      seriesName = seriesInfo ? seriesInfo.name : 'Unknown';
    } else {
      seriesName = getSeriesForValue(avg('totalSessions')).name;
    }
    return { name: inst, sectionCount: rosterSectionCount || sections.length || 1, avgSessions: avg('totalSessions'), avgClassSize: avg('classSize'), avgLectureCompletion: avg('lectureCompletion'), avgPracticeCompletion: avg('practiceCompletion'), avgExamCompletion: avg('examCompletion'), avgOverallCompletion: (avg('lectureCompletion') + avg('practiceCompletion') + avg('examCompletion')) / 3, avgWorkload: avg('avgTime'), avgP80Workload: avg('p80Time'), avgPracticeWorkload: avg('practiceAvgTime'), avgPracticeP80Workload: avg('practiceP80Time'), series: seriesName, allottedHours, avgAssessmentScore: avgScore, avgParticipation, avgSkillPassRate, avgGradedPassRate };
  });

  const seriesData = {};
  SERIES_RANGES.forEach(s => {
    const univs = univMetrics.filter(u => u.series === s.name);
    if (!univs.length) { seriesData[s.name] = { universities: [], avgSessions: 0, avgClassSize: 0, avgLectureCompletion: 0, avgPracticeCompletion: 0, avgExamCompletion: 0, avgOverallCompletion: 0, avgWorkload: 0, avgP80Workload: 0, avgPracticeWorkload: 0, avgPracticeP80Workload: 0, totalStudents: 0, avgAssessmentScore: null, avgParticipation: null, avgSkillPassRate: null, avgGradedPassRate: null, avgAllottedHours: 0 }; return; }
    const avg = (k) => univs.reduce((s, u) => s + u[k], 0) / univs.length;
    const univsWithScore = univs.filter(u => u.avgAssessmentScore !== null);
    const univsWithAllotted = univs.filter(u => u.allottedHours !== null);
    seriesData[s.name] = { universities: univs, avgSessions: avg('avgSessions'), avgClassSize: avg('avgClassSize'), avgLectureCompletion: avg('avgLectureCompletion'), avgPracticeCompletion: avg('avgPracticeCompletion'), avgExamCompletion: avg('avgExamCompletion'), avgOverallCompletion: avg('avgOverallCompletion'), avgWorkload: avg('avgWorkload'), avgP80Workload: avg('avgP80Workload'), avgPracticeWorkload: avg('avgPracticeWorkload'), avgPracticeP80Workload: avg('avgPracticeP80Workload'), totalStudents: univs.reduce((s, u) => s + Math.round(u.avgClassSize * u.sectionCount), 0), avgAssessmentScore: univsWithScore.length ? univsWithScore.reduce((s, u) => s + u.avgAssessmentScore, 0) / univsWithScore.length : null, avgParticipation: univsWithScore.length ? univsWithScore.reduce((s, u) => s + u.avgParticipation, 0) / univsWithScore.length : null, avgSkillPassRate: average(univs.map(u => u.avgSkillPassRate)), avgGradedPassRate: average(univs.map(u => u.avgGradedPassRate)), avgAllottedHours: univsWithAllotted.length ? univsWithAllotted.reduce((s, u) => s + u.allottedHours, 0) / univsWithAllotted.length : 0 };
  });

  if (analysisType === 'design') {
    const unknownUnivs = univMetrics.filter(u => u.series === 'Unknown');
    if (unknownUnivs.length > 0) seriesData['Unknown'] = { universities: unknownUnivs, avgSessions: unknownUnivs.reduce((s, u) => s + u.avgSessions, 0) / unknownUnivs.length, avgClassSize: unknownUnivs.reduce((s, u) => s + u.avgClassSize, 0) / unknownUnivs.length, avgLectureCompletion: 0, avgPracticeCompletion: 0, avgExamCompletion: 0, avgOverallCompletion: 0, avgWorkload: 0, avgP80Workload: 0, avgPracticeWorkload: 0, avgPracticeP80Workload: 0, totalStudents: 0, avgAssessmentScore: null, avgParticipation: null, avgSkillPassRate: null, avgGradedPassRate: null, avgAllottedHours: 0 };
  }
  return seriesData;
};
