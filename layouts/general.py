import logging as log
import uuid, urllib.parse
from matplotlib import cm
import dash, dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from webconfig import config
from webvalidation import measure_names, measure_short_names

# --------------------------------------------------------------

# Default external stylesheets to use
external_stylesheets = [dbc.themes.BOOTSTRAP]

# --------------------------------------------------------------

class GeneralLayout:
	""" An empty general purpose layout for a TopicScan page, designed to be subclassed. """

	def __init__( self, webcore ):
		self.webcore = webcore
		self.color_map_name = "tab10"
		# page details
		self.page_title = "TopicScan"
		self.page_suffix = ""

	def generate_layout( self ):
		return html.Div([ 
				self.generate_header(),
				self.generate_navbar(),
				self.generate_main_panel() 
			], className='root'
		)

	def generate_header( self ):
		return html.Header(
			html.Div( 
					html.Div( [
						html.A( 
								html.Img(src="assets/img/logo%s.png" % self.page_suffix, className="headerlogo"),
							className='navbar-brand', href='#'),
						html.Span( self.get_header_subtext(), className="headersubtext" ), ],
						className='navbar-header'),
				className='top-left'),
			className='header'
		)

	def get_header_subtext( self ):
		""" Return the string which is displayed in the header, beside the logo. """
		return ""

	def generate_navbar( self ):
		""" Return the navigation bar layout for this page """
		return ""

	def generate_main_panel( self ):
		""" Generate the main panel for this page. """
		return ""

	def get_colors( self, num_colors=10 ):
		""" Return a palette with the specified number of colors. """
		return cm.get_cmap(self.color_map_name, num_colors).colors

	def get_barchart_height( self, num_rows ):
		""" Return a fixed height for a horizontal bar chart, based on the specific number of rows. """
		if num_rows < 3:
			return 300
		elif num_rows <= 6:
			return 400
		elif num_rows <= 10:
			return 510
		elif num_rows <= 20:
			return 650
		elif num_rows <= 40:
			return 750
		return 850

	def generate_embedding_dropdown( self ):
		""" Utility function to generate a dropdown component which allows the user
		to choose between different word embedding models. """
		embed_options = []
		for embed_id in self.webcore.get_embedding_ids():
			em = self.webcore.get_embedding_metadata(embed_id)
			if em is None:
				continue
			label = "%s (%s)" % ( embed_id, em["description"] )
			embed_options.append( { "label":label, "value": embed_id } ) 
		if len(embed_options) > 0:
			return dbc.Select(
				id='embed-dropdown',
				options=embed_options,
				value=embed_options[0]["value"]
			)
		return dbc.Select(id='embed-dropdown', options=embed_options )

	def generate_measure_dropdown( self ):
		""" Utility function to generate a dropdown component which allows the user
		to choose between different topic evaluation measures. """
		measure_options = []
		for measure_id in measure_names:
			measure_options.append( 
				{ 
					"label": "%s (%s)" %( measure_names[measure_id], measure_short_names[measure_id] ), 
					"value": measure_id 
			} ) 
		default_measure = config.get( "default_measure", measure_options[0]["value"] )
		return dbc.Select(
			id='measure-dropdown',
			options=measure_options,
			value=default_measure
		)

	def format_color_string( self, color ):
		""" Utility function to convert a Matplotlib color into a rgb string. """
		rgb = [ str(round(c*255)) for c in color ]
		return "rgb(%s)" % ", ".join(rgb)

	def generate_link( self, pathname, query ):
		""" Takes a pathname, query parameters, and adds a unique identifier to it as a query paramter. """
		query["uid"] = str(uuid.uuid1()).replace("-","")
		url = "%s?" % pathname
		for name in query:
			if url[-1] != "?":
				url += "&"
			url += "%s=%s" % ( name, urllib.parse.quote( query[name] ) )
		return url
