#Command Line Interface loop
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    file_path = os.path.join(project_root, 'assets', 'Welcome.txt')
    try:
        with open(file_path, 'r') as file:
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
            #mcp_server.function()
            continue
        elif menu_choice == "2":
            #pdf_upload.function()
            continue
        elif menu_choice == "3":
            print("Thank you for using DocInsight!")
            break
        else:
            print("Please enter the number corresponding to the menu option provided")
    

if __name__ == '__main__':
    main()
