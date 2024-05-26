import rsa
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

def verify_key_validity(public_key):
    pass

def rsa_encrypt_message(message, public_key):
    try:
        return rsa.encrypt(message.encode("utf-8"), public_key)
    except Exception as error:
        print(f"encryption error: {str(error)}")
        return
    
def rsa_decrypt_message(message, private_key):
    try:
        return rsa.decrypt(message, private_key).decode("utf-8")
    except Exception as error:
        print(f"decryption error: {str(error)}")
        return

def hash_data(data):
    pass