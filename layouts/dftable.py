import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

# --------------------------------------------------------------

class DataFrameTable:
	""" Layout component which populates a standard Bootstrap Table from 
	a Pandas Data Frame. """

	def __init__( self, df, id = "dftable", alignments = {}, links = {}, show_index = False, 
			bordered = False, striped = False, hover = False, summary_row = False ):
		self.id = id
		self.df = df
		self.alignments = alignments
		self.links = links
		# display the index as a column?
		self.show_index = show_index
		self.index_name = "Index"
		# highlight the final row?
		self.summary_row = summary_row
		# appearance settings
		self.bordered = bordered
		self.striped = striped
		self.hover = hover

	def generate_layout( self ):
		""" Generate the full layout for the current table """
		if self.df is None:
			return ""
		# create the header
		columns = list( self.df.columns )
		table_header = self.generate_header( columns )
		# create the content
		table_rows = []
		for index, row in self.df.iterrows():
			is_summary = self.summary_row and ( len(table_rows) == len(self.df) - 1 )
			table_rows.append( self.generate_row( index, row, columns, is_summary ) )
		table_body = [html.Tbody( table_rows )]
		# create the full table as a Bootstrap Table
		return dbc.Table(table_header + table_body, 
			bordered=self.bordered, striped=self.striped, hover=self.hover,
			id = self.id, className="dftable")

	def generate_header( self, columns ):
		""" Generate the header row layout for the table """
		th_list = []
		# display the index as a column?
		if self.show_index:
			style = {}
			if "index" in self.alignments:
				 style["text-align"] = self.alignments["index"]
			th_list.append( html.Th(self.index_name, style=style, className="dftable-header-name") )
		for col in columns:
			style = {}
			if col in self.alignments:
				 style["text-align"] = self.alignments[col]
			th_list.append( html.Th(col, style=style, className="dftable-header-name") )
		table_header = [
	    	html.Thead( html.Tr(th_list), className="dftable-header")
		]
		return table_header

	def generate_row( self, index, row, columns, is_summary = False ):
		""" Generate the content for an individual table row """
		row_cells = []
		# add index cell?
		if self.show_index:
			row_cells.append( html.Td( index ) )
		url = None if not index in self.links else self.links[index]
		for col in columns:
			style = {}
			if col in self.alignments:
				 style["text-align"] = self.alignments[col]
			value = row[col]
			# if type(value) == int:
			# 	value = '{:,}'.format(value)
			if url is None:
				row_cells.append( html.Td( value, style=style, className="dftable-cell" ) ) 
			else:
				row_cells.append( html.Td( html.A(value, href=url, target="_blank"), 
					style=style, className="dftable-cell" ) ) 
		if is_summary:
			return html.Tr( row_cells, className="dftable-summaryrow" )
		return html.Tr( row_cells, className="dftable-row" )
