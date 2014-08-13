'''
# xy_index.py: xy binning index class and accessories.
# is it a proper "index"? maybe. (x,y) are presumably spatial coordinates,
# but they can be any (x,y). the basic structure is a dictionary of dictionaries containing lists
# of any objects. objects can be augmented like [x,y,object].
# or like {(x,y):object}
#
# my_xy ~ {0:{0:[(0,0) objects...], 1:[(0,1) objects], 2:[(0,2) objects]}, 1:{0:[(1,0) objects], 1:[(1,1) objects], 2:[(1,2) objects]}}
# 
# indices are defined by bin width: i_x = (x-x0)/dx
#
'''

class xy_index(dict):
	
	#
	def __init__(self, x0=0., y0=0., dx=.1, dy=.1):
		self.x0 = x0
		self.y0 = y0
		self.dx = dx
		self.dy = dy
		#
		#self.catalog={}
		#
		#
	#
	def add_item(self, x, y, item=None):
		i_x = self.get_x_index(x)
		i_y = self.get_y_index(y)	# note that y0, dy (and x0, dx) will by default come from the class namespace.
		#
		if self.has_key(i_x)==False:
			self[i_x]={}
		if self[i_x].has_key(i_y)==False:
			self[i_x][i_y]={}
