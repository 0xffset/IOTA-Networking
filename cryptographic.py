from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import os
import secrets




# Genera una clave secreta segura
def generate_secret_key():
	return secrets.token_bytes(32); # 32 bytes para AES-256

SECRET_KEY = generate_secret_key();

ENCRYPTED_DIR = './store'
DECRYPTED_DIR = './store'

os.makedirs(ENCRYPTED_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)

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
