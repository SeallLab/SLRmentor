import hmac
import secrets
import hashlib
# import os
# from dotenv import load_dotenv
# from flask_bcrypt import Bcrypt

# load_dotenv()

# EMAIL_HASH_KEY = os.getenv("EMAIL_HASH_KEY").encode()
# bcrypt = Bcrypt()

def generate_hash(hash_length_bytes: int, hash_length_str: int) -> str:
    """Returns a random hash with specifed length param"""
    random_bytes = secrets.token_bytes(hash_length_bytes)
    hash = hashlib.sha256(random_bytes).hexdigest()
    
    if len(hash) <= hash_length_str:
        return hash
    else:
        return hash[:hash_length_str]

# def encrypt_text(text: str, encryption_key: str) -> str:
#     """Return an encrypted version of the text using the ecryption key"""
#     return -1

# def decrypt_text(text: str, encryption_key: str) -> str:
#     """Return an decrypted version of the text using the ecryption key"""

#     return -1
