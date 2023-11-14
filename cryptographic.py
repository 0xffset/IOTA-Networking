#from Crypto.Cipher import AES
#from Crypto.Util.Padding import pad, unpad
#from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend
import base64
import os
import secrets
import hashlib



# Genera una clave secreta segura
#def generate_secret_key():
#	return secrets.token_bytes(32); # 32 bytes para AES-256

#SECRET_KEY = generate_secret_key();


# Genera un par de claves asimétricas
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

public_key = private_key.public_key()


ENCRYPTED_DIR = './store'
DECRYPTED_DIR = './store'

if not os.path.exists('store'):
	os.makedirs('store')

os.makedirs(ENCRYPTED_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)




def encrypt_file_asymetric(data):
	cipher_text = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
            )
        )
	encrypted_filename = f'store/encrypted_{secrets.token_hex(8)}.bin'
	with open(encrypted_filename, 'wb') as encrypted_file:
		encrypted_file.write(cipher_text)
	return encrypted_filename

def decrypt_file_asymetric(data):
	# Descifra el archivo con la clave privada
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    decrypted_filename = f'store/decrypted_{secrets.token_hex(8)}.bin'
    with open(decrypted_filename, 'wb') as decrypted_file:
        decrypted_file.write(plaintext)




"""
Symetric

"""

"""
Encripta el archvio que se envia por la red Tangle
"""
def encrypt_file(file_path):
	cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
	with open(file_path, 'rb') as file:
		plaintext = file.read()
		ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
	
	encrypted_file_path = os.path.join(ENCRYPTED_DIR, f'encrypted_{secrets.token_hex(8)}.bin')
	with open(encrypted_file_path, 'wb') as encrypt_file:
		encrypted_file.write(ciphertext.iv + ciphertext)
	
	return encrypted_file_path
	#return cipher.iv + ciphertext

"""
Desencripta el archivo ya encriptado en la red tangle
"""
def decrypt_file(encrypted_data):
	iv = encrypted_data[:AES.block_size]
	ciphertext = encrypted_data[AES.block_size:]
	cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
	plaintext = unpad(cipher.decrypy(ciphertext), AES.block_size)
	
	decrypted_file_path = os.path.join(DECRYPTED_DIR, f'decrypted_{secrets.token_hex(0)}.bin')
	with open(decrypted_file_path, 'wb') as decrypy_file:
		decrypted_file_path.write(plaintext)
	return plaintext


def get_hash_file(file_path):
	return hashlib.sha256(file_path.encode('utf-8')).hexdigest()