#!/usr/bin/env python
#coding=utf-8
from pulp import * 
import table
import math


def colVar(x, ctype):
	return "col%s_is_%s"%(x,ctype)
	
def rowVar(y, rtypes):
	return "row%s_is_%s"%(y,rtypes)
	
def tokVar(t, ttypes):
	return "tok%s_is_%s"%(t,ttypes)
	
class TableModel:	
	
	def __init__(self, ctypes, table):
		self.ctypes = ctypes;
		self.rtypes = ["unknown", "product", "header"]
		self.ttypes = ["unclassified"]
		self.ttypes_dec = []
		self.ttypes_val = []
		for ctype in ctypes:
			self.ttypes_dec.append(ctype + "_dec")
			self.ttypes_val.append(ctype + "_val")
			self.ttypes.append(ctype + "_dec")
			self.ttypes.append(ctype + "_val")	
		
		self.table = table
		
		#build LP problem		
		self.lp = LpProblem("table", LpMaximize)
		self.v = {}
		
		#build column type variables and constrain only one-of-n is active
		for x in range(table.width):
			cats = []
			for ctype in self.ctypes:
				cats.append(self.addVariable(colVar(x, ctype), 0,1,cat='Integer'))
			
			self.lp += lpSum(cats) == 1
		#build row type variables and constrain only one-of-n is active
		for y in range(table.height):
			cats = []
			for rtype in self.rtypes:
				cats.append(self.addVariable(rowVar(y, rtype), 0,1,cat='Integer'))
			
			self.lp += lpSum(cats) == 1
		
		#ensure at least one row in the top three is a header
		'''
		cats = []
		for y in range(min(3, table.height)):
			cats.append(self.v[rowVar(y, "header")])
		self.lp += lpSum(cats) >=1
		'''
			
		row_decs = {}
		row_vals = {}
		
		#build token type variables and constrain only one-of-n is active	
		for tid, (x_s, x_e, y, word) in enumerate(table.get_tokens()):
			print word
			cats = []
			for ttype in self.ttypes:
				cats.append(self.addVariable(tokVar(tid, ttype), 0,1,cat='Integer'))
			
			self.lp += lpSum(cats) == 1
			
			#furthermore, ensure only declarations (or unclassified) appear in header rows
			#and values appear only in product rows
			decs = []
			vals = []
			for ttype in self.ttypes_dec:
				decs.append(self.v[tokVar(tid, ttype)])
			vals = []
			for ttype in self.ttypes_val:
				vals.append(self.v[tokVar(tid, ttype)])
									
			self.lp += lpSum(decs) == self.v[rowVar(y, "header")]
			self.lp += lpSum(vals) == self.v[rowVar(y, "product")]
			
			#furthermore, ensure column types match either a token val or declaration, or unknown
			#in entire range of the token
			for x in range(x_s, x_e):
				for ctype in self.ctypes:
					self.lp += \
						self.v[tokVar(tid, ctype + "_dec")] + \
						self.v[tokVar(tid, ctype + "_val")] + \
						self.v[tokVar(tid, "unclassified")] \
						>= self.v[colVar(x, ctype)]
						
						
	def solve(self, token_probability_fn):
		#maximize log probability of function that maps words to types
		obj = []
		for tid, (x_s, x_e, y, word) in enumerate(table.get_tokens()):
			for ttype in self.ttypes:
				p = math.log(token_probability_fn(ttype, word))
				
				obj.append( p * self.v[tokVar(tid, ttype)])
		self.lp += lpSum(obj)
		
		print "solving"
		self.lp.solve()
		print "Status:", LpStatus[self.lp.status]
		
		for x in range(self.table.width):
			for ctype in self.ctypes:
				if self.v[colVar(x, ctype)].varValue > 0.5:
					self.table.setColType(x, ctype)
					print colVar(x, ctype), " is true"
		
		for y in range(self.table.height):
			for rtype in self.rtypes:
				if self.v[rowVar(y, rtype)].varValue > 0.5:
					self.table.setRowType(y, rtype)
					print rowVar(y, rtype), " is true"
					
		for tid, (x_s, x_e, y, word) in enumerate(self.table.get_tokens()):
			for ttype in self.ttypes:
				if self.v[tokVar(tid, ttype)].varValue > 0.5:
					self.table.setTokType(tid, ttype)
					pass 
					print word, tokVar(tid, ttype), " is true"
		
	def addVariable(self, name, LB=None, UB=None, cat='Continuous'):
		self.v[name] = LpVariable(name, LB,UB,cat)
		return self.v[name]
	
def probabilityCatagoryGivenWord(catagory, word):
	if word == "Digi-Key" and catagory == "ordercode_dec":
			return 0.9
	
	if word.endswith("-ND") and catagory == "ordercode_val":
			return 0.8
				
	if "-" in word and catagory == "partnum_val":
			return 0.4
			
	if catagory == "unclassified" or catagory == "unknown_val" or catagory == "unknown_dec":
		return 0.3
	
	return 0.1


if __name__ == "__main__":
	table = table.read_table(sys.argv[1])
	model = TableModel(["unknown", "partnum", "ordercode"], table)
	
	model.solve(probabilityCatagoryGivenWord)
	
	print table
	
