import json
from uuid import uuid4
from tangle import Tangle
from cryptographics import encrypt_file_asymmetric, decrypt_file_asymmetric, get_hash_file
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request, render_template, flash
from flask_toastr import Toastr
from forms import *

app = Flask(__name__)
app.secret_key = '9omdDUxxFM'
app.config['SESSION_TYPE'] = 'filesystem'
toastr = Toastr()
# initialize toastr on the app within create_app()
toastr.init_app(app)


node_identifier = str(uuid4()).replace('-','')

# Initialize the Blockchain
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


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	# update tangle
	tangle.resolve_conflicts
	# begin transaction
	values = {
		'sender': request.form['sender'],
		'recipient': request.form['recipient'],
		'file': request.files['file']
	}
	print(values)

	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'file']
	if  all(k in values.keys() for k in required) and not all(values.values()):
		return 'Missing values', 400

	# Encrypt the file sender
	file = request.files['file'].read()
	# Get the SHA-256 file signature 
	encrypted_file_path = encrypt_file_asymmetric(file)
	sha256_signature = get_hash_file(encrypted_file_path)

	values['signature'] = sha256_signature
	values['file'] = encrypted_file_path

	# Create a new Transaction
	index = tangle.send_transaction(values)

	response = {'message': 'Transaction will added to Block' + str(index)}
	# tell peers to update tangle
	for peer in tangle.peers:
		requests.get(f"http://{peer}/peers/resolve")
	flash("La nueva transacción fue agregada satisfactoriamente al a red tangle.", 'success')
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