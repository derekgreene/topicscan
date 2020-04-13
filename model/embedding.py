import gensim
import numpy as np

# --------------------------------------------------------------

class Embedding:
	""" 
	Convenience wrapper for a Gensim word embedding, which caches pairwise similarity values
	to improve performance when we need to repeatedly measure the similarity between the same
	pairs of terms.
	"""
	def __init__(self, embedding_path):
		# make sure it's a string, not a Path
		embedding_path = str(embedding_path)
		if "-ft" in embedding_path:
			self.embedding = gensim.models.FastText.load(embedding_path)
			self.vocab = set(self.embedding.wv.vocab.keys())
		else:
			# note we always assume that we are using the binary format for word2vec
			self.embedding = gensim.models.KeyedVectors.load_word2vec_format(embedding_path, binary=True)
			self.vocab = set(self.embedding.vocab.keys())
		# cache for pairwise term similarity scores
		self.similarity_cache = {}

	def similarity(self, term1, term2):
		""" Return the similarity between two terms in the embedding space """
		pair = frozenset([term1,term2])
		# have we already calculated the similarity between two terms?
		if not pair in self.similarity_cache:
			# note: we don't permit negative values
			self.similarity_cache[pair] = max(self.embedding.similarity(term1, term2), 0)
		return self.similarity_cache[pair]

	def distance(self, term1, term2):
		""" Return the distance between two terms in the embedding space """
		return 1.0 - self.similarity(term1, term2)

	def get_neighbors(self, query, num_neighbors=10):
		# is it a single term, or a list?
		if type(query) == list:
			valid_terms = []
			for term in query:
				if term in self:
					valid_terms.append(term)
			if len(valid_terms) == 0:
				return []
			most_similar = self.embedding.most_similar(positive=valid_terms, topn=num_neighbors)
		else:
			if not query in self:
				return []
			most_similar = self.embedding.most_similar(positive=[query], topn=num_neighbors)
		return [ x[0] for x in most_similar ]

	def __contains__(self, term):
		return term in self.vocab

	def __len__(self):
		return len(self.vocab)
