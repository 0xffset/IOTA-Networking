import props as properties
import json
from time import time
import hashlib
import requests
from urllib.parse import urlparse

"""
Los nodos en la red Tangle (DAG) son representados en el formato JSON descrito:
ellos pueden ser transmitidos a través de la red
 Node = {
            'index': "índice",
            'timestamp': time(),
            'data': "datos de la transacción donde los datos se guardarán",
            'proof': "prueba de trabajo",
            'previous_hashs': "Los hashes de los dos últimos nodos conectados",
            'previous_nodes': 'índice de nodos previos',
            'next_nodes': 'índices de los nodos que apuntan a él,
            'validity': número de veces que el nodo ha sido probado
        }
"""

class Tangle(object):
	"""docstring for Tangle"""
	def __init__(self):
		super(Tangle, self).__init__()
		self.nodes = []
		self.peers = set()
		# Crea un bloque inicial
		for i in range(properties.REQUIRED_PROOF):
			self.nodes.append(self.create_node(None, [], len(self.nodes), 
			validity = properties.REQUIRED_PROOF))

		""" Se asegura que el nodo tenga el número correcto de ceros.

		Returns:
			bool: Si la cantida de ceros es correcta.  
		"""
	@staticmethod	
	def valid_proof(last_proof, last_hash, proof):
		guess = (str(last_proof) + str(last_hash) + str(proof)).encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"

		"""Se hace la prueba de trabajo
		"""
	def proof_of_work(self, last_proof, last_hash):
		proof = 0
		while self.valid_proof(last_proof, last_hash, proof) is False:
			proof += 1
		return proof
		
		""" Crear n nuevo hash para un nodo 

		Returns:
			sha256: hash sha-256 del nodo
		"""
	@staticmethod
	def hash(node):
		# Hace un hash para el block
		# Nos aseguramos que el dictionario este ordenado de lo contrario tendremos hashes inconsistentes
		node_string = json.dumps(node, sort_keys=True).encode()
		return hashlib.sha256(node_string).hexdigest()

		""" Valida el nodo
		"""
	def validate_node(self, node):
		if self.nodes[node['index']]['validity'] < properties.REQUIRED_PROOF:
			last_proof = self.nodes[node['index']]['proof'] # This nodes proof
			last_hash = ""
			print(node['index'])
			for prev_hash in self.nodes[node['index']]['previous_hashs']:
				last_hash += prev_hash # the hashes of the nodes his node connects
			self.nodes[node['index']]['proof'] = self.proof_of_work(last_proof, last_hash)
			self.nodes[node['index']]['validity'] =+ 1

	
		"""Crear un nuevo nodo
		"""
	def create_node(self, data, prev_nodes, new_index, validity=0): # Estos prev_nodes son los índices en el dag que apuntan al nodo.
		prev_hashes = []
		'''
		Se podría agregar una futura actualización para
  		que actualize cada nodo para que actualize aquellos 
    	nodos que apuntes a esta transacción.
		'''

		for i in prev_nodes:
			prev_hashes.append(self.hash(self.nodes[i]))
			#Ahora les decimos a los nodos a los que estamos apuntando que les estamos apuntando   			
			self.nodes[i]['next_nodes'].append(new_index)

		Node = {
			'index': new_index,
			'timestamp': time(),
			'data': data,
			'proof': 0,
			'previous_hashs': prev_hashes,
			'previous_nodes': prev_nodes,
			'next_nodes': [],
			'validity': validity,
		}
		return Node

		""" Enviar una transacción
		"""
	def send_transaction(self, data):
		# Encontrar dos nodos en la red que esten provados. 
		node_to_attach = []
		nodes_indexes = []
		new_index = len(self.nodes)
		worst_cases_scinario = []
		worst_cases_scinario_indexes = []

		'''
		Se podría agregar una futura actualización donde esta función haga la búsqueda de forma aleatoria. 
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

		# Si no hay suficientes transacciones varificadas, use transacciones verificadas

		while len(node_to_attach) < properties.NUMBER_OF_VALIDATION_NODES:
			node_to_attach.append(worst_cases_scinario.pop())
			nodes_indexes.append(worst_cases_scinario_indexes.pop())
		
		# Nodo en proceso de adjuntar
		for node in node_to_attach:
			self.validate_node(node)
   
		# Se adjunta el nodo a la red Tangle(DAG)
		self.nodes.append(self.create_node(data, nodes_indexes, new_index))
		return new_index


		"""Este es el algoritmo de consenso
		"""
	def valid_tangle(self, tangle):
		for node in tangle:
			if node['index'] >= properties.NUMBER_OF_VALIDATION_NODES: # do not test genesis nodes
				validity_of_node = node['validity']
				# Se asegura que el mismo número de nodos que posee. 
				# Se valida el nodo y su nivel de validad. 
				next_nodes = node['next_nodes']
				if validity_of_node < len(next_nodes):
					return False
				# Se asegura que esos nodos estan apuntado al él.
				for n_node in next_nodes:
					if node['index'] not in tangle[n_node]['previous_nodes']:
						return False
		return True

		"""Se registra un peer
		"""
	def register_peer(self, address):
		parsed_url = urlparse(address)
		self.peers.add(parsed_url.netloc)

		""" Algoritmo que verifica si este algún conflicto con los nodos
		"""
	def resolve_conflicts(self):
		neighbours = self.peers
		new_tangle = None

		# Solo buscamos una cadena que larga que la que se está procesando. 
		max_length = len(self.nodes)

		# Obtiene y verifica las cadenas de todos los pares de nuestra red.
		for peer in neighbours:
			response = requests.get("http://"+ str(peer) +"/tangle")
			if response.status_code == 200:
				length = response.json()['length']
				tangle = response.json()['tangle']

				# Compruebe si la longitud es más larga y la cadena es válida
				if length > max_length and self.valid_tangle(tangle):
					max_length = length
					new_tangle = tangle

		# Reemplazar nuestro chan si descubrimos una cadena nueva y válida más larga que la nuestra
		if new_tangle:
			self.nodes = new_tangle
			return True
		return False		
