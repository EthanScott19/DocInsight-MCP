import sqlite3
from typing import Any, Dict, Optional, List


def get_connection(db_path: str = "docinsight.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Users (
        UID INTEGER PRIMARY KEY AUTOINCREMENT,
        applicantName TEXT,
        MUID TEXT,
        GPA REAL,
        gender TEXT,
        emailAddress TEXT,
        physAddress TEXT
    );

    CREATE TABLE IF NOT EXISTS AdmissionNotes (
        adID INTEGER PRIMARY KEY AUTOINCREMENT,
        adNote TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Degrees (
        dID INTEGER PRIMARY KEY AUTOINCREMENT,
        dNm TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Applications (
        appID INTEGER PRIMARY KEY,
        adID INTEGER NOT NULL,
        dID INTEGER NOT NULL,
        uID INTEGER NOT NULL,
        appDate INTEGER,
        gradType INTEGER,
        term TEXT,
        admissionsStatus TEXT,
        studentType TEXT,
        decisionReason TEXT,
        FOREIGN KEY (adID) REFERENCES AdmissionNotes(adID),
        FOREIGN KEY (dID) REFERENCES Degrees(dID),
        FOREIGN KEY (uID) REFERENCES Users(UID)
    );

    CREATE TABLE IF NOT EXISTS ApplicationDocuments (
        docID INTEGER PRIMARY KEY AUTOINCREMENT,
        appID INTEGER NOT NULL,
        displayName TEXT NOT NULL,
        status TEXT,
        dateReceived TEXT,
        FOREIGN KEY (appID) REFERENCES Applications(appID)
    );

    CREATE TABLE IF NOT EXISTS MissingItems (
        missingID INTEGER PRIMARY KEY AUTOINCREMENT,
        appID INTEGER NOT NULL,
        itemName TEXT NOT NULL,
        FOREIGN KEY (appID) REFERENCES Applications(appID)
    );
    CREATE TABLE IF NOT EXISTS ApplicantCourses (
        courseID INTEGER PRIMARY KEY AUTOINCREMENT,
        appID INTEGER NOT NULL,
        term TEXT,
        subject TEXT,
        courseNumber TEXT,
        courseTitle TEXT,
        creditHours REAL,
        grade TEXT,
        qualityPoints REAL,
        FOREIGN KEY(appID) REFERENCES Applications(appID)
    );
    """)

    conn.commit()


def seed_reference_data(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    admission_notes = [
        ("Full Admission",),
        ("Provisional Admission",),
        ("Denied Admission",),
    ]

    degree_codes = [
        ("CSC",),
        ("BIO",),
        ("MTH",),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO AdmissionNotes (adNote)
        VALUES (?)
    """, admission_notes)

    cursor.executemany("""
        INSERT OR IGNORE INTO Degrees (dNm)
        VALUES (?)
    """, degree_codes)

    conn.commit()


def map_admission_status(parser_status: Optional[str]) -> Optional[str]:
    mapping = {
        "Conditional Admission": "Provisional Admission",
        "Not Admitted": "Denied Admission",
        "Denied Admission": "Denied Admission",
        "Full Admission": "Full Admission",
    }
    return mapping.get(parser_status, parser_status)


def map_degree_name(parser_degree: Optional[str]) -> Optional[str]:
    mapping = {
        "Computer Science (MS)": "CSC",
        "Biology (MS)": "BIO",
        "Mathematics (MS)": "MTH",
    }
    return mapping.get(parser_degree, parser_degree)


def get_degree_id(conn: sqlite3.Connection, degree_name: str) -> Optional[int]:
    cursor = conn.cursor()
    cursor.execute("SELECT dID FROM Degrees WHERE dNm = ?", (degree_name,))
    row = cursor.fetchone()
    return row["dID"] if row else None


def get_admission_note_id(conn: sqlite3.Connection, ad_note: str) -> Optional[int]:
    cursor = conn.cursor()
    cursor.execute("SELECT adID FROM AdmissionNotes WHERE adNote = ?", (ad_note,))
    row = cursor.fetchone()
    return row["adID"] if row else None


def insert_user(conn: sqlite3.Connection, data: Dict[str, Any]) -> int:
    """
    Inserts a user row but does NOT commit.
    The caller controls the transaction.
    """
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Users (applicantName, MUID, GPA, gender, emailAddress, physAddress)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("applicant_name"),
        data.get("muid"),
        data.get("gpa"),
        data.get("gender"),
        data.get("email_address"),
        data.get("phys_address"),
    ))

    return cursor.lastrowid


