-- =====================================================
-- NGO DATA MART — FINAL CLEAN PIPELINE
-- =====================================================

-- ============================
-- 1. RESET
-- ============================
DROP DATABASE IF EXISTS ngo_mart;
CREATE DATABASE ngo_mart;
USE ngo_mart;

-- ============================
-- 2. DIMENSIONS
-- ============================

CREATE TABLE dim_school (
    school_key INT PRIMARY KEY AUTO_INCREMENT,
    school_id INT,
    school_name VARCHAR(100),
    state VARCHAR(50),
    district VARCHAR(50),
    urban_rural VARCHAR(10)
);

CREATE TABLE dim_student (
    student_key INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT,
    student_name VARCHAR(100),
    gender VARCHAR(10),
    grade INT,
    school_key INT,
    FOREIGN KEY (school_key) REFERENCES dim_school(school_key)
);

CREATE TABLE dim_program (
    program_key INT PRIMARY KEY AUTO_INCREMENT,
    program_id INT,
    program_name VARCHAR(100),
    program_type VARCHAR(50)
);

CREATE TABLE dim_instructor (
    instructor_key INT PRIMARY KEY AUTO_INCREMENT,
    instructor_id INT,
    instructor_name VARCHAR(100)
);

CREATE TABLE dim_activity (
    activity_key INT PRIMARY KEY AUTO_INCREMENT,
    activity_id INT,
    activity_name VARCHAR(100)
);

CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE,
    month INT,
    year INT
);

-- ============================
-- 3. FACT TABLES
-- ============================

