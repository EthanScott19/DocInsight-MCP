import os
import json
import shutil

from pdf_ingest import parse_application_pdf
from db import get_connection, insert_application
from mcp_server import execute_query
from llm.service import generate_tool_call


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


def get_seen_basenames(project_root: str) -> set[str]:
    """
    Collect base filenames already present in staged/, processed/, or failed/
    using the .json filenames as the source of truth.
    """
    seen = set()

    for folder_name in ["staged", "processed", "failed"]:
        folder_path = os.path.join(project_root, folder_name)
        if not os.path.isdir(folder_path):
            continue

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".json"):
                seen.add(os.path.splitext(filename)[0])

    return seen


def get_pdf_files_from_directory(directory_path: str) -> list[str]:
    """
    Return all PDF files in the given directory, sorted by filename.
    Only scans the top level of the directory.
    """
    pdf_files = []

    for filename in os.listdir(directory_path):
        full_path = os.path.join(directory_path, filename)

        if os.path.isfile(full_path) and filename.lower().endswith(".pdf"):
            pdf_files.append(full_path)

    pdf_files.sort(key=lambda path: os.path.basename(path).lower())
    return pdf_files


def get_new_pdf_files(pdf_paths: list[str], project_root: str) -> tuple[list[str], list[str]]:
    """
    Split a list of PDF paths into:
    - new files
    - already seen files
    based on base filename
    """
    seen_basenames = get_seen_basenames(project_root)

    new_files = []
    already_seen = []

    for pdf_path in pdf_paths:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        if base_name in seen_basenames:
            already_seen.append(pdf_path)
        else:
            new_files.append(pdf_path)

    return new_files, already_seen


def prompt_for_exclusions(new_pdf_paths: list[str]) -> list[str]:
    """
    Show numbered new PDFs and allow the user to exclude any by number.
    User enters numbers one at a time until they enter q.
    Returns the list of excluded file paths.
    """
    if not new_pdf_paths:
        return []

    print("\nNew PDFs found:")
    for index, pdf_path in enumerate(new_pdf_paths, start=1):
        print(f"  ({index}) {os.path.basename(pdf_path)}")

    print("\nEnter the numbers of any PDFs you want to exclude.")
    print("Enter one number at a time. Enter 'q' when finished.")

    excluded_indices = set()

    while True:
        user_input = input("Exclude file number (or q to finish): ").strip().lower()

        if user_input == "q":
            break

        if not user_input.isdigit():
            print("Please enter a valid number or 'q'.")
            continue

        selected_index = int(user_input)

        if selected_index < 1 or selected_index > len(new_pdf_paths):
            print("That number is out of range.")
            continue

        if selected_index in excluded_indices:
            print("That file is already excluded.")
            continue

        excluded_indices.add(selected_index)
        print(f"Excluded: {os.path.basename(new_pdf_paths[selected_index - 1])}")

    excluded_paths = [new_pdf_paths[i - 1] for i in sorted(excluded_indices)]
    return excluded_paths


def process_single_pdf(pdf_path: str, project_root: str, db_path: str) -> tuple[bool, str]:
    """
    Process one PDF through parse -> stage -> insert -> move.
    Returns (success, message).
    """
    conn = None
    staged_json_path = None

    try:
        parsed_data = parse_application_pdf(pdf_path)

        staged_json_path = stage_parsed_data(project_root, pdf_path, parsed_data)
        print(f"Staged: {os.path.basename(pdf_path)}")

        conn = get_connection(db_path)
        insert_application(conn, parsed_data)

        processed_path = move_staged_file(project_root, staged_json_path, "processed")

        return True, f"Success: {os.path.basename(pdf_path)} -> {processed_path}"

    except Exception as e:
        if staged_json_path and os.path.exists(staged_json_path):
            failed_path = move_staged_file(project_root, staged_json_path, "failed")
            return False, f"Failed: {os.path.basename(pdf_path)} -> {failed_path} | Error: {e}"

        return False, f"Failed: {os.path.basename(pdf_path)} | Error: {e}"

    finally:
        if conn:
            conn.close()


