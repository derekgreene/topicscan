#!/usr/bin/env python
"""
Applies NMF to the specified dataset to generate one or more topic models.

Sample usage:
python topicscan/topic_nmf.py bbc.pkl --init random --kmin 5 --kmax 5 -r 5 --maxiters 100 -o models/bbc
"""
import sys, json
from pathlib import Path
import logging as log
from optparse import OptionParser
import numpy as np
import text.util, model.nmf, model.util

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] corpus_file")
	parser.add_option("--seed", action="store", type="int", dest="seed", help="random seed", default=1000)
	parser.add_option("--kmin", action="store", type="int", dest="kmin", help="minimum number of topics (default is 5)", default=5)
	parser.add_option("--kmax", action="store", type="int", dest="kmax", help="maximum number of topics (if not specified, this will be kmin)", default=-1)
	parser.add_option('--step' ,type="int", dest="step", help="Step size for incrementing the number of topics", default=1)
	parser.add_option("-i","--init", action="store", type="string", dest="init_strategy", help="initialization strategy (random or nndsvd)", default="random")
	parser.add_option("--maxiters", action="store", type="int", dest="maxiters", help="maximum number of iterations", default=100)
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
	# validate the number of topics
	kmin, kmax = options.kmin, options.kmax
	if kmin < 2:
		log.error("Error: Invalid value for number of topics kmin=%s" % kmin)
		sys.exit(1)
	if kmax < 2:
		kmax = kmin

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
	impl = model.nmf.NMFWrapper(max_iters=options.maxiters, init_strategy=options.init_strategy)

	# generate all NMF topic models for the specified numbers of topics
	log.info("Generating NMF models in range k=[%d,%d], init_strategy=%s" % (kmin, kmax, options.init_strategy))
	for k in range(kmin, kmax+1, options.step):
		# set the current random state
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
		# create a template for the metadata
		metadata_template = {
			"type":"topic_model",
			"corpus":corpus_id,
			"documents":len(doc_ids),
			"terms":len(terms),
			"k":k,
			"algorithm":{ "id":"nmf-%s" % options.init_strategy } 
		}
		metadata_template["algorithm"]["params"] = { 
			"k":k, 
			"init":options.init_strategy, 
			"seed":options.seed, 
			"max_iterations":options.maxiters
		} 
		# execute the specified number of runs
		for r in range(options.runs):
			log.info("NMF run %d/%d (k=%d, max_iters=%d)" % (r+1, options.runs, k, options.maxiters))
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
			fname_ranks = "%s_ranks.pkl" % file_prefix
			ranks_out_path = dir_out_k / fname_ranks
			log.debug("Writing term ranking set to %s" % ranks_out_path)
			model.util.save_term_rankings(ranks_out_path, term_rankings)
			# write document partition
			partition = impl.generate_partition()
			fname_partition = "%s_partition.pkl" % file_prefix
			partition_out_path = dir_out_k / fname_partition
			log.debug("Writing document partition to %s" % partition_out_path)
			model.util.save_partition(partition_out_path, partition, doc_ids)			
			# write the complete factorization
			fname_factors = "%s_factors.pkl" % file_prefix
			factor_out_path = dir_out_k / fname_factors
			# NB: need to make a copy of the factors
			log.debug("Writing factorization to %s" % factor_out_path)
			model.util.save_nmf_factors(factor_out_path, np.array(impl.W), np.array(impl.H), doc_ids, terms)
			# update the metadata and write it
			metadata = metadata_template.copy()
			metadata["files"] = {
				"factors":fname_factors,
				"partition":fname_partition,
				"ranks":fname_ranks
			}
			metadata["descriptors"] = []
			truncated_rankings = model.util.truncate_term_rankings( term_rankings, 10 )
			for descriptor in truncated_rankings:
				metadata["descriptors"].append(descriptor)
			metadata["algorithm"]["params"]["run"] = r+1
			metadata_out_path = dir_out_k / ("%s.meta" % file_prefix)
			log.info("Writing topic model metadata to %s" % metadata_out_path)
			with open(metadata_out_path, "w", encoding="utf8", errors="ignore") as fout:
				fout.write(json.dumps(metadata, indent=4))
				fout.write("\n")
		  
# --------------------------------------------------------------

if __name__ == "__main__":
	main()
