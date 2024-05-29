import rsa
from cryptography.fernet import Fernet
import base64
import hashlib
import os

def generate_keys(SIZE, PATH):
    # if one of the keys is missing, generate new ones
        if os.path.isfile(f"./{PATH}/private.pem") and os.path.isfile(f"./{PATH}/public.pem"):
            # TODO: write a key check to see if the encryption key is valid

            with open(f"{PATH}/public.pem", "rb") as f:
                public_key = rsa.PublicKey.load_pkcs1(f.read())

            with open(f"{PATH}/private.pem", "rb") as f:
                private_key = rsa.PrivateKey.load_pkcs1(f.read())
        else:

            public_key, private_key = rsa.newkeys(SIZE)

            with open(f"{PATH}/public.pem", "wb") as f:
                f.write(public_key.save_pkcs1("PEM"))

            with open(f"{PATH}/private.pem", "wb") as f:
                f.write(private_key.save_pkcs1("PEM"))
        
        return public_key, private_key

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
    return rsa.encrypt(message.encode("utf-8"), public_key)
    
def rsa_decrypt_message(message, private_key):
    return rsa.decrypt(message, private_key).decode("utf-8")



def hash_data(data):
    pass