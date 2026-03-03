import os
import glob
import time

# Base filename for the database
DB_NAME = "room_server.db"


def main():
    print("\n========================================")
    print("      DATABASE CLEANER TOOL      ")
    print("========================================")

    # 1. Find all related database files (.db, .db-wal, .db-shm)
    # This acts like "ls room_server.db*" in terminal
    files_to_delete = glob.glob(f"{DB_NAME}*")

    if not files_to_delete:  # If no files are found, we can exit early
        print(f" No database files found starting with '{DB_NAME}'.")
        print(" System is already clean.")
        return

    print(f"⚠️  Found {len(files_to_delete)} file(s) to delete:")
    for f in files_to_delete:
        print(f"   - {f}")  # list of the files to be deleted

    print("\nIMPORTANT: Please ensure 'main.py' is NOT running.")

    # 2. Get confirmation from user
    confirm = input(f"❓ Do you want to delete these files? (y/n): ")

    if confirm.lower() != 'y':
        print(" Operation cancelled.")
        return

    # 3. Remove the files
    print("\n Deleting files...")
    success_count = 0  # Counter to track how many files were successfully
    # deleted, so we can give feedback at the end about whether the operation was
    # fully successful or if there were issues (like files being in use)

    for f in files_to_delete:
        try:
            os.remove(f)
            print(f"   Deleted: {f}")
            success_count += 1
        except OSError as e:
            print(f"   Error deleting '{f}': {e}")
            print("      (The file might be in use. Stop the server first!)")

    if success_count == len(files_to_delete):
        print("\n Success! Database has been completely reset.")
        print(" When you restart the server, a fresh DB will be created.")
    else:
        print("\n Warning: Some files could not be deleted.")


if __name__ == "__main__":
    main()
