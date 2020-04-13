import json
from collections import Counter
from pathlib import Path
import logging as log
import numpy as np
import pandas as pd
from unsupervised.util import load_nmf_factors, load_partition, load_term_rankings, truncate_term_rankings
from validation.embedding import Embedding
from webconfig import config

# --------------------------------------------------------------

class WebCore:

	def __init__(self, dir_core):
		self.dir_core = Path(dir_core)
		log.info("Starting TopicScan core - working directory: %s ..." % self.dir_core)
		# metadata and cache
		self.embedding_meta = {}
		self.embedding_cache = {}
		self.model_meta = {}
		self.df_embeddings = None
		self.df_models = None

	def init(self, preload_embeddings):
		""" Find all the relevant files in the core directory, and parse them. """
		self.__find_metadata()
		self.__parse_embedding_metadata()
		self.__parse_model_metadata()
		# should we load all of the word embeddings into memory now?
		if preload_embeddings:
			log.info("Preloading word embeddings ...")
			for embed_id in self.embedding_meta:
				self.get_embedding(embed_id)	
			log.info("Preloaded %d word embeddings" % len(self.embedding_cache))

	def get_embedding_ids(self):
		return sorted(self.embedding_meta.keys())

	def get_embedding_count(self):
		return len(self.embedding_meta)

	def get_embedding_metadata(self, embed_id):
		""" Return the metadata associated with a given word embedding """
		if not embed_id in self.embedding_meta:
			return None
		return self.embedding_meta[embed_id]

	def get_embedding(self, embed_id):
		""" Return the actual word embedding associated with a given ID """
		if not embed_id in self.embedding_meta:
			return None
		if embed_id in self.embedding_cache:
			log.info("Using cached embedding for %s" % embed_id)
			return self.embedding_cache[embed_id]
		# load the associated word embedding
		em = self.embedding_meta[embed_id]
		in_path = em.dir_base / em["file"]
		log.info("Loading word embedding from %s" % in_path)
		try:
			self.embedding_cache[embed_id] = Embedding(in_path)
		except Exception as e:
			log.warning("Failed to load word embedding: %s" % in_path)
			log.warning(e)
			return None
		return self.embedding_cache[embed_id]

	def get_topic_model_ids(self):
		return sorted(self.model_meta.keys())
	
	def get_topic_model_count(self):
		return len(self.model_meta)

	def get_topic_model_metadata(self, model_id):
		""" Return the metadata associated with a given word topic model """
		if not model_id in self.model_meta:
			return None
		return self.model_meta[model_id]

	def __find_metadata(self):
		self.embedding_meta = {}
		self.model_meta = {}
		extension = config.get("file_extension", ".meta")
		meta_file_paths = self.dir_core.glob('**/*' + extension)
		for meta_file_path in meta_file_paths:
			log.debug("Checking metadata from %s" % meta_file_path)
			try:
				with open(meta_file_path, "r") as fin:
					data = json.load(fin)
					if type(data) != dict:
						continue
					# create the ID as a relative path minus the extension
					relative = str(Path(meta_file_path).relative_to(self.dir_core))
					meta_id = relative[0:len(relative)-len(extension)]
					if data["type"] == "embedding":
						self.embedding_meta[meta_id] = EmbeddingMeta(meta_id, meta_file_path)
					elif data["type"] == "topic_model":
						self.model_meta[meta_id] = TopicModelMeta(meta_id, meta_file_path)
					else:
						log.info("Unknown metadata type %s in file %s" % (data["type"], meta_file_path))
			except Exception as e:
				log.warning("Skipping file: %s" % meta_file_path)
				log.warning(e)
		log.info("Found %d embeddings, %d topic models" 
			% (len(self.embedding_meta), len(self.model_meta)))

	def __parse_model_metadata(self):
		rows = []
		for model_id in self.model_meta:
			row = { 
				"Name" : model_id, 
				"Corpus" : self.model_meta[model_id]["corpus"],
				"Algorithm" : self.model_meta[model_id]["algorithm"]["id"],
				"Topics" : self.model_meta[model_id]["k"],
				"Documents" : self.model_meta[model_id]["documents"],
				"Terms" : self.model_meta[model_id]["terms"] }
			rows.append(row)
		self.df_models = pd.DataFrame(rows)

	def __parse_embedding_metadata(self):
		rows = []
		for embed_id in self.embedding_meta:
			row = { "Name" : embed_id, 
				"Description" : self.embedding_meta[embed_id]["description"],
				"Algorithm" : self.embedding_meta[embed_id]["algorithm"]["id"], 
				"Dimensions" : self.embedding_meta[embed_id]["dimensions"], 
				"Documents" : self.embedding_meta[embed_id]["documents"],
				"Terms" : self.embedding_meta[embed_id]["terms"] }
			rows.append(row)
		self.df_embeddings = pd.DataFrame(rows)

