import random
import numpy as np
import joblib

# --------------------------------------------------------------

def init_random_seeds(random_seed):
	"""
	Initialize all required random seeds.
	"""
	if random_seed < 0:
		random_seed = random.randint(1,100000)
	np.random.seed(random_seed)
	random.seed(random_seed)			
	return random_seed
	
# --------------------------------------------------------------

def save_term_rankings(out_path, term_rankings, labels = None):
	"""
	Save a list of multiple term rankings using Joblib.
	"""
	# no labels? generate some default ones
	if labels is None:
		labels = []
		for i in range(len(term_rankings)):
			labels.append("C%02d" % (i+1))
	joblib.dump((term_rankings,labels), out_path) 

def load_term_rankings(in_path):
	"""
	Load a list of multiple term rankings using Joblib.
	"""
	(term_rankings,labels) = joblib.load(in_path)
	return (term_rankings,labels)

def save_nmf_factors(out_path, W, H, doc_ids, terms):
    """
    Save a NMF factorization result using Joblib.
    """
    joblib.dump((W,H,doc_ids,terms), out_path) 

def load_nmf_factors(in_path):
	"""
	Load a NMF factorization result using Joblib.
	"""
	(W,H,doc_ids,terms) = joblib.load(in_path)
	return (W,H,doc_ids,terms)

def save_partition(out_path, partition, doc_ids):
	"""
	Save a disjoint partition documments result using Joblib.
	This is represent as a 0-indexed list, with one entry per document.
	"""
	joblib.dump((partition,doc_ids), out_path) 


def load_partition(in_path):
	"""
	Load a disjoint partition of documments result using Joblib.
	This is represent as a 0-indexed list, with one entry per document.
	"""
	(partition,doc_ids) = joblib.load(in_path)
	return (partition,doc_ids) 

# --------------------------------------------------------------

def truncate_term_rankings(orig_rankings, top, vocab = None):
	"""
	Truncate a list of multiple term rankings to the specified length, possibly filtered based
	on the specified vocabulary.
	"""
	trunc_rankings = []
	# no limited vocabulary?
	if vocab is None:
		if top < 1:
			return orig_rankings
		for ranking in orig_rankings:
			trunc_rankings.append(ranking[0:min(len(ranking),top)])
	else:
		total = 0
		for ranking in orig_rankings:
			counter = 0
			temp = []
			for term in ranking:
				if term in vocab:
					temp.append(term)
				else:
					counter += 1
				if len(temp) == top:
					break
			total += counter
			trunc_rankings.append(temp)
	return trunc_rankings

def clustermap_to_partition(cluster_map, doc_ids):
	""" Convert a dictionary, representing a clustering of documents, into a partition. """
	cluster_names = list(cluster_map.keys())
	cluster_names.sort()
	# build document map
	partition = []
	doc_map = {}
	for i in range(len(doc_ids)):
		partition.append(-1)
		doc_map[ doc_ids[i] ] = i
	# now create the document partition
	for cluster_index in range(len(cluster_map)):
		for doc_id in cluster_map[cluster_names[cluster_index]]:
			partition[doc_map[doc_id]] = cluster_index
	return partition
