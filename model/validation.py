import itertools
import numpy as np

# --------------------------------------------------------------

class CoherenceScore:
	"""
	Uses a word embedding (e.g. Word2Vec embedding) to evaluate the semantic coherence of the
	descriptors from a topic model.
	"""
	def __init__(self, embedding):
		self.embedding = embedding

	def is_maximize(self):
		""" Should good topics maximize this score? """
		return True

	def evaluate_model(self, descriptors):
		""" Calculate the overall model score as the average of the topic scores """
		return self.evaluate_topics(descriptors).mean()

	def evaluate_topics(self, descriptors):
		topic_scores = []
		for descriptor in descriptors:
			topic_scores.append(self.evaluate_topic(descriptor))
		return np.array(topic_scores)

	def evaluate_topic(self, descriptor):	
		pair_scores = []
		for term1, term2 in itertools.combinations(descriptor, 2):
			if term1 in self.embedding and term2 in self.embedding:
				pair_scores.append(self.embedding.similarity(term1, term2))
		if len(pair_scores) == 0:
			return 0.0
		return np.array(pair_scores).mean()


class TopicDifferenceScore:
	"""
	Uses a word embedding to evaluate how different the descriptors in a topic model are
	from one another.
	"""
	def __init__(self, embedding):
		self.embedding = embedding

	def is_maximize(self):
		""" Should good topics maximize this score? """
		return True

	def evaluate_model(self, descriptors):
		topic_pair_scores = []
		for descriptor1, descriptor2 in itertools.combinations(descriptors, 2):
			topic_pair_scores.append(self.evaluate_distance(descriptor1, descriptor2))
		return np.array(topic_pair_scores).mean()

	def evaluate_topics(self, descriptors):
		k = len(descriptors)
		topic_scores = np.zeros(k)
		for i in range(k):
			for j in range(i+1, k):
				dist = self.evaluate_distance(descriptors[i], descriptors[j])
				topic_scores[i] += dist
				topic_scores[j] += dist
		topic_scores /= (k-1)
		return topic_scores

	def evaluate_distance(self, descriptor1, descriptor2):
		return 1.0 - self.evaluate_similarity(descriptor1, descriptor2)

	def evaluate_similarity(self, descriptor1, descriptor2):
		pair_scores = []
		for term1 in descriptor1:
			for term2 in descriptor2:
				if term1 in self.embedding and term2 in self.embedding:
					pair_scores.append(self.embedding.similarity(term1, term2))
		if len(pair_scores) == 0:
			return 0.0
		return np.array(pair_scores).mean()


class MinMaxScore:
	""" 
	Version of the distinctiveness score, where normalization is loosely based on the min-max cluster similarity measure 
	proposed by Ding et al (2001). Note that for this measure better models will have lower scores.
	"""
	def __init__(self, embedding):
		self.embedding = embedding

	def is_maximize(self):
		""" Should good topics maximize this score? """
		return False

	def evaluate_model(self, descriptors):
		""" Calculate the overall model score based on the mean score across all unique pairs
		of topics """
		topic_pair_scores = []
		for descriptor1, descriptor2 in itertools.combinations(descriptors, 2):
			topic_pair_scores.append(self.evaluate_similarity(descriptor1, descriptor2))
		return np.array(topic_pair_scores).mean()

	def evaluate_topics(self, descriptors):
		""" Return the scores for all individual topics """
		k = len(descriptors)
		topic_scores = np.zeros(k)
		for i in range(k):
			for j in range(i+1, k):
				sim = self.evaluate_similarity(descriptors[i], descriptors[j])
				topic_scores[i] += sim
				topic_scores[j] += sim
		topic_scores /= (k-1)
		return topic_scores

	def evaluate_similarity(self, descriptor1, descriptor2):
		""" Calculate the normalized similarity score """
		numer = self.evaluate_raw_similarity(descriptor1, descriptor2)
		denom = (self.evaluate_raw_similarity(descriptor1, descriptor1) * self.evaluate_raw_similarity(descriptor2, descriptor2))
		if denom == 0:
			return 0.0
		return numer/denom

	def evaluate_raw_similarity(self, descriptor1, descriptor2):
		""" Calculate the raw (non-normalized) similarity score """
		pair_scores = []
		for term1 in descriptor1:
			for term2 in descriptor2:
				if term1 in self.embedding and term2 in self.embedding:
					pair_scores.append(self.embedding.similarity(term1, term2))
		if len(pair_scores) == 0:
			return 0.0
		return np.array(pair_scores).mean()


