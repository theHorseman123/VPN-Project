from cryptography.fernet import Fernet
import base64
import hashlib

# Define the password
password = "secret-horsem4n-NMEX123"

# Derive a key from the password using SHA-256 hash function
key = hashlib.sha256(password.encode()).digest()

# Ensure the key length is 32 bytes for Fernet
key = base64.urlsafe_b64encode(key[:32])

# Create a Fernet object using the derived key
fernet = Fernet(key)

# Retrieve the key from the Fernet object
print(fernet._encryption_key)
print(fernet._signing_key)
retrieved_key = fernet._signing_key + fernet._encryption_key

# Display the retrieved symmetric key
print("Retrieved Symmetric Key:", base64.urlsafe_b64encode(retrieved_key).decode())


Fernet(b"blah")
