from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend
import os
import secrets
import hashlib




# Genera un par de claves asimétricas
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
    backend=default_backend()
)
public_key = private_key.public_key()


DIRECTORY = os.path.dirname(__file__) + '/store'
# Se verifica la existencia del directorio. Si no existe, se crear. 
if not os.path.exists('store'):
	os.makedirs('store')


"""Función que encripta el archivo enviar en la transacción y lo guarda en un directorio 

Keyword arguments: data
data -- Recibe el byte-stream del archivo enviado a encriptar.
Return: Retorna a dirección donde se almacenó el archivo encriptado.
"""

def encrypt_file_asymmetric(data):
	cipher_text = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
            )
        )
	encrypted_filename = f'{DIRECTORY}/encrypted_{secrets.token_hex(8)}.bin'
	with open(encrypted_filename, 'wb') as encrypted_file:
		encrypted_file.write(cipher_text)
	return encrypted_filename

""" Desencripta el archivo encriptado un archivo encriptado y lo guarda en un directorio. 

Keyword arguments: data
data -- Recibe el los bytes a desencriptar.
Return: Any
"""

def decrypt_file_asymmetric(file_path, file_extension):
    # Buscarmos el archivo por su signature
    ifile=open(file_path, 'rb');
    data  = ifile.read()
    plain_text = private_key.decrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    decrypted_filename = f'{DIRECTORY}/decrypted_{secrets.token_hex(8)}{file_extension}'
    with open(decrypted_filename, 'wb') as decrypted_file:
        decrypted_file.write(plain_text)
    return decrypted_filename


"""Funcion que recibe la el archivo y lo almacena devuelve una hash sha-256 como la firma de este archivo.

Keyword arguments: file_path
file_path -- Dirección del archivo.
Return: Retorna la un hash sha256 asociado a la firma de este archivo. 
"""

def get_hash_file(file_path):
	return hashlib.sha256(file_path.encode('utf-8')).hexdigest()