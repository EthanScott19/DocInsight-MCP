from db import get_connection, insert_application
import random


def generate_fake_application(app_id):
    degrees = [
    "Computer Science (MS)",
    "Biology (MS)",
    "Mathematics (MS)"
    ]
    
    statuses = ["Conditional Admission", "Full Admission", "Denied Admission"]
    student_types = ["First-Time Graduate", "Transfer Graduate"]

    return {
        "app_id": app_id,
        "major": random.choice(degrees),
        "term": "Fall 2025",
        "grad_type": 1,
        "admissions_status": "Completed App",
        "student_type": random.choice(student_types),
        "gpa": round(random.uniform(2.0, 4.0), 2),
        "missing_items": random.choice([
            [],
            ["Final Transcript"],
            ["Recommendation Letter"]
        ]),
        "decision_status": random.choice(statuses),
        "decision_reason": "Auto-generated for testing.",
        "applicant_name": f"Student {app_id}",
        "muid": f"M{1000 + app_id}",
        "gender": random.choice([0, 1, 2]),
        "email_address": f"student{app_id}@marshall.edu",
        "phys_address": f"{app_id} University Ave",
        "documents": [
            {
                "display_name": "Application Fee",
                "status": "Waived",
                "date_received": "05182025"
            },
            {
                "display_name": "Transcript",
                "status": random.choice(["Received", "Missing"]),
                "date_received": random.choice(["05182025", None])
            }
        ]
    }


def main():
    conn = get_connection("docinsight.db")

    for i in range(1, 21):  # 20 fake applications
        data = generate_fake_application(5000 + i)
        insert_application(conn, data)

    conn.close()
    print("Fake data inserted successfully.")


if __name__ == "__main__":
    main()
