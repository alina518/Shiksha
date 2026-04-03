-- =============================================================
-- NGO EDUCATION IMPACT PIPELINE — CLEAN FINAL VERSION
-- Run this file from scratch against a fresh MySQL instance.
-- Order: source DB → source data → mart DB → dims → facts → summaries
-- =============================================================

-- ─────────────────────────────────────────────────────────────
-- 0.  FRESH START  (drop & recreate both databases)
-- ─────────────────────────────────────────────────────────────
DROP DATABASE IF EXISTS ngo_source;
DROP DATABASE IF EXISTS ngo_mart;

-- ─────────────────────────────────────────────────────────────
-- 1.  SOURCE DATABASE
-- ─────────────────────────────────────────────────────────────
CREATE DATABASE ngo_source CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ngo_source;

CREATE TABLE schools_raw (
    school_id   INT PRIMARY KEY,
    school_name VARCHAR(100),
    state       VARCHAR(50),
    district    VARCHAR(50),
    urban_rural VARCHAR(10)
);

CREATE TABLE programs_raw (
    program_id   INT PRIMARY KEY,
    program_name VARCHAR(100),
    program_type VARCHAR(50)
);

CREATE TABLE students_raw (
    student_id   INT PRIMARY KEY,
    student_name VARCHAR(100),
    gender       VARCHAR(10),
    grade        INT,
    school_id    INT,
    FOREIGN KEY (school_id) REFERENCES schools_raw(school_id)
);

CREATE TABLE instructors_raw (
    instructor_id   INT PRIMARY KEY,
    instructor_name VARCHAR(100)
);

CREATE TABLE activities_raw (
    activity_id   INT PRIMARY KEY,
    activity_name VARCHAR(100)
);

CREATE TABLE attendance_raw (
    attendance_id     INT PRIMARY KEY AUTO_INCREMENT,
    student_id        INT,
    program_id        INT,
    date              DATE,
    attendance_status VARCHAR(10),
    FOREIGN KEY (student_id) REFERENCES students_raw(student_id),
    FOREIGN KEY (program_id) REFERENCES programs_raw(program_id)
);

CREATE TABLE assessment_raw (
    assessment_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id    INT,
    program_id    INT,
    date          DATE,
    test_type     VARCHAR(20),
    score         INT,
    max_score     INT,
    FOREIGN KEY (student_id) REFERENCES students_raw(student_id),
    FOREIGN KEY (program_id) REFERENCES programs_raw(program_id)
);

CREATE TABLE sessions_raw (
    session_id    INT PRIMARY KEY AUTO_INCREMENT,
    school_id     INT,
    program_id    INT,
    instructor_id INT,
    activity_id   INT,
    date          DATE,
    FOREIGN KEY (school_id)     REFERENCES schools_raw(school_id),
    FOREIGN KEY (program_id)    REFERENCES programs_raw(program_id),
    FOREIGN KEY (instructor_id) REFERENCES instructors_raw(instructor_id),
    FOREIGN KEY (activity_id)   REFERENCES activities_raw(activity_id)
);

CREATE TABLE exposure_raw (
    exposure_id       INT PRIMARY KEY AUTO_INCREMENT,
    session_id        INT,
    students_count    INT,
    teachers          INT,
    community_members INT,
    FOREIGN KEY (session_id) REFERENCES sessions_raw(session_id)
);


-- ─────────────────────────────────────────────────────────────
-- 3.  MART DATABASE — DIMENSIONS
-- ─────────────────────────────────────────────────────────────
CREATE DATABASE ngo_mart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ngo_mart;

CREATE TABLE dim_school (
    school_key  INT PRIMARY KEY AUTO_INCREMENT,
    school_id   INT,
    school_name VARCHAR(100),
    state       VARCHAR(50),
    district    VARCHAR(50),
    urban_rural VARCHAR(10)
);

