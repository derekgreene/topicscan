import logging as log
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from webconfig import config
from .general import GeneralLayout
from .dftable import DataFrameTable

# --------------------------------------------------------------

class IndexLayout( GeneralLayout ):
	""" Implements the main page of the TopicScan web interface. """

	def __init__( self, webcore, show_navbar = True ):
		super(IndexLayout, self).__init__( webcore )
		self.show_navbar = show_navbar
		# page details
		self.page_suffix = "-main"

	def get_header_subtext( self ):
		""" Return the string which is displayed in the header, beside the logo. """
		return "%s" % str(self.webcore.dir_core)

	def generate_navbar( self ):
		""" Generate the Dash top navigation bar component. """
		# do we want a navbar?
		if not self.show_navbar:
			return ""
		# build the navbar and items
		return html.Div(
			dbc.NavbarSimple(
				children=[
					dbc.NavItem(dbc.NavLink("Topic Models", href="#amodels", external_link=True)),
					dbc.NavItem(dbc.NavLink("Word Embeddings", href="#aembeddings", external_link=True)),
				],
				dark=False,
				className='navbar-light bg-light container-fullwidth'
			), className='subnav'
	 	)

	def generate_main_panel( self ):
		""" Generate the main panel area of this page. """
		return html.Div([
			dbc.Row(
				html.Div([
					dcc.Link(id="amodels"),
					dbc.Col( self.generate_model_card() ) ],
					className='col-lg-12'
				) ),
			dbc.Row(
				html.Div([
					dcc.Link(id="aembeddings"),
					dbc.Col( self.generate_embedding_card() ) ],
					className='col-lg-12'
				) ),
			], className='content'
		)

	def generate_model_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Topic Models", className="card-header"),
				dbc.CardBody(
					[
						html.Div( self.generate_model_card_text(), className="card-text"),
						html.Div( self.generate_model_table() ),
					]
				),
			],
		)

	def generate_embedding_card( self ):
		return dbc.Card(
			[
				dbc.CardHeader("Word Embeddings"),
				dbc.CardBody(
					[
						html.Div( self.generate_embedding_card_text(), className="card-text"),
						html.Div( self.generate_embedding_table() ),
					]
				),
			],
		)

	def generate_model_card_text( self ):
		count = self.webcore.get_topic_model_count()
		if count == 1:
			text = "Found 1 topic model in the directory *%s*." % ( self.webcore.dir_core )
		else:
			text = "Found %d topic models in the directory *%s*." % ( count, self.webcore.dir_core )
		text += " To explore a model in detail, click on a row below."
		return dcc.Markdown( text )

	def generate_embedding_card_text( self ):
		count = self.webcore.get_embedding_count()
		if count == 1:
			text = "Found 1 word embedding in the directory *%s*." % ( self.webcore.dir_core )
		else:
			text = "Found %d word embeddings in the directory *%s*." % ( count, self.webcore.dir_core )
		text += " To explore a mowword embedding in detail, click on a row below."
		return dcc.Markdown( text )

	def generate_model_table( self ):
		""" Generate a Bootstrap table containing list of current topic model metadata. """
		df = self.webcore.df_models.sort_values( by=["Corpus","Name"] )
		alignments = { "Topics" : "right", "Documents" : "right", "Terms" : "right" }
		# create the links to other pages
		links = {}
		for index, row in df.iterrows():
			model_id = row["Name"]
			links[index] = self.generate_link( "topics", { "id":model_id } )
		return DataFrameTable( df, id="model-table", links=links, alignments=alignments, striped=False, hover=True ).generate_layout()

	def generate_embedding_table( self ):
		""" Generate a Bootstrap table containing list of current word embedding metadata. """
		df = self.webcore.df_embeddings.sort_values( by="Name" )
		alignments = { "Dimensions" : "right", "Documents" : "right", "Terms" : "right" }
		# create the links to other pages
		links = {}
		for index, row in df.iterrows():
			model_id = row["Name"]
			links[index] = self.generate_link( "embedding", { "id":model_id } )
		return DataFrameTable( df, id="embedding-table", links=links, alignments=alignments, striped=False, hover=True ).generate_layout()