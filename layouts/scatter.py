import logging as log
import warnings
import dash, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from sklearn import manifold
# TopicScan imports
from webconfig import config
from webvalidation import TopicValidator
from layouts.general import GeneralLayout

# --------------------------------------------------------------

class ScatterLayout( GeneralLayout ):

	def __init__( self, webcore, model_metadata ):
		super(ScatterLayout, self).__init__( webcore )
		# validation measures
		self.validator = TopicValidator()
		# page details
		self.page_title = "%s - Scatter Plots" % self.page_title
		self.page_suffix = "-scatter"
		# current state
		self.metadata = model_metadata
		self.current_embed_id = None
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
				dbc.CardHeader("Overview: Scatter Plots", className="card-header"),
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
				dbc.CardHeader("Topic-Level Scatter Plot", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_topiclevel_card_text(), className="card-text"),
						html.Div( self.generate_topiclevel_plot(), id='scatter_content_topiclevel'),
					]
				)
			],
		)

	def generate_term_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Term-Level Scatter Plot", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_termlevel_card_text(), className="card-text"),
						html.Div( self.generate_termlevel_plot(), id='scatter_content_termlevel'),
					]
				)
			],
		)

	def generate_overview_card_text( self ):
		text = "The scatter plots below visualize the relationships between the %s topics, or their associated terms, generated on the *%s* corpus using the *%s* algorithm." % ( 
			self.metadata["k"], self.metadata["corpus"], self.metadata["algorithm"]["id"] )
		text += " Distances between topics and between terms are calculated based on the word embedding selected below." 
		return dcc.Markdown( text )

	def generate_topiclevel_card_text( self ):
		text = "This scatter plot shows inter-topics distances, visualized in 2 dimensions using *Multidimensional scaling* (MDS),"
		text += " for all %d topics in the current model." % self.metadata["k"]
		text += " The distance between a pair of topics is calculated as the average distance between the terms appearing in their descriptors,"
		text += " based on the word embedding selected above."
		return dcc.Markdown( text )

	def generate_termlevel_card_text( self ):
		text = "This scatter plot shows the distances between all pairs of terms which appear in the %d topic descriptors in the current model," % self.metadata["k"]
		text += " visualized in 2 dimensions using *Multidimensional scaling* (MDS)."
		text += " Distances between terms are calculated based on the word embedding selected above."
		return dcc.Markdown( text )

	def generate_topiclevel_plot( self ):
		if self.current_embed_id is None:
			return ""
		descriptors = self.metadata.get_descriptors()
		if descriptors is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.topiclevel_cache:
			coords = self.topiclevel_cache[self.current_embed_id]
			log.info("Using cached MDS coordinates for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			# get the distance matrix
			log.info("Applying MDS to topic model using %s ..." % self.current_embed_id )
			D = self.validator.get_topic_distance_matrix( self.metadata, embed )
			if D is None:
				return ""
			# apply MDS
			coords = self.__apply_mds( D )
			self.topiclevel_cache[self.current_embed_id] = coords		
		# generate the chart
		num_fmt = "%02d" if self.metadata["k"] < 100 else "%03d"
		labels, hovertext = [], []
		for i in range( 1, self.metadata["k"] + 1 ):
			labels.append( num_fmt % i )
			hovertext.append( ", ".join( descriptors[i-1]) )
		if len(descriptors) <= 6:
			point_size = 55
		elif len(descriptors) <= 8:
			point_size = 50
		elif len(descriptors) <= 12:
			point_size = 45
		else:
			point_size = 35
		colors = self.get_colors( self.metadata["k"] )
		s_colors = [ self.format_color_string(color) for color in colors ]
		return dcc.Graph(
			id='chart_topicscatter',
			figure={
				'data': [
					{
						'x': coords[:, 0],  
						'y': coords[:, 1], 
						'text': labels,
						'hovertext' : hovertext,
						'type': 'scatter',
						'mode': 'markers+text',
						'hoverinfo': 'text',
						'hovermode': 'closest',
						'hovertemplate': '<b>Topic %{text}</b><br>%{hovertext}<extra></extra>',
						'marker': { 
							'size': point_size, 
							'color' : s_colors, 'opacity': 0.4, 
							'line': {'width': 0.5, 'color': 'white'} },
						'textfont': { "size" : 16 },
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
					},
				],
				'layout': 
				{ 
					'margin': { "t" : 2 },
					'height': 600,
					'yaxis' : { 'tickfont' : { "size" : 14 }, 'zeroline' : False, 'hoverformat' : ".2f" },
					'xaxis' : { 'tickfont' : { "size" : 14 }, 'zeroline' : False, 'hoverformat' : ".2f" },
				}
			})	

	def generate_termlevel_plot( self ):
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.termlevel_cache:
			( terms, coords ) = self.termlevel_cache[self.current_embed_id]
			log.info("Using cached MDS term coordinates for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			# get the distance matrix
			log.info("Applying MDS to terms using %s ..." % self.current_embed_id )
			df = self.validator.get_term_distance_df( self.metadata, embed )
			if df is None:
				return ""
			terms = list( df.index )
			# apply MDS
			coords = self.__apply_mds( df )
			self.termlevel_cache[self.current_embed_id] = ( list(df.index), coords )
		# generate the chart
		if len(terms) <= 30:
			point_size = 30
		else:
			point_size = 25
		term_map = self.metadata.get_term_map()
		topic_colors = self.get_colors( self.metadata["k"] )
		#s_multi = 'rgba(180, 180, 180, 0.7)'
		s_multi = 'rgba(240, 240, 0, 1.0)'
		s_colors, hovertext = [], []
		for term in terms:
			if len(term_map[term]) == 1:
				topic_index = term_map[term][0]
				s_colors.append( self.format_color_string(topic_colors[topic_index]) )
				hovertext.append( "Topic %d" % ( topic_index+1 ) )
			else:
				s_colors.append( s_multi )
				s_indexes = [ str(i+1) for i in term_map[term] ]
				hovertext.append( "Topics %s" % ", ".join(s_indexes) )
		return dcc.Graph(
			id='chart_termscatter',
			figure={
				'data': [
					{
						'x': coords[:, 0],  
						'y': coords[:, 1], 
						'text': terms,
						'hovertext' : hovertext,
						'type': 'scatter',
						'mode': 'markers+text',
						'hoverinfo': 'text',
						'hovermode': 'closest',
						'hovertemplate': '<b>%{text}</b>: %{hovertext}<extra></extra>',
						'marker': { 
							'size': point_size, 
							'color' : s_colors,  'opacity': 0.4,
							# 'color': 'rgba(0, 116, 0, 0.7)', 'opacity': 0.6, 
							'line': {'width': 0.5, 'color': 'white'} },
						'textfont': { "size" : 13 },
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
					},
				],
				'layout': 
				{ 
					'margin': { "t" : 2 },
					'height': 800,
					'yaxis' : { 'tickfont' : { "size" : 14 }, 'zeroline' : False, 'hoverformat' : ".2f" },
					'xaxis' : { 'tickfont' : { "size" : 14 }, 'zeroline' : False, 'hoverformat' : ".2f" },
				}
			})	

	def __apply_mds( self, D ):
		""" Applies Multidimensional scaling (MDS) to the specified distance matrix
		and returns the resulting coordinates """
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")		
			mds = manifold.MDS(n_components=2, random_state=config.get("random_seed", 100), dissimilarity="euclidean")
			results = mds.fit(D)
		# we just need the coordinates
		return results.embedding_		
