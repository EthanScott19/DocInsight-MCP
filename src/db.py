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
        gender INTEGER,
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