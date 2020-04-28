import logging as log
import pandas as pd
import dash, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
# TopicScan imports
from model.validation import TopicMatcher
from webconfig import config
from webvalidation import ModelValidator, measure_names, measure_short_names
from layouts.general import GeneralLayout
from layouts.dftable import DataFrameTable
# --------------------------------------------------------------

class ComparisonLayout(GeneralLayout):

	def __init__( self, webcore, all_model_metadata ):
		super(ComparisonLayout, self).__init__( webcore )
		# validation measures
		self.validator = ModelValidator()
		# page details
		self.page_title = "%s - Comparison" % self.page_title
		self.page_suffix = "-comparison"
		# current state
		self.top_terms = config.get("top_terms", 10)
		self.all_metadata = all_model_metadata
		self.current_embed_id = None
		self.current_metadata_indices = [0, 1]
		# cache of validation results
		self.validation_cache = {}

	def get_header_subtext( self ):
		""" Return the string which is displayed in the header, beside the logo. """
		return ""

	def generate_main_panel( self ):
		""" Generate the main panel for this page. """
		return html.Div([
			dbc.Row(
				html.Div([
					dbc.Col( self.generate_overview_card() ) ],
					className='col-lg-12'
				) ),
			dbc.Row( [
					html.Div([
						dcc.Link(id="avtable", href=""),
						dbc.Col( self.generate_vtable_card() ) ],
						className='col-lg-12'
					), 
				] ),
			dbc.Row( [
					html.Div([
						dcc.Link(id="avchart", href=""),
						dbc.Col( self.generate_vchart_card() ) ],
						className='col-lg-12'
					), 
				] ),
			dbc.Row( [
					html.Div([
						dcc.Link(id="amatching", href=""),
						dbc.Col( self.generate_matching_card() ) ],
						className='col-lg-12'
					), 
				] ),			
			], className='content'
		)

	def generate_overview_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Overview: Model Summary", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_overview_card_text(), className="card-text"),
						html.Div( self.generate_model_table(), className="comparison-table" ),
					]
				),
			],
		)

	def generate_vtable_card( self ):
		""" Generate Dash layout for table of validation scores for each topic model. """
		return dbc.Card(
			[
				dbc.CardHeader("Validation Scores", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_vtable_card_text(), className="card-text", id="title_vtext1"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Embedding", addon_type="prepend"),
								self.generate_embedding_dropdown()
							]
						),
						html.Div( self.generate_vtable(), id='content_compare_vtable'),
					]
				),
			], id="content_vtable_card")

	def generate_vchart_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Validation Charts", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_vchart_card_text(), className="card-text"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Measure", addon_type="prepend"),
								self.generate_measure_dropdown()
							]
						),
						html.Div( self.generate_vchart(), id='content_compare_vchart'),
					]
				),
			])

	def generate_matching_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Topic Matching", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_matching_card_text(), className="card-text"),
						dbc.Row( [
							dbc.InputGroup(
								[
									dbc.InputGroupAddon("Select Model 1", addon_type="prepend"),
									self.generate_model_dropdown(1)
								], className="col-sm"
							),
							dbc.InputGroup(
								[
									dbc.InputGroupAddon("Select Model 2", addon_type="prepend"),
									self.generate_model_dropdown(2)
								], className="col-sm"
							),
						] ),
						html.Div( self.generate_matching_table(), id='content_compare_matching'),
					]
				),
			])

	def generate_overview_card_text( self ):
		text = "Validation measures can be applied to compare the %d topic models listed below:" % ( len(self.all_metadata) ) 
		return dcc.Markdown( text )

	def generate_vtable_card_text( self ):		
		text = "Comparison of model-level validation scores for %d topic models," % len(self.all_metadata)
		text += " using %d validation measures, where distances and similarities are calculated using the word embedding selected below." % len(measure_short_names)
		return dcc.Markdown(text)

	def generate_vchart_card_text( self ):
		text = "Select a topic validation measure below to view a chart comparing %d topic models," % len(self.all_metadata)
		text += " based on the word embedding selected above."
		return dcc.Markdown(text)

	def generate_matching_card_text( self ):
		text = "Select 2 topic models below to identify the best matching topic pairs between both selected models."
		text += " The similarity scores used in the matching process are calculated using the word embedding selected above."
		return dcc.Markdown(text)

	def generate_model_table( self ):
		""" Generate a Bootstrap table containing list of current topic model metadata. """
		df = self.__create_model_df().sort_values( by=["Corpus","Name"] )
		alignments = { "Topics" : "right", "Documents" : "right", "Terms" : "right" }
		return DataFrameTable( df, id="model-table", alignments=alignments, striped=False, hover=False ).generate_layout()

	def __create_model_df( self ):
		""" Create a Pandas Data Frame summarizing details for all models currently being compared. """
		rows = []
		for meta in self.all_metadata:
			row = { 
				"Name" : meta["id"], 
				"Corpus" : meta["corpus"],
				"Algorithm" : meta["algorithm"]["id"],
				"Topics" : meta["k"],
				"Documents" : meta["documents"],
				"Terms" : meta["terms"] }
			rows.append( row )
		return pd.DataFrame( rows )

	def generate_vtable( self ):
		""" Generates a Dash table containing topic-level validation scores. """
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.validation_cache:
			df = self.validation_cache[self.current_embed_id]
			log.info("Using cached comparison validation scores for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			# perform the evaluation
			log.info("Performing comparison on %d topic models using %s ..." % (len(self.all_metadata), self.current_embed_id) )
			df = self.validator.get_validation_df( self.all_metadata, embed )
			if df is None:
				return ""
			# round it
			df = df.round( config.get("precision", 3) )
			self.validation_cache[self.current_embed_id] = df
		if df is None:
			return ""
		data = df.to_dict('records')
		columns = []
		for i in df.columns:
			if i in measure_short_names:
				columns.append( {"name": measure_short_names[i], "id": i, "deletable": False, "selectable": False} )
			else:
				columns.append( {"name": i, "id": i, "deletable": False, "selectable": False} )
		return dash_table.DataTable(
		    id='validation_model',
		    columns=columns,
		    data=data,
		    sort_action='native',
			style_header={
				'backgroundColor': 'white',
				'fontWeight': 'bold',
				'border-top': '1px solid #dee2e6',
				'border-bottom': '2px solid #dee2e6',
				'line-height': 3.1
			},			
			style_cell=
				{
					'textAlign': 'right',
					'border-top': '1px solid #dee2e6',
					'line-height': 3.1
				},
			style_cell_conditional=[
				{
					'if': {'column_id': c},
					'textAlign': 'left'
				} for c in ['Name', 'Corpus']
			],
		    style_as_list_view=True
		)

	def generate_vchart( self ):
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.validation_cache:
			df = self.validation_cache[self.current_embed_id]
			log.info("Using cached validation scores for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			# perform the evaluation
			log.info("Evaluating topic model using %s ..." % self.current_embed_id )
			df = self.validator.get_validation_df( self.all_metadata, embed )
			self.validation_cache[self.current_embed_id] = df
		if df is None:
			return ""
		# get the appropriate values
		measure_name = measure_names[self.current_measure_id]
		# sort the results in reverse order
		if self.current_measure_id == "minmax":
			df2 = df.sort_values(by=self.current_measure_id, ascending=False)
		else:
			df2 = df.sort_values(by=self.current_measure_id, ascending=True)
		xvalues, yvalues, hovertext, s_colors = [], [], [], []
		for i, row in df2.iterrows():
			xvalues.append( row[self.current_measure_id] )
			yvalues.append( row["Name"] )
		# generate the chart
		chart_height = self.get_barchart_height( len(xvalues) )
		return dcc.Graph(
			id='chart_validation',
			figure={
				'data': [
					{
						'x': xvalues, 
						'y': yvalues, 
						'type': 'bar',
						'orientation' : 'h',
						'marker' : { 'color': 'rgba(18, 0, 230, 0.6)', 'opacity': 0.6 },
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
				],
				'layout': 
				{ 
					'height' : chart_height,
					'margin': { "t" : 40, "l" : 320, "r" : 50 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : measure_names[self.current_measure_id], 'titlefont' : { "size" : 15 } },
					'tickfont' : { "size" : 14 },
					'titlefont' : { "size" : 15 } 
				}
			})	

	def generate_matching_table( self ):
		if self.current_embed_id is None:
			return ""
		embed = self.webcore.get_embedding(self.current_embed_id)
		if embed is None:
			return ""
		descriptors1 = self.all_metadata[self.current_metadata_indices[0]].get_descriptors()
		descriptors2 = self.all_metadata[self.current_metadata_indices[1]].get_descriptors()
		if descriptors1 is None or descriptors2 is None:
			return ""
		# perform the match
		matcher = TopicMatcher(embed)
		permutation, similarities = matcher.match(descriptors1, descriptors2)
		# create the table
		k1, k2 = len(descriptors1), len(descriptors2)
		num_fmt = "%02d" if max(k1,k2) < 100 else "%03d"
		rows = []
		matched_model2 = []
		for topic_index1 in range(k1):
			topic_index2 = permutation[topic_index1]
			matched_model2.append(topic_index2)
			ranking1 = descriptors1[topic_index1]
			row = { "Topic 1":num_fmt % (topic_index1+1) }
			row["Descriptor 1"] = ", ".join(ranking1[0:self.top_terms])
			if topic_index2 < k2:
				ranking2 = descriptors2[topic_index2]
				row["Topic 2"] = num_fmt % (topic_index2+1)
				row["Descriptor 2"] = ", ".join(ranking2[0:self.top_terms])
				row["Similarity"] = config.get("float_format","%.3f") % similarities[topic_index1]
			else:
				row["Topic 2"] = ""
				row["Descriptor 2"] = ""
				row["Similarity"] = ""
			rows.append( row )
		for topic_index2 in range(k2):
			if topic_index2 in matched_model2:
				continue
			ranking2 = descriptors2[topic_index2]
			row = { "Topic 2":num_fmt % (topic_index2+1) }
			row["Descriptor 2"] = ", ".join(ranking2[0:self.top_terms])
			row["Topic 1"] = ""
			row["Descriptor 1"] = ""
			row["Similarity"] = ""
			rows.append( row )
		df = pd.DataFrame(rows)
		alignments = { "Topic 1":"center", "Topic 2":"center", "Similarity":"center" }
		return DataFrameTable( df, id="matching-table", alignments=alignments, striped=False, hover=False ).generate_layout()

	def generate_model_dropdown( self, dropdown_number ):
		""" Utility function to generate a dropdown component which allows the user
		to choose between different topic models. """
		model_options = []
		for i, meta in enumerate(self.all_metadata):
			model_options.append( { "label":meta["id"], "value":str(i) } ) 
		component_id = "compare-model-dropdown%d" % dropdown_number
		if len(model_options) > dropdown_number-1:
			return dbc.Select(
				id=component_id,
				options=model_options,
				value=str(self.current_metadata_indices[dropdown_number-1])
			)
		return dbc.Select(id=component_id, options=model_options )
