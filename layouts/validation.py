import logging as log
import dash, dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
# TopicScan imports
from webconfig import config
from webvalidation import TopicValidator, measure_names, measure_short_names
from layouts.general import GeneralLayout
from layouts.dftable import DataFrameTable

# --------------------------------------------------------------

class ValidationLayout( GeneralLayout ):

	def __init__( self, webcore, all_model_metadata, show_navbar = True  ):
		super(ValidationLayout, self).__init__( webcore )
		# validation measures
		self.validator = TopicValidator()
		# page details
		self.show_navbar = show_navbar
		self.page_title = "%s - Validation" % self.page_title
		self.page_suffix = "-validation"
		# current state
		self.metadata = all_model_metadata
		self.current_embed_id = None
		self.current_measure_id = config.get( "default_measure", "coherence" )
		# cache of validation results
		self.validation_cache = {}
		self.term_distribution_cache = {}

	def get_header_subtext( self ):
		""" Return the string which is displayed in the header, beside the logo. """
		return self.metadata["id"]

	def generate_navbar( self ):
		""" Generate the Dash top navigation bar component. """
		# do we want a navbar?
		if not self.show_navbar:
			return ""
		# build the navbar and items
		return html.Div(
			dbc.NavbarSimple(
				children=[
					dbc.NavItem(dbc.NavLink("Validation Scores", href="#avtable", external_link=True)),
					dbc.NavItem(dbc.NavLink("Validation Charts", href="#avchart", external_link=True)),
					dbc.NavItem(dbc.NavLink("Similarity Distributions", href="#avdistribution", external_link=True)),
				],
				dark=False,
				className='navbar-light bg-light container-fullwidth'
			), className='subnav'
	 	)

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
						dcc.Link(id="avtable"),
						dbc.Col( self.generate_vtable_card() ) ],
						className='col-lg-12'
					), 
				] ),
			dbc.Row( [
					html.Div([
						dcc.Link(id="avchart"),
						dbc.Col( self.generate_vchart_card() ) ],
						className='col-lg-12'
					), 
				] ),
			dbc.Row( [
					html.Div([
						dcc.Link(id="avdistribution"),
						dbc.Col( self.generate_vdistribution_card() ) ],
						className='col-lg-12'
					), 
				] ),
			], className='content'
		)

	def generate_overview_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Overview: Topic Validation", className="card-header"),
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

	def generate_vtable_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Validation Scores", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_vtable_card_text1(), className="card-text", id="title_vtext1"),
						html.Div( self.generate_vtable(), id='content_vtable'),
						html.Div( self.generate_vtable_card_text2(), className="card-text", id="title_vtext2"),
						html.Div( self.generate_vsummary(), id='content_vsummary'),
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
						html.Div( self.generate_vchart(), id='content_vchart'),
					]
				),
			])

	def generate_vdistribution_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Term Similarity Distributions", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_vdistribution_card_text(), className="card-text"),
						html.Div( self.generate_vdistribution(), id='content_vdistribution'),
					]
				),
			], id="content_vdistribution_card")

	def generate_overview_card_text( self ):
		text = "Validation measures applied to the %s topics generated on the *%s* corpus using the *%s* algorithm." % ( 
			self.metadata["k"], self.metadata["corpus"], self.metadata["algorithm"]["id"] )
		text += "\n\nThe similarity and distance values in these measures are calculated using the word embedding selected below." 
		return dcc.Markdown( text )

	def generate_vtable_card_text1( self ):		
		text = "Validation of %d individual topics using a range of measures, based on the word embedding selected above." % self.metadata["k"]
		return dcc.Markdown(text)

	def generate_vtable_card_text2( self ):		
		text = "Validation of the overall topic model, for the %d measures above." % len(measure_short_names)
		text += " In each case, the overall score is the mean of the %d individual topic scores." % self.metadata["k"]
		return dcc.Markdown(text)

	def generate_vchart_card_text( self ):
		text = "Select a topic validation measure below to view a chart comparing the %d topics in this model." % self.metadata["k"]
		text += "  Topics are arranged in descending order by quality."
		return dcc.Markdown(text)

	def generate_vdistribution_card_text( self ):
		text = "The normalized histograms below show the distribution of *intra-topic* and *inter-topic* similarity values for the terms across all %d descriptors"  % self.metadata["k"]
		text += ", as calculated using the word embedding selected below." 
		text += " Values close to 1 correspond to pairs of terms which are semantically highly similar, while values close to 0 correspond to dissimilar pairs of terms."
		return dcc.Markdown(text)

	def generate_vtable( self ):
		""" Generates a Dash table containing topic-level validation scores. """
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
			df = self.validator.get_validation_df( self.metadata, embed )
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
			style_cell=
				{
					'textAlign': 'center'
				},
			style_header={
			        'backgroundColor': 'white',
			        'fontWeight': 'bold',
			        'border-bottom': '2px solid #808080'
			    },				
			style_cell_conditional=[
				{
					'if': {'column_id': c},
					'textAlign': 'left'
				} for c in ['Descriptor']
			],
		    style_as_list_view=True
		)

	def generate_vsummary( self ):
		""" Generates a Dash table containing overall model-level validation scores. """
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
			log.info("Evaluating overall topic model using %s ..." % self.current_embed_id )
			df = self.validator.get_validation_df( self.metadata, embed )
			self.validation_cache[self.current_embed_id] = df
		if df is None:
			return ""
		# generate data
		df_mean = df.mean( axis = 0)
		df_mean = df_mean.round( config.get("precision",3) )
		data = []
		columns = [ "Measure", "Mean Value" ]
		for i, value in df_mean.iteritems():
			if not i in measure_names:
				continue
			label = "%s (%s)" %( measure_names[i], measure_short_names[i] )
			data.append( { "Measure" : label, "Mean Value" : value } )
		# generate 
		return dash_table.DataTable(
		    id='validation_summary',
		    columns=[{"name": i, "id": i, "deletable": False, "selectable": False} for i in columns],
		    data=data,
			style_cell=
				{
					'textAlign': 'center'
				},
			style_header={
			        'backgroundColor': 'white',
			        'fontWeight': 'bold',
			        'border-bottom': '2px solid #808080'
			    },				
			style_cell_conditional=[
				{
					'if': {'column_id': c},
					'textAlign': 'left'
				} for c in ['Measure']
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
			df = self.validator.get_validation_df( self.metadata, embed )
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
		colors = self.get_colors( self.metadata["k"] )
		xvalues, yvalues, hovertext, s_colors = [], [], [], []
		for i, row in df2.iterrows():
			xvalues.append( row[self.current_measure_id] )
			yvalues.append( "Topic %s " % row["Topic"] )
			hovertext.append( row["Descriptor"] )
			s_colors.append( self.format_color_string(colors[i-1]) )
		# generate the chart
		chart_height = self.get_barchart_height( len(xvalues) )
		return dcc.Graph(
			id='chart_validation',
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
					'margin': { "t" : 30 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : measure_names[self.current_measure_id], 'titlefont' : { "size" : 15 } },
					'tickfont' : { "size" : 14 },
					'titlefont' : { "size" : 15 } 
				}
			})	

	def generate_vdistribution( self ):
		""" Generates a Dash histogram plot of descriptor term pairwise similarity values. """
		if self.current_embed_id is None:
			return ""
		# already cached these results?
		if self.current_embed_id in self.term_distribution_cache:
			df = self.term_distribution_cache[self.current_embed_id]
			log.info("Using cached term similarity distribution values for embedding %s" % self.current_embed_id )
		else:
			# get the word embedding
			embed = self.webcore.get_embedding(self.current_embed_id)
			if embed is None:
				return ""
			log.info("Applying term similarity distribution analysis to topic model using %s ..." % self.current_embed_id )
			df = self.validator.get_term_pair_similarity_df( self.metadata, embed, unique_only = True )
			if df is None:
				return ""
			self.term_distribution_cache[self.current_embed_id] = df
		# separate out the intra-topic and inter-topic values
		sim_intra = df[df["intra"]==True]["sim"]
		sim_inter = df[df["intra"]==False]["sim"]
		log.info("Plotting term similarity distribution for %d intra- and %d inter-topic values" % (
			len(sim_intra), len(sim_inter) ) )
		# generate the chart
		num_intra = '{:0,d}'.format( len(sim_intra) )
		num_inter = '{:0,d}'.format( len(sim_inter) )
		title = "Normalized histograms of similarities for %s intra-topic and %s inter-topic term pairs" % ( num_intra, num_inter )
		return dcc.Graph(
			id='chart_vdistribution',
			figure={
				'data': [
					{
						'x': sim_inter, 
						'name': "Inter-topic",
						'type': 'histogram',
						# 'nbinsx': 10,
						'bingroup': 1,
						'histnorm' : 'probability',
						'marker' : { 'color': 'rgba(18, 0, 230, 0.6)', 'opacity': 0.6 },
						'hovertemplate': 'Probability = %{y}<extra></extra>',
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
					{
						'x': sim_intra, 
						'name': "Intra-topic",
						'type': 'histogram',
						# 'nbinsx': 10,
						'bingroup': 1,
						'histnorm' : 'probability',
						'marker' : { 'color': 'rgba(103, 232, 0, 0.6)', 'opacity': 0.6 },
						'hovertemplate': 'Probability = %{y}<extra></extra>',
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
				],
				'layout': 
				{ 
					'title' : { 'text': title, 'font' : { "size" : 15 } },
					'barmode': 'overlay',	
					'margin': { "t" : 32, "l" : 100, "r" : 50 },
					'legend': {  'font' : { "size" : 15 }, 'orientation' : 'h' },
					'yaxis' : { 'title' : 'Probability', 
						'tickformat': '.2f',
						'titlefont' : { "size" : 15 },
						'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Term Similarity", 
						'zeroline' : False,
						'tickfont' : { "size" : 14 },
						'titlefont' : { "size" : 15 },
						'range': [0, 1] }
				}
			})	
