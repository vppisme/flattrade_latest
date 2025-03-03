import pyotp

def get_totp_code(totp_key):
    totp = pyotp.TOTP(totp_key)
    # print(totp.now())
    return totp.now()
