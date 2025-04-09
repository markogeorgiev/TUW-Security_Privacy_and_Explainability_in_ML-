#!/usr/bin/env python3

import base64
import binascii
import json
import random
import re
import string
import sys
from datetime import date, datetime
from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA3_256
from Cryptodome.Util.Padding import pad, unpad


def die(message):
    print(message)
    sys.exit(1)


def read_string(prompt, minlength=1, maxlength=1024):
    while True:
        s = input(prompt + ': ').strip()
        if minlength <= len(s) <= maxlength:
            return s
        if len(s) == 0:
            print('Please enter a non-empty string.')
        else:
            print(f'Please enter a string with at least {minlength} and at most {maxlength} characters.')


def read_date(prompt):
    while True:
        try:
            s = input(prompt + ' (format dd/mm/yyyy): ').strip()
            d = datetime.strptime(s, '%d/%m/%Y').date()
            if d >= date.today():
                return d
            print('The date cannot be in the past.')
        except ValueError:
            print('Please enter a valid date using the format dd/mm/yyyy.')


def read_redeem_code(prompt):
    while True:
        code = input(prompt + ': ').strip()
        if re.match(r'\d{17}$', code) is not None:
            return code
        print('Invalid redeem code provided.')


def print_start_message():
    print('Welcome to CryptoNotes, the platform to store encrypted notes, access them from any device '
          'and share them securely with your friends.')
    print('CryptoNotes is still under development. Please report eventual bugs.')


def print_menu_guests():
    while True:
        try:
            print('\nChoose from the following options:')
            print('1. Create a new account')
            print('2. Login')
            print('3. Quit')
            choice = int(input('Enter your choice: '))
            if 1 <= choice <= 3:
                return choice
            print('Invalid choice. Please try again.')
        except ValueError:
            print('Invalid choice. Please try again.')


def load_user_tokens_key():
    with open('./service/user_tokens_key.bin', 'rb') as f:
        return f.read()


def load_access_tokens_key():
    with open('./service/access_tokens_key.bin', 'rb') as f:
        return f.read()


def generate_user_token(user, debug=True):
    json_user = json.dumps(user)
    if debug:
        print(f'Encrypting the following data: {json_user}')
    key = load_user_tokens_key()
    cipher = AES.new(key, AES.MODE_CTR)
    encrypted_user_data = cipher.nonce + cipher.encrypt(json_user.encode())
    user_token = base64.b64encode(encrypted_user_data).decode()
    return user_token


def create_account():
    user = {'admin': 0}
    user['nickname'] = read_string('Enter your nickname')
    user['password'] = read_string('Enter your password (at least 8 characters)', 8)
    user_token = generate_user_token(user)
    print(f'Here is your user token needed for the login: {user_token}')


def parse_user_token(user_token, debug=True):
    try:
        encrypted_user_data = base64.b64decode(user_token)
        key = load_user_tokens_key()
        cipher = AES.new(key, AES.MODE_CTR, nonce=encrypted_user_data[:8])
        user_data = cipher.decrypt(encrypted_user_data[8:]).decode()
        if debug:
            print(f'Decrypted user token: {user_data}')
        user = json.loads(user_data)
        if any(k not in user for k in ('nickname', 'password', 'admin')):
            die('Corrupted user token. Terminating.')
        return user
    except (json.JSONDecodeError, UnicodeDecodeError, binascii.Error):
        die('Corrupted user token. Terminating.')


def login_user():
    user_token = read_string('Enter your user token')
    password = read_string('Enter your password')

    user = parse_user_token(user_token)
    if user['password'] != password:
        print('Incorrect password.')
        return None
    print(f'Welcome {user["nickname"]}!')
    return user


def print_menu_users():
    while True:
        try:
            print('\nChoose from the following options:')
            print('1. Create a new note')
            print('2. Access a note via access token')
            print('3. Print your profile')
            print('4. Inspect an access token (only for admins)')
            print('5. Quit')
            choice = int(input('Enter your choice: '))
            if 1 <= choice <= 5:
                return choice
            print('Invalid choice. Please try again.')
        except ValueError:
            print('Invalid choice. Please try again.')


def derive_note_encryption_key(redeem_code):
    prev_hash = redeem_code.encode()
    for _ in range(100_000):
        h = SHA3_256.new(prev_hash)
        prev_hash = h.digest()
    return prev_hash