CREATE TABLE fact_attendance (
    attendance_key INT PRIMARY KEY AUTO_INCREMENT,
    student_key INT,
    program_key INT,
    date_key INT,
    attendance_flag INT,
    FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
    FOREIGN KEY (program_key) REFERENCES dim_program(program_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE fact_assessment (
    assessment_key INT PRIMARY KEY AUTO_INCREMENT,
    student_key INT,
    program_key INT,
    date_key INT,
    score INT,
    max_score INT,
    FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
    FOREIGN KEY (program_key) REFERENCES dim_program(program_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE fact_session_event (
    session_key INT PRIMARY KEY AUTO_INCREMENT,
    school_key INT,
    program_key INT,
    instructor_key INT,
    activity_key INT,
    date_key INT,
    FOREIGN KEY (school_key) REFERENCES dim_school(school_key),
    FOREIGN KEY (program_key) REFERENCES dim_program(program_key),
    FOREIGN KEY (instructor_key) REFERENCES dim_instructor(instructor_key),
    FOREIGN KEY (activity_key) REFERENCES dim_activity(activity_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- ============================
-- 4. LOAD DIMENSIONS
-- ============================

-- SCHOOL
INSERT INTO dim_school 
(school_id, school_name, state, district, urban_rural)
SELECT 
    school_id,
    TRIM(school_name),
    TRIM(state),
    TRIM(district),
    CASE 
        WHEN LOWER(urban_rural) IN ('urban','u') THEN 'Urban'
        WHEN LOWER(urban_rural) IN ('rural','r') THEN 'Rural'
        ELSE 'Unknown'
    END
FROM ngo_source.schools_raw;


-- PROGRAM
INSERT INTO dim_program (program_id, program_name, program_type)
SELECT 
    program_id,
    TRIM(program_name),
    TRIM(program_type)
FROM ngo_source.programs_raw;


-- INSTRUCTOR
-- ============================
-- LOAD DIMENSIONS
-- ============================

-- INSTRUCTOR
INSERT INTO dim_instructor (instructor_id, instructor_name)
SELECT 
    instructor_id,
    TRIM(instructor_name)
FROM ngo_source.instructors_raw;

-- ACTIVITY
INSERT INTO dim_activity (activity_id, activity_name)
SELECT DISTINCT
    activity_id,
    CONCAT('Activity ', activity_id)
FROM ngo_source.sessions_raw;

-- DATE (ALL SOURCES BEFORE FACTS)
INSERT INTO dim_date (date_key, full_date, month, year)
SELECT DISTINCT
    CAST(DATE_FORMAT(date, '%Y%m%d') AS UNSIGNED),
    date,
    MONTH(date),
    YEAR(date)
FROM (
    SELECT date FROM ngo_source.attendance_raw
    UNION
    SELECT date FROM ngo_source.sessions_raw
    UNION
    SELECT date FROM ngo_source.assessment_raw
) AS all_dates;

-- STUDENT (after school)
INSERT INTO dim_student (student_id, student_name, gender, grade, school_key)
SELECT 
    s.student_id,
    TRIM(s.student_name),
    CASE 
        WHEN LOWER(s.gender) IN ('m','male') THEN 'Male'
        WHEN LOWER(s.gender) IN ('f','female') THEN 'Female'
        ELSE 'Other'
    END,
    CAST(s.grade AS UNSIGNED),
    d.school_key
FROM ngo_source.students_raw s
JOIN dim_school d ON s.school_id = d.school_id;

-- ============================
-- LOAD FACT TABLES
-- ============================

-- ATTENDANCE
INSERT INTO fact_attendance (student_key, program_key, date_key, attendance_flag)
SELECT 
    ds.student_key,
    dp.program_key,
    CAST(DATE_FORMAT(a.date, '%Y%m%d') AS UNSIGNED),
    CASE 
        WHEN LOWER(a.attendance_status) = 'present' THEN 1
        ELSE 0
    END
FROM ngo_source.attendance_raw a
JOIN dim_student ds ON a.student_id = ds.student_id
JOIN dim_program dp ON a.program_id = dp.program_id;

-- ASSESSMENT
INSERT INTO fact_assessment (student_key, program_key, date_key, score, max_score)
SELECT 
    ds.student_key,
    dp.program_key,
    CAST(DATE_FORMAT(a.date, '%Y%m%d') AS UNSIGNED),
    a.score,
    a.max_score
FROM ngo_source.assessment_raw a
JOIN dim_student ds ON a.student_id = ds.student_id
JOIN dim_program dp ON a.program_id = dp.program_id;

-- SESSION EVENT
INSERT INTO fact_session_event (school_key, program_key, instructor_key, activity_key, date_key)
SELECT 
    ds.school_key,
    dp.program_key,
    di.instructor_key,
    da.activity_key,
    CAST(DATE_FORMAT(s.date, '%Y%m%d') AS UNSIGNED)
FROM ngo_source.sessions_raw s
JOIN dim_school ds ON s.school_id = ds.school_id
JOIN dim_program dp ON s.program_id = dp.program_id
JOIN dim_instructor di ON s.instructor_id = di.instructor_id
JOIN dim_activity da ON s.activity_id = da.activity_id;


-- ============================
-- 6. VALIDATION (RUN AFTER)
-- ============================

SELECT 'dim_school', COUNT(*) FROM dim_school UNION ALL
SELECT 'dim_student', COUNT(*) FROM dim_student UNION ALL
SELECT 'dim_program', COUNT(*) FROM dim_program UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date UNION ALL
SELECT 'fact_attendance', COUNT(*) FROM fact_attendance UNION ALL
SELECT 'fact_assessment', COUNT(*) FROM fact_assessment UNION ALL
SELECT 'fact_session_event', COUNT(*) FROM fact_session_event;

CREATE OR REPLACE VIEW vw_school_performance AS

-- ======================
-- ATTENDANCE (BASE TABLE)
-- ======================
WITH attendance_agg AS (
    SELECT 
        st.school_key,
        dd.year,
        dd.month,
        AVG(fa.attendance_flag) * 100 AS attendance_pct
    FROM fact_attendance fa
    JOIN dim_student st 
        ON fa.student_key = st.student_key
    JOIN dim_date dd 
        ON fa.date_key = dd.date_key
    GROUP BY 
        st.school_key, dd.year, dd.month
),

-- ======================
-- SCORES (OPTIONAL DATA)
-- ======================
score_agg AS (
    SELECT 
        st.school_key,
        dd.year,
        dd.month,
        AVG(fas.score / NULLIF(fas.max_score,0)) * 100 AS score_pct
    FROM fact_assessment fas
    JOIN dim_student st 
        ON fas.student_key = st.student_key
    JOIN dim_date dd 
        ON fas.date_key = dd.date_key
    GROUP BY 
        st.school_key, dd.year, dd.month
)

-- ======================
-- FINAL JOIN (LESS AGGRESSIVE)
-- ======================
SELECT 
    ds.school_key,
    ds.school_name,
    ds.state,
    ds.district,
    ds.urban_rural,

    a.year,
    a.month,

    ROUND(a.attendance_pct, 2) AS attendance_pct,

    -- 👇 Allow NULL scores instead of dropping rows
    ROUND(s.score_pct, 2) AS score_pct,

    -- 👇 Only calculate learning gain when score exists
    CASE 
        WHEN s.score_pct IS NOT NULL 
        THEN ROUND(s.score_pct - a.attendance_pct, 2)
        ELSE NULL
    END AS learning_gain

FROM attendance_agg a

-- 🔥 KEY CHANGE: LEFT JOIN (NOT INNER JOIN)
LEFT JOIN score_agg s 
    ON a.school_key = s.school_key
    AND a.year = s.year
    AND a.month = s.month

JOIN dim_school ds 
    ON a.school_key = ds.school_key

-- 👇 Only basic sanity filter (NOT aggressive)
WHERE a.year IS NOT NULL 
  AND a.month IS NOT NULL;

-- ======================
-- SCORE AGG (clean)
-- ======================


-- ======================
-- FINAL JOIN (NO FAN-OUT)
-- ======================
SELECT 
    ds.school_key,
    ds.school_name,
    ds.state,
    ds.district,
    ds.urban_rural,

    a.year,
    a.month,

    ROUND(a.attendance_pct, 2) AS attendance_pct,
    ROUND(s.score_pct, 2) AS score_pct,

    ROUND(s.score_pct - a.attendance_pct, 2) AS learning_gain

FROM attendance_agg a

INNER JOIN score_agg s 
    ON a.school_key = s.school_key
    AND a.year = s.year
    AND a.month = s.month

JOIN dim_school ds 
    ON a.school_key = ds.school_key

WHERE a.year IS NOT NULL 
  AND a.month IS NOT NULL;

CREATE OR REPLACE VIEW vw_program_effectiveness AS

WITH attendance_agg AS (
    SELECT 
        program_key,
        AVG(attendance_flag) * 100 AS attendance_pct
    FROM fact_attendance
    GROUP BY program_key
),

score_agg AS (
    SELECT 
        program_key,
        AVG(score / NULLIF(max_score,0)) * 100 AS score_pct
    FROM fact_assessment
    GROUP BY program_key
)

SELECT 
    dp.program_key,
    dp.program_name,

    ROUND(a.attendance_pct, 2) AS attendance_pct,
    ROUND(s.score_pct, 2) AS score_pct

FROM dim_program dp

LEFT JOIN attendance_agg a 
    ON dp.program_key = a.program_key

LEFT JOIN score_agg s 
    ON dp.program_key = s.program_key;


CREATE OR REPLACE VIEW vw_instructor_effectiveness AS
SELECT 
    di.instructor_name,

    COUNT(DISTINCT f.session_key) AS sessions_conducted,

    ROUND(AVG(fa.attendance_flag) * 100, 2) AS avg_attendance,

    ROUND(AVG(fas.score / NULLIF(fas.max_score,0)) * 100, 2) AS avg_score,

    -- 🔥 THIS COLUMN WAS MISSING / WRONG
    ROUND(
        (AVG(fas.score / NULLIF(fas.max_score,0)) * 100)
        -
        (AVG(fa.attendance_flag) * 100)
    , 2) AS learning_gain

FROM fact_session_event f

JOIN dim_instructor di 
    ON f.instructor_key = di.instructor_key

LEFT JOIN fact_attendance fa 
    ON f.date_key = fa.date_key

LEFT JOIN fact_assessment fas 
    ON f.date_key = fas.date_key
    AND fa.student_key = fas.student_key

GROUP BY di.instructor_name;




CREATE OR REPLACE VIEW vw_exposure_metrics AS
SELECT 
    COUNT(DISTINCT st.student_key) AS total_students,
    COUNT(DISTINCT di.instructor_key) AS total_teachers,
    COUNT(DISTINCT ds.school_key) * 50 AS community_reach
FROM dim_student st
JOIN dim_school ds 
    ON st.school_key = ds.school_key
LEFT JOIN fact_session_event f 
    ON ds.school_key = f.school_key
LEFT JOIN dim_instructor di 
    ON f.instructor_key = di.instructor_key;


CREATE OR REPLACE VIEW vw_school_performance_band AS
SELECT *,
    CASE 
        WHEN score_pct >= 80 THEN 'Excellent'
        WHEN score_pct >= 60 THEN 'Good'
        WHEN score_pct >= 40 THEN 'Average'
        ELSE 'Needs Improvement'
    END AS performance_band
FROM vw_school_performance;

