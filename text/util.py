import os, os.path, re
from sklearn.feature_extraction.text import TfidfVectorizer
import logging as log
import joblib

# --------------------------------------------------------------

token_pattern = re.compile(r"\b\w\w+\b", re.U)
url_pattern = re.compile('https?[:;]?/?/?\S*')
min_term_length = 2

# --------------------------------------------------------------

def find_text_files( root_path ):
	""" Find all files in the specified directory and its subdirectories, and store them as 
	strings in a list. """
	filepaths = []
	for dir_path, subFolders, files in os.walk(root_path):
		for filename in files:
			if filename.startswith(".") or filename.startswith("_"):
				continue
			filepath = os.path.join(dir_path,filename)
			filepaths.append( filepath )
	filepaths.sort()
	return filepaths	

def read_text( in_path ):
	""" Read and normalize body text from the specified text file. """
	body = ""
	with open(in_path, 'r', encoding="utf8", errors='ignore') as fin:
		while True:
			line = fin.readline()
			if not line:
				break
			# Remove URIs at this point (Note: this simple regex captures MOST URIs but may occasionally let others slip through)
			normalized_line = re.sub(url_pattern, '', line.strip())
			if len(normalized_line) > 1:
				body += normalized_line
				body += "\n"
	return body

def read_text_lines( in_path ):
	""" Read and normalize body text from the specified text file, and
	return multiple documents, one for each line. """
	return read_text( in_path ).split( "\n" )

def load_word_set( in_path ):
	""" Load stopwords from a file into a set. """
	stopwords = set()
	with open(in_path) as f:
		lines = f.readlines()
		for l in lines:
			l = l.strip().lower()
			if len(l) > 0:
				stopwords.add(l)
	return stopwords

# --------------------------------------------------------------

def custom_tokenizer( s ):
	""" Custom string tokenizer. """
	return [x.lower() for x in token_pattern.findall(s) if (len(x) >= min_term_length and x[0].isalpha() ) ]

def preprocess( docs, stopwords, min_df = 3, ngram_range = (1,1), apply_tfidf = True, apply_norm = True ):
	""" Preprocess a list containing text documents stored as strings. """	
	if apply_norm:
		norm_function = "l2"
	else:
		norm_function = None
	# build the Vector Space Model, apply TF-IDF and normalize lines to unit length all in one call
	tfidf = TfidfVectorizer(stop_words=stopwords, lowercase=True, strip_accents="unicode", 
		tokenizer=custom_tokenizer, use_idf=apply_tfidf, norm=norm_function, min_df = min_df, ngram_range = ngram_range) 
	X = tfidf.fit_transform(docs)
	terms = []
	# create the vocabulary map
	v = tfidf.vocabulary_
	for i in range(len(v)):
		terms.append("")
	for term in v.keys():
		terms[ v[term] ] = term
	return (X,terms)

# --------------------------------------------------------------

def save_corpus(out_prefix, X, terms, doc_ids, document_labels = None):
	""" Save a pre-processed scikit-learn corpus and associated metadata using Joblib. """
	matrix_outpath = "%s.pkl" % out_prefix 
	log.info( "Saving document-term matrix to %s" % matrix_outpath )
	joblib.dump((X,terms,doc_ids,document_labels), matrix_outpath ) 

def load_corpus(in_path):
	""" Load a pre-processed scikit-learn corpus and associated metadata using Joblib. """
	(X,terms,doc_ids,document_labels) = joblib.load( in_path )
	return (X, terms, doc_ids, document_labels)

# --------------------------------------------------------------

class FileTokenGenerator:
	""" A generator which yields tokens from a collection of text files,
	where each file represents a separate document. """

	def __init__(self, file_paths, min_doc_length, stopwords = set()):
		self.file_paths = file_paths
		self.min_doc_length = min_doc_length
		self.stopwords = stopwords
		self.placeholder = "<stopword>"

	def __iter__( self ):
		for in_path in self.file_paths:
			doc = read_text( in_path ).lower()
			if len(doc) < self.min_doc_length:
				log.debug("Skipping short document: %s" % in_path)
				continue
			tokens = []
			for tok in custom_tokenizer(doc):
				if tok in self.stopwords:
					tokens.append(self.placeholder)
				else:
					tokens.append(tok)
			yield tokens

class LineTokenGenerator(FileTokenGenerator):
	""" A generator which yields tokens from a collection of text files,
	where each line in a file represents a separate document. """

	def __init__(self, file_paths, min_doc_length, stopwords = set()):
		super(LineTokenGenerator, self).__init__(file_paths, min_doc_length, stopwords)

	def __iter__( self ):
		for in_path in self.file_paths:
			text = read_text( in_path ).lower()
			for doc in text.split("\n"):
				if len(doc) < self.min_doc_length:
					log.debug("Skipping short document: %s" % in_path)
					continue
				tokens = []
				for tok in custom_tokenizer(doc):
					if tok in self.stopwords:
						tokens.append(self.placeholder)
					else:
						tokens.append(tok)
				yield tokens
