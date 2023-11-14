import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from tangle import Tangle
from cryptographic import encrypt_file_asymetric, decrypt_file_asymetric, get_hash_file
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request, render_template
from forms import *

app = Flask(__name__)
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

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
	# update tangle
	tangle.resolve_conflicts
	# begin transaction
	values = {
		'sender': request.form['sender'],
		'recipient': request.form['recipient'],
		'amount': request.form['amount'],
		'file': request.files['file']
	}
	print(values)

	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'amount', 'file']
	if  all(k in values.keys() for k in required) and not all(values.values()):
		return 'Missing values', 400

	# Encrypt the file sender
	file = request.files['file'].read()
	# Get the SHA-256 file signature 
	encrypted_file_path = encrypt_file_asymetric(file)
	sha256_signature = get_hash_file(encrypted_file_path)

	values['signature'] = sha256_signature
	values['file'] = encrypted_file_path

	# Create a new Transaction
	index = tangle.send_transaction(values)

	response = {'message': 'Transaction will added to Block' + str(index)}
	# tell peers to update tangle
	for peer in tangle.peers:
		requests.get(f"http://{peer}/peers/resolve")

	return jsonify(response), 201

@app.route('/tangle', methods=['GET'])
def full_chain():
	response = {
		'tangle': tangle.nodes,
		'length': len(tangle.nodes)
	}
	return jsonify(response), 200



# Consesus
@app.route('/peers/register', methods=['POST'])
def register_nodes():
	values = request.get_json()
	peers = None
	if type("") == type(values):
		print(json.loads(values))
		peers = json.loads(values)['peers']
	else:
		peers = values.get('peers')
	if peers is None:
		return "Error: Please supply a valid list of nodes", 400

	for peer in peers:
		tangle.register_peer(peer)

	response = {
		'message': 'New peers have been added',
		'total_nodes': list(tangle.peers)
	}

	return jsonify(response), 201

@app.route('/peers/resolve', methods=['GET'])
def consensus():
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
	return jsonify(response), 200

@app.route('/peers', methods=['GET'])
def list_peers():
	response = {
		'know_peers': list(tangle.peers)
	}
	return jsonify(response), 201

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5001)