CREATE TABLE dim_student (
    student_key  INT PRIMARY KEY AUTO_INCREMENT,
    student_id   INT,
    student_name VARCHAR(100),
    gender       VARCHAR(10),
    grade        INT,
    school_key   INT,
    FOREIGN KEY (school_key) REFERENCES dim_school(school_key)
);

CREATE TABLE dim_program (
    program_key  INT PRIMARY KEY AUTO_INCREMENT,
    program_id   INT,
    program_name VARCHAR(100),
    program_type VARCHAR(50)
);

CREATE TABLE dim_instructor (
    instructor_key  INT PRIMARY KEY AUTO_INCREMENT,
    instructor_id   INT,
    instructor_name VARCHAR(100)
);

CREATE TABLE dim_activity (
    activity_key  INT PRIMARY KEY AUTO_INCREMENT,
    activity_id   INT,
    activity_name VARCHAR(100)
);

-- date_key is YYYYMMDD integer
CREATE TABLE dim_date (
    date_key   INT PRIMARY KEY,
    full_date  DATE,
    month      INT,
    year       INT,
    month_name VARCHAR(20)
);

-- ─────────────────────────────────────────────────────────────
-- 4.  MART DATABASE — FACTS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE fact_attendance (
    attendance_key INT PRIMARY KEY AUTO_INCREMENT,
    student_key    INT,
    program_key    INT,
    date_key       INT,
    attendance_flag TINYINT,
    FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
    FOREIGN KEY (program_key) REFERENCES dim_program(program_key),
    FOREIGN KEY (date_key)    REFERENCES dim_date(date_key)
);

CREATE TABLE fact_assessment (
    assessment_key INT PRIMARY KEY AUTO_INCREMENT,
    student_key    INT,
    program_key    INT,
    date_key       INT,
    test_type      VARCHAR(20),
    score          INT,
    max_score      INT,
    FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
    FOREIGN KEY (program_key) REFERENCES dim_program(program_key),
    FOREIGN KEY (date_key)    REFERENCES dim_date(date_key)
);

CREATE TABLE fact_session_event (
    session_key    INT PRIMARY KEY AUTO_INCREMENT,
    session_id     INT,
    date_key       INT,
    school_key     INT,
    program_key    INT,
    instructor_key INT,
    activity_key   INT,
    FOREIGN KEY (date_key)       REFERENCES dim_date(date_key),
    FOREIGN KEY (school_key)     REFERENCES dim_school(school_key),
    FOREIGN KEY (program_key)    REFERENCES dim_program(program_key),
    FOREIGN KEY (instructor_key) REFERENCES dim_instructor(instructor_key),
    FOREIGN KEY (activity_key)   REFERENCES dim_activity(activity_key)
);

CREATE TABLE fact_exposure (
    exposure_key      INT PRIMARY KEY AUTO_INCREMENT,
    session_key       INT,
    students_count    INT,
    teachers          INT,
    community_members INT,
    FOREIGN KEY (session_key) REFERENCES fact_session_event(session_key)
);

-- ─────────────────────────────────────────────────────────────
-- 5.  ETL — LOAD DIMENSIONS
-- ─────────────────────────────────────────────────────────────
INSERT INTO dim_school (school_id,school_name,state,district,urban_rural)
SELECT school_id,school_name,state,district,urban_rural FROM ngo_source.schools_raw;

INSERT INTO dim_program (program_id,program_name,program_type)
SELECT program_id,program_name,program_type FROM ngo_source.programs_raw;

INSERT INTO dim_student (student_id,student_name,gender,grade,school_key)
SELECT s.student_id,s.student_name,s.gender,s.grade,ds.school_key
FROM ngo_source.students_raw s
JOIN dim_school ds ON s.school_id = ds.school_id;

INSERT INTO dim_instructor (instructor_id,instructor_name)
SELECT instructor_id,instructor_name FROM ngo_source.instructors_raw;

INSERT INTO dim_activity (activity_id,activity_name)
SELECT activity_id,activity_name FROM ngo_source.activities_raw;

