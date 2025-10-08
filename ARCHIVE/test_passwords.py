#!/usr/bin/env python3
import bcrypt
import hashlib

# Тестируем bcrypt пароли из users.json
admin_hash = "$2b$12$Kh7w1ZwFdwrj4olKcF3m7e2fPzkdSIWsfAQxhMsQ3TUMdCfKoaow2"
user_hash = "$2b$12$Sfdz99Xq6OAbwRoOYBBsfe9XiyliRub2TgPml6XlQN5CmkpRmbxbq"

passwords_to_try = ['admin', 'password', '123456', 'admin123', 'qwerty', 'user', 'test']

print("Testing admin hash...")
for pwd in passwords_to_try:
    try:
        result = bcrypt.checkpw(pwd.encode('utf-8'), admin_hash.encode('utf-8'))
        print(f'Password "{pwd}": {result}')
        if result:
            print(f'FOUND ADMIN PASSWORD: {pwd}')
            break
    except Exception as e:
        print(f'Error testing "{pwd}": {e}')

print()
print("Testing user hash...")
for pwd in passwords_to_try:
    try:
        result = bcrypt.checkpw(pwd.encode('utf-8'), user_hash.encode('utf-8'))
        print(f'Password "{pwd}": {result}')
        if result:
            print(f'FOUND USER PASSWORD: {pwd}')
            break
    except Exception as e:
        print(f'Error testing "{pwd}": {e}')