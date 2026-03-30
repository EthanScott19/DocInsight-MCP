from db import get_connection, create_tables, seed_reference_data

def main():
    conn = get_connection("docinsight.db")
    create_tables(conn)
    seed_reference_data(conn)
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    main()
