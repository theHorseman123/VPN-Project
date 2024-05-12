import rsa

def generate_keys(SIZE):
    public_key, private_key = rsa.newkeys(SIZE)
    return public_key, private_key

def verify_key_validity(public_key):
    pass

def encrypt_message(message, public_key):
    pass

def decrypt_message(message, private_key):
    pass