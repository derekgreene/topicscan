#!/usr/bin/env python
"""
Script providing access to the TopicScan page for inspecting an individual topic model.

Sample usage:
``` python topicscan/scan_topics.py ~/sample/models/bbc/nmf_k05/bbc_k05_001.meta ```
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
from layouts.topics import TopicModelLayout

# --------------------------------------------------------------

def main():
	parser = OptionParser(usage="usage: %prog [options] meta_file_path")
	parser.add_option("--debug", action="store_true", dest="debug", help="enable debugging information", default=True)
	parser.add_option("--preload", action="store_true", dest="preload", help="preload all word embeddings", default=False)
	(options, args) = parser.parse_args()
	if len(args) != 1 :
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
		layout = TopicModelLayout(webcore, topic_metadata)
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
	# Callbacks for TopicModelLayout 

	@app.callback(Output('content_term_assoc', 'children'), [Input('topic-term-dropdown', 'value')])
	def topics_term_assoc_topic(topic_index):
		log.info("Callback: topics_term_assoc_topic: %s" % topic_index)
		layout.current_term_topic_index = int(topic_index)
		return layout.generate_term_association_chart()

	@app.callback(Output('content_document_assoc', 'children'), [Input('topic-document-dropdown', 'value')])
	def topics_document_assoc_topic(topic_index):
		log.info("Callback: topics_document_assoc_topic: %s" % topic_index)
		layout.current_document_topic_index = int(topic_index)
		return layout.generate_document_association_chart()

	# --------------------------------------------------------------

	# start the web server
	app.run_server(debug=options.debug)

# --------------------------------------------------------------

if __name__ == "__main__":
	main()
