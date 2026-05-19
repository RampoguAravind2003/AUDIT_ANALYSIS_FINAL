import {
  COURSE_MAPPING_BY_SEMESTER,
  ALLOTTED_HOURS_BY_SEMESTER,
  SEMESTER_DATES_BY_SEMESTER,
  SERIES_RANGES,
  COURSE_TO_SUBJECT_MAPPING_SEM2,
  SUBJECT_DISPLAY_ORDER_SEM2,
  isAllowedSubject,
} from '../constants';

export const getCourseMapping = (semester) =>
  COURSE_MAPPING_BY_SEMESTER[semester] || COURSE_MAPPING_BY_SEMESTER['Semester 1'];

export const getAllottedHours = (name, semester) => {
  const semHours = ALLOTTED_HOURS_BY_SEMESTER[semester] || ALLOTTED_HOURS_BY_SEMESTER['Semester 1'];
  if (semHours[name]) return semHours[name];
  for (const k of Object.keys(semHours)) {
    if (name.toLowerCase().includes(k.toLowerCase().split(' ')[0])) return semHours[k];
  }
  return null;
};

export const getSemesterDatesForInstitute = (name, sem) => {
  const semDates = SEMESTER_DATES_BY_SEMESTER[sem] || SEMESTER_DATES_BY_SEMESTER['Semester 1'];
  if (semDates[name]) return semDates[name];
  for (const k of Object.keys(semDates)) {
    if (name.toLowerCase().includes(k.toLowerCase().split(' ')[0])) return semDates[k];
  }
  return null;
};

export const getSeriesForValue = (v) =>
  SERIES_RANGES.find(s => v >= s.min && v < s.max) || SERIES_RANGES[5];

export const getSeriesForAllottedHours = (name, semester) => {
  const hours = getAllottedHours(name, semester);
  if (!hours) return null;
  return SERIES_RANGES.find(s => hours >= s.min && hours < s.max) || SERIES_RANGES[5];
};

export const r2 = (v) => Math.round(v * 100) / 100;

const COURSE_ALIAS_GROUPS_BY_SEMESTER = {
  'Semester 1': {
    'Introduction to Generative AI': ['generative ai', 'introduction to generative ai'],
    'Mathematics for Computer Science': ['mathematics', 'mathematics for computer science'],
    'Web Application Development I': [
      'build your own static website',
      'build your own responsive website',
      'modern responsive web design',
      'responsive web design using flexbox',
      'html & css',
      'web application development i',
    ],
    'Communication English Foundation': [
      'communicative english foundation',
      'communication english foundation',
      'english foundation',
    ],
    'Computer Programming': [
      'programming foundations',
      'programing foundation',
      'python programming',
      'problem solving with python programming',
      'computer programming',
      'introduction to niat',
      'niat practice page',
      'logical thinking',
      'oops',
      'more python problem solving',
    ],
    'Quantitative Aptitude': ['quantitative aptitude', 'numerical aptitude'],
  },
  'Semester 2': {
    'Web Application Development 2': [
      'web application development 2',
      'build your own dynamic web application',
      'js essentials',
      'javascript essentials',
      'js programming',
      'introduction to react js',
      'react js',
      'node js',
    ],
    'Database Management Systems': [
      'database management systems',
      'introduction to database',
      'introduction to databases',
    ],
    'Data Structures': [
      'data structures',
      'data structures and algorithm',
      'dsa',
      'dsa foundation',
      'dsa level 1',
      'dsa extra coding questions',
      'dsa - beginner',
      'niat - dsa',
      'academy - dsa',
      'phase 1 : data structures and algorithms',
      'foundations of data structures and algorithms',
    ],
    'Numerical Aptitude': ['numerical aptitude', 'quantitative aptitude', 'logical thinking'],
    'English Advanced': ['english advanced', 'communicative english foundation', 'business english'],
    'Large Language Models': ['large language models', 'llm', 'generative ai'],
    'Physics': ['physics'],
    'Chemistry': ['chemistry'],
    'Yoga': ['yoga'],
    'Talent Development Program': ['talent development program', 'tdp'],
    'Human Values & Ethics': ['human values', 'human values & ethics', 'hvs'],
    'Assessment': ['assessment'],
    'Business English': ['business english'],
    'Indian Knowledge System': ['indian knowledge system', 'iks'],
    'Linear Algebra and Calculus': [
      'linear algebra',
      'linear algebra & calculus',
      'linear algebra and calculus',
      'calculus',
      'calculus & differential equations',
      'calculus and differential equations',
      'mathematics',
      'maths',
      'math',
    ],
    'Environmental Science': ['environmental science'],
    'Indian Constitution': ['indian constitution'],
    'Language Elective': ['language elective'],
    'Engineering Drawing': ['engineering drawing'],
    'Cloud Computing': ['cloud computing'],
  },
};

