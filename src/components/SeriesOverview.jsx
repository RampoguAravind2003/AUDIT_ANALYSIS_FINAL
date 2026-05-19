import { useTheme } from '../context/ThemeContext';
import AnimatedView from './ui/AnimatedView';
import ScrollToTop from './ui/ScrollToTop';
import { SERIES_RANGES } from '../constants';
import { addRipple } from '../utils/ripple';

export default function SeriesOverview({ seriesData, onSelectSeries, analysisType, semester, batch, filters }) {
  const { isDark } = useTheme();

  const pageBg = 'ui-shell';
  const headingColor = isDark ? 'text-slate-100' : 'text-gray-900';
  const subColor = isDark ? 'text-slate-300' : 'text-slate-600';
  const muted = isDark ? 'text-slate-400' : 'text-slate-500';
  const infoBg = isDark
    ? 'panel-surface text-slate-200'
    : 'panel-surface text-slate-700';
  const infoHeading = isDark ? 'text-slate-100' : 'text-slate-900';
  const infoText = isDark ? 'text-slate-300' : 'text-slate-600';
  const infoIconBg = isDark ? 'bg-slate-800' : 'bg-slate-100';
  const infoIconColor = isDark ? 'text-slate-200' : 'text-slate-700';

  return (
    <AnimatedView>
      <div className={`min-h-screen ${pageBg} p-4 sm:p-6`}>
        <div className="max-w-6xl mx-auto">
          <div className="hero-panel mb-6 rounded-3xl p-6 sm:mb-8 sm:p-8 animate-fade-slide-up">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-blue-100/80">Overview</p>
            <h1 className={`text-2xl sm:text-3xl font-bold mb-2 ${isDark ? 'text-white' : headingColor}`}>University Series Overview</h1>
            <div className="flex flex-wrap gap-2 justify-center mt-4">
              <span className="dashboard-chip border-white/16 bg-white/10 text-white">{semester}</span>
              <span className="dashboard-chip border-white/16 bg-white/10 text-white">{batch}</span>
              {filters?.startDate && filters?.endDate && (
                <span className="dashboard-chip border-white/16 bg-white/10 text-white">{filters.startDate} to {filters.endDate}</span>
              )}
              <span className="dashboard-chip border-white/16 bg-white/10 text-white">
                {analysisType === 'design' ? 'Design perspective' : 'Delivery perspective'}
              </span>
            </div>
          </div>

          <div
            className={`max-w-4xl mx-auto mb-6 sm:mb-8 rounded-2xl p-5 animate-fade-slide-up ${infoBg}`}
            style={{ animationDelay: '0.05s' }}
          >
            <div className="flex items-start gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${infoIconBg}`}>
                <svg className={`w-4 h-4 ${infoIconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className={`text-sm font-semibold mb-1 ${infoHeading}`}>
                  {analysisType === 'design' ? 'Design Perspective' : 'Delivery Perspective'}
                </h4>
                <p className={`text-sm ${infoText}`}>
                  {analysisType === 'design' ? (
                    <>Universities categorized by <span className="font-semibold">Initial Allotted Hours</span> from Academic Calendar.</>
                  ) : (
                    <>Universities categorized by <span className="font-semibold">Average Sessions Delivered</span> (actual engagement).</>
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
            {SERIES_RANGES.map((series) => {
              const data = seriesData[series.name];
              if (!data || data.universities.length === 0) return null;
              return (
                <div
                  key={series.name}
                  onClick={() => onSelectSeries(series.name)}
                  onMouseDown={addRipple}
                  className={`card-enter ripple-btn rounded-2xl overflow-hidden cursor-pointer transform transition-all duration-200 hover:-translate-y-1 hover:shadow-lg active:scale-[0.99] focus-visible:ring-2 focus-visible:ring-blue-500 ${
                    isDark ? 'panel-surface' : 'panel-surface'
                  }`}
                  tabIndex={0}
                  role="button"
                  aria-label={`View Series ${series.name}`}
                  onKeyDown={(e) => e.key === 'Enter' && onSelectSeries(series.name)}
                >
                  <div className={`bg-gradient-to-r ${series.bg} p-5 text-white`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white/80 text-sm font-medium">Series</p>
                        <h2 className="text-3xl font-bold">{series.name}</h2>
                        <p className="text-white/80 text-xs mt-1">
                          {series.min}–{series.max === Infinity ? '∞' : series.max} allotted hrs
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-4xl font-bold">{data.universities.length}</p>
                        <p className="text-white/80 text-sm">universities</p>
                      </div>
                    </div>
                  </div>

                  <div className="p-5">
                    <div className="grid grid-cols-3 gap-2 sm:gap-3 mb-4">
                      <div className={`panel-muted rounded-lg p-2 sm:p-3 text-center`}>
                        <p className={`text-[10px] sm:text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Avg Allotted</p>
                        <p className="text-lg sm:text-xl font-bold text-amber-600">
                          {data.avgAllottedHours ? data.avgAllottedHours.toFixed(0) : '—'}
                        </p>
                      </div>
                      <div className={`panel-muted rounded-lg p-2 sm:p-3 text-center`}>
                        <p className={`text-[10px] sm:text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Avg University Delivery</p>
                        <p className={`text-lg sm:text-xl font-bold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>
                          {data.avgSessions.toFixed(0)}
                        </p>
                      </div>
                      <div className={`panel-muted rounded-lg p-2 sm:p-3 text-center`}>
                        <p className={`text-[10px] sm:text-xs ${isDark ? 'text-slate-400' : 'text-gray-500'}`}>Total Students</p>
                        <p className={`text-lg sm:text-xl font-bold ${isDark ? 'text-slate-100' : 'text-gray-800'}`}>
                          {data.totalStudents}
                        </p>
                      </div>
                    </div>

                    {(data.avgSkillPassRate != null || data.avgGradedPassRate != null) && (
                      <div className={`panel-muted rounded-lg p-3 mb-4`}>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className={`text-xs font-medium ${muted}`}>Skill Pass</p>
                            <p className={`text-2xl font-bold ${headingColor}`}>
                              {data.avgSkillPassRate != null ? `${(data.avgSkillPassRate * 100).toFixed(1)}%` : '—'}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className={`text-xs font-medium ${muted}`}>Graded Pass</p>
                            <p className={`text-2xl font-bold ${headingColor}`}>
                              {data.avgGradedPassRate != null ? `${(data.avgGradedPassRate * 100).toFixed(1)}%` : '—'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className={isDark ? 'text-slate-400' : 'text-gray-600'}>Overall Completion</span>
                        <span className={`font-semibold ${isDark ? 'text-slate-200' : 'text-gray-800'}`}>
                          {data.avgOverallCompletion.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <div className={`border-t pt-4 ${isDark ? 'border-slate-700' : 'border-gray-100'}`}>
                      <p className={`text-xs mb-2 ${isDark ? 'text-slate-500' : 'text-gray-500'}`}>Universities:</p>
                      <div className="flex flex-wrap gap-1">
                        {data.universities.slice(0, 4).map((u, i) => (
                          <span
                            key={i}
                            className={`px-2 py-0.5 text-xs rounded-full truncate max-w-[140px] ${
                              isDark ? 'bg-slate-700 text-slate-300' : 'bg-gray-100 text-gray-600'
                            }`}
                            title={u.name}
                          >
                            {u.name}
                          </span>
                        ))}
                        {data.universities.length > 4 && (
                          <span className={`px-2 py-0.5 text-xs rounded-full ${isDark ? 'bg-slate-600 text-slate-400' : 'bg-gray-200 text-gray-600'}`}>
                            +{data.universities.length - 4}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="px-5 pb-4">
                    <button className="dashboard-button-secondary w-full py-2 rounded-lg text-sm font-medium transition-colors touch-target">
                      View Details →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <ScrollToTop />
      </div>
    </AnimatedView>
  );
}