# --------------------------------------------------------------

class TopicModelMeta(dict):

	def __init__(self, model_id, meta_file_path):
		log.info("Parsing model metadata from %s" % meta_file_path)
		# read the JSON
		fin = open(meta_file_path, "r")
		data = json.load(fin)
		fin.close()
		if type(data) != dict:
			raise Exception("Invalid JSON format in metadata file")
		if not "type" in data:
			raise Exception("No type specified in metadata file")
		if data["type"] != "topic_model":
			raise Exception("Metadata does not describe a topic model")
		if not "files" in data:
			raise Exception("No file paths specified in metadata file")
		# add the metadata
		self["id"] = model_id
		for key in data:
			self[key] = data[key]
		# ensure we have the mandatory metadata
		if not "corpus" in self:
			self["corpus"] = "unknown"
		if not "algorithm" in self:
			self["algorithm"] = { "id" : "unknown", "parameters" : {} }
		for key in ["topics", "documents", "terms"]:
			if not key in self:
				self[key] = 0
		# other properties
		self.meta_file_path = Path(meta_file_path)
		self.dir_base = meta_file_path.parent
		self.term_rankings = None
		self.partition = None
		self.term_associations = None
		self.document_associations = None
		# other settings
		self.top_terms = config.get("top_terms", 10)
		self.extended_top_terms = config.get("extended_top_terms", 20)

	def load_all_files(self):
		""" Preload all the required files associated with this model """
		self.get_rankings()
		self.get_partition()
		self.__load_factors()
		self.get_document_associations()
		self.get_term_associations()	

	def get_rankings(self):
		if not self.term_rankings is None:
			return self.term_rankings
		# load the associated rankings for the topic model
		in_path = self.dir_base / self["files"]["ranks"]
		log.info("Loading term rankings from %s" % in_path)
		(self.term_rankings,labels) = load_term_rankings(in_path)
		return self.term_rankings

	def get_partition(self):
		if not self.partition is None:
			return self.partition
		# load the associated topic model data
		in_path = self.dir_base / self["files"]["partition"]
		log.info("Loading partition from %s" % in_path)
		self.partition, partition_doc_ids = load_partition(in_path)
		return self.partition

	def get_partition_sizes(self):
		partition = self.get_partition()
		if partition is None:
			return None
		sizes = np.zeros(self["k"], dtype=int)
		for i in partition:
			sizes[i] += 1
		return sizes

	def get_partition_percentages(self):
		partition = self.get_partition()
		if partition is None:
			return None
		n = len(partition)
		return (100.0 * self.get_partition_sizes())/n

	def get_descriptors(self, top = 0):
		if top < 1:
			top = self.top_terms
		if self.term_rankings is None:
			self.get_rankings()
		return truncate_term_rankings(self.term_rankings, top)

	def get_all_descriptor_terms(self):
		""" Return sorted list of all unique terms appearing across all topic descriptors. """
		all_terms = set()
		for ranking in self.get_descriptors(self.top_terms):
			all_terms = set(ranking).union(all_terms)
		return sorted(all_terms)

	def get_term_map(self):
		""" Return a map of terms to topic descriptors to which they have been assigned """
		term_map = {}
		for i, ranking in enumerate(self.get_descriptors(self.top_terms)):
			for term in ranking:
				if not term in term_map:
					term_map[term] = [ i ]
				else:
					term_map[term].append(i)
		return term_map

	def get_partition_df(self):
		sizes = self.get_partition_sizes()
		descriptors = self.get_descriptors()
		partition_per = self.get_partition_percentages()
		if sizes is None or descriptors is None or partition_per is None:
			return None
		# build the data frame
		rows = []
		num_fmt = "Topic %02d" if len(descriptors) < 100 else "Topic %03d"
		for i in range(len(descriptors)):
			s_per = " %.2f%%" % partition_per[i]
			row = { "Label" : (num_fmt % (i+1)), 
				"Descriptor" : ", ".join(descriptors[i]), 
				"Percentage" : s_per, "Size" : sizes[i], "Number" : (i+1) }
			rows.append(row)
		return pd.DataFrame(rows).set_index("Label")

	def get_descriptor_df(self):
		rows = []
		descriptors = self.get_descriptors(self.extended_top_terms)
		if descriptors is None:
			return None
		num_fmt = "%02d" if len(descriptors) < 100 else "%03d"
		for i, ranking in enumerate(descriptors):
			s_descriptor = ", ".join(ranking[0:self.top_terms])
			s_extended = ", ".join(ranking[self.top_terms+1:])
			row = { "Topic" : num_fmt % (i+1), "Descriptor" : s_descriptor, "Extended Descriptor" : s_extended }
			rows.append(row)
		return pd.DataFrame(rows)

	def get_descriptor_term_counts(self):
		""" Return the number of descriptors in which each term appears """
		counts = Counter()
		descriptors = self.get_descriptors()
		if descriptors is None:
			return counts
		for d in descriptors:
			for term in d:
				counts[term] += 1
		return counts

	def __load_factors(self):
		""" Load the NMF factors associated with this topic model. """
		in_path = self.dir_base / self["files"]["factors"]
		log.info("Loading factors from %s" % in_path)
		(W,H,doc_ids,terms) = load_nmf_factors(in_path)
		columns = np.arange(1, self["k"]+1, dtype=int)
		self.document_associations = pd.DataFrame(W, index = doc_ids, columns = columns)
		self.term_associations = pd.DataFrame(np.transpose(H), index = terms, columns = columns)

	def get_document_associations(self):
		if not self.document_associations is None:
			return self.document_associations
		self.__load_factors()
		return self.document_associations

	def get_term_associations(self):
		if not self.term_associations is None:
			return self.term_associations
		self.__load_factors()
		return self.term_associations

	def get_term_partition(self):
		df_term_associations = self.get_term_associations()
		# get the maximum column for each row
		# note we need to switch to 0 indexing
		return np.array(df_term_associations.idxmax(axis=1)) - 1

	def get_term_partition_sizes(self):
		term_partition = self.get_term_partition()
		if term_partition is None:
			return None
		sizes = np.zeros(self["k"], dtype=int)
		for i in term_partition:
			sizes[i] += 1
		return sizes

	def get_term_partition_percentages(self):
		term_partition = self.get_term_partition()
		if term_partition is None:
			return None
		n = len(term_partition)
		return (100.0 * self.get_term_partition_sizes())/n		

	def get_term_partition_df(self):
		sizes = self.get_term_partition_sizes()
		descriptors = self.get_descriptors()
		term_partition_per = self.get_term_partition_percentages()
		if sizes is None or descriptors is None or term_partition_per is None:
			return None
		# build the data frame
		rows = []
		num_fmt = "Topic %02d" if len(descriptors) < 100 else "Topic %03d"
		for i in range(len(descriptors)):
			s_per = " %.2f%%" % term_partition_per[i]
			row = { "Label" : (num_fmt % (i+1)), 
				"Descriptor" : ", ".join(descriptors[i]), 
				"Percentage" : s_per, "Size" : sizes[i], "Number" : (i+1) }
			rows.append(row)
		return pd.DataFrame(rows).set_index("Label")

# --------------------------------------------------------------

class EmbeddingMeta(dict):

	def __init__(self, embed_id, meta_file_path):
		log.info("Parsing embedding metadata from %s" % meta_file_path)
		# read the JSON
		fin = open(meta_file_path, "r")
		data = json.load(fin)
		fin.close()
		if type(data) != dict:
			raise Exception("Invalid JSON format in metadata file")
		if "type" not in data:
			raise Exception("No type specified in metadata file")
		if data["type"] != "embedding":
			raise Exception("Metadata does not describe a word embedding")
		if "file" not in data:
			raise Exception("No file path specified in metadata file")
		# add the metadata
		self["id"] = embed_id
		for key in data:
			self[key] = data[key]
		# ensure we have the mandatory metadata
		if "description" not in self:
			self["description"] = "unknown"
		if "algorithm" not in self:
			self["algorithm"] = { "id" : "unknown", "parameters" : {} }
		if "id" not in self["algorithm"]:
			self["algorithm"]["id"] = "unknown"
		for key in ["documents", "terms", "dimensions"]:
			if key not in self:
				self[key] = 0
		# other properties
		self.meta_file_path = Path(meta_file_path)
		self.dir_base = meta_file_path.parent

