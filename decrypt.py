import base64
import hashlib
import time


def think_decrypt(data, key):
    data = data + '=' * (4 - len(data) % 4)
    data = base64.urlsafe_b64decode(data.encode())
    expire = int(data[0:10])
    if 0 < expire < int(time.time()):
        return ''
    m = hashlib.md5()
    m.update(key.encode())
    key = m.hexdigest()
    data = data[10:]
    ld = len(data)
    l = len(key)
    char = s = ''
    x = 0
    for i in range(0, ld):
        if x == l:
            x = 0
        char += key[x]
        x += 1
    char = char.encode()
    for i in range(0, ld):
        if data[i] < char[i]:
            s += chr(data[i] + 256 - char[i])
        else:
            s += chr(data[i] - char[i])
    s = s + '=' * (4 - len(s) % 4)
    return base64.b64decode(s.encode()).decode()
