import { useTheme } from '../context/ThemeContext';
import AnimatedView from './ui/AnimatedView';
import ScrollToTop from './ui/ScrollToTop';
import WorkloadBar from './ui/WorkloadBar';
import { SERIES_RANGES } from '../constants';
import { getAllottedHours } from '../utils/semesterHelpers';
import { addRipple } from '../utils/ripple';

export default function SeriesDetail({ seriesName, seriesData, onBack, onSelectUniversity, analysisType, semester }) {
  const { isDark } = useTheme();
  const series = SERIES_RANGES.find(s => s.name === seriesName);
  const data = seriesData[seriesName];
  if (!data) return null;

  const pageBg = 'ui-shell';
  const cardBg = 'panel-surface';
  const headingColor = isDark ? 'text-slate-100' : 'text-slate-900';
  const subColor = isDark ? 'text-slate-300' : 'text-slate-600';
  const tableBg = isDark ? 'bg-slate-900/85' : 'bg-white';
  const tableHeaderBg = isDark ? 'bg-slate-800' : 'bg-gray-50';
  const tableHeaderText = isDark ? 'text-slate-400' : 'text-gray-500';
  const tableRowHover = isDark ? 'hover:bg-slate-800/60' : 'hover:bg-slate-50';
  const tableRowDivide = isDark ? 'divide-slate-700' : 'divide-gray-50';
  const tableCellSticky = isDark ? 'bg-slate-900/95 hover:bg-slate-800/90 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.3)]' : 'bg-white hover:bg-slate-50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.06)]';
  const tableStickyHeader = isDark ? 'bg-slate-800 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.3)]' : 'bg-gray-50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.08)]';
  const backBtnCls = isDark
    ? 'text-slate-400 hover:text-slate-100 hover:bg-slate-700'
    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100';

  return (
    <AnimatedView>
      <div className={`min-h-screen ${pageBg} p-4 sm:p-5`}>
        <div className="max-w-6xl mx-auto">
          <button
            onClick={onBack}
            onMouseDown={addRipple}
            className={`ripple-btn touch-target flex items-center gap-2 mb-4 -ml-1 px-2 rounded-lg transition-colors ${backBtnCls}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Overview
          </button>

          {/* Series Header */}
          <div className="hero-panel rounded-2xl p-6 sm:p-7 text-white mb-6 animate-fade-slide-up">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/75 text-xs font-semibold uppercase tracking-[0.18em]">Series</p>
                <h1 className="text-3xl sm:text-4xl font-bold">{seriesName}</h1>
                <p className="text-white/75 mt-2 text-sm">
                  {series.min}–{series.max === Infinity ? '∞' : series.max}{' '}
                  {analysisType === 'design' ? 'allotted hours' : 'delivered sessions'}
                </p>
              </div>
              <div className="text-right">
                <p className="text-4xl sm:text-5xl font-bold">{data.universities.length}</p>
                <p className="text-white/80">universities</p>
              </div>
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-12 gap-4 sm:gap-5 mb-6">
            {/* Series Averages */}
            <div className={`col-span-12 md:col-span-3 rounded-xl p-5 ${cardBg}`}>
              <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Series Averages</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className={subColor}>Average University Delivery (sessions)</span>
                  <span className={`text-2xl font-bold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>{data.avgSessions.toFixed(0)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className={subColor}>Avg Class Size</span>
                  <span className={`text-2xl font-bold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>{data.avgClassSize.toFixed(0)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className={subColor}>Total Students</span>
                  <span className={`text-2xl font-bold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>{data.totalStudents}</span>
                </div>
              </div>
            </div>

            {/* Avg Completion */}
            <div className={`col-span-12 md:col-span-3 rounded-xl p-5 ${cardBg}`}>
              <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Avg Completion</h3>
              <div className="grid grid-cols-2 gap-3">
                <div className="panel-muted rounded-lg p-3 text-center">
                  <p className={`text-xs ${subColor}`}>Lecture</p>
                  <p className={`text-xl font-bold ${headingColor}`}>{data.avgLectureCompletion.toFixed(1)}%</p>
                </div>
                <div className="panel-muted rounded-lg p-3 text-center">
                  <p className={`text-xs ${subColor}`}>Practice</p>
                  <p className={`text-xl font-bold ${headingColor}`}>{data.avgPracticeCompletion.toFixed(1)}%</p>
                </div>
                <div className="panel-muted rounded-lg p-3 text-center">
                  <p className={`text-xs ${subColor}`}>Exam</p>
                  <p className={`text-xl font-bold ${headingColor}`}>{data.avgExamCompletion.toFixed(1)}%</p>
                </div>
                <div className="panel-muted rounded-lg p-3 text-center">
                  <p className={`text-xs ${subColor}`}>Overall</p>
                  <p className={`text-xl font-bold ${headingColor}`}>{data.avgOverallCompletion.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            {/* Assessment */}
            <div className={`col-span-12 md:col-span-3 rounded-xl p-5 ${cardBg}`}>
              <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Assessment Metrics</h3>
              {data.avgSkillPassRate != null || data.avgGradedPassRate != null ? (
                <div className="space-y-3">
                  <div className="panel-muted rounded-lg p-4 text-center">
                    <p className={`text-xs font-medium mb-1 ${subColor}`}>Skill Pass</p>
                    <p className={`text-3xl font-bold ${headingColor}`}>
                      {data.avgSkillPassRate != null ? `${(data.avgSkillPassRate * 100).toFixed(1)}%` : '—'}
                    </p>
                  </div>
                  <div className="panel-muted rounded-lg p-4 text-center">
                    <p className={`text-xs font-medium mb-1 ${subColor}`}>Graded Pass</p>
                    <p className={`text-3xl font-bold ${headingColor}`}>
                      {data.avgGradedPassRate != null ? `${(data.avgGradedPassRate * 100).toFixed(1)}%` : '—'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className={`h-full flex items-center justify-center text-sm ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>
                  No assessment data
                </div>
              )}
            </div>

            {/* Workload */}
            <div className={`col-span-12 md:col-span-3 rounded-xl p-5 ${cardBg}`}>
              <h3 className={`text-sm font-semibold mb-4 ${headingColor}`}>Avg Engagement per Student</h3>
              <WorkloadBar label="Avg" value={data.avgWorkload} maxValue={500} color="#ef4444" />
              <WorkloadBar label="P80" value={data.avgP80Workload} maxValue={500} color="#f97316" />
              <WorkloadBar label="Practice" value={data.avgPracticeWorkload} maxValue={200} color="#fbbf24" />
              <WorkloadBar label="Practice (P80)" value={data.avgPracticeP80Workload} maxValue={200} color="#fcd34d" />
            </div>
          </div>

          {/* Universities Table */}
          <div
            className={`rounded-xl overflow-hidden animate-fade-slide-up ${cardBg}`}
            style={{ animationDelay: '0.1s' }}
          >
            <div className={`px-5 py-4 border-b flex items-center justify-between ${isDark ? 'border-slate-700 bg-slate-900/40' : 'border-slate-200 bg-white/70'}`}>
              <h3 className={`text-sm font-semibold ${headingColor}`}>Universities in this Series</h3>
              <span className={`text-xs sm:hidden ${isDark ? 'text-slate-500' : 'text-gray-400'}`}>← scroll →</span>
            </div>
            <div className="table-scroll-container overflow-x-auto">
              <table className={`w-full min-w-[700px] ${tableBg}`}>
                <thead className={tableHeaderBg}>
                  <tr className={`text-xs uppercase tracking-wider ${tableHeaderText}`}>
                    <th className={`text-left px-4 py-3 font-medium sticky left-0 z-10 ${tableStickyHeader}`}>University</th>
                    <th className="text-center px-2 py-3 font-medium">Sections</th>
                    <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-amber-900/30 text-amber-400' : 'bg-amber-50 text-amber-700'}`}>Allotted Hrs</th>
                    <th className="text-center px-2 py-3 font-medium">Avg Delivery</th>
                    <th className="text-center px-2 py-3 font-medium">Lecture %</th>
                    <th className="text-center px-2 py-3 font-medium">Practice %</th>
                    <th className="text-center px-2 py-3 font-medium">Exam %</th>
                    <th className="text-center px-2 py-3 font-medium">Overall %</th>
                    <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-purple-900/30 text-purple-400' : 'bg-purple-50 text-purple-600'}`}>Skill Pass %</th>
                    <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-fuchsia-900/30 text-fuchsia-400' : 'bg-fuchsia-50 text-fuchsia-600'}`}>Graded Pass %</th>
                    <th className={`text-center px-2 py-3 font-medium ${isDark ? 'bg-indigo-900/30 text-indigo-400' : 'bg-indigo-50 text-indigo-600'}`}>Participation #</th>
                    <th className="text-center px-2 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${tableRowDivide}`}>
                  {data.universities.map((u, i) => {
                    const allottedHrs = getAllottedHours(u.name, semester);
                    return (
                      <tr key={i} className={`transition-colors ${tableRowHover}`}>
                        <td className={`px-4 py-3 text-sm font-medium whitespace-nowrap sticky left-0 z-10 ${tableCellSticky} ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                          {u.name}
                        </td>
                        <td className={`px-2 py-3 text-center text-sm ${subColor}`}>{u.sectionCount}</td>
                        <td className={`px-2 py-3 text-center text-sm font-semibold ${isDark ? 'text-amber-400 bg-amber-900/20' : 'text-amber-700 bg-amber-50/50'}`}>
                          {allottedHrs || '—'}
                        </td>
                        <td className={`px-2 py-3 text-center text-sm font-semibold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>{u.avgSessions.toFixed(0)}</td>
                        <td className="px-2 py-3 text-center text-sm text-blue-500">{u.avgLectureCompletion.toFixed(1)}%</td>
                        <td className="px-2 py-3 text-center text-sm text-emerald-500">{u.avgPracticeCompletion.toFixed(1)}%</td>
                        <td className="px-2 py-3 text-center text-sm text-amber-500">{u.avgExamCompletion.toFixed(1)}%</td>
                        <td className={`px-2 py-3 text-center text-sm font-semibold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>{u.avgOverallCompletion.toFixed(1)}%</td>
                        <td className={`px-2 py-3 text-center text-sm font-semibold ${isDark ? 'text-purple-300 bg-purple-900/20' : 'text-purple-700 bg-purple-50/50'}`}>
                          {u.avgSkillPassRate != null ? `${(u.avgSkillPassRate * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className={`px-2 py-3 text-center text-sm font-semibold ${isDark ? 'text-fuchsia-300 bg-fuchsia-900/20' : 'text-fuchsia-700 bg-fuchsia-50/50'}`}>
                          {u.avgGradedPassRate != null ? `${(u.avgGradedPassRate * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className={`px-2 py-3 text-center text-sm font-semibold ${isDark ? 'text-indigo-300 bg-indigo-900/20' : 'text-indigo-700 bg-indigo-50/50'}`}>
                          {u.avgParticipation !== null ? `${u.avgParticipation.toFixed(0)}` : '—'}
                        </td>
                        <td className="px-2 py-3 text-center">
                          <button
                            onClick={() => onSelectUniversity(u.name)}
                            onMouseDown={addRipple}
                            className="ripple-btn dashboard-button-secondary touch-target px-3 py-1.5 rounded text-xs font-medium transition-colors"
                          >
                            Details →
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <ScrollToTop />
    </AnimatedView>
  );
}
