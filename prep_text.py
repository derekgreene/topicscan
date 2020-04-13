#!/usr/bin/env python
"""
Tool to preprocess a corpus of documents and construct a vector space model representation. 

When running the tool specify one or more directories containing documents to preprocess. There are 
two possible input formats for files:
1. Each text file represents a single document.
2. Every line of each text file represents a different document. 

Sample usage:
``` python topicscan/prep_text.py -s topicscan/text/stopwords/english.txt --tfidf --norm -o bbc --lines ./topicscan/data/bbc.txt ```
"""
import os, os.path, sys
import logging as log
from optparse import OptionParser
import text.util

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] dir1 dir2 ...")
	parser.add_option("-l","--lines", action="store_true", dest="is_lines", help="each line in a file represents a separate document")
	parser.add_option("--df", action="store", type="int", dest="min_df", help="minimum number of documents for a term to appear", default=20)
	parser.add_option("--tfidf", action="store_true", dest="apply_tfidf", help="apply TF-IDF term weight to the document-term matrix")
	parser.add_option("--norm", action="store_true", dest="apply_norm", help="apply unit length normalization to the document-term matrix")
	parser.add_option("--minlen", action="store", type="int", dest="min_doc_length", help="minimum document length (in characters)", default=50)
	parser.add_option("-s", action="store", type="string", dest="stoplist_file", help="custom stopword file path", default=None)
	parser.add_option("-o", action="store", type="string", dest="prefix", help="output prefix for corpus files", default=None)
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=False)
	# parse command line arguments
	(options, args) = parser.parse_args()
	if len(args) < 1:
		parser.error("Must specify at least one directory of file path")	
	# control level of log output
	log_level = log.DEBUG if options.debug else log.INFO
	log.basicConfig(level=log_level, format='%(message)s')

	# Find all relevant files in the directories specified by user
	file_paths = []
	args.sort()
	for in_path in args:
		# does this exist?
		if not os.path.exists(in_path):
			log.error("Error: No such input path %s" % in_path)
			sys.exit(1)
		# is this a directory?
		if os.path.isdir(in_path):
			log.info("Searching %s for text files ..." % in_path)
			for fpath in text.util.find_text_files(in_path):
				file_paths.append(fpath)
		else:
			file_paths.append(in_path)
	log.info("Found %d text files to parse" % len(file_paths))

	# Read the documents
	log.info("Reading documents ...")
	documents, document_ids = [], []
	num_short_documents = 0
	label_counts, labels = {}, {}
	for in_path in file_paths:
		# create the document ID
		label = os.path.basename(os.path.dirname(in_path).replace(" ", "_"))
		doc_id = os.path.splitext(os.path.basename(in_path))[0]
		if not doc_id.startswith(label):
			doc_id = "%s_%s" % (label, doc_id)
		if label not in labels:
			labels[label] = set()
			label_counts[label] = 0
		log.debug("Reading text from %s ..." % in_path)
		# is each line a separate document?
		if options.is_lines:
			for i, body in enumerate(text.util.read_text_lines(in_path)):
				if len(body) < options.min_doc_length:
					num_short_documents += 1
					continue
				documents.append(body)	
				line_doc_id = "%s_%04d" % (doc_id,(i+1))
				document_ids.append(line_doc_id)	
				labels[label].add(line_doc_id)
				label_counts[label] += 1
		# otherwise each file is a sparate document
		else:
			body = text.util.read_text(in_path)
			if len(body) < options.min_doc_length:
				num_short_documents += 1
				continue
			documents.append(body)	
			document_ids.append(doc_id)	
			labels[label].add(doc_id)
			label_counts[label] += 1
	log.info("Kept %d documents. Skipped %d documents with length < %d" % 
		(len(documents), num_short_documents, options.min_doc_length))
	# any document labels?
	if len(labels) >= 2:
		log.info("Document categories: %d labels - %s" % (len(labels), label_counts))

	# load stopwords, if any file path has been specified
	stopwords = set()
	if not options.stoplist_file is None:
		stopwords = text.util.load_word_set(options.stoplist_file)
		log.info("Using %d stopwords from %s" % (len(stopwords), options.stoplist_file) )

	# Convert the documents to a vector representation
	log.info("Preprocessing data (%d stopwords, tfidf=%s, normalize=%s, min_df=%d) ..." % 
		(len(stopwords), options.apply_tfidf, options.apply_norm, options.min_df))
	(X,terms) = text.util.preprocess(documents, stopwords, min_df = options.min_df, 
		apply_tfidf = options.apply_tfidf, apply_norm = options.apply_norm)
	log.info("Built document-term matrix: %d documents, %d terms" % (X.shape[0], X.shape[1]))
	
	# Save the preprocessed corpus
	prefix = options.prefix
	if prefix is None:
		prefix = "corpus"
	log.info("Saving corpus '%s'" % prefix)
	text.util.save_corpus(prefix, X, terms, document_ids, labels)
  
# --------------------------------------------------------------

if __name__ == "__main__":
	main()