def handle_single_pdf_upload(pdf_path: str, project_root: str, db_path: str) -> None:
    if not os.path.exists(pdf_path):
        print("Error: That path does not exist.")
        return

    if not os.path.isfile(pdf_path):
        print("Error: That path is not a file.")
        return

    if not pdf_path.lower().endswith(".pdf"):
        print("Error: That file is not a PDF.")
        return

    success, message = process_single_pdf(pdf_path, project_root, db_path)
    print(message)


def handle_directory_upload(directory_path: str, project_root: str, db_path: str) -> None:
    if not os.path.exists(directory_path):
        print("Error: That path does not exist.")
        return

    if not os.path.isdir(directory_path):
        print("Error: That path is not a directory.")
        return

    pdf_files = get_pdf_files_from_directory(directory_path)

    if not pdf_files:
        print("No PDF files were found in that directory.")
        return

    new_pdf_files, already_seen_files = get_new_pdf_files(pdf_files, project_root)

    print(f"\nTotal PDFs found: {len(pdf_files)}")
    print(f"Already seen by filename: {len(already_seen_files)}")
    print(f"New PDFs available for ingest: {len(new_pdf_files)}")

    if already_seen_files:
        print("\nAlready seen files:")
        for pdf_path in already_seen_files:
            print(f"  - {os.path.basename(pdf_path)}")

    if not new_pdf_files:
        print("\nThere are no new PDFs to ingest.")
        return

    excluded_files = prompt_for_exclusions(new_pdf_files)
    excluded_set = set(excluded_files)

    files_to_process = [pdf for pdf in new_pdf_files if pdf not in excluded_set]

    if not files_to_process:
        print("\nNo files selected for ingest.")
        return

    print("\nBeginning batch ingest...\n")

    success_count = 0
    failure_count = 0

    for pdf_path in files_to_process:
        success, message = process_single_pdf(pdf_path, project_root, db_path)
        print(message)

        if success:
            success_count += 1
        else:
            failure_count += 1

    print("\nBatch ingest summary:")
    print(f"  Total PDFs found: {len(pdf_files)}")
    print(f"  Already seen: {len(already_seen_files)}")
    print(f"  Excluded: {len(excluded_files)}")
    print(f"  Attempted: {len(files_to_process)}")
    print(f"  Succeeded: {success_count}")
    print(f"  Failed: {failure_count}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    file_path = os.path.join(project_root, "assets", "Welcome.txt")
    db_path = os.path.join(script_dir, "docinsight.db")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
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
            user_query = input("Enter your question: ").strip()

            if not user_query:
                print("Error: Question cannot be empty.")
                continue

            conn = None

            try:
                tool_call = generate_tool_call(user_query)

                conn = get_connection(db_path)
                result = execute_query(conn, tool_call)

                print("\nGenerated tool call:")
                print(json.dumps(tool_call, indent=2))

                print("\nQuery result:")
                print(json.dumps(result, indent=2))

            except Exception as e:
                print(f"Error while answering question: {e}")

            finally:
                if conn:
                    conn.close()

            continue

        elif menu_choice == "2":
            user_path = input(
                "Enter the full path to a PDF file or a directory containing PDFs: "
            ).strip()

            if not os.path.exists(user_path):
                print("Error: That path does not exist.")
                continue

            if os.path.isfile(user_path):
                handle_single_pdf_upload(user_path, project_root, db_path)
                continue

            if os.path.isdir(user_path):
                handle_directory_upload(user_path, project_root, db_path)
                continue

            print("Error: Path must be a PDF file or a directory.")
            continue

        elif menu_choice == "3":
            print("Thank you for using DocInsight!")
            break

        else:
            print("Please enter the number corresponding to the menu option provided")


if __name__ == "__main__":
    main()