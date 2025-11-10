from werkzeug.security import generate_password_hash

def main():
    print("=== QuietQueue Admin Password Hasher ===")
    password = input("Enter the password to hash: ").strip()
    if not password:
        print("Error: Password cannot be empty.")
        return

    hashed_password = generate_password_hash(password)
    print("\nHashed Password Generated Successfully!")
    print("Copy and paste this into your MySQL 'admins' table:\n")
    print(hashed_password)
    print("\nExample SQL:")
    print("INSERT INTO admins (username, email, password) VALUES ('Admin', 'admin@example.com', '" + hashed_password + "');")

if __name__ == "__main__":
    main()