def store_message(f, note, redeem_code):
    key = derive_note_encryption_key(redeem_code)
    cipher = AES.new(key, AES.MODE_CBC)
    f.write(cipher.iv + cipher.encrypt(pad(note.encode(), AES.block_size)))
    f.close()


def retrieve_message(note_id, redeem_code):
    key = derive_note_encryption_key(redeem_code)
    try:
        with open(f'./notes/{note_id}.bin', 'rb') as f:
            encrypted_msg = f.read()
    except FileNotFoundError:
        die('There is no note with the provided id.')
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=encrypted_msg[:16])
        return unpad(cipher.decrypt(encrypted_msg[16:]), AES.block_size).decode()
    except ValueError:
        die('Decryption failed. Probably the false decryption key was used.')


def generate_access_token(key, note_id, expiry_date, redeem_code):
    access_token_content = note_id + expiry_date.strftime('%d%m%Y') + redeem_code
    cipher = AES.new(key, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(access_token_content.encode())).decode()


def decrypt_access_token(key, access_token):
    cipher = AES.new(key, AES.MODE_ECB)
    try:
        dec_token = cipher.decrypt(base64.b64decode(access_token)).decode()
        if len(dec_token) != 32:
            die('Corrupted access token. Terminating.')
        return dec_token
    except (binascii.Error, UnicodeDecodeError, ValueError):
        die('Corrupted access token. Terminating.')


def create_note():
    note = read_string('Enter your note (max 1024 characters)', maxlength=1024)

    attempts = 0
    found_name = False
    note_id = ''
    f = None
    while not found_name and attempts < 1024:
        note_id = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
        try:
            f = open(f'./notes/{note_id}.bin', 'xb')
            found_name = True
        except FileExistsError:
            attempts += 1

    if not found_name:
        die('We cannot generate a unique ID for your note. Please try again later.')

    print(f'Your note has been created with ID: {note_id}')
    print('Now we create an access token to retrieve the contents of the note.')
    redeem_code = read_redeem_code('Provide a 17 digits code which can be used to redeem the token')
    expiry_date = read_date('Provide the expiry date of the token')
    access_token = generate_access_token(load_access_tokens_key(), note_id, expiry_date, redeem_code)
    store_message(f, note, redeem_code)

    print(f'Here is the access token: {access_token}')
    print('Share it with your friends together with the redeem code to grant them access to your note.')


def redeem_access_token():
    access_token = read_string('Provide the access token for the note you want to access')
    dec_access_token = decrypt_access_token(load_access_tokens_key(), access_token)

    attempts = 0
    correct_code = False
    while not correct_code and attempts < 100:
        redeem_code = read_redeem_code('Provide the 17 digits redeem code')
        if redeem_code != dec_access_token[15:32]:
            print('Incorrect redeem code. Please try again.')
            attempts += 1
        else:
            correct_code = True

    if not correct_code:
        die('Too many false attempts. Terminating.')

    note_id = dec_access_token[:7]
    expire_date = datetime.strptime(dec_access_token[7:15], '%d%m%Y').date()
    if date.today() <= expire_date:
        print('Here is the note:')
        print(retrieve_message(note_id, dec_access_token[15:32]))
    else:
        print('The access token is expired.')


def print_profile(user):
    print(f'User: {user["nickname"]}')
    print(f'Admin: {bool(user["admin"])}')


def inspect_access_token():
    access_token = read_string('Provide the access token you want to inspect')
    dec_access_token = decrypt_access_token(load_access_tokens_key(), access_token)
    print(f'Note ID: ' + dec_access_token[:7])
    date_part = dec_access_token[7:15]
    try:
        expire_date = datetime.strptime(date_part, '%d%m%Y').date()
        print(f'Expire date: {expire_date.strftime('%d/%m/%Y')}')
    except ValueError:
        print('Failure parsing the date ' + date_part)


def main():
    logged_in_user = None
    exit_program = False

    print_start_message()
    while not exit_program:
        if logged_in_user is None:
            choice = print_menu_guests()
            if choice == 1:
                create_account()
            elif choice == 2:
                logged_in_user = login_user()
            else:
                exit_program = True
        else:
            choice = print_menu_users()
            if choice == 1:
                create_note()
            elif choice == 2:
                redeem_access_token()
            elif choice == 3:
                print_profile(logged_in_user)
            elif choice == 4:
                if logged_in_user['admin']:
                    inspect_access_token()
                else:
                    print('Operation forbidden. You are not an administrator.')
            else:
                exit_program = True


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
