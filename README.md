# TopicScan

*TopicScan* is an interactive web-based dashboard for exploring and evaluating topic models created using Non-negative Matrix Factorization (NMF).
TopicScan contains tools for preparing text corpora, generating topic models with NMF, and validating these models. 

TopicScan interface features include:

- Inspection of topic descriptors, term-topic associations,  document-topic associations, and document partitions.
- Validation of individual topics and overall models based on topic distinctiveness using a range of new measures based on word embeddings.
- Comparisons across multiple topic models using these measures.
- Visualization of topics and models via term similarity heatmaps, term silhouette plots, and multidimensional scaling  scatter plots.

<!---
For more details on TopicScan, see the paper:

	TopicScan: A Visual Validation Tool for NMF Topic Models
	Derek Greene, Mark Belford. Under Review, 2020.
-->
The web interface for TopicScan was created using the Python [Dash platform](https://plotly.com/dash) and [Bootstrap](https://getbootstrap.com) with a variant of the [ElaAdmin theme](https://github.com/puikinsh/ElaAdmin). It is designed to be run locally as a single-user web application, rather than hosted online as a multi-user web application.

## Dependencies

Tested with Python 3.7, and requiring the following packages, which are available via PIP:

- pandas, numpy, matplotlib
- scikit-learn, gensim
- dash, dash-bootstrap-components

## Usage Overview

Using TopicScan involves the follow steps:

1. Preprocessing the plain text data for your corpus.
2. Generate one or more topic models using NMF on your preprocessed corpus files.
3. Explore and compare the resulting topic models in the TopicScan web interface.

To validate and visualize your topic models, you will also need one or more pre-trained word embeddingss.

## Usage: Preprocessing Corpora

Before we run topic modeling for the first time, we need to preprocess the input corpus, by running the script *prep_text.py*. When running the tool specify one or more directories containing documents to preprocess. There are 
two possible input formats for files:

1. Each text file correspond to a single document.
2. Every line of each text file represents a separate document. 

Example where every line of each text file represents a separate document:

``` python prep_text.py -s text/stopwords/english.txt --tfidf --norm -o data/prep/bbc --lines data/corpora/bbc.txt```

Example where every line in each file represents a separate document:

``` python prep_text.py -s text/stopwords/english.txt --tfidf --norm -o data/prep/bbc data/corpora/bbc/*```

## Usage: Generating Topic Models

Once we have a preprocessed corpus prepared, we can generate topic models via the NMF algorithm.

To generate a single topic model with randomly-initialized NMF, containing *k=5* topics, we can execute:

``` python topic_nmf.py data/prep/bbc.pkl --kmin 5 -r 1 -o data/models/bbc```

To execute 10 runs of randomly-initialized NMF, each containing *k=5* topics, we can execute:

``` python topic_nmf.py data/prep/bbc.pkl --kmin 5 -r 10 -o data/models/bbc```

To execute 10 runs of randomly-initialized NMF, for each value of *k* from 5 to 12, we execute:

``` python topic_nmf.py data/prep/bbc.pkl --kmin 5 --kmax 12 -r 10 -o data/models/bbc```

Instead of using randomly-initialized NMF, we can use NNDSVD-based initialization (Boutsidis, 2007):

``` python topic_nmf.py data/prep/bbc.pkl --init nndsvd --kmin 5 -r 1 -o data/models/bbc```

Each run of NMF produces four output files. For instance, for the first run above the script produces one JSON file (#1) and three binary files (#2-4):

1. *data/models/bbc/nmf_k05/bbc_1000_001.meta*: Metadata for topic model, as used by the TopicScan web interface.
2. *data/models/bbc/nmf_k05/bbc_1000_001_ranks.pkl*: Full set of ranked terms for each topic in the model.
3. *data/models/bbc/nmf_k05/bbc_1000_001_partition.pkl*: Disjoint partition of the documents in the model.
4. *data/models/bbc/nmf_k05/bbc_1000_001_factors.pkl*: The complete factor matrices produced by NMF for the model.


## Usage: TopicScan Web Interface

To start the TopicScan interface, run the script *scan.py*. By default this will search the current directory and its subdirectories for topic model and word embedding metadata files:

```python scan.py```

We can also specify an alternative working directory to search:

```python scan.py data/```

Once the local web server has started, you should be able to access it in your browser at [http://127.0.0.1:8050](http://127.0.0.1:8050)

The different pages of TopicScan interface can also be run individually. In each case, we need to specify the path to the relevant metadata file(s):

```python scan_topics.py data/models/bbc/nmf_k05/bbc_k05_001.meta```

```python scan_validation.py data/models/bbc/nmf_k05/bbc_k05_001.meta```

```python scan_silhouette.py data/models/bbc/nmf_k05/bbc_k05_001.meta```

```python scan_scatter.py  data/models/bbc/nmf_k05/bbc_k05_001.meta```

```python scan_heatmap.py  data/models/bbc/nmf_k05/bbc_k05_001.meta```

## Usage: Generating Word Embeddings

A number of pre-trained word embeddings are available online [here](data/) for validating models. 

Custom embeddings can also be trained using *prep_word2vec.py*. As before, the inputs can either be documents as separate text files, or files with one document per line. The word embedding variant can either be Skipgram (sg) or Continuous Bag of Words (cbow).

Example of generating a word2vec Skipgram (sg) model, where every line in each input file represents a separate document:

``` python prep_word2vec.py -m sg -s text/stopwords/english.txt -o data/embeddings/bbc-w2v-sg.bin data/corpora/bbc/*```

Example of generating a word2vec Continuous Bag of Words (cbow) model, where every line of each input text file represents a separate document:

``` python prep_word2vec.py -m cbow -s text/stopwords/english.txt -o data/embeddings/bbc-w2v-cbow.bin --lines data/corpora/bbc.txt```
