import props as properties
import json
from time import time
import hashlib
import requests
from urllib.parse import urlparse




"""
nodes in the dag are represented in json as folows
they can be transmitted across the network in this form and then can be
initialized in this form
        Node = {
            'index': "int value",
            'timestamp': time(),
            'data': "this is the transaction data that is being stored",
            'proof': "proof of work",
            'previous_hashs': "the hash of the previous 2 nodes that it is connected to",
            'previous_nodes': 'index values',
            'next_nodes': 'indexes of the nodes pointing to it',
            'validity': the number of times the node has been proven
        }

"""

class Tangle(object):
	"""docstring for Tangle"""
	def __init__(self):
		super(Tangle, self).__init__()
		self.nodes = []
		self.peers = set()
		# Create the genesis block
		for i in range(properties.REQUIRED_PROOF):
			self.nodes.append(self.create_node(None, [], len(self.nodes), 
			validity = properties.REQUIRED_PROOF))


	@staticmethod	
	def valid_proof(last_proof, last_hash, proof):
		# Ensures that the nodes has the correct number of zeros
		guess = (str(last_proof) + str(last_hash) + str(proof)).encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"

	def proof_of_work(self, last_proof, last_hash):
		# Compute the proof of work
		proof = 0
		while self.valid_proof(last_proof, last_hash, proof) is False:
			proof += 1
		return proof
		

	@staticmethod
	# Compute the hash
	def hash(node):
		# Make a hash of the block
		# We must make sure that the Dictionary is Ordered, or we will have inconsistent hashes
		node_string = json.dumps(node, sort_keys=True).encode()
		return hashlib.sha256(node_string).hexdigest()

	def validate_node(self, node):
		if self.nodes[node['index']]['validity'] < properties.REQUIRED_PROOF:
			last_proof = self.nodes[node['index']]['proof'] # This nodes proof
			last_hash = ""
			for prev_hash in self.nodes[nodes['index']]['previous_hash']:
				last_hash += prev_hash # the hashes of the nodes his node connects
			self.nodes[node['index']]['proof'] = self.proof_of_work(last_proof, last_hash)
			self.nodes[node['index']]['validity'] =+ 1

	
	""" Create a new node """
	def create_node(self, data, prev_nodes, new_index, validity=0): # These prev_nodes are the indexes in the dag the points to the
		prev_hashes = []
		'''
		many need to update every node that points to this when sendign trasaction
		'''

		for i in prev_nodes:
			prev_hashes.append(self.hash(self.nodes[i]))
			#Now we tell the nodes that we are pointing to that we are pointing to them
			self.nodes[i]['next_nodes'].append(new_index)

		Node = {
			'index': new_index,
			'timestamp': time(),
			'data': data,
			'proof': 0,
			'file': '',
			'previous_hashs': prev_hashes,
			'previous_nodes': prev_nodes,
			'next_nodes': [],
			'validity': validity,
		}
		return Node

	""" Send a transaction """
	def send_transaction(self, data):
		# Find 2 nodes in the network that are un proven
		node_to_attach = []
		nodes_indexes = []
		new_index = len(self.nodes)
		worst_cases_scinario = []
		worst_cases_scinario_indexes = []

		'''
		This function should be changed to search randomly
		'''

		for i in range(len(self.nodes)-1, -1, -1):
			node=self.nodes[i]
			if node['validity'] < properties.REQUIRED_PROOF:
				node_to_attach.append(node)
				nodes_indexes.append(node['index'])
			else:
				if worst_cases_scinario == [] or len(worst_cases_scinario) < properties.NUMBER_OF_VALIDATION_NODES:
					worst_cases_scinario.append(node)
					worst_cases_scinario_indexes.append(node['index'])
			if len(node_to_attach) == properties.NUMBER_OF_VALIDATION_NODES:
				break

		# If there are not enough varified transaction the use verfied transactions

		while len(node_to_attach) < properties.NUMBER_OF_VALIDATION_NODES:
			node_to_attach.append(worst_cases_scinario.pop())
			nodes_indexes.append(worst_cases_scinario_indexes.pop())
		
		# Process nodes to attatch

		for node in node_to_attach:
			self.validate_node(node)

		# Now that those nodes are proven
		# we can now attach our node to the dag
		self.nodes.append(self.create_node(data, nodes_indexes, new_index))
		return new_index


	# this is the consesus algorithm

	def valid_tangle(self, tangle):
		for node in tangle:
			if node['index'] >= properties.NUMBER_OF_VALIDATION_NODES: # do not test genesis nodes
				validity_of_node = node['validity']
				# Make sure that the same number of nodes saying that they have
				# validated him as his validity level
				next_nodes = node['next_nodes']
				print(next_nodes)
				if validity_of_node < len(next_nodes):
					return False
				# Make sure these nodes are pointing to him
				for n_node in next_nodes:
					print(tangle[n_node])
					if node['index'] not in tangle[n_node]['previous_nodes']:
						return False
		return True


	def register_peer(self, address):
		parsed_url = urlparse(address)
		self.peers.add(parsed_url.netloc)

	def resolve_conflicts(self):
		neighbours = self.peers
		new_tangle = None

		# We are only looking chaing longer than ours
		max_length = len(self.nodes)

		# Grab and verify the chains from all the peers in our network
		for peer in neighbours:
			print(peer)
			response = requests.get("http://"+ str(peer) +"/tangle")
			if response.status_code == 200:
				length = response.json()['length']
				tangle = response.json()['tangle']

				# Check if length is longer and the chain is valid
				if length > max_length and self.valid_tangle(tangle):
					max_length = length
					new_tangle = tangle

		# Replace our chan if we discovered a new, valid chain longer than ours
		if new_tangle:
			self.nodes = new_tangle
			return True
		return False		
