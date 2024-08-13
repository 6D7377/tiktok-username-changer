# coding:utf-8
import hashlib
import json
from time import time
from hashlib import md5
from copy import deepcopy
from random import choice
import requests
import random
from urllib.parse import quote

def file_data(path):
    """Read binary data from file."""
    with open(path, "rb") as f:
        return f.read()

def hex_string(num):
    """Convert a number to a two-character hexadecimal string."""
    return f"{num:02x}"

def reverse(num):
    """Reverse the hex representation of a number."""
    tmp_string = hex(num)[2:].zfill(2)
    return int(tmp_string[::-1], 16)

def RBIT(num):
    """Reverse the bits of a byte."""
    return int(f"{num:08b}"[::-1], 2)

class XG:
    def __init__(self, debug):
        self.length = 0x14
        self.debug = debug
        self.hex_CE0 = [
            0x05,
            0x00,
            0x50,
            choice(range(0xFF)),
            0x47,
            0x1E,
            0x00,
            8 * choice(range(0x1F)),
        ]

    def addr_BA8(self):
        """Generate hex_BA8 array."""
        hex_BA8 = list(range(0x100))
        tmp = ""
        for i in range(0x100):
            if i == 0:
                A = 0
            elif tmp:
                A = tmp
            else:
                A = hex_BA8[i - 1]

            B = self.hex_CE0[i % 0x8]
            if A == 0x05 and i != 1 and tmp != 0x05:
                A = 0

            C = (A + i + B) % 0x100
            if C < i:
                tmp = C
            else:
                tmp = ""

            hex_BA8[i] = hex_BA8[C]
        return hex_BA8

    def initial(self, debug, hex_BA8):
        """Initialize debug array."""
        tmp_add = []
        tmp_hex = deepcopy(hex_BA8)
        for i in range(self.length):
            A = debug[i]
            B = tmp_add[-1] if tmp_add else 0
            C = (hex_BA8[i + 1] + B) % 0x100
            tmp_add.append(C)
            D = tmp_hex[C]
            tmp_hex[i + 1] = D
            E = (D + D) % 0x100
            F = tmp_hex[E]
            G = A ^ F
            debug[i] = G
        return debug

    def calculate(self, debug):
        """Calculate final debug values."""
        for i in range(self.length):
            A = debug[i]
            B = reverse(A)
            C = debug[(i + 1) % self.length]
            D = B ^ C
            E = RBIT(D)
            F = E ^ self.length
            G = (~F + 0x100000000) % 0x100000000
            debug[i] = int(hex(G)[-2:], 16)
        return debug

    def main(self):
        """Generate the X-Gorgon header."""
        result = "".join(hex_string(item) for item in self.calculate(self.initial(self.debug, self.addr_BA8())))
        return f"8402{hex_string(self.hex_CE0[7])}{hex_string(self.hex_CE0[3])}{hex_string(self.hex_CE0[1])}{hex_string(self.hex_CE0[6])}{result}"

def getxg(param="", stub="", cookie=""):
    """Generate X-Gorgon and X-Khronos headers based on parameters."""
    gorgon = [int(md5(param.encode()).hexdigest()[2 * i:2 * i + 2], 16) for i in range(4)]
    gorgon += [int(stub[2 * i:2 * i + 2], 16) for i in range(4)] if stub else [0x0] * 4
    gorgon += [int(md5(cookie.encode()).hexdigest()[2 * i:2 * i + 2], 16) for i in range(4)] if cookie else [0x0] * 4
    gorgon += [0x0, 0x8, 0x10, 0x9]

    khronos = hex(int(time()))[2:].zfill(8)
    gorgon += [int(khronos[2 * i:2 * i + 2], 16) for i in range(4)]

    xg = XG(gorgon)
    return {"X-Gorgon": xg.main(), "X-Khronos": str(int(time()))}

def get_stub(data):
    """Generate MD5 hash of data."""
    if isinstance(data, (dict, str)):
        data = json.dumps(data) if isinstance(data, dict) else data
        data = data.encode('utf-8') if isinstance(data, str) else data
    return hashlib.md5(data).hexdigest().upper() if data else "00000000000000000000000000000000"

def getxg_m(param, data):
    """Generate X-Gorgon and X-Khronos headers for modified requests."""
    return getxg(param, hashlib.md5(data.encode()).hexdigest() if data else None, None)

def get_profile(session_id, device_id, iid):
    """Retrieve TikTok profile for given session."""
    try:
        parm = f"device_id={device_id}&iid={iid}&id=kaa&version_code=34.0.0&language=en&app_name=lite&app_version=34.0.0&carrier_region=SA&tz_offset=10800&mcc_mnc=42001&locale=en&sys_region=SA&aid=473824&screen_width=1284&os_api=18&ac=WIFI&os_version=17.3&app_language=en&tz_name=Asia/Riyadh&carrier_region1=SA&build_number=340002&device_platform=iphone&device_type=iPhone13,4"
        sig = getxg_m(parm, None)
        url = f"https://api16.tiktokv.com/aweme/v1/user/profile/self/?{parm}"
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": f"sessionid={session_id}",
            "sdk-version": "2",
            "user-agent": "com.zhiliaoapp.musically/432424234 (Linux; U; Android 5; en; fewfwdw; Build/PI;tt-ok/3.12.13.1)",
            "X-Gorgon": sig["X-Gorgon"],
            "X-Khronos": sig["X-Khronos"],
        }
        response = requests.get(url, headers=headers, cookies={"sessionid": session_id})
        return response.json().get("user", {}).get("unique_id", "None")
    except Exception:
        return "None"

