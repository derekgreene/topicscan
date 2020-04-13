import numpy as np
from sklearn import decomposition

# --------------------------------------------------------------

class NMFWrapper:
	""" Wrapper class backed by the scikit-learn package NMF implementation. """
	
	def __init__(self, max_iters = 100, init_strategy="random"):
		self.max_iters = max_iters
		self.init_strategy = init_strategy
		self.W = None
		self.H = None

	def apply(self, X, k = 2):
		""" Apply NMF to the specified document-term matrix X. """
		self.W = None
		self.H = None
		model = decomposition.NMF(init=self.init_strategy, n_components=k, max_iter=self.max_iters)
		self.W = model.fit_transform(X)
		self.H = model.components_			
		
	def rank_terms(self, topic_index, top = -1):
		""" Return the top ranked terms for the specified topic, generated during the last NMF run. """
		if self.H is None:
			raise ValueError("No results for previous run available")
		# NB: reverse
		top_indices = np.argsort(self.H[topic_index,:])[::-1]
		# truncate if necessary
		if top < 1 or top > len(top_indices):
			return top_indices
		return top_indices[0:top]

	def generate_partition(self):
		""" Produce a disjoint partition of documents based on the factor generate during the last run. """
		if self.W is None:
			raise ValueError("No results for previous run available")
		return np.argmax(self.W, axis = 1).flatten().tolist()		
