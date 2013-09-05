#!/usr/bin/env python
#coding=utf-8
from sh import pdftoppm, pdftotext
import numpy as np
import re

NON_WHITESPACE_RE = re.compile('\S+')
TRAILING_CHARS = ",.~†"

class COLOR:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

        

class Table():
	'''
	Storage model for a plain text table
	'''		
	def __init__(self, lines):
		self.lines = lines		
		self.width = 0
		for line in lines:
			self.width = max(len(line), self.width)
		self.height = len(lines)
		self.rtypes = {}
		self.ctypes = {}
		self.ttypes = {}
		
	
	def get_tokens(self):
		for y, row in enumerate(self.lines):
			for match in NON_WHITESPACE_RE.finditer(row):
				word =  match.string[match.start():match.end()]
				while len(word) > 0 and word[-1] in TRAILING_CHARS:
					word = word[0:-1]
					
				yield (match.start(), match.start() + len(word), y, word)				
			
	def __repr__(self):
		return "\n".join(self.lines)

	def setColType(self, x, ctype):
		self.ctypes[x] = ctype

	def setRowType(self, y, rtype):
		self.rtypes[y] = rtype

	def setTokType(self, tid, ttype):
		self.ttypes[tid] = ttype
		
	def __repr__(self):
		lines = []
		
		token_iter = self.get_tokens()
		(x_s, x_e, y, word)	 = token_iter.next()
		tid = 0
		
		for j in range(self.height):
			row = []
			for i in range(self.width):
				
				color = None
				
				try:
					while y < j or (y == j and x_e < i) :
						tid +=1
						(x_s, x_e, y, word)	 = token_iter.next()
						
					if y == j and x_s <= i and i < x_e:
						char = str(word[i - x_s])
						if ord(char) >= 128:
							char = "?"							
					else:
						char = " "
					
				except StopIteration:
					char = " "
					
				if char != " ":
					if self.ttypes[tid] == "ordercode_dec":
						color = COLOR.OKBLUE
					elif self.ttypes[tid] == "ordercode_val":
						color = COLOR.OKGREEN
					elif self.ttypes[tid] == "partnum_dec":
						color = COLOR.WARNING
					elif self.ttypes[tid] == "partnum_val":
						color = COLOR.FAIL
					elif char != " ":
						char = "?"
				
					
				if color != None:
					row.append(color)
				row.append(char)
				if color != None:
					row.append(COLOR.ENDC)
			
			lines.append("".join(row))
		return "\n".join(lines)	
		
		
		

def read_table(filepath):		
	with open(filepath) as f:
		table_lines = []
		for line in f:			
			table_lines.append(line[0:-1])
		return Table(table_lines)					