-- dim_date — union ALL date sources (attendance + assessment + sessions)
INSERT INTO dim_date (date_key,full_date,month,year,month_name)
SELECT DISTINCT
    CAST(DATE_FORMAT(date,'%Y%m%d') AS UNSIGNED),
    date, MONTH(date), YEAR(date), MONTHNAME(date)
FROM ngo_source.attendance_raw
UNION
SELECT DISTINCT
    CAST(DATE_FORMAT(date,'%Y%m%d') AS UNSIGNED),
    date, MONTH(date), YEAR(date), MONTHNAME(date)
FROM ngo_source.assessment_raw
UNION
SELECT DISTINCT
    CAST(DATE_FORMAT(date,'%Y%m%d') AS UNSIGNED),
    date, MONTH(date), YEAR(date), MONTHNAME(date)
FROM ngo_source.sessions_raw;

-- ─────────────────────────────────────────────────────────────
-- 6.  ETL — LOAD FACTS
-- ─────────────────────────────────────────────────────────────
INSERT INTO fact_attendance (student_key,program_key,date_key,attendance_flag)
SELECT
    ds.student_key,
    dp.program_key,
    CAST(DATE_FORMAT(a.date,'%Y%m%d') AS UNSIGNED),
    CASE WHEN a.attendance_status='Present' THEN 1 ELSE 0 END
FROM ngo_source.attendance_raw a
JOIN dim_student ds ON a.student_id = ds.student_id
JOIN dim_program dp ON a.program_id = dp.program_id;

INSERT INTO fact_assessment (student_key,program_key,date_key,test_type,score,max_score)
SELECT
    ds.student_key,
    dp.program_key,
    CAST(DATE_FORMAT(a.date,'%Y%m%d') AS UNSIGNED),
    a.test_type, a.score, a.max_score
FROM ngo_source.assessment_raw a
JOIN dim_student ds ON a.student_id = ds.student_id
JOIN dim_program dp ON a.program_id = dp.program_id;

INSERT INTO fact_session_event (session_id,date_key,school_key,program_key,instructor_key,activity_key)
SELECT
    s.session_id,
    CAST(DATE_FORMAT(s.date,'%Y%m%d') AS UNSIGNED),
    ds.school_key, dp.program_key, di.instructor_key, da.activity_key
FROM ngo_source.sessions_raw s
JOIN dim_school      ds ON s.school_id     = ds.school_id
JOIN dim_program     dp ON s.program_id    = dp.program_id
JOIN dim_instructor  di ON s.instructor_id = di.instructor_id
JOIN dim_activity    da ON s.activity_id   = da.activity_id;

INSERT INTO fact_exposure (session_key,students_count,teachers,community_members)
SELECT
    f.session_key, e.students_count, e.teachers, e.community_members
FROM ngo_source.exposure_raw e
JOIN fact_session_event f ON e.session_id = f.session_id;

-- ─────────────────────────────────────────────────────────────
-- 7.  SUMMARY TABLES  (the key fix: proper correlated joins)
-- ─────────────────────────────────────────────────────────────

-- 7a. school_performance_summary
--     attendance averaged per school/month, scores from assessment (same student,
--     same program) — avoids cross-join inflation by using a per-student subquery.
CREATE TABLE school_performance_summary AS
WITH student_scores AS (
    -- one row per student: their avg score % and learning gain
    SELECT
        student_key,
        program_key,
        ROUND(AVG(score / max_score) * 100, 2)                                        AS avg_score_pct,
        ROUND(
            AVG(CASE WHEN test_type = 'Endline'   THEN score ELSE NULL END) -
            AVG(CASE WHEN test_type = 'Baseline'  THEN score ELSE NULL END)
        , 2)                                                                           AS learning_gain
    FROM fact_assessment
    GROUP BY student_key, program_key
),
attendance_base AS (
    SELECT
        fa.student_key,
        fa.program_key,
        d.year,
        d.month,
        fa.attendance_flag
    FROM fact_attendance fa
    JOIN dim_date d ON fa.date_key = d.date_key
)
SELECT
    ab.year,
    ab.month,
    s.school_key,
    ROUND(AVG(ab.attendance_flag) * 100, 2)  AS avg_attendance_pct,
    ROUND(AVG(ss.avg_score_pct),  2)         AS avg_score_pct,
    ROUND(AVG(ss.learning_gain),  2)         AS learning_gain
