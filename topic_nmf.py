#!/usr/bin/env python
"""
Applies NMF to the specified dataset to generate one or more topic models.

Sample usage:
python topicscan/topic_nmf.py bbc.pkl --init random --kmin 5 --kmax 5 -r 5 --maxiters 100 -o models/bbc
"""
import sys
from pathlib import Path
import logging as log
from optparse import OptionParser
import numpy as np
import text.util, model.nmf, model.util

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] corpus_file")
	parser.add_option("--seed", action="store", type="int", dest="seed", help="random seed", default=1000)
	parser.add_option("--kmin", action="store", type="int", dest="kmin", help="minimum number of topics", default=5)
	parser.add_option("--kmax", action="store", type="int", dest="kmax", help="maximum number of topics", default=5)
	parser.add_option('--step' ,type="int", dest="step", help="Step size for incrementing the number of topics", default=1)
	parser.add_option("-i","--init", action="store", type="string", dest="init_strategy", help="initialization strategy (random or nndsvd)", default="random")
	parser.add_option("--maxiters", action="store", type="int", dest="maxiter", help="maximum number of iterations", default=100)
	parser.add_option("-r","--runs", action="store", type="int", dest="runs", help="number of runs", default=1)
	parser.add_option("-o","--outdir", action="store", type="string", dest="dir_out", help="base output directory (default is current directory)", default=None)
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=False)
	# parse command line arguments
	(options, args) = parser.parse_args()
	if len(args) < 1:
		parser.error("Must specify at least one preprocess corpus file")	
	# control level of log output
	log_level = log.DEBUG if options.debug else log.INFO
	log.basicConfig(level=log_level, format='%(message)s')

	# where will we store the output files?
	if options.dir_out is None:
		dir_out_base = Path.cwd()
	else:
		dir_out_base = Path(options.dir_out)
		if not ( dir_out_base.exists() and dir_out_base.is_dir() ):
			log.error("Error: Invalid output directory %s" % dir_out_base)
			sys.exit(1)

	# load the preprocessed corpus
	corpus_path = Path(args[0])
	if not corpus_path.exists():
		log.error("Error: No such input file %s" % corpus_path)
		sys.exit(1)
	(X,terms,doc_ids,_) = text.util.load_corpus(corpus_path)
	corpus_id = corpus_path.stem
	log.info("Loaded preprocessed corpus '%s': %d documents, %d terms" % (corpus_id, len(doc_ids), len(terms)))

	# get the algorithm implementation
	impl = model.nmf.NMFWrapper(max_iters = options.maxiter, init_strategy = options.init_strategy)

	# generate all NMF topic models for the specified numbers of topics
	log.info("Generating NMF models in range k=[%d,%d], init_strategy=%s" % (options.kmin, options.kmax, options.init_strategy))
	for k in range(options.kmin, options.kmax+1, options.step):
		# Set random state
		model.util.init_random_seeds(options.seed)
		log.info("Applying NMF (k=%d, runs=%d, seed=%s) ..." % (k, options.runs, options.seed))
		# choose the appropriate output directory
		if options.init_strategy == "random":
			dir_out_k = dir_out_base / ("nmf_k%02d" % k)
		else:
			dir_out_k = dir_out_base / ("%s_k%02d" % (options.init_strategy.lower(), k))
		if not dir_out_k.exists():
			dir_out_k.mkdir(parents=True, exist_ok=True)	
		log.debug("Results will be written to %s" % dir_out_k)
		# execute the specified number of runs
		for r in range(options.runs):
			log.info("NMF run %d/%d (k=%d, max_iters=%d)" % (r+1, options.runs, k, options.maxiter))
			file_prefix = "%s_%s_%03d" % (corpus_id, options.seed, r+1)
			# apply NMF
			impl.apply(X, k)
			# get term rankings for each topic
			term_rankings = []
			for topic_index in range(k):		
				ranked_term_indices = impl.rank_terms(topic_index)
				term_ranking = [terms[i] for i in ranked_term_indices]
				term_rankings.append(term_ranking)
			# write term rankings
			ranks_out_path = dir_out_k / ("%s_ranks.pkl" % file_prefix)
			log.debug("Writing term ranking set to %s" % ranks_out_path)
			model.util.save_term_rankings(ranks_out_path, term_rankings)
			# write document partition
			partition = impl.generate_partition()
			partition_out_path = dir_out_k / ("%s_partition.pkl" % file_prefix)
			log.debug("Writing document partition to %s" % partition_out_path)
			model.util.save_partition(partition_out_path, partition, doc_ids)			
			# write the complete factorization
			factor_out_path = dir_out_k / ("%s_factors.pkl" % file_prefix)
			# NB: need to make a copy of the factors
			log.debug("Writing factorization to %s" % factor_out_path)
			model.util.save_nmf_factors(factor_out_path, np.array(impl.W), np.array(impl.H), doc_ids, terms)
		  
# --------------------------------------------------------------

if __name__ == "__main__":
	main()
