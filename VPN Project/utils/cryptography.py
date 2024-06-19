import rsa
from cryptography.fernet import Fernet
import base64
import hashlib
import os

def generate_keys(SIZE):
    # if one of the keys is missing, generate new ones
        if os.path.isfile(f"./private.pem") and os.path.isfile(f"./public.pem"):
            # TODO: write a key check to see if the encryption key is valid

            with open(f"public.pem", "rb") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read())

            with open(f"private.pem", "rb") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read())
        else:

            public_key, private_key = rsa.newkeys(SIZE)

            with open(f"public.pem", "wb") as f:
                f.write(public_key.save_pkcs1("PEM"))

            with open(f"private.pem", "wb") as f:
                f.write(private_key.save_pkcs1("PEM"))
        
        return public_key, private_key

def generate_base64(SIZE):
    random_bytes = os.urandom(SIZE)
    base64_encoded_bytes = base64.b64encode(random_bytes)
    return base64_encoded_bytes

def generate_random_base64(length: int) -> str:
    # Generate random bytes
    random_bytes = os.urandom(length)
    # Encode the bytes to base64
    base64_encoded = base64.b64encode(random_bytes).decode('utf-8')
    return base64_encoded

def aes_generate_key(passkey=None):
    if passkey:
        # Derive a key from the password using SHA-256 hash function
        key = hashlib.sha256(passkey.encode()).digest()

            # Ensure the key length is 32 bytes for Fernet
        key = base64.urlsafe_b64encode(key[:32])

        return Fernet(key)
    
    return Fernet(Fernet.generate_key())
 
def aes_retreive_key(fernet:Fernet):
    retrieved_key = fernet._signing_key + fernet._encryption_key
    return base64.urlsafe_b64encode(retrieved_key)


def verify_key_validity(public_key):
    pass

def rsa_encrypt_message(message, public_key):
    try:
        return rsa.encrypt(message.encode("utf-8"), public_key)
    except:
        return

def rsa_decrypt_message(message, private_key):
    try:
        return rsa.decrypt(message, private_key).decode("utf-8")
    except:
        return 


def hash_data(data):
    pass