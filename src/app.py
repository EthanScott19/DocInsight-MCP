import os
import json
import shutil
from pdf_ingest import parse_application_pdf
from db import get_connection, insert_application


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def stage_parsed_data(project_root: str, pdf_path: str, parsed_data: dict) -> str:
    """
    Save parsed JSON into staged/ before DB insertion.
    Returns the staged JSON path.
    """
    staged_dir = os.path.join(project_root, "staged")
    ensure_directory(staged_dir)

    pdf_base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    json_filename = f"{pdf_base_name}.json"
    staged_json_path = os.path.join(staged_dir, json_filename)

    with open(staged_json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2)

    return staged_json_path


def move_staged_file(project_root: str, staged_json_path: str, destination_folder: str) -> str:
    """
    Move staged JSON into processed/ or failed/
    """
    destination_dir = os.path.join(project_root, destination_folder)
    ensure_directory(destination_dir)

    destination_path = os.path.join(destination_dir, os.path.basename(staged_json_path))
    shutil.move(staged_json_path, destination_path)
    return destination_path


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    file_path = os.path.join(project_root, 'assets', 'Welcome.txt')
    db_path = os.path.join(script_dir, "docinsight.db")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_contents = file.read()
            print(file_contents)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    print("\nPlease select one of the options below:")

    while True:
        menu_choice = input("(1) Ask a question\n(2) Upload PDFs\n(3) Exit\n").strip()

        if menu_choice == "1":
            print("Question answering is not connected yet.")
            continue

        elif menu_choice == "2":
            pdf_path = input("Enter the full path to the PDF: ").strip()

            if not os.path.exists(pdf_path):
                print("Error: That path does not exist.")
                continue

            if not os.path.isfile(pdf_path):
                print("Error: That path is not a file.")
                continue

            if not pdf_path.lower().endswith(".pdf"):
                print("Error: That file is not a PDF.")
                continue

            conn = None
            staged_json_path = None

            try:
                parsed_data = parse_application_pdf(pdf_path)

                staged_json_path = stage_parsed_data(project_root, pdf_path, parsed_data)
                print("Data has been staged")
                # Insert into DB
                conn = get_connection(db_path)
                insert_application(conn, parsed_data)

                # Move staged file to processed after successful insert
                processed_path = move_staged_file(project_root, staged_json_path, "processed")

                print("\nData inserted into database successfully.")
                print(f"Staged JSON moved to: {processed_path}")

            except Exception as e:
                print(f"Error while processing PDF: {e}")

                if staged_json_path and os.path.exists(staged_json_path):
                    failed_path = move_staged_file(project_root, staged_json_path, "failed")
                    print(f"Staged JSON moved to: {failed_path}")

            finally:
                if conn:
                    conn.close()

            continue

        elif menu_choice == "3":
            print("Thank you for using DocInsight!")
            break

        else:
            print("Please enter the number corresponding to the menu option provided")


if __name__ == '__main__':
    main()
