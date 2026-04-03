import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================
# 1. DATABASE CONFIG
# ==========================================
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'ngo_source'

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ==========================================
# 2. FILE → TABLE MAPPING (ORDER MATTERS)
# ==========================================
csv_to_table_map = [
    ('schools_raw.csv', 'schools_raw', 'school_id'),
    ('programs_raw.csv', 'programs_raw', 'program_id'),
    ('instructors_raw.csv', 'instructors_raw', 'instructor_id'),
    ('activities_raw.csv', 'activities_raw', 'activity_id'),
    ('students_raw.csv', 'students_raw', 'student_id'),
    ('sessions_raw.csv', 'sessions_raw', None),
    ('attendance_raw.csv', 'attendance_raw', None),
    ('assessment_raw.csv', 'assessment_raw', None),
    ('exposure_raw.csv', 'exposure_raw', None)
]

# ==========================================
# 3. TRUNCATE ORDER (REVERSE DEPENDENCY)
# ==========================================
truncate_order = [
    'exposure_raw',
    'assessment_raw',
    'attendance_raw',
    'sessions_raw',
    'students_raw',
    'activities_raw',
    'instructors_raw',
    'programs_raw',
    'schools_raw'
]

# ==========================================
# 4. HELPER: CLEAN DATAFRAME
# ==========================================
def clean_dataframe(df):
    # Remove unwanted columns like 'Unnamed: 0'
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

# ==========================================
# 5. HELPER: HANDLE DUPLICATES
# ==========================================
def handle_duplicates(df, table_name, pk):
    if pk is None:
        return df

    if df[pk].duplicated().any():
        dup_count = df[pk].duplicated().sum()
        print(f"   ⚠ Found {dup_count} duplicate {pk} in {table_name} → keeping last")
        df = df.drop_duplicates(subset=[pk], keep='last')

    return df

# ==========================================
# 6. HELPER: BASIC VALIDATION
# ==========================================
def validate_dataframe(df, table_name):
    if df.empty:
        raise ValueError(f"{table_name} is empty!")

# ==========================================
# 7. MAIN ETL FUNCTION
# ==========================================
def load_csvs_to_mysql():
    print("\n🚀 STARTING DATA LOAD\n" + "=" * 50)

    # --------------------------------------
    # STEP 1: CLEAN EXISTING DATA
    # --------------------------------------
    with engine.connect() as conn:
        try:
            print("\n🧹 Clearing existing tables...")

            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

            for table in truncate_order:
                try:
                    conn.execute(text(f"TRUNCATE TABLE {table}"))
                    print(f"   ✔ {table} cleared")
                except Exception as e:
                    print(f"   ⚠ Skipped {table}: {e}")

            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        except Exception as e:
            print(f"\n❌ Cleanup failed: {e}")
            return

    # --------------------------------------
    # STEP 2: LOAD DATA
    # --------------------------------------
    for file_name, table_name, pk in csv_to_table_map:
        try:
            print(f"\n📥 Loading {file_name} → {table_name}")

            # Read CSV
            df = pd.read_csv(file_name)

            # Clean
            df = clean_dataframe(df)

            # Validate
            validate_dataframe(df, table_name)

            # Handle duplicates
            df = handle_duplicates(df, table_name, pk)

            # Insert into DB
            df.to_sql(
                name=table_name,
                con=engine,
                if_exists='append',
                index=False
            )

            print(f"   ✅ {len(df)} rows inserted")

        except FileNotFoundError:
            print(f"   ❌ File not found: {file_name}")

        except Exception as e:
            print(f"   ❌ Error in {table_name}: {e}")

    print("\n🎉 DATA LOAD COMPLETE\n" + "=" * 50)


# ==========================================
# 8. RUN
# ==========================================
if __name__ == "__main__":
    load_csvs_to_mysql()
