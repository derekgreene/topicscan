# TopicScan

TopicScan is an interactive web-based dashboard for exploring and evaluating topic models created using Non-negative Matrix Factorization (NMF). 

TopicScan contains tools for preparing text corpora, generating topic models with NMF, and validating these models using a variety of measures based on [word embeddings](https://en.wikipedia.org/wiki/Word_embedding).

The web interface for TopicScan was created using the Python [Dash platform](https://plotly.com/dash) and [Bootstrap](https://getbootstrap.com), with the [ElaAdmin theme](https://github.com/puikinsh/ElaAdmin). It is designed to be run locally as a personal web application, rather than online as a multi-user web application.

## Dependencies

- pandas
- numpy
- scikit-learn
- gensim
- plotly
- matplotlib
- dash
- dash-table
- dash-bootstrap-components
