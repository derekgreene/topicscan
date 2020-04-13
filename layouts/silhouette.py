import logging as log
import warnings
import pandas as pd
from sklearn import manifold
import dash, dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
# TopicScan imports
from webconfig import config
from webvalidation import TopicValidator, measure_names, measure_short_names
from layouts.general import GeneralLayout

# --------------------------------------------------------------

class SilhouetteLayout( GeneralLayout ):

	def __init__( self, webcore, model_metadata ):
		super(SilhouetteLayout, self).__init__( webcore )
		# validation measures
		self.validator = TopicValidator()
		# page details
		self.page_title = "%s - Silhouettes" % self.page_title
		self.page_suffix = "-silhouette"
		# current state
		self.metadata = model_metadata
		self.current_embed_id = None
		self.current_topic_index = 1
		# cache for validation scores
		self.topiclevel_cache = {}
		self.termlevel_cache = {}

	def get_header_subtext( self ):
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
			dbc.Row(
				html.Div([
					dbc.Col( self.generate_distribution_card() ) ],
					className='col-lg-12'
				) ),
			], className='content'
		)

	def generate_overview_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Overview: Silhouette Scores", className="card-header"),
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
				dbc.CardHeader("Topic-Level Silhouettes", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_topiclevel_card_text(), className="card-text"),
						html.Div( self.generate_topiclevel_chart(), id='silhouette_content_topiclevel'),
					]
				)
			],
		)

	def generate_term_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Term-Level Silhouettes", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_termlevel_card_text(), className="card-text"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Topic", addon_type="prepend"),
								self.generate_topic_dropdown()
							]
						),
						html.Div( self.generate_termlevel_chart(), id='silhouette_content_termlevel'),
					]
				),
			],
		)

	def generate_distribution_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Term-Level Silhouette Distribution", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_distribution_card_text(), className="card-text"),
						html.Div( self.generate_distribution_chart(), id='silhouette_content_distribution' ),
					]
				),
			],
		)

	def generate_overview_card_text( self ):
		text = "Evaluation of %s topics generated on the *%s* corpus using the *%s* algorithm" % ( 
			self.metadata["k"], self.metadata["corpus"], self.metadata["algorithm"]["id"] )
		text += ", using the *Topic Silhouette Score*, based on the word embedding selected below." 
		return dcc.Markdown( text )

	def generate_topiclevel_card_text( self ):
		text = "Mean topic-level silhouette scores for each of the %d topics generated on the *%s* corpus using the *%s* algorithm." % ( 
			self.metadata["k"], self.metadata["corpus"], self.metadata["algorithm"]["id"] )
		text += " Topics are arranged in descending order by score,"
		text += " where a score close to 1 indicates a high-quality topic and a score close to -1 indicates a low-quality topic."
		return dcc.Markdown( text )

	def generate_termlevel_card_text( self ):
		text = "Individual term-level silhouette scores for the top %d terms in the descriptor of the topic selected below." % ( 
			config.get( "top_terms", 10) )
		text += " Terms are arranged in descending order by score."
		text += " where a score close to 1 indicates a term that is semantically coherent with respect to its topic,"
		text += " while a score close to -1 indicates a term that does not fit well with its topic."
		return dcc.Markdown( text )

	def generate_distribution_card_text( self ):
		counts = self.metadata.get_descriptor_term_counts()
		text = "The normalized histogram belows shows the distribution of Term Silhouette scores for all %d unique terms appearing in the %d topic descriptors." % (
			len(counts), self.metadata["k"] )
		text += " A score close to 1 indicates that a term that is semantically coherent with respect to its topic,"
		text += " while a score close to -1 indicates a term that does not fit well with its topic."
		return dcc.Markdown( text ) 

	def generate_topic_dropdown( self ):
		topic_options = []
		num_fmt = "Topic %02d" if self.metadata["k"] < 100 else "Topic %03d"
		for topic_index in range( 1, self.metadata["k"] + 1 ):
			label = num_fmt % topic_index
			topic_options.append( { "label": label, "value": topic_index } ) 
		return dbc.Select(
			id='topic-sil-dropdown',
			options=topic_options,
			value=topic_options[0]["value"]
		)

	def generate_topiclevel_chart( self ):
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.topiclevel_cache:
			df_sil = self.topiclevel_cache[self.current_embed_id]
			log.info("Using cached silhouette scores for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			log.info("Applying silhouette analysis to topic model using %s ..." % self.current_embed_id )
			df_sil = self.validator.get_topiclevel_silhouette_df( self.metadata, embed )
			if df_sil is None:
				return ""
			# round it 
			df_sil = df_sil.round( config.get("precision", 3) )
			self.topiclevel_cache[self.current_embed_id] = df_sil
		# sort the results in reverse order
		df_sil = df_sil.sort_values(by="Score", ascending=True)
		colors = self.get_colors( self.metadata["k"] )
		xvalues, yvalues, hovertext, s_colors = [], [], [], []
		for label, row in df_sil.iterrows():
			xvalues.append( row["Score"] )
			yvalues.append( label + " " )
			hovertext.append( row["Descriptor"] )
			s_colors.append( self.format_color_string(colors[row["Number"]-1]) )
		# choose a sensible range for the x-axis
		if ( min(df_sil["Score"]) <= -0.5) or (max(df_sil["Score"]) >= 0.5):
			min_value, max_value = -1, 1
		else:
			min_value, max_value = -0.5, 0.5
		# generate the chart
		if len(xvalues) <= 6:
			chart_height = 400
		elif len(xvalues) <= 10:
			chart_height = 500
		else:
			chart_height = 600
		return dcc.Graph(
			id='chart_topicsil',
			figure={
				'data': [
					{
						'x': xvalues, 
						'y': yvalues, 
						'hovertext' : hovertext,
						'type': 'bar',
						'orientation' : 'h',
						'marker' : { 'color' : s_colors, 'opacity': 0.4 },
						'hovertemplate': '<b>%{y}</b>: %{x}<br>%{hovertext}<extra></extra>',
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
				],
				'layout': 
				{ 
					'height' : chart_height,
					'margin': { "t" : 20 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Topic Silhouette Score", 
					'tickfont' : { "size" : 13 },
					'titlefont' : { "size" : 15 },
					'range': [min_value, max_value] }
				}
			})	

	def generate_termlevel_chart( self ):
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.termlevel_cache:
			scores = self.termlevel_cache[self.current_embed_id]
			log.info("Using cached term-level silhouette scores for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			log.info("Applying term-level silhouette analysis to topic model using %s ..." % self.current_embed_id )
			scores = self.validator.get_termlevel_silhouette_scores( self.metadata, embed )
			if scores is None:
				return ""
			self.termlevel_cache[self.current_embed_id] = scores
		# create the values for the chart, based on the currently selected topic
		term_scores = pd.Series( scores[self.current_topic_index-1] ).sort_values(ascending=True)
		xvalues, yvalues = [], []
		for term, score in term_scores.iteritems():
			xvalues.append( round( score, config.get("precision", 3) ) )
			yvalues.append( term )
		# choose a sensible range for the x-axis
		min_value, max_value = -1, 1
		# get the color from the palette
		colors =  self.get_colors( self.metadata["k"] )
		s_rgb = self.format_color_string( colors[self.current_topic_index-1] )
		# generate the chart
		return dcc.Graph(
			id='chart_topicsil',
			figure={
				'data': [
					{
						'x': xvalues, 
						'y': yvalues, 
						'type': 'bar',
						'orientation' : 'h',
						'marker' : { 'color': s_rgb, 'opacity': 0.4 },
						'hovertemplate': '<b>%{y}</b>: %{x}<extra></extra>',
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
				],
				'layout': 
				{ 
					'margin': { "t" : 30, "l" : 120, "r" : 120 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Term Silhouette Score", 
						'tickfont' : { "size" : 14 },
						'titlefont' : { "size" : 15 },
						'range': [min_value, max_value] }
				}
			})	

	def generate_distribution_chart( self ):
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.termlevel_cache:
			scores = self.termlevel_cache[self.current_embed_id]
			log.info("Using cached term distribution silhouette scores for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			log.info("Applying term distribution silhouette analysis to topic model using %s ..." % self.current_embed_id )
			scores = self.validator.get_termlevel_silhouette_scores( self.metadata, embed )
			if scores is None:
				return ""
			self.termlevel_cache[self.current_embed_id] = scores
		all_scores = []
		for topic_scores in scores:
			all_scores += topic_scores.values()
		log.info("Plotting distribution for %d values" % len(all_scores) )
		# generate the chart
		return dcc.Graph(
			id='chart_topicdist',
			figure={
				'data': [
					{
						'x': all_scores, 
						'type': 'histogram',
						'histnorm' : 'probability',
						'marker' : { 'color': 'rgba(55, 83, 139, 0.6)', 'opacity': 0.7 },
						'hovertemplate': 'Probability = %{y}<extra></extra>',
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
				],
				'layout': 
				{ 
					'margin': { "t" : 20, "l" : 120, "r" : 120  },
					'yaxis' : { 'title' : 'Probability', 
						'tickformat': '.2f',
						'titlefont' : { "size" : 15 },
						'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Term Silhouette Score", 
						'zeroline' : True,
						'tickfont' : { "size" : 14 },
						'titlefont' : { "size" : 15 },
						'range': [-1, 1] }
				}
			})	
