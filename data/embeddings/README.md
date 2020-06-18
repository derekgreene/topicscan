# TopicScan 

Word embeddings can be placed in this directory for use by TopicScan.

### Word Embeddings

A number of pretrained word embeddings for use with *TopicScan* are listd below. Note these are hosted elsewhere and can be downloaded and placed here. 

| Embedding                   | Algorithm     | Description                                                                            | Terms   | Download    |
|-----------------------------|---------------|----------------------------------------------------------------------------------------|---------|-------------|
| *cnndailymail-w2v-cbow-d100*  | word2vec cbow | Collection of 312k CNN and Daily Mail news articles, compiled by Hermann et al in 2015. | 243863  | ZIP (95MB)  |
| *cnndailymail-w2v-sg-d100*    | word2vec sg   | Collection of 312k CNN and Daily Mail news articles, compiled by Hermann et al in 2015. | 243863  | ZIP (95MB)  |
| *guardian15-w2v-cbow-d100*    | word2vec cbow | Corpus of over 1.5m articles from 15 years of Guardian online news, compiled by Belford & Greene.                     | 557937  | ZIP (218MB) |
| *guardian15-w2v-sg-d100*      | word2vec sg   | Corpus of over 1.5m articles from 15 years of Guardian online news, compiled by Belford & Greene                     | 557937  | ZIP (218MB) |
| *wapo-w2v-cbow-d100*          | word2vec cbow | A corpus of 595k Washington Post news articles from the [TREC News Track](http://trec-news.org/).                | 298515  | ZIP (117MB) |
| *wapo-w2v-sg-d100*            | word2vec sg   | A corpus of 595k Washington Post news articles from the [TREC News Track](http://trec-news.org/).                 | 298515  | ZIP (117MB) |
| *wikipedia2016-w2v-cbow-d100* | word2vec cbow | Collection of 4.9m Wikipedia long abstracts, compiled by Qureshi & Greene in 2016.                                  | 1333306 | ZIP (521MB) |
| *wikipedia2016-w2v-sg-d100*   | word2vec sg   | Collection of 4.9m Wikipedia long abstracts, compiled by Qureshi & Greene in 2016.                                 | 1333306 | ZIP (521MB) |


### References

References in relation to the corpora and embeddings above:

- M. Belford and D. Greene, Explainable Ensemble Topic Models using Weighted Term Co-associations Mark Belford. Under review, 2020.
- M. Qureshi and D. Greene, EVE: Explainable vector based embedding technique using Wikipedia, Journal of Intelligent Information Systems, 2018. [[PDF]](http://derekgreene.com/papers/qureshi18eve.pdf)
- K. M. Hermann et al. Teaching Machines to Read and Comprehend. In Proc. Neural Information Processing Systems, 2015.
- D. Greene and P. Cunningham, Practical Solutions to the Problem of Diagonal Dominance in Kernel Document Clustering, in Proc. 23rd International Conference on Machine learning (ICML’06), 2006. [[PDF]](http://derekgreene.com/papers/greene06icml.pdf)