def insert_application(conn: sqlite3.Connection, data: Dict[str, Any]) -> None:
    """
    Inserts one full application transactionally.
    If anything fails, nothing is committed.
    """
    try:
        cursor = conn.cursor()

        mapped_degree = map_degree_name(data.get("major"))
        mapped_admission = map_admission_status(data.get("decision_status"))

        dID = get_degree_id(conn, mapped_degree) if mapped_degree else None
        adID = get_admission_note_id(conn, mapped_admission) if mapped_admission else None

        if dID is None:
            raise ValueError(f"No matching degree found for parser value: {data.get('major')}")

        if adID is None:
            raise ValueError(
                f"No matching admission note found for parser value: {data.get('decision_status')}"
            )

        app_id = data.get("app_id")
        if app_id is None:
            raise ValueError("Parsed data is missing app_id.")

        # Optional duplicate guard
        cursor.execute("SELECT 1 FROM Applications WHERE appID = ?", (app_id,))
        existing = cursor.fetchone()
        if existing:
            raise ValueError(f"Application with appID {app_id} already exists.")

        uID = insert_user(conn, data)

        cursor.execute("""
            INSERT INTO Applications (
                appID, adID, dID, uID, appDate, gradType, term,
                admissionsStatus, studentType, decisionReason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            adID,
            dID,
            uID,
            data.get("app_date"),
            data.get("grad_type"),
            data.get("term"),
            data.get("admissions_status"),
            data.get("student_type"),
            data.get("decision_reason"),
        ))

        for item in data.get("missing_items", []):
            cursor.execute("""
                INSERT INTO MissingItems (appID, itemName)
                VALUES (?, ?)
            """, (app_id, item))

        for doc in data.get("documents", []):
            cursor.execute("""
                INSERT INTO ApplicationDocuments (appID, displayName, status, dateReceived)
                VALUES (?, ?, ?, ?)
            """, (
                app_id,
                doc.get("display_name"),
                doc.get("status"),
                doc.get("date_received"),
            ))
        for course in data.get("courses", []):
            cursor.execute("""
                INSERT INTO ApplicantCourses (
                    appID,
                    term,
                    subject,
                    courseNumber,
                    courseTitle,
                    creditHours,
                    grade,
                    qualityPoints
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            app_id,
            course.get("term"),
            course.get("subject"),
            course.get("course_number"),
            course.get("course_title"),
            course.get("credit_hours"),
            course.get("grade"),
            course.get("quality_points"),
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise


# -----------------------------
# Basic query helper functions
# -----------------------------

def get_application_by_id(conn: sqlite3.Connection, app_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.appID,
            a.appDate,
            a.gradType,
            a.term,
            a.admissionsStatus,
            a.studentType,
            a.decisionReason,
            u.UID,
            u.applicantName,
            u.MUID,
            u.GPA,
            u.gender,
            u.emailAddress,
            u.physAddress,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE a.appID = ?
    """, (app_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_all_applications(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.appID,
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            a.admissionsStatus,
            a.studentType
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        ORDER BY a.appID
    """)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_missing_items_for_application(conn: sqlite3.Connection, app_id: int) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT missingID, appID, itemName
        FROM MissingItems
        WHERE appID = ?
        ORDER BY missingID
    """, (app_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_documents_for_application(conn: sqlite3.Connection, app_id: int) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT docID, appID, displayName, status, dateReceived
        FROM ApplicationDocuments
        WHERE appID = ?
        ORDER BY docID
    """, (app_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_applications_by_degree(conn: sqlite3.Connection, degree_code: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.appID,
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE d.dNm = ?
        ORDER BY a.appID
    """, (degree_code,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_applications_by_admission_note(conn: sqlite3.Connection, admission_note: str) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.appID,
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE n.adNote = ?
        ORDER BY a.appID
    """, (admission_note,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def count_all_applications(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM Applications")
    row = cursor.fetchone()
    return row["total"]


def count_applications_by_admission_note(conn: sqlite3.Connection, admission_note: str) -> int:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM Applications a
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE n.adNote = ?
    """, (admission_note,))
    row = cursor.fetchone()
    return row["total"]


def count_applications_by_degree(conn: sqlite3.Connection, degree_code: str) -> int:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM Applications a
        JOIN Degrees d ON a.dID = d.dID
        WHERE d.dNm = ?
    """, (degree_code,))
    row = cursor.fetchone()
    return row["total"]


def filter_applications(
        conn: sqlite3.Connection,
        degree_code: Optional[str] = None,
        admission_note: Optional[str] = None,
        min_gpa: Optional[float] = None,
        max_gpa: Optional[float] = None,
        student_type: Optional[str] = None,
        term: Optional[str] = None,
) -> list[dict]:
    cursor = conn.cursor()

    query = """
        SELECT
            a.appID,
            u.applicantName,
            u.MUID,
            u.GPA,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            a.admissionsStatus,
            a.studentType,
            a.decisionReason
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE 1=1
    """

    params = []

    if degree_code is not None:
        query += " AND d.dNm = ?"
        params.append(degree_code)

    if admission_note is not None:
        query += " AND n.adNote = ?"
        params.append(admission_note)

    if min_gpa is not None:
        query += " AND u.GPA >= ?"
        params.append(min_gpa)

    if max_gpa is not None:
        query += " AND u.GPA <= ?"
        params.append(max_gpa)

    if student_type is not None:
        query += " AND a.studentType = ?"
        params.append(student_type)

    if term is not None:
        query += " AND a.term = ?"
        params.append(term)

    query += " ORDER BY a.appID"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def count_filtered_applications(
        conn: sqlite3.Connection,
        degree_code: Optional[str] = None,
        admission_note: Optional[str] = None,
        min_gpa: Optional[float] = None,
        max_gpa: Optional[float] = None,
        student_type: Optional[str] = None,
        term: Optional[str] = None,
) -> int:
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*) AS total
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE 1=1
    """

    params = []

    if degree_code is not None:
        query += " AND d.dNm = ?"
        params.append(degree_code)

    if admission_note is not None:
        query += " AND n.adNote = ?"
        params.append(admission_note)

    if min_gpa is not None:
        query += " AND u.GPA >= ?"
        params.append(min_gpa)

    if max_gpa is not None:
        query += " AND u.GPA <= ?"
        params.append(max_gpa)

    if student_type is not None:
        query += " AND a.studentType = ?"
        params.append(student_type)

    if term is not None:
        query += " AND a.term = ?"
        params.append(term)

    cursor.execute(query, params)
    row = cursor.fetchone()
    return row["total"]
def get_random_applicant(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            a.appID,
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            u.GPA
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    return dict(row) if row else None
def get_applicant_admission_status(conn, name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            n.adNote AS admissionNote,
            a.admissionsStatus
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE u.applicantName LIKE ?
        LIMIT 1
    """, (f"%{name}%",))

    row = cursor.fetchone()
    return dict(row) if row else None

def get_applicant_term(conn, name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            a.term
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        WHERE u.applicantName LIKE ?
        LIMIT 1
    """, (f"%{name}%",))

    row = cursor.fetchone()
    return dict(row) if row else None
def get_applicant_gpa(conn, name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            u.GPA
        FROM Users u
        WHERE u.applicantName LIKE ?
        LIMIT 1
    """, (f"%{name}%",))

    row = cursor.fetchone()
    return dict(row) if row else None
def search_applicants_by_name(conn, name_query):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            u.GPA
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE u.applicantName LIKE ?
        ORDER BY u.applicantName
    """, (f"%{name_query}%",))

    rows = cursor.fetchall()
    return [dict(row) for row in rows]
def get_applicant_muid(conn, name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            u.MUID
        FROM Users u
        WHERE u.applicantName LIKE ?
        LIMIT 1
    """, (f"%{name}%",))

    row = cursor.fetchone()
    return dict(row) if row else None
def get_full_admission_percentage(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM Applications
    """)

    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS full_admissions
        FROM Applications a
        JOIN AdmissionNotes n
            ON a.adID = n.adID
        WHERE n.adNote = 'Full Admission'
    """)

    full_admissions = cursor.fetchone()["full_admissions"]

    percentage = 0

    if total > 0:
        percentage = round((full_admissions / total) * 100, 2)

    return {
        "totalApplicants": total,
        "fullAdmissions": full_admissions,
        "percentage": percentage
    }
def get_average_gpa_for_admitted_students(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            AVG(u.GPA) AS averageGPA,
            COUNT(*) AS admittedCount
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE n.adNote IN (
            'Full Admission',
            'Conditional Admission',
            'Provisional Admission'
        )
    """)

    row = cursor.fetchone()

    return {
        "averageGPA": round(row["averageGPA"], 2) if row["averageGPA"] is not None else None,
        "admittedCount": row["admittedCount"]
    }
def get_major_with_highest_average_gpa(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            d.dNm AS degreeCode,
            ROUND(AVG(u.GPA), 2) AS averageGPA,
            COUNT(*) AS applicantCount
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        GROUP BY d.dNm
        ORDER BY averageGPA DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    return dict(row) if row else None
def get_applicants_who_took_course(conn, course_query):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            c.subject,
            c.courseNumber,
            c.courseTitle,
            c.grade
        FROM ApplicantCourses c
        JOIN Applications a ON c.appID = a.appID
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE c.courseTitle LIKE ?
           OR c.subject || ' ' || c.courseNumber LIKE ?
           OR c.subject || c.courseNumber LIKE ?
        ORDER BY u.applicantName
    """, (
        f"%{course_query}%",
        f"%{course_query}%",
        f"%{course_query}%"
    ))

    rows = cursor.fetchall()
    return [dict(row) for row in rows]
def get_applicants_by_course_grade_filter(conn, course_query, grade_filter):
    grade_rank = {
        "A": 4,
        "B": 3,
        "C": 2,
        "D": 1,
        "F": 0,
        "W": -1
    }

    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            u.applicantName,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            c.subject,
            c.courseNumber,
            c.courseTitle,
            c.grade
        FROM ApplicantCourses c
        JOIN Applications a ON c.appID = a.appID
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE c.courseTitle LIKE ?
           OR c.subject || ' ' || c.courseNumber LIKE ?
           OR c.subject || c.courseNumber LIKE ?
        ORDER BY u.applicantName
    """, (
        f"%{course_query}%",
        f"%{course_query}%",
        f"%{course_query}%"
    ))

    rows = cursor.fetchall()
    results = []

    for row in rows:
        row_dict = dict(row)
        grade = row_dict["grade"]

        if grade not in grade_rank:
            continue

        if grade_filter == "below_b" and grade_rank[grade] < grade_rank["B"]:
            results.append(row_dict)

        elif grade_filter == "at_least_b" and grade_rank[grade] >= grade_rank["B"]:
            results.append(row_dict)

        elif grade_filter == "a_only" and grade == "A":
            results.append(row_dict)

        elif grade_filter == "exact_b" and grade == "B":
            results.append(row_dict)

        elif grade_filter == "passed" and grade not in ("F", "W"):
            results.append(row_dict)

    return results
def get_applicant_strongest_subject(conn, name):
    grade_rank = {
        "A": 4.0,
        "B": 3.0,
        "C": 2.0,
        "D": 1.0,
        "F": 0.0
    }

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            c.subject,
            c.grade
        FROM ApplicantCourses c
        JOIN Applications a ON c.appID = a.appID
        JOIN Users u ON a.uID = u.UID
        WHERE u.applicantName LIKE ?
    """, (f"%{name}%",))

    rows = cursor.fetchall()

    if not rows:
        return None

    subject_totals = {}
    subject_counts = {}

    applicant_name = rows[0]["applicantName"]

    for row in rows:
        subject = row["subject"]
        grade = row["grade"]

        if grade not in grade_rank:
            continue

        subject_totals[subject] = subject_totals.get(subject, 0) + grade_rank[grade]
        subject_counts[subject] = subject_counts.get(subject, 0) + 1

    if not subject_totals:
        return None

    averages = {
        subject: subject_totals[subject] / subject_counts[subject]
        for subject in subject_totals
    }

    strongest_subject = max(averages, key=averages.get)

    return {
        "applicantName": applicant_name,
        "strongestSubject": strongest_subject,
        "averageGradeScore": round(averages[strongest_subject], 2)
    }

def count_applicant_courses_by_subject(conn, name, subject):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.applicantName,
            ? AS subject,
            COUNT(*) AS completedCourseCount
        FROM ApplicantCourses c
        JOIN Applications a ON c.appID = a.appID
        JOIN Users u ON a.uID = u.UID
        WHERE u.applicantName LIKE ?
          AND c.subject = ?
          AND c.grade NOT IN ('F', 'W')
        GROUP BY u.applicantName
    """, (
        subject,
        f"%{name}%",
        subject
    ))

    row = cursor.fetchone()
    return dict(row) if row else None

def get_full_profile_by_name(conn, name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.appID,
            u.applicantName,
            u.MUID,
            u.GPA,
            u.gender,
            u.emailAddress,
            u.physAddress,
            d.dNm AS degreeCode,
            n.adNote AS admissionNote,
            a.term,
            a.admissionsStatus,
            a.studentType,
            a.decisionReason
        FROM Applications a
        JOIN Users u ON a.uID = u.UID
        JOIN Degrees d ON a.dID = d.dID
        JOIN AdmissionNotes n ON a.adID = n.adID
        WHERE u.applicantName LIKE ?
        LIMIT 1
    """, (f"%{name}%",))

    applicant = cursor.fetchone()

    if not applicant:
        return None

    app_id = applicant["appID"]

    cursor.execute("""
        SELECT itemName
        FROM MissingItems
        WHERE appID = ?
    """, (app_id,))
    missing_items = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT displayName, status, dateReceived
        FROM ApplicationDocuments
        WHERE appID = ?
    """, (app_id,))
    documents = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT
            term,
            subject,
            courseNumber,
            courseTitle,
            creditHours,
            grade,
            qualityPoints
        FROM ApplicantCourses
        WHERE appID = ?
        ORDER BY term, subject, courseNumber
    """, (app_id,))
    courses = [dict(row) for row in cursor.fetchall()]

    return {
        "applicant": dict(applicant),
        "missingItems": missing_items,
        "documents": documents,
        "courses": courses
    }
