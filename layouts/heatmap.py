import logging as log
import warnings
import dash, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from sklearn import manifold
# TopicScan imports
from webconfig import config
from webvalidation import TopicValidator, measure_names, measure_short_names
from layouts.general import GeneralLayout

# --------------------------------------------------------------

class HeatmapLayout( GeneralLayout ):

	def __init__( self, webcore, model_metadata ):
		super(HeatmapLayout, self).__init__( webcore )
		# validation measures
		self.validator = TopicValidator()
		# page details
		self.page_title = "%s - Heatmaps" % self.page_title
		self.page_suffix = "-heatmap"
		# current state
		self.metadata = model_metadata
		self.current_embed_id = None
		self.current_topic_index = 1
		# cache for validation scores
		self.topiclevel_cache = {}
		self.termlevel_cache = {}

	def get_header_subtext( self ):
		""" Return the string which is displayed in the header, beside the logo. """
		return self.metadata["id"]

	def generate_main_panel( self ):
		return html.Div([
			dbc.Row(
				html.Div([
					dbc.Col( self.generate_overview_card() ) ],
					className='col-lg-12'
				) ),
			dbc.Row(
				html.Div([
					dbc.Col( self.generate_topic_card() ) ],
					className='col-lg-12'
				) ),
			dbc.Row(
				html.Div([
					dbc.Col( self.generate_term_card() ) ],
					className='col-lg-12'
				) ),
			], className='content'
		)

	def generate_overview_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Overview: Heatmaps", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_overview_card_text(), className="card-text"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Embedding", addon_type="prepend"),
								self.generate_embedding_dropdown()
							]
						),
					]
				),
			],
		)

	def generate_topic_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Topic-Level Heatmap", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_topiclevel_card_text(), className="card-text"),
						html.Div( self.generate_topiclevel_heatmap(), id='heatmap_content_topiclevel'),
					]
				)
			],
		)

	def generate_term_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Term-Level Heatmap", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_termlevel_card_text(), className="card-text"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Topic", addon_type="prepend"),
								self.generate_heatmap_topic_dropdown()
							]
						),
						html.Div( self.generate_termlevel_heatmap(), id='heatmap_content_termlevel'),
					]
				)
			],
		)

	def generate_overview_card_text( self ):
		text = "Heatmap visualizations showing the relationship between the %s topics generated on the *%s* corpus using the *%s* algorithm." % ( 
			self.metadata["k"], self.metadata["corpus"], self.metadata["algorithm"]["id"] )
		text += " Distances are calculated on the word embedding selected below." 
		return dcc.Markdown( text )

	def generate_topiclevel_card_text( self ):
		text = "The heatmap below shows inter-topics similarities, for all %d topics in the current model." % self.metadata["k"]
		text += " The distance between a pair of topics is calculated as the average distance between the terms appearing in their descriptors,"
		text += " based on the word embedding selected above."
		return dcc.Markdown( text )

	def generate_termlevel_card_text( self ):
		text = "The heatmap below shows the intra-topic similarities for the %d terms which appear in the descriptor of the selected topic." % (
			self.metadata.top_terms )
		return dcc.Markdown( text )

	def generate_topiclevel_heatmap( self ):
		""" Generate a heatmap depicting pairwise topic-topic similarities. """
		if self.current_embed_id is None:
			return ""
		descriptors = self.metadata.get_descriptors()
		if descriptors is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.topiclevel_cache:
			df = self.topiclevel_cache[self.current_embed_id]
			log.info("Using cached similarites for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			log.info("Computing similarities for topic model using %s ..." % self.current_embed_id )
			df = self.validator.get_topic_pair_similarity_df( self.metadata, embed )
			if df is None:
				return ""
			# round it
			df = df.round( config.get("precision",3) )
			self.topiclevel_cache[self.current_embed_id] = df
		# generate the chart
		hovertext = []
		for i, row in df.iterrows():
			topic_num1 = int(row["topic1"].replace("Topic ","")) - 1
			topic_num2= int(row["topic2"].replace("Topic ","")) - 1
			s = "<b>%s</b>: %s<br><b>%s</b>: %s" % ( 
				row["topic1"], ", ".join( descriptors[topic_num1] ), 
				row["topic2"], ", ".join( descriptors[topic_num2] ) )
			hovertext.append( s )
		return dcc.Graph(
			id='chart_topicheatmap',
			figure={
				'data': [
					{
						'x': df["topic1"], 
						'y': df["topic2"],
						'z': df["sim"],
						'hovertext' : hovertext,
						'type': 'heatmap',		    		
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' },
						'hovertemplate': '%{hovertext}<br>Similarity: %{z}<extra></extra>',
					},
				],
				'layout': 
				{ 
					'margin': { "t" : 2 },
					'height': 600,
					"yaxis" : { "autorange" : 'reversed' },
				}
			})	

	def generate_termlevel_heatmap( self ):
		""" Generate a heatmap showing the similarities between the pairs of terms which appear in the descriptor
		of an individual topic. """
		if self.current_embed_id is None:
			return ""
		descriptors = self.metadata.get_descriptors()
		if descriptors is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.termlevel_cache:
			df = self.termlevel_cache[self.current_embed_id]
			log.info("Using cached term similarites for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			log.info("Computing term similarities for topic model using %s ..." % self.current_embed_id )
			df = self.validator.get_term_pair_similarity_df( self.metadata, embed )
			if df is None:
				return ""
			# round it
			df = df.round( config.get("precision",3) )
			self.termlevel_cache[self.current_embed_id] = df
		# now get the relevant terms for this topic and filter the Data Frame
		current_descriptor = descriptors[self.current_topic_index-1]
		current_descriptor_set = set(current_descriptor)
		xvalues, yvalues, zvalues, hovertext = [], [], [], []
		# TODO: make this more effecient
		for i, row in df.iterrows():
			if row["term1"] in current_descriptor_set and row["term2"] in current_descriptor_set:
				xvalues.append( row["term1"] )
				yvalues.append( row["term2"] )
				zvalues.append( row["sim"] )		
				hovertext.append( "<b>(%s, %s)</b>" % ( row["term1"], row["term2"] ) )
		# generate the chart
		title = "Topic %02d: %s" % ( self.current_topic_index, ", ".join( current_descriptor ) )
		return dcc.Graph(
			id='chart_topicheatmap',
			figure={
				'data': [
					{
						'x': xvalues, 
						'y': yvalues,
						'z': zvalues,
						'hovertext' : hovertext,
						'type': 'heatmap',		    		
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' },
						'hovertemplate': '%{hovertext}<br>Similarity: %{z}<extra></extra>',
					},
				],
				'layout': 
				{ 
					'title' : { 'text': title, 'font' : { "size" : 15 } },
					'margin': { "t" : 40, "l" : 200, "r" : 200 },
					'height': 600,
					'xaxis' : { 'tickfont' : { "size" : 14 } },
					"yaxis" : { "autorange" : 'reversed', 'tickfont' : { "size" : 14 } },
				}
			})	

	def generate_heatmap_topic_dropdown( self ):
		""" Generate a Dash dropdown component to select a topic from the model. """
		# create the options
		topic_options = []
		num_fmt = "Topic %02d" if self.metadata["k"] < 100 else "Topic %03d"
		for topic_index in range( 1, self.metadata["k"] + 1 ):
			label = num_fmt % topic_index
			topic_options.append( { "label": label, "value": topic_index } ) 		
		# create the Dash form component
		return dbc.Select(
			id='termlevel-dropdown',
			options=topic_options,
			value=topic_options[0]["value"]
		)
