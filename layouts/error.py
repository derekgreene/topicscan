import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from layouts.general import GeneralLayout

class ErrorLayout( GeneralLayout ):
	""" Implements the error/404 page of the TopicScan web interface. """

	def __init__( self, webcore, message ):
		super(ErrorLayout, self).__init__( webcore )
		self.show_navbar = False
		self.message = message

	def generate_main_panel( self ):
		full_message = "Sorry, an error has occured. %s" % self.message
		return html.Div([
			dbc.Row(
				html.Div([
					dbc.Col( [  
						html.H4( "TopicScan Error" ),
						html.Br(),
						dcc.Markdown( full_message ) 
						] ) ],
					className='col-lg-12'
				) ),
			], className='content'
		)
