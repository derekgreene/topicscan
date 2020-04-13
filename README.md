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

## Running the TopicScan Interface

To start the TopicScan interface, run the script *scan.py*. By default this will search the current directory and its subdirectories for topic model and word embedding metadata files:

```python topicscan/scan.py```

We can also specify an alternative working directory to search:

```python topicscan/scan.py ~/sample```

### Running Individual Pages

The different pages of TopicScan interface can also be run individually. In each case, we need to specify the path to the relevant metadata file(s):

```python topicscan/scan_topics.py ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_validation.py ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_silhouette.py ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_scatter.py  ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta```

```python topicscan/scan_heatmap.py  ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta```
