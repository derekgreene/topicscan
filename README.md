# TopicScan

*TopicScan* is an interactive web-based dashboard for exploring and evaluating topic models created using Non-negative Matrix Factorization (NMF).
TopicScan contains tools for preparing text corpora, generating topic models with NMF, and validating these models using a variety of measures based on [word embeddings](https://en.wikipedia.org/wiki/Word_embedding).

For more details on TopicScan, please see the paper:

	TopicScan: A Visual Validation Tool for NMF Topic Models
	Derek Greene, Mark Belford. Under Review, 2020.

The web interface for TopicScan was created using the Python [Dash platform](https://plotly.com/dash) and [Bootstrap](https://getbootstrap.com), with the [ElaAdmin theme](https://github.com/puikinsh/ElaAdmin). It is designed to be run locally as a personal web application, rather than online as a multi-user web application.

## Dependencies

Tested with Python 3.7, and requiring the following packages, which are available via PIP:

- pandas, numpy, matplotlib
- scikit-learn, gensim
- dash, dash-table, dash-bootstrap-components

## Usage Overview

Using TopicScan involves the follow steps:

1. Preprocessing the plain text data for your corpus.
2. Generate one or more topic models using NMF on your preprocessed corpus files.
3. Explore and compare the resulting topic models in the TopicScan web interface.

To validate and visualize your topic models, you will also need one or more pre-trained word embeddingss.

## Usage: Preprocessing Corpora

Before we run topic modeling for the first time, we need to preprocess the input corpus, by running the script *prep_text.py*. When running the tool specify one or more directories containing documents to preprocess. There are 
two possible input formats for files:

1. Each text file represents a single document.
2. Every line of each text file represents a different document. 

Example where every line each file represents a different document:

``` python topicscan/prep_text.py -s topicscan/text/stopwords/english.txt --tfidf --norm -o bbc data/bbc/*```

Example where every line of each text file represents a different document:

``` python topicscan/prep_text.py -s topicscan/text/stopwords/english.txt --tfidf --norm -o bbc --lines data/bbc.txt```


## Usage: Generating Topic Models

Once we have a preprocessed corpus prepared, we can generate topic models via the NMF algorithm.

To generate a single topic model with randomly-initialized NMF, containing $k=5$ topics, we can run:

``` python topicscan/topic_nmf.py bbc.pkl --init random --kmin 5 --kmax 5 -r 1 --maxiters 100 -o models/bbc```

To execute 10 runs of randomly-initialized NMF, each containing $k=5$ topics, we can run:

``` python topicscan/topic_nmf.py bbc.pkl --init random --kmin 5 --kmax 5 -r 10 --maxiters 100 -o models/bbc```

To execute 10 runs of randomly-initialized NMF, for each value of $k$ from 5 to 8, run:

``` python topicscan/topic_nmf.py bbc.pkl --init random --kmin 5 --kmax 8 -r 10 --maxiters 100 -o models/bbc```

Instead of using randomly-initialized NMF, we can use NNDSVD-based initialization (Boutsidis, 2007):

``` python topicscan/topic_nmf.py bbc.pkl --init nndsvd --kmin 5 --kmax 5 -r 1 --maxiters 100 -o models/bbc```

## Usage: TopicScan Web Interface

To start the TopicScan interface, run the script *scan.py*. By default this will search the current directory and its subdirectories for topic model and word embedding metadata files:

```python topicscan/scan.py```

We can also specify an alternative working directory to search:

```python topicscan/scan.py ~/sample```

The different pages of TopicScan interface can also be run individually. In each case, we need to specify the path to the relevant metadata file(s):

```python topicscan/scan_topics.py models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_validation.py models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_silhouette.py models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_scatter.py  models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_heatmap.py  models/bbc/nmf_k05/bbc_k05_001.meta```