const normalizeText = (value) =>
  String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

export const normalizeCourseName = (courseName, semester) => {
  const raw = String(courseName || '').trim();
  if (!raw) return raw;

  const courseMap = getCourseMapping(semester);
  if (courseMap[raw]) return courseMap[raw];

  const normalizedRaw = normalizeText(raw);
  const aliasGroups = COURSE_ALIAS_GROUPS_BY_SEMESTER[semester] || {};

  for (const [canonicalName, aliases] of Object.entries(aliasGroups)) {
    if (aliases.some((alias) => normalizedRaw === normalizeText(alias) || normalizedRaw.includes(normalizeText(alias)))) {
      return canonicalName;
    }
  }

  return raw;
};

// Subject mapping helpers for Semester 2
export function getSubjectFromCourse(courseName, semester = 'Semester 2') {
  if (semester !== 'Semester 2') return courseName;

  const normalized = String(courseName || '').trim();
  if (!normalized) return normalized;

  // Direct lookup
  if (COURSE_TO_SUBJECT_MAPPING_SEM2[normalized]) {
    return COURSE_TO_SUBJECT_MAPPING_SEM2[normalized];
  }

  // Case-insensitive lookup
  const lowerNormalized = normalized.toLowerCase();
  for (const [course, subject] of Object.entries(COURSE_TO_SUBJECT_MAPPING_SEM2)) {
    if (course.toLowerCase() === lowerNormalized) {
      return subject;
    }
  }

  // Partial match
  for (const [course, subject] of Object.entries(COURSE_TO_SUBJECT_MAPPING_SEM2)) {
    if (lowerNormalized.includes(course.toLowerCase()) ||
        course.toLowerCase().includes(lowerNormalized)) {
      return subject;
    }
  }

  // Return original if no mapping found
  return normalized;
}

// Group course data by subject
export function groupCoursesBySubject(courseGroups, semester = 'Semester 2') {
  if (semester !== 'Semester 2') return courseGroups;

  const subjectGroups = {};

  for (const [courseName, rows] of Object.entries(courseGroups)) {
    const subjectName = getSubjectFromCourse(courseName, semester);

    // Skip if no subject mapping found or subject not in allowed list
    if (!subjectName || !isAllowedSubject(subjectName)) {
      continue;
    }

    if (!subjectGroups[subjectName]) {
      subjectGroups[subjectName] = [];
    }

    subjectGroups[subjectName].push(...rows);
  }

  return subjectGroups;
}

// Sort subjects by predefined order
export function sortSubjectsByOrder(subjects) {
  return subjects.sort((a, b) => {
    const indexA = SUBJECT_DISPLAY_ORDER_SEM2.indexOf(a);
    const indexB = SUBJECT_DISPLAY_ORDER_SEM2.indexOf(b);

    // If both are in the order list, sort by index
    if (indexA !== -1 && indexB !== -1) {
      return indexA - indexB;
    }

    // If only one is in the list, prioritize it
    if (indexA !== -1) return -1;
    if (indexB !== -1) return 1;

    // Otherwise alphabetical
    return a.localeCompare(b);
  });
}

// Aggregate assessment data by subject
export function groupAssessmentBySubject(courseScores, semester = 'Semester 2') {
  if (semester !== 'Semester 2') return courseScores;

  const subjectScores = {};

  for (const [courseName, data] of Object.entries(courseScores)) {
    const subjectName = getSubjectFromCourse(courseName, semester);

    // Skip if no subject mapping found or subject not in allowed list
    if (!subjectName || !isAllowedSubject(subjectName)) {
      continue;
    }

    if (!subjectScores[subjectName]) {
      subjectScores[subjectName] = { scores: [], parts: [], skillPass: [], gradedPass: [] };
    }

    subjectScores[subjectName].scores.push(...(data.scores || []));
    subjectScores[subjectName].parts.push(...(data.parts || []));
    subjectScores[subjectName].skillPass.push(...(data.skillPass || []));
    subjectScores[subjectName].gradedPass.push(...(data.gradedPass || []));
  }

  return subjectScores;
}
