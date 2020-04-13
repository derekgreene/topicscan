#!/usr/bin/env python
"""
Script providing access to the TopicScan page for comparing two or more topic models.

Sample usage:
``` python topicscan/scan_compare.py ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta ```
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
from layouts.comparison import ComparisonLayout

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] meta_file_path1 meta_file_path2 ...")
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=True)
	parser.add_option("--preload", action="store_true", dest="preload", help="preload all word embeddings", default=False)
	(options, args) = parser.parse_args()
	if len(args) < 2:
		parser.error("Must specify two or more topic model metadata file paths")
	# control level of log output
	log_level = log.DEBUG if options.debug else log.INFO
	log.basicConfig(level=log_level, format='%(message)s')

	# use the current working directory as the core directory
	dir_core = Path.cwd()

	# create the core
	webcore = WebCore(dir_core)
	webcore.init(options.preload)

	# read the topic model metadata input files
	all_metadata = []
	for in_path in args:
		in_path = Path(in_path)
		if not in_path.exists():
			log.error("Error: Invalid topic model path specified: %s" % in_path)
			sys.exit(1)
		# load the model metadata
		try:
			topic_metadata = TopicModelMeta(in_path.stem, in_path)
			# preload the other associated files
			topic_metadata.load_all_files()
			all_metadata.append(topic_metadata)
		except Exception as e:
			log.error("Error: Failed to load topic model metadata from %s" % in_path)
			log.error(e)
			sys.exit(1)
	log.info("Loaded metadata for %d topic models" % len(all_metadata))

	# create the page layout
	layout = ComparisonLayout(webcore, all_metadata)

	# create the Dash app
	app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
	app.title = layout.page_title

	# create the parent layout which will hold the main page
	app.layout = html.Div([
		html.Div(layout.generate_layout(), id='page-content')
	])

	# set up the callbacks
	@app.callback(
		Output('content_vtable', 'children'),
		[Input('embed-dropdown', 'value')])
	def update_embed_dropdown(embed_id):
		log.info("Callback: update_embed_dropdown: embed_id=%s" % embed_id)
		layout.current_embed_id = embed_id
		return layout.generate_vtable()

	@app.callback(
		Output('content_vchart', 'children'),
		[Input('measure-dropdown', 'value'), Input('embed-dropdown', 'value')])
	def update_measure_dropdown(measure_id, embed_id):
		log.info("Callback: update_measure_dropdown: measure_id=%s embed_id=%s" % (measure_id, embed_id))
		layout.current_measure_id = measure_id
		layout.current_embed_id = embed_id
		return layout.generate_vchart()

	# start the web server
	app.run_server(debug=options.debug)

# --------------------------------------------------------------

if __name__ == "__main__":
	main()
