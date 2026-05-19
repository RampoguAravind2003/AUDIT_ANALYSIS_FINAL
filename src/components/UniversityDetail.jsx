import { useState, useMemo } from 'react';
import { useTheme } from '../context/ThemeContext';
import AnimatedView from './ui/AnimatedView';
import ScrollToTop from './ui/ScrollToTop';
import DonutChart from './ui/DonutChart';
import WorkloadBar from './ui/WorkloadBar';
import {
  getSemesterDatesForInstitute,
  normalizeCourseName,
  r2,
  groupCoursesBySubject,
  sortSubjectsByOrder,
  groupAssessmentBySubject,
} from '../utils/semesterHelpers';
import { addRipple } from '../utils/ripple';

const avg = (values) => {
  const nums = values.filter(v => Number.isFinite(v));
  return nums.length ? nums.reduce((sum, value) => sum + value, 0) / nums.length : null;
};

const isSkillAssessment = (row) => String(row.assessment_type || '').toLowerCase().includes('skill');
const isGradedAssessment = (row) => String(row.assessment_type || '').toLowerCase().includes('graded');
const passMetric = (row) => {
  const value = row.pass_rate ?? row.avg_score;
  return Number.isFinite(value) ? value : null;
};

export default function UniversityDetail({ data, assessmentData, selectedInstitute, onBack, onReset, semester }) {
  const { isDark } = useTheme();
  const [selectedSection, setSelectedSection] = useState('');
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [viewMode, setViewMode] = useState('course'); // 'course' or 'subject'

  const sections = useMemo(
    () => [...new Set(
      data
        .filter(d => d.institute === selectedInstitute)
        .map(d => String(d.section || '').trim())
        .filter(section => section && section.toLowerCase() !== 'unknown')
    )].sort(),
    [data, selectedInstitute]
  );

  const activeSection = sections.includes(selectedSection) ? selectedSection : '';

  const assessmentMetrics = useMemo(() => {
    if (!assessmentData) return null;
    let filtered = assessmentData.filter(d => d.university === selectedInstitute);
    if (activeSection) filtered = filtered.filter(d => d.section === activeSection);
    if (!filtered.length) return null;
    const courseScores = {};
    filtered.forEach(d => {
      const name = normalizeCourseName(d.course_code, semester);
      if (!courseScores[name]) courseScores[name] = { scores: [], parts: [], skillPass: [], gradedPass: [] };
      courseScores[name].scores.push(d.avg_score);
      courseScores[name].parts.push(d.avg_participation);
      if (isSkillAssessment(d)) courseScores[name].skillPass.push(passMetric(d));
      if (isGradedAssessment(d)) courseScores[name].gradedPass.push(passMetric(d));
    });

    // Group by subject if in subject view mode (Semester 2 only)
    const groupedScores = viewMode === 'subject' && semester === 'Semester 2'
      ? groupAssessmentBySubject(courseScores, semester)
      : courseScores;

    const courses = Object.keys(groupedScores).map(c => ({
      name: c,
      avgScore: avg(groupedScores[c].scores),
      avgParticipation: avg(groupedScores[c].parts),
      skillPassRate: avg(groupedScores[c].skillPass || []),
      gradedPassRate: avg(groupedScores[c].gradedPass || []),
    }));
    return {
      courses,
      overallScore: avg(courses.map(c => c.avgScore)),
      overallParticipation: avg(courses.map(c => c.avgParticipation)),
      overallSkillPassRate: avg(courses.map(c => c.skillPassRate)),
      overallGradedPassRate: avg(courses.map(c => c.gradedPassRate)),
    };
  }, [assessmentData, selectedInstitute, activeSection, semester, viewMode]);

  const metrics = useMemo(() => {
    let filtered = data.filter(d => d.institute === selectedInstitute);
    if (activeSection) filtered = filtered.filter(d => d.section === activeSection);
    if (!filtered.length) return null;
    const courseGroups = filtered.reduce((acc, row) => {
      const courseName = normalizeCourseName(row.course, semester);
      if (!acc[courseName]) acc[courseName] = [];
      acc[courseName].push(row);
      return acc;
    }, {});

    // Group by subject if in subject view mode (Semester 2 only)
    const displayGroups = viewMode === 'subject' && semester === 'Semester 2'
      ? groupCoursesBySubject(courseGroups, semester)
      : courseGroups;

    const courses = viewMode === 'subject' && semester === 'Semester 2'
      ? sortSubjectsByOrder(Object.keys(displayGroups))
      : Object.keys(displayGroups).sort();

    const lec = filtered.filter(d => d.session_type === 'LECTURE');
    const prac = filtered.filter(d => d.session_type === 'PRACTICE');
    const exam = filtered.filter(d => d.session_type === 'EXAM');
    const sum = (a, k) => a.reduce((s, d) => s + (d[k] || 0), 0);
    const avg = (a, k) => a.length ? sum(a, k) / a.length : 0;
    const rosterSize = activeSection
      ? Math.max(...filtered.map(d => d.students || 0), 0)
      : [...filtered.reduce((sectionMap, row) => {
        const section = String(row.section || '').trim();
        if (section && section.toLowerCase() !== 'unknown') {
          sectionMap.set(section, Math.max(sectionMap.get(section) || 0, row.students || 0));
        }
        return sectionMap;
      }, new Map()).values()].reduce((total, students) => total + students, 0) || Math.max(...filtered.map(d => d.students || 0), 0);

    return {
      courses, courseCount: courses.length,
      courseGroups: displayGroups,
      lectureCount: sum(lec, 'sessions'),
      practiceCount: sum(prac, 'sessions'),
      examCount: sum(exam, 'sessions'),
      totalSessions: sum(filtered, 'sessions'),
      classSize: rosterSize,
      overallCompletion: avg(filtered, 'completion'),
      lectureCompletion: avg(lec, 'completion'),
      practiceCompletion: avg(prac, 'completion'),
      examCompletion: avg(exam, 'completion'),
      avgTime: sum(filtered, 'avg_time'),
      p80Time: sum(filtered, 'p80_time'),
      practiceAvgTime: sum(prac, 'avg_time'),
      practiceP80Time: sum(prac, 'p80_time'),
      filtered,
    };
  }, [data, selectedInstitute, activeSection, semester, viewMode]);

  if (!metrics) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-slate-900' : 'bg-gray-50'}`}>
        <div className="text-center">
          <p className={`mb-4 ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>No data</p>
          <button onClick={onBack} className="text-blue-500 hover:underline">Go Back</button>
        </div>
      </div>
    );
  }

  const dates = getSemesterDatesForInstitute(selectedInstitute, semester);

  // Theme helpers
  const pageBg = 'ui-shell';
  const cardBg = 'panel-surface';
  const headingColor = isDark ? 'text-slate-100' : 'text-slate-900';
  const subColor = isDark ? 'text-slate-300' : 'text-slate-600';
  const muted = isDark ? 'text-slate-500' : 'text-gray-500';
  const bodyText = isDark ? 'text-slate-100' : 'text-gray-900';
  const borderColor = isDark ? 'border-slate-700' : 'border-gray-100';
  const statAccentBg = 'panel-muted';
  const statGrayBg = 'panel-muted';
  const completionBg = 'panel-muted';
  const tableBg = isDark ? 'bg-slate-900/85' : 'bg-white';
  const tableHeaderBg = isDark ? 'bg-slate-800' : 'bg-gray-50';
  const tableHeaderText = isDark ? 'text-slate-400' : 'text-gray-500';
  const tableRowHover = isDark ? 'hover:bg-slate-800/60' : 'hover:bg-slate-50';
  const tableRowDivide = isDark ? 'divide-slate-700' : 'divide-gray-50';
  const tableCellSticky = isDark
    ? 'bg-slate-900/95 hover:bg-slate-800/90 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.3)]'
    : 'bg-white hover:bg-indigo-50/30 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.06)]';
  const tableStickyHeader = isDark
    ? 'bg-slate-800 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.3)]'
    : 'bg-gray-50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.08)]';
  const backBtnCls = isDark
    ? 'text-slate-400 hover:text-slate-100 hover:bg-slate-700'
    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100';

  const SidebarContent = ({ viewMode }) => (
    <>
      <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Semester Timeline</h3>
      {dates ? (
        <div className="space-y-3">
          <div className={`rounded-lg p-4 border ${isDark ? 'bg-emerald-900/30 border-emerald-700/50' : 'bg-emerald-50 border-emerald-100'}`}>
            <p className={`text-xs font-medium uppercase mb-1 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>Start Date</p>
            <p className={`text-lg font-bold ${bodyText}`}>{dates.start}</p>
          </div>
          <div className={`rounded-lg p-4 border ${isDark ? 'bg-rose-900/30 border-rose-700/50' : 'bg-rose-50 border-rose-100'}`}>
            <p className={`text-xs font-medium uppercase mb-1 ${isDark ? 'text-rose-400' : 'text-rose-600'}`}>End Date</p>
            <p className={`text-lg font-bold ${bodyText}`}>{dates.end}</p>
          </div>
        </div>
      ) : (
        <p className={`text-sm italic ${muted}`}>Dates not available</p>
      )}
      <div className={`mt-5 pt-5 border-t ${borderColor}`}>
        <h4 className={`text-xs font-semibold uppercase mb-3 ${muted}`}>Quick Stats</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className={subColor}>{viewMode === 'subject' ? 'Subjects' : 'Courses'}</span>
            <span className={`font-semibold ${bodyText}`}>{metrics.courseCount}</span>
          </div>
          <div className="flex justify-between">
            <span className={subColor}>Students</span>
            <span className={`font-semibold ${bodyText}`}>{r2(metrics.classSize)}</span>
          </div>
          <div className="flex justify-between">
            <span className={subColor}>Total Sessions</span>
            <span className={`font-semibold ${bodyText}`}>{r2(metrics.totalSessions)}</span>
          </div>
        </div>
      </div>
              {assessmentMetrics && (
                <div className={`mt-5 pt-5 border-t ${borderColor}`}>
                  <h4 className={`text-xs font-semibold uppercase mb-3 ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>Assessment Summary</h4>
                  <div className="space-y-3">
                    <div className={`rounded-lg p-3 border ${isDark ? 'bg-purple-900/30 border-purple-700/50' : 'bg-purple-50 border-purple-100'}`}>
              <p className={`text-xs mb-1 ${isDark ? 'text-purple-400' : 'text-purple-600'}`}>Skill Pass</p>
              <p className={`text-xl font-bold ${isDark ? 'text-purple-300' : 'text-purple-700'}`}>
                {assessmentMetrics.overallSkillPassRate != null ? `${(assessmentMetrics.overallSkillPassRate * 100).toFixed(1)}%` : '—'}
              </p>
            </div>
            <div className={`rounded-lg p-3 border ${isDark ? 'bg-fuchsia-900/30 border-fuchsia-700/50' : 'bg-fuchsia-50 border-fuchsia-100'}`}>
              <p className={`text-xs mb-1 ${isDark ? 'text-fuchsia-400' : 'text-fuchsia-600'}`}>Graded Pass</p>
              <p className={`text-xl font-bold ${isDark ? 'text-fuchsia-300' : 'text-fuchsia-700'}`}>
                {assessmentMetrics.overallGradedPassRate != null ? `${(assessmentMetrics.overallGradedPassRate * 100).toFixed(1)}%` : '—'}
              </p>
            </div>
            <div className={`rounded-lg p-3 border ${isDark ? 'bg-indigo-900/30 border-indigo-700/50' : 'bg-indigo-50 border-indigo-100'}`}>
              <p className={`text-xs mb-1 ${isDark ? 'text-indigo-400' : 'text-indigo-600'}`}>Avg Participation</p>
              <p className={`text-xl font-bold ${isDark ? 'text-indigo-300' : 'text-indigo-700'}`}>
                {assessmentMetrics.overallParticipation !== null ? assessmentMetrics.overallParticipation.toFixed(0) : '—'}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );

  const NON_CORE_COURSES = new Set([
    'Introduction to NIAT',
    'NIAT Practice Page',
    'Logical Thinking',
    'Talent Development Program',
    'Yoga',
    'Human Values & Ethics',
    'Indian Constitution',
    'Environmental Science',
    'Language Elective',
    'Engineering Drawing',
    'Business English',
    'Node JS',
  ]);

  const getCourseRows = () => {
    return metrics.courses
      .map((course) => {
        const displayName = course;
        const cd = metrics.courseGroups[course] || [];

        const summarizeType = (sessionType) => {
          const rows = cd.filter((d) => d.session_type === sessionType);
          if (!rows.length) return null;
          const totalSessions = rows.reduce((sum, row) => sum + (row.sessions || 0), 0);
          const totalAvgTime = rows.reduce((sum, row) => sum + (row.avg_time || 0), 0);
          const totalP80Time = rows.reduce((sum, row) => sum + (row.p80_time || 0), 0);
          const avgCompletion = rows.reduce((sum, row) => sum + (row.completion || 0), 0) / rows.length;
          return {
            sessions: totalSessions,
            completion: avgCompletion,
            avg_time: totalAvgTime,
            p80_time: totalP80Time,
          };
        };

        const l = summarizeType('LECTURE');
        const p = summarizeType('PRACTICE');
        const e = summarizeType('EXAM');
        const lc = l?.sessions || 0;
        const pc = p?.sessions || 0;
        const ec = e?.sessions || 0;
        const total = lc + pc + ec;
        const avgT = cd.reduce((s, d) => s + (d.avg_time || 0), 0);
        const p80T = cd.reduce((s, d) => s + (d.p80_time || 0), 0);
        const ca = assessmentMetrics?.courses.find((c) => c.name === displayName);

        return {
          course,
          displayName,
          l,
          p,
          e,
          lc,
          pc,
          ec,
          total,
          avgT,
          p80T,
          ca,
        };
      })
      .filter((row) => {
        const hasDelivery = row.total > 0;
        const hasAssessment = Boolean(row.ca);
        const isSupportCourse = NON_CORE_COURSES.has(row.displayName);
        return (hasDelivery || hasAssessment) && !isSupportCourse;
      })
      .sort((a, b) => b.total - a.total);
  };

  const courseRows = getCourseRows();

  return (
    <AnimatedView>
      <div className={`min-h-screen ${pageBg} p-4 sm:p-5`}>
        {/* Top bar */}
        <div className="hero-panel max-w-7xl mx-auto mb-5 rounded-2xl p-5 sm:p-6">
          <button
            onClick={onBack}
            onMouseDown={addRipple}
            className={`ripple-btn touch-target flex items-center gap-2 mb-4 -ml-1 px-2 rounded-lg transition-colors ${backBtnCls}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Series
          </button>
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap min-w-0">
              <span className="w-3 h-3 rounded-full bg-blue-500 flex-shrink-0" />
              <span className={`text-base font-semibold truncate ${bodyText}`}>{selectedInstitute}</span>
              {sections.length > 0 && (
                <>
                  <span className={subColor}>—</span>
                  <select
                    value={activeSection}
                    onChange={(e) => setSelectedSection(e.target.value)}
                    className={`${isDark ? 'styled-select-dark' : 'styled-select'} text-base font-semibold border rounded-lg px-2 py-1 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-300 hover:border-blue-300 transition-colors min-h-[36px] ${
                      isDark
                        ? 'bg-slate-700 text-slate-100 border-slate-600'
                        : 'bg-transparent text-gray-800 border-gray-200'
                    }`}
                  >
                    <option value="">All Sections</option>
                    {sections.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </>
              )}
            </div>
            <button
              onClick={onReset}
              onMouseDown={addRipple}
              className={`ripple-btn touch-target text-sm flex items-center gap-1.5 font-medium px-2 py-1 rounded-lg transition-colors flex-shrink-0 ${
                isDark
                  ? 'text-blue-400 hover:text-blue-300 hover:bg-blue-900/30'
                  : 'text-blue-600 hover:text-blue-800 hover:bg-blue-50'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              New Upload
            </button>
          </div>
        </div>

        {/* Mobile collapsible sidebar */}
        <div className="max-w-7xl mx-auto lg:hidden mb-4">
          <button
            onClick={() => setSidebarExpanded(!sidebarExpanded)}
            className={`panel-surface w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium touch-target ${
              isDark ? 'text-slate-300' : 'text-gray-700'
            }`}
          >
            <span className="flex items-center gap-2">
              <svg className={`w-4 h-4 ${isDark ? 'text-slate-400' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Timeline &amp; Quick Stats
            </span>
            <svg
              className={`w-4 h-4 transition-transform duration-200 ${sidebarExpanded ? 'rotate-180' : ''} ${isDark ? 'text-slate-500' : 'text-gray-400'}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {sidebarExpanded && (
            <div className={`mt-2 rounded-xl p-5 animate-fade-slide-up ${cardBg}`}>
              <SidebarContent viewMode={viewMode} />
            </div>
          )}
        </div>

        <div className="max-w-7xl mx-auto flex gap-5">
          {/* Desktop sidebar */}
          <div className="hidden lg:block w-64 flex-shrink-0">
            <div className={`rounded-xl p-5 sticky top-5 ${cardBg}`}>
              <SidebarContent viewMode={viewMode} />
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="grid grid-cols-12 gap-5">
              {/* Sessions mix */}
              <div className="col-span-12 md:col-span-3 space-y-5">
                <div className={`rounded-xl p-5 ${cardBg}`}>
                  <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Sessions mix</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className={subColor}>Lecture</span>
                      <span className={`text-lg font-bold ${bodyText}`}>{r2(metrics.lectureCount)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className={subColor}>Practice</span>
                      <span className={`text-lg font-bold ${bodyText}`}>{r2(metrics.practiceCount)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className={subColor}>Exam</span>
                      <span className={`text-lg font-bold ${bodyText}`}>{r2(metrics.examCount)}</span>
                    </div>
                  </div>
                </div>
          <div className={`rounded-xl p-5 ${statAccentBg}`}>
            <p className={`text-xs uppercase font-medium mb-1 ${muted}`}>TOTAL SESSIONS</p>
            <p className={`text-4xl font-bold ${bodyText}`}>{r2(metrics.totalSessions)}</p>
          </div>
                <div className={`rounded-xl p-5 ${statGrayBg}`}>
                  <p className={`text-xs uppercase font-medium mb-1 ${muted}`}>CLASS SIZE</p>
                  <p className={`text-4xl font-bold ${bodyText}`}>{r2(metrics.classSize)}</p>
                </div>
              </div>

              {/* Completion */}
              <div className="col-span-12 md:col-span-5 space-y-5">
                <div className={`rounded-xl p-5 ${cardBg}`}>
                  <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Completion</h3>
                  <div className="grid grid-cols-3 gap-3">
                    <div className={`rounded-xl p-4 text-center ${completionBg}`}>
                      <p className={`text-xs mb-2 ${muted}`}>Overall</p>
                      <p className={`text-2xl font-bold ${bodyText}`}>{metrics.overallCompletion.toFixed(1)}%</p>
                    </div>
                    <div className={`rounded-xl p-4 text-center ${completionBg}`}>
                      <p className={`text-xs mb-2 ${muted}`}>Lecture</p>
                      <p className={`text-2xl font-bold ${bodyText}`}>{metrics.lectureCompletion.toFixed(1)}%</p>
                    </div>
                    <div className={`rounded-xl p-4 text-center ${completionBg}`}>
                      <p className={`text-xs mb-2 ${muted}`}>Practice</p>
                      <p className={`text-2xl font-bold ${bodyText}`}>{metrics.practiceCompletion.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
                <div className={`rounded-xl p-5 ${cardBg}`}>
                  <div className="flex items-center gap-5">
                    <div className="relative">
                      <DonutChart value={metrics.examCompletion} size={90} strokeWidth={10} color="#f59e0b" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-lg font-bold ${bodyText}`}>{metrics.examCompletion.toFixed(1)}%</span>
                      </div>
                    </div>
                    <div>
                      <h4 className={`text-lg font-semibold ${bodyText}`}>Exam Completion</h4>
                    </div>
                  </div>
                </div>
              </div>

              {/* Workload */}
              <div className="col-span-12 md:col-span-4">
                <div className={`rounded-xl p-5 h-full ${cardBg}`}>
                  <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Workload (per-student)</h3>
                  <WorkloadBar label="Avg" value={metrics.avgTime} maxValue={500} color="#ef4444" />
                  <WorkloadBar label="P80" value={metrics.p80Time} maxValue={500} color="#f97316" />
                  <WorkloadBar label="Practice" value={metrics.practiceAvgTime} maxValue={200} color="#fbbf24" />
                  <WorkloadBar label="Practice (P80)" value={metrics.practiceP80Time} maxValue={200} color="#fcd34d" />
                </div>
              </div>
            </div>

            {/* Course-wise / Subject-wise Breakdown */}
            <div
              className={`mt-5 rounded-xl overflow-hidden animate-fade-slide-up ${cardBg}`}
              style={{ animationDelay: '0.12s' }}
            >
              <div className={`px-5 py-4 border-b flex items-center justify-between ${isDark ? 'border-slate-700 bg-slate-900/40' : 'border-slate-200 bg-white/70'}`}>
                <div className="flex items-center gap-4">
                  <div>
                    <h3 className={`text-sm font-semibold ${headingColor}`}>
                      {viewMode === 'subject' ? 'Subject-wise Breakdown' : 'Course-wise Breakdown'}
                    </h3>
                    <p className={`mt-0.5 text-xs ${muted}`}>
                      {viewMode === 'subject'
                        ? 'Aggregated data by subject across all courses. Practice% and Exam% are completion rates. Skill Pass% and Graded Pass% are assessment pass rates.'
                        : 'Practice% and Exam% are completion rates. Skill Pass% and Graded Pass% are assessment pass rates. Participation# is average learner count.'}
                    </p>
                  </div>
                  {/* View Mode Toggle - only show for Semester 2 */}
                  {semester === 'Semester 2' && (
                    <div className={`flex items-center gap-1 rounded-lg p-1 ${isDark ? 'bg-slate-700' : 'bg-gray-100'}`}>
                      <button
                        onClick={() => setViewMode('course')}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                          viewMode === 'course'
                            ? isDark
                              ? 'bg-slate-600 text-white'
                              : 'bg-white text-gray-800 shadow-sm'
                            : isDark
                              ? 'text-slate-400 hover:text-slate-200'
                              : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        Course
                      </button>
                      <button
                        onClick={() => setViewMode('subject')}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                          viewMode === 'subject'
                            ? isDark
                              ? 'bg-slate-600 text-white'
                              : 'bg-white text-gray-800 shadow-sm'
                            : isDark
                              ? 'text-slate-400 hover:text-slate-200'
                              : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        Subject
                      </button>
                    </div>
                  )}
                </div>
                <span className={`text-xs sm:hidden ${muted}`}>← scroll →</span>
              </div>
              <div className="table-scroll-container overflow-x-auto">
                <table className={`w-full min-w-[780px] ${tableBg}`}>
                  <thead className={tableHeaderBg}>
                    <tr className={`text-xs uppercase tracking-wider ${tableHeaderText}`}>
                      <th className={`text-left px-4 py-3 font-medium sticky left-0 z-10 ${tableStickyHeader}`}>
                        {viewMode === 'subject' ? 'Subject' : 'Course'}
                      </th>
                      <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-50 text-blue-600'}`}>Lect Sess</th>
                      <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-emerald-900/30 text-emerald-400' : 'bg-emerald-50 text-emerald-600'}`}>Prac Sess</th>
                      <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-amber-900/30 text-amber-400' : 'bg-amber-50 text-amber-600'}`}>Exam Sess</th>
                      <th className="text-center px-2 py-3 font-medium">Total Sess</th>
                      <th className="text-center px-2 py-3 font-medium">Lecture %</th>
                      <th className="text-center px-2 py-3 font-medium">Practice %</th>
                      <th className="text-center px-2 py-3 font-medium">Exam %</th>
                      <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-purple-900/30 text-purple-400' : 'bg-purple-50 text-purple-600'}`}>Skill Pass %</th>
                      <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-fuchsia-900/30 text-fuchsia-400' : 'bg-fuchsia-50 text-fuchsia-600'}`}>Graded Pass %</th>
                      <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-indigo-900/30 text-indigo-400' : 'bg-indigo-50 text-indigo-600'}`}>Participation #</th>
                      <th className="text-center px-2 py-3 font-medium">Avg Time</th>
                      <th className="text-center px-2 py-3 font-medium">P80 Time</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${tableRowDivide}`}>
                    {courseRows.map((row) => {
                      return (
                        <tr key={row.course} className={`transition-colors ${tableRowHover}`}>
                          <td className={`px-4 py-3 text-sm font-medium sticky left-0 z-10 whitespace-nowrap max-w-[180px] truncate ${tableCellSticky} ${isDark ? 'text-slate-200' : 'text-gray-800'}`} title={row.displayName}>
                            {row.displayName}
                          </td>
                          <td className="px-2 py-3 text-center">
                            <span className="panel-muted inline-flex items-center justify-center w-10 h-7 text-xs font-bold rounded">{r2(row.lc)}</span>
                          </td>
                          <td className="px-2 py-3 text-center">
                            <span className="panel-muted inline-flex items-center justify-center w-10 h-7 text-xs font-bold rounded">{r2(row.pc)}</span>
                          </td>
                          <td className="px-2 py-3 text-center">
                            <span className="panel-muted inline-flex items-center justify-center w-10 h-7 text-xs font-bold rounded">{r2(row.ec)}</span>
                          </td>
                          <td className={`px-2 py-3 text-sm text-center font-semibold ${isDark ? 'text-slate-300' : 'text-gray-700'}`}>{r2(row.total)}</td>
                          <td className={`px-2 py-3 text-center text-sm ${isDark ? 'text-slate-300' : ''}`}>{row.l ? `${row.l.completion.toFixed(1)}%` : '—'}</td>
                          <td className={`px-2 py-3 text-center text-sm ${isDark ? 'text-slate-300' : ''}`}>{row.p ? `${row.p.completion.toFixed(1)}%` : '—'}</td>
                          <td className={`px-2 py-3 text-center text-sm ${isDark ? 'text-slate-300' : ''}`}>{row.e ? `${row.e.completion.toFixed(1)}%` : '—'}</td>
                          <td className={`px-2 py-3 text-center text-sm font-semibold ${bodyText}`}>
                            {row.ca?.skillPassRate !== null && row.ca?.skillPassRate !== undefined ? `${(row.ca.skillPassRate * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className={`px-2 py-3 text-center text-sm font-semibold ${bodyText}`}>
                            {row.ca?.gradedPassRate !== null && row.ca?.gradedPassRate !== undefined ? `${(row.ca.gradedPassRate * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className={`px-2 py-3 text-center text-sm font-semibold ${bodyText}`}>
                            {row.ca?.avgParticipation !== null && row.ca?.avgParticipation !== undefined ? `${row.ca.avgParticipation.toFixed(0)}` : '—'}
                          </td>
                          <td className={`px-2 py-3 text-sm text-center ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>{row.avgT.toFixed(1)}h</td>
                          <td className={`px-2 py-3 text-sm text-center ${isDark ? 'text-slate-400' : 'text-gray-600'}`}>{row.p80T.toFixed(1)}h</td>
                        </tr>
                      );
                    })}
                    {courseRows.length === 0 && (
                      <tr>
                        <td colSpan={13} className={`px-4 py-5 text-center text-sm ${muted}`}>
                          No core courses found for this university and section.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
      <ScrollToTop />
    </AnimatedView>
  );
}
