#!/usr/bin/env python
"""
Tool to pre-process a corpus of documents and build a Word2Vec word embedding. 

This implementation requires Gensim. For documentation regarding the various parameters, see:
https://radimrehurek.com/gensim/models/word2vec.html

When running the tool specify one or more directories containing documents to preprocess. There are 
two possible input formats for files:
1. Each text file represents a single document.
2. Every line of each text file represents a different document. 

Sample usage:
python topicscan/prep_word2vec.py -m sg -d 100 -s topicscan/text/stopwords/english.txt -o bbc-w2v-sg.bin --lines ./topicscan/data/bbc.txt
"""
import os, os.path, sys, json
import logging as log
from optparse import OptionParser
import numpy as np
from gensim.models import Word2Vec
import text.util
from model.util import init_random_seeds

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] directory1 directory2 ...")
	parser.add_option("--seed", action="store", type="int", dest="seed", help="random seed", default=1000)
	parser.add_option("-l","--lines", action="store_true", dest="is_lines", help="each line in a file represents a separate document")
	parser.add_option("--df", action="store", type="int", dest="min_df", help="minimum number of documents for a term to appear", default=20)
	parser.add_option("-d","--dimensions", action="store", type="int", dest="dimensions", help="the dimensionality of the word vectors", default=100)
	parser.add_option("--window", action="store", type="int", dest="window_size", 
		help="the maximum distance for Word2Vec to use between the current and predicted word within a sentence", default=5)
	parser.add_option("-m", action="store", type="string", dest="embed_type", help="type of word embedding to build (sg or cbow)", default="sg")
	parser.add_option("-s", action="store", type="string", dest="stoplist_file", help="custom stopword file path", default=None)
	parser.add_option("--minlen", action="store", type="int", dest="min_doc_length", help="minimum document length (in characters)", default=10)
	parser.add_option("-o", action="store", type="string", dest="out_path", help="output path for corpus files", default=None)
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=False)
	# parse command line arguments
	(options, args) = parser.parse_args()
	if len(args) < 1:
		parser.error("Must specify at least one directory of file path")	
	# control level of log output
	log_level = log.DEBUG if options.debug else log.INFO
	log.basicConfig(level=log_level, format='%(message)s')

	# set the random state
	init_random_seeds(options.seed)

	# load stopwords, if any file path has been specified
	stopwords = set()
	if not options.stoplist_file is None:
		stopwords = text.util.load_word_set(options.stoplist_file)
		log.info("Using %d stopwords from %s" % (len(stopwords), options.stoplist_file) )

	# Find all relevant files in the directories specified by user
	file_paths = []
	args.sort()
	for in_path in args:
		# does this exist?
		if not os.path.exists(in_path):
			log.error("Error: No such input path %s" % in_path)
			sys.exit(1)
		# is this a directory? if so, then walk the directory
		if os.path.isdir(in_path):
			log.info("Searching %s for text files ..." % in_path)
			for fpath in text.util.find_text_files(in_path):
				file_paths.append(fpath)
		else:
			file_paths.append(in_path)
	if len(file_paths) == 0:
		log.error("Error: Found no text files to preprocess")
		sys.exit(1)
	log.info("Found %d text files to preprocess" % len(file_paths))

	# process all specified inputs
	if options.is_lines:
		token_generator = text.util.LineTokenGenerator(file_paths, options.min_doc_length, stopwords)
	else:
		token_generator = text.util.FileTokenGenerator(file_paths, options.min_doc_length, stopwords)

	# build the Word2Vec embedding from the documents that we have found
	log.info( "Building Word2vec %s embedding..." % options.embed_type )
	if options.embed_type == "cbow":
		sg = 0
	elif options.embed_type == "sg":
		sg = 1
	else:
		log.error("Unknown embedding variant type '%s'" % options.embed_type )
		sys.exit(1)
	embed = Word2Vec(token_generator, size=options.dimensions, min_count=options.min_df, 
		window=options.window_size, workers=4, sg = sg, seed=options.seed)
	log.info( "Built word embedding %s" % embed )

	# save the Word2Vec model
	out_path = options.out_path
	if out_path is None:
		out_path = "w2v-%s-d%d.bin" % ( options.embed_type, options.dimensions )
	log.info( "Writing word embedding to %s ..." % out_path )
	# always save in binary format
	embed.wv.save_word2vec_format(out_path, binary=True) 

	# create the metadata for this embedding
	out_filename = os.path.split(out_path)[-1]
	metadata = {
		"type":"embedding",
		"file":out_filename,
		"corpus":os.path.splitext(out_filename)[0],
		"description":"",
		"dimensions":options.dimensions,
		"terms":3078,
		"algorithm":{ 
			"id":"word2vec-%s" % options.embed_type,
			"parameters":{
				"window":options.window_size,
				"dimensions":options.dimensions,
				"seed":options.seed
			}
		} 
	}	
	# write the metadata
	metadata_out_path = "%s.meta" % os.path.splitext(out_path)[0]
	log.info("Writing topic model metadata to %s" % metadata_out_path)
	with open(metadata_out_path, "w", encoding="utf8", errors="ignore") as fout:
		fout.write(json.dumps(metadata, indent=4))
		fout.write("\n")
			
# --------------------------------------------------------------

if __name__ == "__main__":
	main()
