import logging as log
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
# TopicScan imports
from webconfig import config
from layouts.general import GeneralLayout
from layouts.dftable import DataFrameTable

# --------------------------------------------------------------

class TopicModelLayout( GeneralLayout ):

	def __init__( self, webcore, model_metadata, show_navbar = True ):
		super(TopicModelLayout, self).__init__( webcore )
		self.show_navbar = show_navbar
		# page details
		self.page_title = "%s - Topic Model" % self.page_title
		self.page_suffix = "-topics"
		# number of top associations
		self.top_associations = config.get("num_associations", 20)
		# current state
		self.metadata = model_metadata
		self.current_term_topic_index = 1
		self.current_document_topic_index = 1
		# cache
		self.term_associations = None
		self.document_associations = None
		self.partition_df = None

	def get_header_subtext( self ):
		""" Return the string which is displayed in the header, beside the logo. """
		return self.metadata["id"]

	def generate_navbar( self ):
		# do we want a navbar?
		if not self.show_navbar:
			return ""
		# create the relevant links
		model_id = self.metadata["id"]
		url_validation = self.generate_link( "validation", { "id":model_id } )
		url_silhouette = self.generate_link( "silhouette", { "id":model_id } )
		url_heatmap = self.generate_link( "heatmap", { "id":model_id } )
		url_scatter = self.generate_link( "scatter", { "id":model_id } )
		# build the navbar and items
		return html.Div(
			dbc.NavbarSimple(
				children=[
					# dbc.NavItem(dbc.NavLink("Topic Descriptors", href="#atopic", external_link=True)),
					dbc.NavItem(dbc.NavLink("Document Partition", href="#apartition", external_link=True)),
					dbc.NavItem(dbc.NavLink("Term Associations", href="#atermassoc", external_link=True)),
					dbc.NavItem(dbc.NavLink("Document Associations", href="#adocumentassoc", external_link=True)),
					dbc.NavItem(dbc.NavLink("Topic Validation", href=url_validation, target="_blank", external_link=True)),
					dbc.NavItem(dbc.NavLink("Silhouette Plots", href=url_silhouette, target="_blank", external_link=True)),
					dbc.NavItem(dbc.NavLink("Heatmap Plots", href=url_heatmap, target="_blank", external_link=True)),
					dbc.NavItem(dbc.NavLink("Scatter Plots", href=url_scatter, target="_blank", external_link=True)),
				],
				dark=False,
				className='navbar-light bg-light container-fullwidth'
			), className='subnav'
	 	)

	def generate_main_panel( self ):
		return html.Div([
			dbc.Row( [
					html.Div([
						dcc.Link(id="atopic", href=""),
						dbc.Col( self.generate_topic_card() ) ],
						className='col-lg-12'
					), 
					html.Div([
						dcc.Link(id="apartition", href=""),
						dbc.Col( self.generate_partition_card() ) ],
						className='col-lg-12'
					), 
					html.Div([
						dcc.Link(id="atermassoc", href=""),
						dbc.Col( self.generate_term_association_card() ) ],
						className='col-lg-12'
					), 
					html.Div([
						dcc.Link(id="adocumentassoc", href=""),
						dbc.Col( self.generate_document_association_card() ) ],
						className='col-lg-12'
					), 
				])
			], className='content'
		)

	def generate_topic_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Overview: Topic Model", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_topic_card_text(), className="card-text"),
						html.Div( self.generate_descriptor_table() ),
					]
				),
			],
		)


	def generate_term_association_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Term-Topic Associations", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_term_association_card_text(), className="card-text"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Topic", addon_type="prepend"),
								self.generate_term_topic_dropdown()
							]
						),
						html.Div( self.generate_term_association_chart(), id='content_term_assoc' ),
					]
				),
			],
		)

	def generate_document_association_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Document-Topic Associations", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_document_association_card_text(), className="card-text"),
						dbc.InputGroup(
							[
								dbc.InputGroupAddon("Select Topic", addon_type="prepend"),
								self.generate_document_topic_dropdown()
							]
						),
						html.Div( self.generate_document_association_chart(), id='content_document_assoc' ),
					]
				),
			],
		)		

	def generate_partition_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Document Partition", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_partition_card_text(), className="card-text"),
						html.Div( self.generate_partition_chart(), id='content_partition' ),
					]
				),
			],
		)

	def generate_topic_card_text( self ):
		text = "Descriptors for %s topics generated on the *%s* corpus using the *%s* algorithm." % ( 
			self.metadata["k"], self.metadata["corpus"], self.metadata["algorithm"]["id"] )
		counts = self.metadata.get_descriptor_term_counts()
		text += " The descriptors contain %d unique terms" % len(counts)
		overlap_count = 0
		for count in counts.values():
			if count > 1:
				overlap_count += 1
		if overlap_count == 1:
			text += ", with 1 term appearing in more than one topic descriptor"
		elif overlap_count > 1:
			text += ", with %d terms appearing in more than one topic descriptor" % overlap_count
		text += "."
		return dcc.Markdown(text)

	def generate_term_association_card_text( self ):
		text = "In the topic model generated by the *%s* algorithm on the *%s* corpus, a term can be associated with each of the %d topics to a different degree." % ( 
			self.metadata["algorithm"]["id"], self.metadata["corpus"], self.metadata["k"] )
		text += " The chart below shows the top %d terms with the highest associations for the selected topic." % self.top_associations
		return dcc.Markdown(text)

	def generate_document_association_card_text( self ):
		text = "In the topic model generated by the *%s* algorithm on the *%s* corpus, a document can be associated with each of the %d topics to a different degree." % ( 
			self.metadata["algorithm"]["id"], self.metadata["corpus"], self.metadata["k"] )
		text += " The chart below shows the identifiers of the %d documents with the highest associations for the selected topic." % self.top_associations
		return dcc.Markdown(text)

	def generate_partition_card_text( self ):		
		text = "The chart below shows the size of each topic in the partition of the %s documents in the *%s* corpus for %d topics" % ( 
			'{:,}'.format(self.metadata["documents"]), self.metadata["corpus"], self.metadata["k"] )
		text += ", where each document is assigned to the single topic for which it has the strongest association."
		return dcc.Markdown(text)

	def generate_descriptor_table( self ):
		""" Generate the topic model table """
		df = self.metadata.get_descriptor_df()
		alignments = { "Topic" : "center" }
		return DataFrameTable( df, id="descriptor-table", alignments=alignments, striped=False, hover=False ).generate_layout()

	def generate_term_association_chart( self ):
		descriptors = self.metadata.get_descriptors()
		if descriptors is None:
			return ""
		if self.term_associations is None:
			self.term_associations = self.metadata.get_term_associations()
		if self.term_associations is None:
			return ""
		# get the top terms for this topic
		weights = self.term_associations[self.current_term_topic_index].sort_values(ascending=False).head( self.top_associations )
		max_value = self.term_associations.max().max()
		# reverse the order
		weights = weights.sort_values(ascending=True)
		xvalues, yvalues = [], []
		for doc_id, score in weights.iteritems():
			xvalues.append( round( score, config.get("precision", 3) ) )
			yvalues.append( doc_id + " ")
		# get the color from the palette
		colors = self.get_colors( self.metadata["k"] )
		s_rgb = self.format_color_string( colors[self.current_term_topic_index-1] )
		# generate the chart
		title = "Topic %02d: %s" % ( self.current_term_topic_index, ", ".join( descriptors[self.current_term_topic_index-1] ) )
		chart_height = self.get_barchart_height( len(xvalues) )
		return dcc.Graph(
			id='chart_term_assoc',
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
					'title' : { 'text': title, 'font' : { "size" : 15 } },
					'height' : chart_height,
					'margin': { "t" : 40, "l" : 200, "r" : 200 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Topic-Term Association", 
						'tickfont' : { "size" : 13 },
						'titlefont' : { "size" : 15 },
						'range': [0, max_value]
					},
				}
			})			

	def generate_document_association_chart( self ):
		descriptors = self.metadata.get_descriptors()
		if descriptors is None:
			return ""
		if self.document_associations is None:
			self.document_associations = self.metadata.get_document_associations()
		if self.document_associations is None:
			return ""
		# get the top documents for this topic
		weights = self.document_associations[self.current_document_topic_index].sort_values(ascending=False).head( self.top_associations )
		max_value = self.document_associations.max().max()
		# reverse the order
		weights = weights.sort_values(ascending=True)
		xvalues, yvalues = [], []
		for doc_id, score in weights.iteritems():
			xvalues.append( round( score, config.get("precision", 3) ) )
			yvalues.append( doc_id + " " )
		# get the color from the palette
		colors = self.get_colors( self.metadata["k"] )
		s_rgb = self.format_color_string( colors[self.current_document_topic_index-1] )
		# generate the chart
		title = "Topic %02d: %s" % ( self.current_document_topic_index, ", ".join( descriptors[self.current_document_topic_index-1] ) )
		chart_height = self.get_barchart_height( len(xvalues) )
		return dcc.Graph(
			id='chart_document_assoc',
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
					'title' : { 'text': title, 'font' : { "size" : 15 } },
					'height' : chart_height,
					'margin': { "t" : 40, "l" : 250, "r" : 100 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Topic-Document Association", 
						'tickfont' : { "size" : 13 },
						'titlefont' : { "size" : 15 },
						'range': [0, max_value]
					},
				}
			})

	def generate_partition_chart( self ):
		if self.partition_df is None:
			self.partition_df = self.metadata.get_partition_df()
		if self.partition_df is None:
			return ""
		# sort the partition topic sizes in reverse order
		s_sizes = self.partition_df.sort_values(by="Size", ascending=True)
		colors = self.get_colors( self.metadata["k"] )
		xvalues, yvalues, hovertext, s_colors = [], [], [], []
		for label, row in s_sizes.iterrows():
			xvalues.append( row["Size"] )
			yvalues.append( label + " " )
			hovertext.append( row["Descriptor"] )
			s_colors.append( self.format_color_string(colors[row["Number"]-1]) )
		# generate the chart
		chart_height = self.get_barchart_height( len(xvalues) )
		return dcc.Graph(
			id='chart_partition',
			figure={
				'data': [
					{
						'x': xvalues, 
						'y': yvalues, 
						'hovertext' : hovertext,
						'type': 'bar',
						'orientation' : 'h',
						# 'marker' : { 'color': 'rgba(55, 83, 139, 0.6)', 'opacity': 0.7 },
						'marker' : { 'color' : s_colors, 'opacity': 0.4 },
						'hovertemplate': '<b>%{y}</b>: %{x} documents<br>%{hovertext}<extra></extra>',
						'hoverlabel' : { 'bgcolor' : 'rgb(250, 246, 208)' }
		    		},
				],
				'layout': 
				{ 
					'height' : chart_height,
					'margin': { "t" : 2, "l" : 200, "r" : 100 },
					'yaxis' : { 'tickfont' : { "size" : 14 } },
					'xaxis' : { 'title' : "Number of Documents", 
						'tickfont' : { "size" : 13 },
						'titlefont' : { "size" : 15 } }
				}
			})	

	def __build_topic_options( self ):
		""" Utility function to create options for a dropdown component, each
		corresponding to a topic in the current model. """
		topic_options = []
		num_fmt = "Topic %02d" if self.metadata["k"] < 100 else "Topic %03d"
		for topic_index in range( 1, self.metadata["k"] + 1 ):
			label = num_fmt % topic_index
			topic_options.append( { "label": label, "value": topic_index } ) 
		return topic_options

	def generate_term_topic_dropdown( self ):
		""" Generate a Dash dropdown component to select a topic from the model. """
		# create the options
		topic_options = self.__build_topic_options()
		# create the Dash form component
		return dbc.Select(
			id='topic-term-dropdown',
			options=topic_options,
			value=topic_options[0]["value"]
		)		

	def generate_document_topic_dropdown( self ):
		""" Generate a Dash dropdown component to select a topic from the model. """
		# create the options
		topic_options = self.__build_topic_options()
		# create the Dash form component
		return dbc.Select(
			id='topic-document-dropdown',
			options=topic_options,
			value=topic_options[0]["value"]
		)