def get_profile_us(session_id, device_id, iid):
    """Retrieve TikTok profile (US version)."""
    try:
        parm = f"device_id={device_id}&iid={iid}&id=kaa&version_code=34.0.0&language=en&app_name=lite&app_version=34.0.0&carrier_region=SA&tz_offset=10800&mcc_mnc=42001&locale=en&sys_region=SA&aid=473824&screen_width=1284&os_api=18&ac=WIFI&os_version=17.3&app_language=en&tz_name=Asia/Riyadh&carrier_region1=SA&build_number=340002&device_platform=iphone&device_type=iPhone13,4"
        sig = getxg_m(parm, None)
        url = f"https://api16-normal-quic-useast2a.tiktokv.com/aweme/v1/user/profile/self/?{parm}"
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": f"sessionid={session_id}",
            "sdk-version": "2",
            "user-agent": "com.zhiliaoapp.musically/432424234 (Linux; U; Android 5; en; fewfwdw; Build/PI;tt-ok/3.12.13.1)",
            "X-Gorgon": sig["X-Gorgon"],
            "X-Khronos": sig["X-Khronos"],
        }
        response = requests.get(url, headers=headers, cookies={"sessionid": session_id})
        return response.json().get("user", {}).get("unique_id", "None")
    except Exception:
        return "None"

def check_is_changed(last_username, session_id, device_id, iid):
    """Check if username has changed in TikTok profile."""
    return get_profile(session_id, device_id, iid) != last_username

def check_is_changed_us(last_username, session_id, device_id, iid):
    """Check if username has changed in TikTok profile (US version)."""
    return get_profile_us(session_id, device_id, iid) != last_username

def change_username(session_id, device_id, iid, last_username, new_username):
    """Attempt to change TikTok username."""
    data = f"unique_id={quote(new_username)}"
    parm = (f"device_id={device_id}&iid={iid}&residence=SA&version_name=1.1.0&os_version=17.4.1"
            "&app_name=tiktok_snail&locale=en&ac=4G&sys_region=SA&version_code=1.1.0&channel=App%20Store"
            "&op_region=SA&os_api=18&device_brand=iphone&idfv={iid}-1ED5-4350-9318-77A1469C0B89"
            "&device_platform=iphone&device_type=iPhone13,4&carrier_region1=&tz_name=Asia/Riyadh"
            "&account_region=eg&build_number=11005&tz_offset=10800&app_language=en&carrier_region="
            "&current_region=&aid=364225&mcc_mnc=&screen_width=1284&uoo=1&content_language=&language=en"
            "&cdid={iid}&openudid={iid}&app_version=1.1.0&scene_id=830")
    sig = getxg_m(parm, data)
    url = f"https://api16.tiktokv.com/aweme/v1/commit/user/?{parm}"
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"sessionid={session_id}",
        "sdk-version": "2",
        "user-agent": f"com.zhiliaoapp.musically/{device_id} (Linux; U; Android 5; en; {iid}; Build/PI;tt-ok/3.12.13.1)",
        "X-Gorgon": sig["X-Gorgon"],
        "X-Khronos": sig["X-Khronos"],
    }
    response = requests.post(url, data=data, headers=headers)
    result = response.text
    if "unique_id" in result and check_is_changed(last_username, session_id, device_id, iid):
        return "Username change successful."
    else:
        return f"Failed to change username: {result}"

def change_username_us(session_id, device_id, iid, last_username, new_username):
    """Attempt to change TikTok username (US version)."""
    data = f"unique_id={quote(new_username)}&device_id={device_id}"
    parm = (f"aid=364225&sdk_version=1012000&refresh_num=11&version_code=30.0.0&language=en-SA"
            "&display_density=1284*2778&device_id=12345678910&channel=AppStore&click_banner=32&mcc_mnc=42001"
            "&show_limit=0&resolution=1284*2778&aid=1233&version_name=9.1.1&os=ios&update_version_code=91115"
            "&access=WIFI&carrier=stc&ac=WIFI&os_version=17.3&is_cold_start=0&reason=0&device_platform=iphone"
            "&device_brand=AppleInc.&device_type=iPhone13,4")
    sig = getxg_m(parm, data)
    url = f"https://api16-normal-quic-useast2a.tiktokv.com/aweme/v1/commit/user/?{parm}"
    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"sessionid={session_id}",
        "sdk-version": "2",
        "user-agent": f"com.zhiliaoapp.musically/{device_id} (Linux; U; Android 5; en; {iid}; Build/PI;tt-ok/3.12.13.1)",
        "X-Gorgon": sig["X-Gorgon"],
        "X-Khronos": sig["X-Khronos"],
    }
    response = requests.post(url, data=data, headers=headers)
    result = response.text
    if "unique_id" in result and check_is_changed_us(last_username, session_id, device_id, iid):
        return "Username change successful."
    else:
        return f"Failed to change username: {result}"

def main():
    """Main function to handle user interaction and username change."""
    device_id = str(random.randint(777777788, 999999999999))
    iid = str(random.randint(777777788, 999999999999))
    session_id = input("Введіть sessionid: ")

    user = get_profile(session_id, device_id, iid)
    if user != "None":
        print(f"Your current TikTok username is: {user}")
        new_username = input("Введіть нікнейм на який хочете змінити: ")
        print(change_username(session_id, device_id, iid, user, new_username))
    else:
        user_us = get_profile_us(session_id, device_id, iid)
        if user_us != "None":
            print(f"Your current TikTok username is: {user_us}")
            new_username = input("Enter the new username you wish to set: ")
            print(change_username_us(session_id, device_id, iid, user_us, new_username))
        else:
            print("Invalid session ID or other error.")
    print("Більше хаків тут: t.me/cybersociety")

if __name__ == "__main__":
    main()
