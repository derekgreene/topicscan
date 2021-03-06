from urllib.parse import urlparse, parse_qs
import logging as log
from dash.dependencies import Input, Output

# --------------------------------------------------------------

# cache for layouts that have already been generated by the Dash application
layout_cache = {}

def extract_uid(href):
	""" Extract a layout page's unique ID from a URL, or return an error meessage
	if it is not present in the URL. """
	parts = urlparse(href.lower())
	query = parse_qs(parts.query)
	error = None
	if "uid" in query and len(query["uid"]) > 0:
		param_uid = query["uid"][0]
		if param_uid not in layout_cache:
			error = "Unknown unique state identifier was provided"
	else:
		error = "No unique state identifier was provided"
	return param_uid, error

# --------------------------------------------------------------

def register_topics_callbacks(app):
	""" Set up the callbacks for TopicModelLayout """

	@app.callback(Output('content_term_assoc', 'children'), 
		[Input('url', 'href'), Input('topic-term-dropdown', 'value')])
	def topics_term_assoc_topic(href, topic_index):
		log.debug("Callback: topics_term_assoc_topic: %s" % topic_index)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_term_topic_index = int(topic_index)
		return layout_cache[uid].generate_term_association_chart()

	@app.callback(Output('content_document_assoc', 'children'), 
		[Input('url', 'href'), Input('topic-document-dropdown', 'value')])
	def topics_document_assoc_topic(href, topic_index):
		log.debug("Callback: topics_document_assoc_topic: %s" % topic_index)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_document_topic_index = int(topic_index)
		return layout_cache[uid].generate_document_association_chart()

# --------------------------------------------------------------

def register_embedding_callbacks(app):
	""" Set up the callbacks for EmbeddingLayout """

	@app.callback(Output('content_neighbor_table', 'children'), 
		[Input('url', 'href'), Input('query-embed', 'value')])
	def embedding_neighbor_query(href, query_string):
		log.info("Callback %s: embedding_neighbor_query: query_string=%s" % (href, query_string))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		return layout_cache[uid].generate_neighbor_table(query_string)

	@app.callback(Output('content_embed_heatmap', 'children'), 
		[Input('url', 'href'), Input('query-embed', 'value')])
	def embedding_heatmap_query(href, query_string):
		log.info("Callback %s: embedding_heatmap_query: query_string=%s" % (href, query_string))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		return layout_cache[uid].generate_embed_heatmap(query_string)

# --------------------------------------------------------------

def register_validation_callbacks(app):
	""" Set up the callbacks for ValidationlLayout """

	@app.callback(Output('content_vtable', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def update_embed_dropdown1(href, embed_id):
		log.debug("Callback: update_embed_dropdown1: embed_id=%s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_vtable()

	@app.callback(Output('content_vchart', 'children'),
		[Input('url', 'href'), Input('measure-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def validation_measure_dropdown1(href, measure_id, embed_id):
		log.debug("Callback: validation_measure_dropdown1: measure_id=%s embed_id=%s" % (measure_id, embed_id))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_measure_id = measure_id
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_vchart()

	@app.callback(Output('content_vsummary', 'children'),
		[Input('url', 'href'), Input('measure-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def validation_measure_dropdown2(href, measure_id, embed_id):
		log.debug("Callback: validation_measure_dropdown2: measure_id=%s embed_id=%s" % (measure_id, embed_id))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_measure_id = measure_id
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_vsummary()

	@app.callback(Output('content_vdistribution', 'children'), 
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def validation_embed_dropdown2(href, embed_id):
		log.debug("Callback: validation_embed_dropdown2: embed_id=%s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_vdistribution()

# --------------------------------------------------------------

def register_silhouette_callbacks(app):
	""" Set up the callbacks for SilhouetteLayout """

	@app.callback(Output('silhouette_content_topiclevel', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def silhouette_embed_topiclevel(href, embed_id):
		log.debug("Callback: silhouette_embed_topiclevel: %s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_topiclevel_chart()

	@app.callback(Output('silhouette_content_distribution', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def silhouette_embed_dist(href, embed_id):
		log.debug("Callback: silhouette_embed_dist: %s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_distribution_chart()

	@app.callback(Output('silhouette_content_termlevel', 'children'),
		[Input('url', 'href'), Input('topic-sil-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def silhouette_topic_termlevel(href, topic_index, embed_id):
		log.debug("Callback: silhouette_topic_termlevel: (%s,%s)" % (topic_index,embed_id))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_topic_index = int(topic_index)
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_termlevel_chart()

# --------------------------------------------------------------

def register_heatmap_callbacks(app):
	""" Set up the callbacks for HeatmapLayout """

	@app.callback(Output('heatmap_content_topiclevel', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def heatmap_embed_topiclevel(href, embed_id):
		""" Callback to handle changes to the embedding dropdown """
		log.debug("Callback: heatmap_embed_topiclevel: %s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_topiclevel_heatmap()

	@app.callback(Output('heatmap_content_termlevel', 'children'),
		[Input('url', 'href'), Input('termlevel-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def heatmap_termlevel_dropdown(href, topic_index, embed_id):
		""" Callback to handle changes to the topic dropdown """
		log.debug("Callback: heatmap_termlevel_dropdown: topic_index=%s embed_id=%s" % (topic_index, embed_id))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_topic_index = int(topic_index)
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_termlevel_heatmap()

# --------------------------------------------------------------

def register_scatter_callbacks(app):
	""" Set up the callbacks for ScatterLayout """

	@app.callback(Output('scatter_content_topiclevel', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def scatter_embed_topiclevel(href, embed_id):
		log.debug("Callback: scatter_embed_topiclevel: %s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_topiclevel_plot()

	@app.callback(Output('scatter_content_termlevel', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def scatter_embed_termlevel(href, embed_id):
		log.debug("Callback: scatter_embed_termlevel: %s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_termlevel_plot()	

# --------------------------------------------------------------

def register_comparison_callbacks(app):
	""" Set up the callbacks for ComparisonLayout """

	@app.callback(Output('content_compare_vtable', 'children'),
		[Input('url', 'href'), Input('embed-dropdown', 'value')])
	def update_compare_embed_dropdown(href, embed_id):
		log.info("Callback: update_embed_dropdown: embed_id=%s" % embed_id)
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_vtable()

	@app.callback(Output('content_compare_vchart', 'children'),
		[Input('url', 'href'), Input('measure-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def update_compare_measure_dropdown(href, measure_id, embed_id):
		log.info("Callback: update_measure_dropdown: measure_id=%s embed_id=%s" % (measure_id, embed_id))
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_measure_id = measure_id
		layout_cache[uid].current_embed_id = embed_id
		return layout_cache[uid].generate_vchart()

	@app.callback(Output('content_compare_matching', 'children'),
		[Input('url', 'href'), Input('compare-model-dropdown1', 'value'), Input('compare-model-dropdown2', 'value')])
	def update_compare_model_dropdown1(href, s_index1, s_index2):
		model_index1, model_index2 = int(s_index1), int(s_index2)
		log.info("Callback: update_compare_model_dropdown: model_index1=%d model_index2=%d" % (model_index1, model_index2) )
		uid, error = extract_uid(href)
		if error is not None:
			log.error("%s: %s" % (error, href))
			return error
		layout_cache[uid].current_metadata_indices = [model_index1, model_index2]
		return layout_cache[uid].generate_matching_table()