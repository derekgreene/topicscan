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
		th_list = self.generate_th_list( columns )
		# display the index as a column?
		if self.show_index:
			style = {}
			if "index" in self.alignments:
				 style["text-align"] = self.alignments["index"]
			th_list.insert( 0, html.Th(self.index_name, style=style, className="dftable-header-name") )
		table_header = [
	    	html.Thead( html.Tr(th_list), className="dftable-header")
		]
		return table_header

	def generate_th_list( self, columns ):
		th_list = []
		for col in columns:
			style = {}
			if col in self.alignments:
				 style["text-align"] = self.alignments[col]
			th_list.append( html.Th(col, style=style, className="dftable-header-name") )
		return th_list		

	def generate_row( self, index, row, columns, is_summary = False ):
		""" Generate the content for an individual table row """
		row_cells = self.generate_row_cells( index, row, columns ) 
		# add index cell?
		if self.show_index:
			row_cells.insert( 0, html.Td( index ) )
		if is_summary:
			return html.Tr( row_cells, className="dftable-summaryrow" )
		return html.Tr( row_cells, className="dftable-row" )

	def generate_row_cells( self, index, row, columns ):
		row_cells = []
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
		return row_cells

# --------------------------------------------------------------

class CheckboxTable(DataFrameTable):

	def __init__( self, df, id = "dfcheckboxtable", alignments = {}, links = {}, show_index = False, 
			bordered = False, striped = False, hover = False, summary_row = False, select_label = "" ):
		super(CheckboxTable, self).__init__( df, id, alignments, links, show_index, bordered, striped, hover, summary_row )
		self.select_label = select_label
		self.checkbox_ids = []

	# def generate_layout( self ):
	# 	""" Generate the full layout for the current table """
	# 	if self.df is None:
	# 		return ""
	# 	# create the header
	# 	columns = list( self.df.columns )
	# 	table_header = self.generate_header( columns )
	# 	# create the content
	# 	table_rows = []
	# 	for index, row in self.df.iterrows():
	# 		is_summary = self.summary_row and ( len(table_rows) == len(self.df) - 1 )
	# 		table_rows.append( self.generate_row( index, row, columns, is_summary ) )
	# 	table_body = [html.Tbody( table_rows )]
	# 	# create the full table as a Bootstrap Table
	# 	tab = dbc.Table(table_header + table_body, 
	# 		bordered=self.bordered, striped=self.striped, hover=self.hover,
	# 		id = self.id, className="dftable")
	# 	return dbc.FormGroup( tab )

	def generate_header( self, columns ):
		""" Generate the header row layout for the table """
		th_list = self.generate_th_list( columns )
		# display the index as a column?
		if self.show_index:
			style = {}
			if "index" in self.alignments:
				 style["text-align"] = self.alignments["index"]
			th_list.insert( 0, html.Th(self.index_name, style=style, className="dftable-header-name") )
		# add selection
		style = { "text-align":"center" }
		th_list.insert( 0, html.Th(self.select_label, style=style, className="dftable-header-name") )
		# return the header row
		table_header = [
	    	html.Thead( html.Tr(th_list), className="dftable-header")
		]
		return table_header

	def generate_row( self, index, row, columns, is_summary = False ):
		""" Generate the content for an individual table row """
		row_cells = self.generate_row_cells( index, row, columns ) 
		# add index cell?
		if self.show_index:
			row_cells.insert( 0, html.Td( index ) )
		if is_summary:
			return html.Tr( row_cells, className="dftable-summaryrow" )
		# add check box cell
		checkbox_id = "check_%s" % len(self.checkbox_ids)
		self.checkbox_ids.append( checkbox_id )
		style = { "text-align":"center" }
		row_cells.insert( 0, html.Td( 
			html.Div( 
					dbc.Checkbox( className="form-check-input", id=checkbox_id, checked=False ),
				className="custom-control custom-checkbox", style=style)
			 ) )
		# return the table row
		return html.Tr( row_cells, className="dftable-row" )		
