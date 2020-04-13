#!/usr/bin/env python
"""
Script providing access to the TopicScan page for viewing heatmap plots for a given topic model.

Sample usage:
``` python topicscan/scan_heatmap.py ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta ```
"""
import sys
from pathlib import Path
import logging as log
from optparse import OptionParser
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
# TopicScan imports
from webcore import WebCore, TopicModelMeta
from layouts.general import external_stylesheets
from layouts.heatmap import HeatmapLayout

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] meta_file_path")
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=True)
	parser.add_option("--preload", action="store_true", dest="preload", help="preload all word embeddings", default=False)
	(options, args) = parser.parse_args()
	if len(args) != 1:
		parser.error("Must specify topic model metadata file path")
	# control level of log output
	log_level = log.DEBUG if options.debug else log.INFO
	log.basicConfig(level=log_level, format='%(message)s')

	# get the input file
	in_path = Path(args[0])
	if not in_path.exists():
		log.error("Error: Invalid topic model path specified: %s" % in_path)
		sys.exit(1)

	# use the current working directory as the core directory
	dir_core = Path.cwd()
	# create the core
	webcore = WebCore(dir_core)
	webcore.init(options.preload)

	try:
		# load the model metadata
		topic_metadata = TopicModelMeta(in_path.stem, in_path)
		# preload the other associated files
		topic_metadata.load_all_files()
		# create the interface
		layout = HeatmapLayout(webcore, topic_metadata)
	except Exception as e:
		log.error("Error: Failed to load topic model metadata from %s" % in_path)
		log.error(e)
		sys.exit(1)

	# create the Dash app
	app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
	app.title = layout.page_title

	# create the parent layout which will hold the main page
	app.layout = html.Div([
		html.Div(layout.generate_layout(), id='page-content')
	])

	# --------------------------------------------------------------
	# Callbacks for HeatmapLayout 

	@app.callback(Output('heatmap_content_topiclevel', 'children'),
		[Input('embed-dropdown', 'value')])
	def heatmap_embed_topiclevel(embed_id):
		""" Callback to handle changes to the embedding dropdown """
		log.info("Callback: heatmap_embed_topiclevel: %s" % embed_id)
		layout.current_embed_id = embed_id
		return layout.generate_topiclevel_heatmap()

	@app.callback(Output('heatmap_content_termlevel', 'children'),
		[Input('termlevel-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def heatmap_termlevel_dropdown(topic_index, embed_id):
		""" Callback to handle changes to the topic dropdown """
		log.info("Callback: heatmap_termlevel_dropdown: topic_index=%s embed_id=%s" % (topic_index, embed_id))
		layout.current_topic_index = int(topic_index)
		layout.current_embed_id = embed_id
		return layout.generate_termlevel_heatmap()

	# --------------------------------------------------------------

	# start the web server
	app.run_server(debug=options.debug)

# --------------------------------------------------------------

if __name__ == "__main__":
	main()
