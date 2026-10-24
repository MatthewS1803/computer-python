import re

print("===== Strong Password Checker =====")

password = input("""Create your password:
- It must be at least 8 characters long
- It must contain uppercase and lowercase letters
- It must contain at least one number
""")

while True:
    if len(password) < 8:
        print("Password must be at least 8 characters long.")
    elif not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password):
        print("Password must contain both uppercase and lowercase letters.")
    elif not re.search(r"\d", password):
        print("Password must contain at least one number.")
    else:
        print("Your password is strong!")
        break

    password = input("Please create a new password: ")