class InternalExternalScore:
	"""
	Topic validation measure loosely based on the community finding fitness function proposed
	by Lancichinetti et al (2009), which balances both intra-topic and inter-topic distance.
	"""
	def __init__(self, embedding):
		self.embedding = embedding

	def is_maximize(self):
		""" Should good topics maximize this score? """
		return True

	def evaluate_model(self, descriptors):
		""" Calculate the overall model score as the average of the topic scores """
		return self.evaluate_topics(descriptors).mean()

	def evaluate_topics(self, descriptors):
		topic_scores = []
		for topic_index1, descriptor in enumerate(descriptors):
			# get the internal score
			internal = self.evaluate_topic_internal(descriptor)
			# get the external score
			other_terms = []
			for topic_index2, descriptor2 in enumerate(descriptors):
				if topic_index1 != topic_index2:
					other_terms += descriptor2
			external = self.evaluate_topic_external(descriptor, other_terms)
			# combine the two scores
			denom = internal + external
			if denom == 0:
				topic_score = 0.0
			else:
				topic_score = internal/denom
			topic_scores.append(topic_score)
		return np.array(topic_scores)

	def evaluate_topic_internal(self, descriptor):	
		pair_scores = []
		for term1, term2 in itertools.combinations(descriptor, 2):
			if term1 in self.embedding and term2 in self.embedding:
				pair_scores.append(self.embedding.similarity(term1, term2))
		if len(pair_scores) == 0:
			return 0.0
		return np.array(pair_scores).mean()

	def evaluate_topic_external(self, descriptor, other_terms):
		pair_scores = []
		for term1 in descriptor:
			for term2 in other_terms:
				if term1 in self.embedding and term2 in self.embedding:
					pair_scores.append(self.embedding.similarity(term1, term2))
		if len(pair_scores) == 0:
			return 0.0
		return np.array(pair_scores).mean()


class TopicSilhouetteScore:
	"""
	Topic validation measure based on the silhouette cluster validation approach proposed by 
	Rousseeuw (1987), which we generalize to evaluate topics using distances computed from a given 
	word embedding. The measure considers aspects of both internal coherence within a single topic, and 
	the associations between different topics. This is first done at an individual term level, 
	and can then be aggregated to the topic or model level.
	"""
	def __init__(self, embedding):
		self.embedding = embedding
		self.topic_term_scores = None

	def is_maximize(self):
		""" Should good topics maximize this score? """
		return True

	def evaluate_model(self, descriptors):
		""" Calculate the overall model score as the average of the topic scores """
		return self.evaluate_topics(descriptors).mean()

	def evaluate_topics(self, descriptors):
		""" Evaluate a single topic """
		topic_scores = []
		self.topic_term_scores = []
		for topic_index1, descriptor1 in enumerate(descriptors):
			topic_score = 0
			term_scores = {}
			# process each term
			for term in descriptor1:
				a, b = 0, None
				for topic_index2, descriptor2 in enumerate(descriptors):
					if topic_index1 == topic_index2:
						a = self.evaluate_term_topic_distance(term, descriptor2, True)
					else:
						topic2_dist = self.evaluate_term_topic_distance(term, descriptor2, False)
						if b is None or topic2_dist < b:
							b = topic2_dist
				# calculate the silhouette score for this term
				numer = b - a
				denom = max(a,b)
				if denom == 0:
					term_sil = 0
				else:
					term_sil = numer/denom
				topic_score += term_sil
				term_scores[term] = term_sil
			# convert to average
			topic_score /= len(descriptor1)
			topic_scores.append(topic_score)
			self.topic_term_scores.append(term_scores)
		return np.array(topic_scores)

	def evaluate_term_topic_distance(self, term, descriptor, ignore_self = False):
		""" Measure the distance between a term and a topic descriptor """
		pair_scores = []
		for term2 in descriptor:
			if term == term2 and ignore_self:
				continue
			if term in self.embedding and term2 in self.embedding:
				pair_scores.append(self.embedding.distance(term, term2))
		if len(pair_scores) == 0:
			return 0.0
		return np.array(pair_scores).mean()