FROM attendance_base ab
JOIN dim_student     st ON ab.student_key  = st.student_key
JOIN dim_school       s ON st.school_key   = s.school_key
LEFT JOIN student_scores ss
       ON ab.student_key  = ss.student_key
      AND ab.program_key  = ss.program_key
GROUP BY ab.year, ab.month, s.school_key;

-- 7b. program_effectiveness
--     attendance per program; scores joined on matching program_key
CREATE TABLE program_effectiveness AS
WITH prog_scores AS (
    SELECT
        student_key,
        program_key,
        ROUND(AVG(score / max_score) * 100, 2) AS avg_score_pct
    FROM fact_assessment
    GROUP BY student_key, program_key
)
SELECT
    p.program_name,
    ROUND(AVG(fa.attendance_flag) * 100, 2)  AS attendance_pct,
    ROUND(AVG(ps.avg_score_pct),  2)         AS avg_score_pct
FROM fact_attendance fa
JOIN dim_program p ON fa.program_key = p.program_key
LEFT JOIN prog_scores ps
       ON fa.student_key  = ps.student_key
      AND fa.program_key  = ps.program_key
GROUP BY p.program_name;

-- 7c. rural_urban_comparison
--     attendance per context; scores from matching student+program
CREATE TABLE rural_urban_comparison AS
WITH prog_scores AS (
    SELECT
        student_key,
        program_key,
        ROUND(AVG(score / max_score) * 100, 2) AS avg_score_pct
    FROM fact_assessment
    GROUP BY student_key, program_key
)
SELECT
    sc.urban_rural,
    ROUND(AVG(fa.attendance_flag) * 100, 2) AS attendance_pct,
    ROUND(AVG(ps.avg_score_pct),  2)        AS score_pct
FROM fact_attendance fa
JOIN dim_student     st ON fa.student_key  = st.student_key
JOIN dim_school      sc ON st.school_key   = sc.school_key
LEFT JOIN prog_scores ps
       ON fa.student_key  = ps.student_key
      AND fa.program_key  = ps.program_key
GROUP BY sc.urban_rural;

-- ─────────────────────────────────────────────────────────────
-- 8.  VERIFICATION  (run these SELECTs to confirm row counts)
-- ─────────────────────────────────────────────────────────────
SELECT 'dim_school'              , COUNT(*) FROM dim_school              UNION ALL
SELECT 'dim_student'             , COUNT(*) FROM dim_student             UNION ALL
SELECT 'dim_program'             , COUNT(*) FROM dim_program             UNION ALL
SELECT 'dim_instructor'          , COUNT(*) FROM dim_instructor          UNION ALL
SELECT 'dim_activity'            , COUNT(*) FROM dim_activity            UNION ALL
SELECT 'dim_date'                , COUNT(*) FROM dim_date                UNION ALL
SELECT 'fact_attendance'         , COUNT(*) FROM fact_attendance         UNION ALL
SELECT 'fact_assessment'         , COUNT(*) FROM fact_assessment         UNION ALL
SELECT 'fact_session_event'      , COUNT(*) FROM fact_session_event      UNION ALL
SELECT 'fact_exposure'           , COUNT(*) FROM fact_exposure           UNION ALL
SELECT 'school_performance_summary', COUNT(*) FROM school_performance_summary UNION ALL
SELECT 'program_effectiveness'   , COUNT(*) FROM program_effectiveness   UNION ALL
SELECT 'rural_urban_comparison'  , COUNT(*) FROM rural_urban_comparison;

-- Quick sanity checks on summary values
SELECT * FROM school_performance_summary  ORDER BY school_key, month;
SELECT * FROM program_effectiveness;
SELECT * FROM rural_urban_comparison;