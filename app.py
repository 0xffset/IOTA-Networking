import json
from uuid import uuid4
from tangle import Tangle
from cryptographics import encrypt_file_asymmetric, decrypt_file_asymmetric, get_hash_file
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request, render_template, flash
from flask_toastr import Toastr
from forms import *
import os

app = Flask(__name__)
app.secret_key = '9omdDUxxFM'
app.config['SESSION_TYPE'] = 'filesystem'
toastr = Toastr()
# initialize toastr on the app within create_app()
toastr.init_app(app)


node_identifier = str(uuid4()).replace('-','')

# Se initializa el Blockchain
tangle = Tangle()

@app.route('/')
def index():
	return render_template('pages/index.html')

@app.route('/about')
def about():
	return render_template('pages/about.html')
	
@app.route('/register')
def register():
	form = RegisterForm(request.form)
	return render_template('forms/register.html', form=form)

@app.route('/login')
def login():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)

@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)


@app.route('/transactions/new', methods=['GET'])
def transaction():
	form = Transaction(request.form)
	return render_template('forms/transaction.html', form=form)



@app.route('/transaction/decrypt', methods=['GET', 'POST'])
def decrypt_file():
    form = DecryptFile(request.form)
    if request.method == 'POST':
       # Se verifica que el signature no este vacío
        signature = request.form['signature']
        if signature == '':
            flash("Se debe ingresar un signature válido", "error")
            return render_template('forms/decrypt_file.html', form=form)
        else:
            response = {
			'tangle': tangle.nodes,
			'length': len(tangle.nodes)
			}
            file_extension = ''
            file_path = ''
            for nodo in tangle.nodes:
                if (nodo['data'] is not None and nodo['data']['signature'] == signature):
                    file_extension = nodo['data']['extension']
                    file_path = nodo['data']['file']
               # if 'data' in nodo and 'signature' in nodo.data and nodo.data['signature'] == signature:
               #     file_extension = nodo['data']['extension']
               #     file_path = nodo['data']['file']
               #     break 
            if (file_extension == '' or file_path == ''):
                flash("Se debe ingresar un signature válido", "error")
                return render_template('forms/decrypt_file.html', form=form)
            else:
                path_file_decrypted = decrypt_file_asymmetric(file_path, file_extension)
                return render_template('forms/decrypt_file.html', response=path_file_decrypted, form=form)
                        
    elif request.method == 'GET':
        form = DecryptFile(request.form)
        return render_template('forms/decrypt_file.html', form=form)
       
    else:
        flash("Error al desencriptar el archivo", "error")
        return render_template('forms/decrypt_file.html', form=form)
            
        

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	# Actualiza tangle
	tangle.resolve_conflicts
	# Inicial la  transacción
	values = {
		'sender': request.form['sender'],
		'recipient': request.form['recipient'],
		'file': request.files['file']
	}

	# Se verifican que los campos requeridos esten en la data de POST
	required = ['sender', 'recipient', 'file']
	if  all(k in values.keys() for k in required) and not all(values.values()):
		return 'Faltan campos', 400

	# Encripta el archivo enviado
	file = request.files['file'].read()
	# Obtener la extensión del archivo enviado
	file_extension = "."+request.files['file'].filename.split('.')[1]
	values['extension'] = file_extension
 	# Obtiene el SHA-256 para la firma del archivo que se quiere agregar. (Esto podría ser de utilidad si en la red se requiere verificar un archivo en ella, en ese sentido, solo se verificaria su firma).
	encrypted_file_path = ""
	try:
		encrypted_file_path = encrypt_file_asymmetric(file)
		print(encrypted_file_path)
	except Exception as e:
		flash(f"Error a encriptar el archivo. Es posible que el archivo sea muy pesado.", 'error')
		return render_template('pages/index.html')

	sha256_signature = get_hash_file(encrypted_file_path)

	values['signature'] = sha256_signature
	values['file'] = encrypted_file_path

	# Crea una nueva transacción
	index = tangle.send_transaction(values)

	response = {'message': 'Transacción agregada al bloque: ' + str(index)}
	# Le dice a los nodos que se actualicen. 
	for peer in tangle.peers:
		requests.get(f"http://{peer}/peers/resolve")
	flash(f"La nueva transacción fue agregada satisfactoriamente al a red tangle. Transacción agregada al bloque: {index}", 'success')
	return render_template('pages/index.html')

@app.route('/tangle', methods=['GET'])
def full_chain():
	response = {
		'tangle': tangle.nodes,
		'length': len(tangle.nodes)
	}
	print(response)
	return render_template('pages/tangle.html', json_data=response)
	#return jsonify(response), 200

@app.route('/peers/add', methods=['POST', 'GET'])
def add_peers():
    if request.method == 'POST':
        values = request.form['peers']
        print(values)
        peers = None
        if  values == "":
           # print(json.loads(values))
           # peers = json.parse(values)['peers']
           peers = request.form['peers']
        else:
            peers = request.form['peers']
            if peers is None:
                flash("Error: Please supply a valid list of nodes", 'Error')
                return "Error: Please supply a valid list of nodes", 400
            tangle.register_peer(peers)
            response = {
				'message': 'New peers have been added',
				'total_nodes': list(tangle.peers)
			}
            flash("El nuevo peer fue agregado satisfactoriamente al a red tangle.", 'Enhorabuena!')
            return render_template('pages/peers.html', json_data=response['total_nodes']), 200
        flash("El peer no fue agregado", 'Error!')
        return render_template('pages/index.html'), 301
    
    elif request.method == 'GET':
        form = Peers(request.form)
        return render_template('forms/add_peer.html', form=form)
    else:
        return render_template('pages/index.html')
    


@app.route('/peers/resolve', methods=['GET'])
def get_peers_resolve():
	replaced = tangle.resolve_conflicts()

	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': tangle.nodes
		}
	else:
		response = {
		'message': 'Our chain is authoritative',
		'chain': tangle.nodes
		}
	return render_template('pages/peers_resolve.html', json_data=response)
	#return jsonify(response), 200

@app.route('/peers', methods=['GET'])
def get_peers():
	response = {
		'know_peers': list(tangle.peers)
	}
	print(response)
	return render_template('pages/peers.html', json_data=response)
	#return jsonify(response), 201

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5001)