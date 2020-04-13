#!/usr/bin/env python
"""
Script implementing the main TopicScan interface.

Sample usage:
``` python topicscan/scan.py ./data/models ```
"""
import sys
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import logging as log
from optparse import OptionParser
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
# TopicScan imports
from webcore import WebCore
from webcallbacks import layout_cache
from webcallbacks import register_topics_callbacks, register_embedding_callbacks, register_validation_callbacks
from webcallbacks import register_heatmap_callbacks, register_scatter_callbacks, register_silhouette_callbacks
from layouts.general import external_stylesheets
from layouts.index import IndexLayout
from layouts.topics import TopicModelLayout
from layouts.embedding import EmbeddingLayout
from layouts.error import ErrorLayout
from layouts.validation import ValidationLayout
from layouts.silhouette import SilhouetteLayout
from layouts.heatmap import HeatmapLayout
from layouts.scatter import ScatterLayout

# --------------------------------------------------------------

def parse_page_url(href):
	""" Tidy and parse the specified page URL """
	parts = urlparse(href.lower())
	pathname = parts.path
	query = parse_qs(parts.query)
	# extract common query parameters
	param_id, param_uid = "", ""
	if "uid" in query and len(query["uid"]) > 0:
		param_uid = query["uid"][0]
	if "id" in query and len(query["id"]) > 0:
		param_id = query["id"][0]
	return pathname, query, param_id, param_uid

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] working_directory")
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=True)
	parser.add_option("--preload", action="store_true", dest="preload", help="preload all word embeddings", default=False)
	(options, args) = parser.parse_args()
	# control level of log output
	log_level = log.DEBUG if options.debug else log.INFO
	log.basicConfig(level=log_level, format='%(message)s')
	
	# get the core directory which contains models and embeddings
	if len(args) > 0:
		dir_core = Path(args[0]).resolve()
	else:
		dir_core = Path.cwd().resolve()
	if not (dir_core.exists() and dir_core.is_dir()):
		log.error("Invalid core directory path specified: %s" % args[0])
		sys.exit(1)

	# create the core
	webcore = WebCore(dir_core)
	webcore.init(options.preload)

	# create the index layout
	layout_index = IndexLayout(webcore)

	# generate the Dash app around the interface
	app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
	app.config.suppress_callback_exceptions = True
	app.title = layout_index.page_title

	# create the parent layout which will hold multiple pages
	app.layout = html.Div([
		dcc.Location(id='url', refresh=False),
		html.Div(id='page-content')
	])

	# Page Routing 
	@app.callback(Output('page-content', 'children'), 
		[Input('url', 'href')])
	def display_page(href):
		""" Display the appropriate layout, based on the current URL. """
		pathname, query, param_id, param_uid = parse_page_url(href)
		layout_name = pathname.strip().lower()
		if layout_name[0] == "/":
			layout_name = layout_name[1:]
		# request for the main page?
		if layout_name == "" or layout_name == "index":
			log.info("Request for %s: Index" % href)
			return layout_index.generate_layout()
		log.info("Request for %s: Layout '%s' %s" % (href, layout_name, query))
		# topic model details page
		if layout_name == "topics":
			if len(param_uid) == 0:
				return ErrorLayout(webcore, "No unique state identifier was provided.").generate_layout()
			if len(param_id) == 0:
				return ErrorLayout(webcore, "No topic model identifier was provided.").generate_layout()
			topic_metadata = webcore.get_topic_model_metadata(param_id)
			topic_metadata.load_all_files()
			layout_cache[param_uid] = TopicModelLayout(webcore, topic_metadata)
			return layout_cache[param_uid].generate_layout()
		# embedding details layout page
		elif layout_name == "embedding":
			if len(param_uid) == 0:
				return ErrorLayout(webcore, "No unique state identifier was provided.").generate_layout()
			if len(param_id) == 0:
				return ErrorLayout(webcore, "No topic word embedding identifier was provided.").generate_layout()
			embed_metadata = webcore.get_embedding_metadata(param_id)
			layout_cache[param_uid] = EmbeddingLayout(webcore, embed_metadata)
			return layout_cache[param_uid].generate_layout()
		# topic model validation layout page
		elif layout_name == "validation":
			if len(param_uid) == 0:
				return ErrorLayout(webcore, "No unique state identifier was provided.").generate_layout()
			if len(param_id) == 0:
				return ErrorLayout(webcore, "No topic model identifier was provided.").generate_layout()
			topic_metadata = webcore.get_topic_model_metadata(param_id)
			topic_metadata.load_all_files()
			layout_cache[param_uid] = ValidationLayout(webcore, topic_metadata)
			return layout_cache[param_uid].generate_layout()
		# silhouette visualization layout page
		elif layout_name == "silhouette":
			if len(param_uid) == 0:
				return ErrorLayout(webcore, "No unique state identifier was provided.").generate_layout()
			if len(param_id) == 0:
				return ErrorLayout(webcore, "No topic model identifier was provided.").generate_layout()
			topic_metadata = webcore.get_topic_model_metadata(param_id)
			topic_metadata.load_all_files()
			layout_cache[param_uid] = SilhouetteLayout(webcore, topic_metadata)
			return layout_cache[param_uid].generate_layout()
		# heatmap visualization layout page
		elif layout_name == "heatmap":
			if len(param_uid) == 0:
				return ErrorLayout(webcore, "No unique state identifier was provided.").generate_layout()
			if len(param_id) == 0:
				return ErrorLayout(webcore, "No topic model identifier was provided.").generate_layout()
			topic_metadata = webcore.get_topic_model_metadata(param_id)
			topic_metadata.load_all_files()
			layout_cache[param_uid] = HeatmapLayout(webcore, topic_metadata)
			return layout_cache[param_uid].generate_layout()			
		# scatter plot layout page
		elif layout_name == "scatter":
			if len(param_uid) == 0:
				return ErrorLayout(webcore, "No unique state identifier was provided.").generate_layout()
			if len(param_id) == 0:
				return ErrorLayout(webcore, "No topic model identifier was provided.").generate_layout()
			topic_metadata = webcore.get_topic_model_metadata(param_id)
			topic_metadata.load_all_files()
			layout_cache[param_uid] = ScatterLayout(webcore, topic_metadata)
			return layout_cache[param_uid].generate_layout()			
		# unknown layout
		log.warning("404: Invalid request for layout %s: %s" % (layout_name, pathname))
		return ErrorLayout(webcore, "Cannot access unknown page **%s**." % layout_name).generate_layout()

	# connect up the rest of the callbacks for the Dash application
	register_topics_callbacks(app)
	register_embedding_callbacks(app)
	register_validation_callbacks(app)
	register_silhouette_callbacks(app)
	register_heatmap_callbacks(app)
	register_scatter_callbacks(app)

	# start the web server
	app.run_server(debug=options.debug)

# --------------------------------------------------------------

if __name__ == "__main__":
	main()
