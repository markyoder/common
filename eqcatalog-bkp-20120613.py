from math import *	
from scipy import *
import scipy
from pylab import *
from matplotlib import *
import numpy.fft as nft
import scipy.optimize as spo
#from matplotlib import pyplot as plt
import pylab as plt
from matplotlib import rc
import numpy


import string
import sys
#from matplotlib import *
#from pylab import *
import os
import random
import time
#
# gamma function lives here:
#import scipy.special
from scipy.special import gamma
#from scipy.optimize import leastsq
from matplotlib import axis as aa
from threading import Thread
#
#
import datetime as dtm
import calendar
import operator
import urllib.request, urllib.parse, urllib.error
import MySQLdb

# maping bits:
import matplotlib	# note that we've tome from ... import *. we should probably eventually get rid of that and use the matplotlib namespace.
#matplotlib.use('Agg')
#from matplotlib.toolkits.basemap import Basemap
from mpl_toolkits.basemap import Basemap as Basemap
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class eqcatalog:
	# a simple catalog class. we'll need X,Y,wt,
	# call like: lf1=m.catalog()
	#
	#
	mc=None	# catalog threshold
	cat=[]	# let's use [[evDateTime, lat, lon, mag, a, b], [...]] and we'll plot with map(), etc.
	subcats=[]
	activefig=None
	catmap=None
	#
	#
	def __init__(self, inData=[]):
		#self.cat=[]
		#self.subcats=[]
		self.initialize(inData)
	
	def initialize(self, inData=[]):
		# what does the data look like?
		self.cat=[]
		self.subcats=[]
		#
		self.cat=inData
		self.sqlport=3306
		self.sqlhost='localhost'
		inData=None
		self.catmap=None
		self.__name__='eqcatalog'
		self.mapres='l'	# basemap map resolution. at some pont, add functions to sort out nonsensical values.
		#
	#
	def getMainEvent(self, thiscat=None):
		# return catalog row of max magnitude (epicenter location (more or less)) event. note, by default we use ths shock-cat because it will
		# be faster than using the fullCat AND, the fullCat is likely to have other large earthquakes.
		if thiscat==None: thiscat=self.cat
		maxMag=thiscat[0][3]
		maxIndex=0
		for i in range(len(thiscat)):
			#print i, maxMag, maxIndex, cat[i][3]
			if thiscat[i][3]>maxMag:
				maxIndex=i
				maxMag=thiscat[i][3]
		return thiscat[maxIndex] + [maxIndex]
	
	def getIndexDtm(self, mindt=None, cat=None, datecol=0):
		if cat==None or type(cat).__name__ not in ('list', 'tuple'): cat=self.cat
		if mindt==None or type(mindt).__name__!='datetime': mindt=self.getMainEvent()[0]
		#
		for rw in cat:
			if rw[datecol]>=mindt: return rw
		return None
		#
		return thiscat[maxIndex] + [maxIndex]
	
	def getSubCat(self, catindex=0):
		if len(self.subcats)==0: return None
		#
		return self.subcats[catindex][1]
	
	def getcat(self, catindex=0):
		# more general and simpler than getSubCat. 0 -> maincat, 1, etc. -> subcats:
		# it would probably be a good idea to also restructure how catalogs are stored inte class:
		# catalogs=[[maincat], [subcat1], [subcat2], ...]
		# self.cat -> catalogs[0]
		if catindex==0: return self.cat
		if len(self.subcats)<(catindex): return None	# this cat index does not exist
		return self.subcats[catindex-1][1]
	
	def getLatLonRange(self, cat=None, latloncols=[1,2]):
		if cat==None: cat=self.cat
		if latloncols==None: latloncols=[1,2]	# latitude, lon cols of catalog (order is lat, lon).
		#
		minLat=cat[0][latloncols[0]]
		maxLat=cat[0][latloncols[0]]
		minLon=cat[0][latloncols[1]]
		maxLon=cat[0][latloncols[1]]
		#
		for rw in cat:
			thisLat=rw[latloncols[0]]
			thisLon=rw[latloncols[1]]
			#
			if thisLat>maxLat: maxLat=thisLat
			if thisLat<minLat: minLat=thisLat
			if thisLon>maxLon: maxLon=thisLon
			if thisLon<minLon: minLon=thisLon
		#
		return [[minLat, minLon], [maxLat, maxLon]]
	
	def ellipseCat(self, fullcat=None, theta=0, clat=35.9, clon=-120.5, ra=1.0, rb=1.0):
		#
		
		#print "event (start) date, catname: %s, %s, %s" % (eventDate, catFname, self.catname)
		#
		if fullcat==None: fullcat=self.cat
		#self.subcats+=[[subcatname], []]
		tempcat=[]
		
		#nEventsSinceMS=0
		for row in fullcat:
			# rotate each element into our aftershock axis, is it in the ellipse?
			newVec=rotatexy(row[2], row[1], clat, clon, theta)
			#
			# is the rotated vector in our ellipse?
			if abs(newVec[0])>ra: continue
			Y=ellipseY(newVec[0], ra, rb)
			if abs(newVec[1])>Y: continue
			# dtm, lat, lon, mag, tX, tY 		(note this is like y,x, x`, y` for the space coordinates).
			#self.subcats[-1][1]+=[[row[0], row[1], row[2], row[3], newVec[0], newVec[1]]]
			tempcat+=[[row[0], row[1], row[2], row[3], newVec[0], newVec[1]]]
		return tempcat
	
	def polycat(self, cat=None, verts=None):
		# as per james' counsel, a "knot theory" approach is much simpler. independent of right/left handedness, the sum of above/below tests is >0 for
		# points inside, 0 for points outside (like EnM).
		# start by making verts -> vectors -> f(x)
		#
		# verts are like: [[x0,y0], [x1, y1], ..., [xn, yn], [x0, y0]]; last point is optional.
		if cat==None: cat=self.cat
		if verts==None or len(verts)<3:
			# don't know. if we don't have verts, what can we do?
			# also, we need at least 3 verts, or we just have a line.
			return None
		#
		if verts[-1]!=verts[0]: verts+=[verts[0]]
		#
		vecs=[]	# like [ [[x0,y0], [x1, y1]], [[x1, y1], [x2, y2]], ...]
		#vecdirs=[]	# vector directions; -1=left, 0=none, 1=right. this determines whether we want to be over or under. the first x-direction vector definds a right/left poly.
		# get lat, lon extrema and make vectors:
		extremeVerts=[verts[0][0], verts[0][0], verts[0][1], verts[0][1]]	# [minLon, maxLon, minLat, maxLat]
		for i in range(len(verts)-1):
			vecs+=[[verts[i], verts[i+1]]]
			if verts[i+1][0]>extremeVerts[1]: extremeVerts[1]=verts[i+1][0]
			if verts[i+1][0]<extremeVerts[0]: extremeVerts[0]=verts[i+1][0]
			if verts[i+1][1]>extremeVerts[3]: extremeVerts[3]=verts[i+1][1]
			if verts[i+1][1]<extremeVerts[2]: extremeVerts[2]=verts[i+1][1]
			#
			# and keep a list of vector directions (right,left; do we need up, down?):
			thisdir=0	# reserve for vertical elements.
			if verts[i+1][0]>verts[i][0]: thisdir=1 #CatMap
			if verts[i+1][0]<verts[i][0]: thisdir=-1
			#vecdirs+=[thisdir]
		#
		# we don't really need the center, but it might be useful later:
		center=scipy.array([extremeVerts[0] + (extremeVerts[1]-extremeVerts[0])/2.0, extremeVerts[2] + (extremeVerts[3]-extremeVerts[2])/2.0])
		#
		# and this way, we don't need the poly-direction.
		# now we can spin through the catalog. inout=sum(x^ * above/below). inout=0 means out; inout>0 means in.
		# where x^ is {-1, 1} for left, right; above/below is {-1, 1} for point is above, below. i don't think which one is -1 and which is 1 matters
		# so long as we are consistent. also, as per old-school gaussian integrals, the number of times we cross a boundary: odd-> in , even -> out
		# applies as well.
		polycat=[]
		for iev in range(len(cat)):
			event=cat[iev]
			x=event[2]
			y=event[1]
			# for speed, if we are outside the extreme vertices, move on:
			if (x<extremeVerts[0] or x>extremeVerts[1] or y<extremeVerts[2] or y>extremeVerts[3]):
					#print "extreme kill (%d, %d)" % (x, y)
					#keepEvent=0
					# and we're done...
					continue
			#
			#keepEvent=1	# start by assuming we keep the event.
			inPolyTracker=0	# running up/down score. by default, do not keep the event.
			#print "*#*#*#"
			for ivec in range(len(vecs)):
				vec=vecs[ivec]
				# make a line (if it's not vertical):
				if vec[1][0]-vec[0][0]==0: continue	# vertical segments do not contribute, and we'll get x/0 error.
				b=(vec[1][1]-vec[0][1])/(vec[1][0]-vec[0][0])
				a=vec[0][1]-b*vec[0][0]
				y0=a+b*x
				#
				# xrange:
				if vec[0][0]>vec[1][0]:
					bigX=vec[0][0]
					smallX=vec[1][0]
				if vec[0][0]<vec[1][0]:
					bigX=vec[1][0]
					smallX=vec[0][0]
				#
				# debug:
				#if iev<40:
				#	print vec[0][0], vec[1][0], x, lookUpDown, y, y0
				#	print (x>=smallX and x<=bigX), (lookUpDown==-1 and y>y0 ), (lookUpDown==1 and y<y0)
				#
				# are we in the current xrange?
				if (x<smallX or x>bigX): continue
				# if it's on the line, keep it:
				if y==y0:
					inPolyTracker=1
					continue
				# is it inside the polygon?
				if y>y0: isUp=1							# point is above
				if y<y0: isUp=-1							# point is below
				if vec[1][0]>vec[0][0]: vecDir=1		# to the right
				if vec[1][0]<vec[0][0]: vecDir=-1	# to the left
				inPolyTracker+=(vecDir*isUp)
				#
			#
			if inPolyTracker!=0: polycat+=[event]
			
		#print extremeVerts
		return polycat
		
		
	def polycat_cp(self, cat=None, verts=None):
		# my original version of polycat using cross products to determine the direction of the polygon. there is a faster way...
		# verts are like: [[x0,y0], [x1, y1], ..., [xn, yn], [x0, y0]]; last point is optional.
		if cat==None: cat=self.cat
		if verts==None or len(verts)<3:
			# don't know. if we don't have verts, what can we do?
			# also, we need at least 3 verts, or we just have a line.
			return None
		#
		if verts[-1]!=verts[0]: verts+=[verts[0]]
		#
		vecs=[]	# like [ [[x0,y0], [x1, y1]], [[x1, y1], [x2, y2]], ...]
		vecdirs=[]	# vector directions; -1=left, 0=none, 1=right. this determines whether we want to be over or under. the first x-direction vector definds a right/left poly.
		# get lat, lon extrema and make vectors:
		extremeVerts=[verts[0][0], verts[0][0], verts[0][1], verts[0][1]]	# [minLon, maxLon, minLat, maxLat]
		for i in range(len(verts)-1):
			vecs+=[[verts[i], verts[i+1]]]
			if verts[i+1][0]>extremeVerts[1]: extremeVerts[1]=verts[i+1][0]
			if verts[i+1][0]<extremeVerts[0]: extremeVerts[0]=verts[i+1][0]
			if verts[i+1][1]>extremeVerts[3]: extremeVerts[3]=verts[i+1][1]
			if verts[i+1][1]<extremeVerts[2]: extremeVerts[2]=verts[i+1][1]
			#
			# and keep a list of vector directions (right,left; do we need up, down?):
			thisdir=0	# reserve for vertical elements.
			if verts[i+1][0]>verts[i][0]: thisdir=1
			if verts[i+1][0]<verts[i][0]: thisdir=-1
			vecdirs+=[thisdir]
		#
		#print vecdirs
		# now, is the poly right or left handed? from the poly center, calculate the mean r x v.
		center=scipy.array([extremeVerts[0] + (extremeVerts[1]-extremeVerts[0])/2.0, extremeVerts[2] + (extremeVerts[3]-extremeVerts[2])/2.0])
		#print "verts: %s" % str(verts)
		#print "vecs: %s" % str(vecs)
		#print "center: %s" % str(center)
		polyDir=0
		for vec in vecs:
			# get the cross product r x vec:
			thisvec=scipy.array(vec[1])-scipy.array(vec[0])
			rvec=scipy.array(vec[0])-center
			cprod=numpy.cross(rvec, thisvec)
			#print vec, thisvec, rvec, cprod, type(cprod)
			# so i guess when your vectors are coplanar, scipy.array knows to retun just a scalar for the cross-product.
			polyDir+=cprod
		if polyDir>0: polyDir=1
		if polyDir<0: polyDir=-1
		#print "polyDir: %f" % polyDir
		#
		# now we can spin through the catalog to find elements above/below poly segments, depending on the direction of the segment and right/left
		# handedness of the poly.
		polycat=[]
		for iev in range(len(cat)):
			event=cat[iev]
			x=event[2]
			y=event[1]
			keepEvent=1	# start by assuming we keep the event.
			#print "*#*#*#"
			for ivec in range(len(vecs)):
				# test the event against each polygon segment. if it falls outside one or more, don't keep it...
				vec=vecs[ivec]
				# make a line:
				if vec[1][0]-vec[0][0]==0: continue
				#
				b=(vec[1][1]-vec[0][1])/(vec[1][0]-vec[0][0])
				a=vec[0][1]-b*vec[0][0]
				#
				lookUpDown=vecdirs[ivec]*polyDir
				y0=a+b*x
				#keep criteria:
				#if (x>=vec[0][0] and vec<=vec[1][0]) and ((lookUpdown==-1 and y<=y0 ) or (lookUpdown==1 and y>=0)):
				# so discard criteria is opposite (in y):
				if vec[0][0]>vec[1][0]:
					bigX=vec[0][0]
					smallX=vec[1][0]
				if vec[0][0]<vec[1][0]:
					bigX=vec[1][0]
					smallX=vec[0][0]
				#	
				if (x<extremeVerts[0] or x>extremeVerts[1] or y<extremeVerts[2] or y>extremeVerts[3]):
					print("extreme kill (%d, %d)" % (x, y))
					keepEvent=0
				if ((x>=smallX and x<=bigX) and ((lookUpDown==-1 and y>y0 ) or (lookUpDown==1 and y<y0))) :
					keepEvent=0
					print("f(x) kill (%d, %d)" % (x, y))
					# and for efficiency:
					continue
				#
			#
			if keepEvent==1: polycat+=[event]
		
			
		print(extremeVerts)
		return polycat
			
		
#[0,0], [2,0], [4,4], [2,6], [0,4]			
	
	def addEllipCat(self, subcatname='newcat', fullcat=None, theta=0, clat=35.9, clon=-120.5, ra=1.0, rb=1.0):
		#
		if fullcat==None: fullcat=self.cat
		
		newcat=self.ellipseCat(fullcat, theta, clat, clon, ra, rb)
		self.subcats+=[[subcatname, newcat]]
	
	def getMagSubcat(self, fullcat=None, minmag=2.5, magcol=3):
		newcat=[]
		for rw in fullcat:
			if rw[magcol]>=minmag: newcat+=[rw]
		return newcat
	def addMagSubcat(self, subcatname='magsubcat', fullcat=None, minmag=2.5, magcol=3):
		subcatname='%s-%s' % (subcatname, str(minmag))
		self.subcats+=[[subcatname, getMagSubcat(fullcat, minmag, magcol)]]
	#
	def getxytSubcat(self, fullcat=None, dts=[], lats=[], lons=[], llcols=[1,2]):
		if type(dts).__name__!='list': dts=[]
		if type(lats).__name__!='list': lats=[]
		if type(lons).__name__!='list': lons=[]
		while len(dts)<2: dts+=[None]
		#
		newcat=self.getTimeRangeCat(fullcat, dts[0], dts[1])
		newcat=self.getLatLonSubcat(newcat, lats, lons, llcols)
		#
		return newcat
	def addxytSubcat(self, subcatname='xytsubcat', fullcat=None, dts=[], lats=[], lons=[], llcols=[1,2]):
		self.subcats+=[[subcatname, self.getxytSubcat(fullcat, dts, lats, lons, llcols)]]
	
	def getTimeRangeCat(self, fullcat=None, dtFrom=None, dtTo=None):
		if fullcat==None: fullcat=self.cat
		if dtFrom==None: dtFrom=fullcat[0][0]
		if dtTo==None: dtTo=fullcat[-1][0]
		newcat=[]
		for rw in fullcat:
			if rw[0]>=dtFrom and rw[0]<=dtTo: newcat+=[rw]
		#
		return newcat
	def addTimeRangeCat(self, subcatname='dtSubcat', fullcat=None, dtFrom=None, dtTo=None):
		self.subcats+=[[subcatname, self.getTimeRangeCat(fullcat, dtFrom, dtTo)]]
	
	def getLatLonSubcat(self, fullcat, lats=[], lons=[], llcols=[1,2]):
		# llcols: lat, lon
		llrange=None
		if lats in [[], None]:
			if llrange==None: llrange=self.getLatLonRange(fullcat, latloncols=[llcols[0], llcols[1]])
			deltaLats=llrange[1][0]-float(llrange[0][0])
			lats=[llrange[0][0]+deltaLats/2.0, llrange[1][0]-deltaLats/2.0]
		
		if lons in [[], None]:
			if llrange==None: llrange=self.getLatLonRange(fullcat, latloncols=[llcols[0], llcols[1]])
			deltaLons=llrange[1][1]-float(llrange[0][1])
			lons=[llrange[0][1]+deltaLons/2.0, llrange[1][1]-deltaLons/2.0]
			
			#lats={get min, max lat,lon from catalog}
		# and same for lons...
		#
		newcat=[]
		for rw in fullcat:
			if (rw[llcols[0]]>=lats[0] and rw[llcols[0]]<=lats[1]) and (rw[llcols[1]]>=lons[0] and rw[llcols[1]]<=lons[1]):
				newcat+=[rw]
			#
		#
		return newcat
	def addLatLonSubcat(self, subcatname='xysubcat', fullcat=None, lats=[], lons=[], llcols=[1,2]):
		self.subcats+=[[subcatname, self.getLatLonSubcat(fullcat, lats, lons, llcols)]] 
	
	def getxytmSubcat(self, fullcat=None, dts=[], lats=[], lons=[], minmag=2.5, llmcols=[1,2,3]):
		# just do the whole thing here, so it's fast:
		if type(dts).__name__!='list': dts=[]
		if type(lats).__name__!='list': lats=[]
		if type(lons).__name__!='list': lons=[]
		if type(llmcols).__name__!='list': llmcols=[1,2,3]
		while len(dts)<2: dts+=[None]
		while len(llmcols)<3: llmcols+=[llmcols[-1]+1]
		llrange=None
		#return llmcols
		if lats in [[], None] or len(lats)!=2:
			if llrange==None: llrange=self.getLatLonRange(fullcat, latloncols=[llmcols[0], llmcols[1]])
			deltaLats=llrange[1][0]-float(llrange[0][0])
			lats=[llrange[0][0]+deltaLats/2.0, llrange[1][0]-deltaLats/2.0]
		
		if lons in [[], None] or len(lons)!=2:
			if llrange==None: llrange=self.getLatLonRange(fullcat, latloncols=[llmcols[0], llmcols[1]])
			deltaLons=llrange[1][1]-float(llrange[0][1])
			lons=[llrange[0][1]+deltaLons/2.0, llrange[1][1]-deltaLons/2.0]
		#
		#newcat=self.getTimeRangeCat(fullcat, dts[0], dts[1])
		#newcat=self.getLatLonSubcat(newcat, lats, lons, llcols)
		newcat=[]
		print(lats, lons, dts)
		for rw in fullcat:
			if rw[llmcols[0]]>=lats[0] and rw[llmcols[0]]<=lats[1] and rw[llmcols[1]]>=lons[0] and rw[llmcols[1]]<=lons[1] and rw[llmcols[2]]>=minmag and rw[0]>=dts[0] and rw[0]<=dts[1]:
				newcat+=[rw]
		return newcat
		#
	def addxytmSubcat(self, subcatname='xytmsubcat', fullcat=None, dts=[], lats=[], lons=[], minmag=2.5, llmcols=[1,2,3]):
		#print llmcols
		self.subcats+=[[subcatname, self.getxytmSubcat(fullcat, dts, lats, lons, minmag, llmcols)]]
			
	def mapOverlay(self, catalog=None, fignum=0, dots='b.', doShow=False):
		# this does not quite work yet. the map does not rescale properly for the distinct catalogs with different lat/lon ranges.
		# it looks like a good approach might be to create a map-class, which can contain a catalog or vice-versa, or maybe one
		# could be a sub-class, but i dont' think that hierarchy is clear.
		# the basic idea: map: lat/lon range, lat/lon center, projection, etc., catalogOverlays [] (are a list of catalogs overlayed on the map. note
		# the lat/lon range will be (at least) max/min(lon/lat from any cat) overlayed onto the map). also, annotationOverlays (text, graphics, etc.),
		# other stuff too...
		if catalog==None: catalog=self.cat
		f0=plt.figure(fignum)
		#
		#set up map:
		llr=self.getLatLonRange(catalog)	# latLonRange
		llr[0][0]-=2.0
		llr[0][1]-=2.0
		llr[1][0]+=2.0
		llr[1][1]+=2.0
		
		cntr=[float(llr[0][0])+(llr[1][0]-float(llr[0][0]))/2.0, float(llr[0][1])+(llr[1][1]-float(llr[0][1]))/2.0]
		catmap=Basemap(llcrnrlon=llr[0][1], llcrnrlat=llr[0][0], urcrnrlon=llr[1][1], urcrnrlat=llr[1][0], resolution =self.mapres, projection='tmerc', lon_0=cntr[1], lat_0=cntr[0])
		canvas=FigureCanvas(f0)
		catmap.ax=f0.add_axes([0,0,1,1])
		f0.set_figsize_inches((8/catmap.aspect,8.))
		#
		catmap.drawcoastlines(color='gray')
		catmap.drawcountries(color='gray')
		catmap.fillcontinents(color='beige')
		xfull, yfull=catmap(list(map(operator.itemgetter(2), catalog)), list(map(operator.itemgetter(1), catalog)))
		#epx, epy=catmap(epicenter[0], epicenter[1])
		catmap.plot(xfull, yfull, dots, label='Full Catalog')
		#catmap.plot(epx, epy, 'ro')
		#canvas.print_figure(saveName)
		
		if doShow: plt.show()
		
		return None
	
	def plotCatMap(self, catalog=None, doShow=True, doSave=False, saveName='catalogPlot.png', epicenter=None, legendLoc='upper left', doCLF=True, eqicon='b,', myaxis=None, fignum=None, padfactor=.25):
		if catalog==None: catalog=self.cat
		
		if epicenter==None:
			mainshock=self.getMainEvent(catalog)
			epicenter=[mainshock[2], mainshock[1]]
		#
		if doShow>=1 and fignum==None: fnum=doShow
		if fignum!=None: fnum=fignum
		
		f0=plt.figure(int(doShow))	
		if doCLF: plt.clf()
		#		
		#set up map:
		#llr=self.getLatLonRange(catalog)	# latLonRange
		llr=self.getLatLonRange(catalog)	# latLonRange #return [[minLat, minLon], [maxLat, maxLon]]
		latpad=padfactor*(llr[1][0]-llr[0][0])
		lonpad=padfactor*(llr[1][1]-llr[0][1])
		llr[0][0]-= latpad	#.5
		llr[0][1]-= lonpad	#.5
		llr[1][0]+= latpad	#.5
		llr[1][1]+= latpad	#.5
		
		cntr=[float(llr[0][0])+(llr[1][0]-float(llr[0][0]))/2.0, float(llr[0][1])+(llr[1][1]-float(llr[0][1]))/2.0]
		if self.catmap==None: self.catmap=Basemap(llcrnrlon=llr[0][1], llcrnrlat=llr[0][0], urcrnrlon=llr[1][1], urcrnrlat=llr[1][0], resolution =self.mapres, projection='tmerc', lon_0=cntr[1], lat_0=cntr[0])
		catmap=self.catmap
		
		canvas=FigureCanvas(f0)
		if myaxis==None: myaxis=f0.add_axes([0,0,1,1])
		#catmap.ax=f0.add_axes([0,0,1,1])
		catmap.ax=myaxis
		#f0.set_figsize_inches((8/catmap.aspect,8.))
		#
		catmap.drawcoastlines(color='gray')
		catmap.drawcountries(color='gray')
		catmap.drawstates(color='gray')
		catmap.drawrivers(color='gray')
		catmap.fillcontinents(color='beige')
		
		catmap.drawmeridians(list(range(int(llr[0][1]-2.0), int(llr[1][1]+2.0))), color='k', labels=[1,1,1,1])
		catmap.drawparallels(list(range(int(llr[0][0]-2.0), int(llr[1][0]+2.0))), color='k', labels=[1, 1, 1, 1])
		
		xfull, yfull=catmap(list(map(operator.itemgetter(2), catalog)), list(map(operator.itemgetter(1), catalog)))
		epx, epy=catmap(epicenter[0], epicenter[1])
		#catmap.plot(xfull, yfull, 'b,', label='Full Catalog')
		catmap.plot(xfull, yfull, eqicon, label='earthquakes')
		catmap.plot(epx, epy, 'ro')
		
		# if we are inclned to save:
		if doSave and saveName!=None: canvas.print_figure(saveName)
		
		#
		#ax=plt.gca()
		#el = Ellipse((self.tLon, self.tLat), 2.0*self.tA, 2.0*self.tB, -self.tTheta, facecolor='b', alpha=0.4)
		#catmap.ax.add_artist(el)
		#ax.add_artist(el)
		#
		#plt.plot(map(operator.itemgetter(2), self.fullCat), map(operator.itemgetter(1), self.fullCat), '+')
		#plt.plot(map(operator.itemgetter(2), self.shockCat), map(operator.itemgetter(1), self.shockCat), '.')
		#plt.plot(map(operator.itemgetter(2), fcat), map(operator.itemgetter(1), fcat), '+', label='Full Catalog')
		#plt.plot(map(operator.itemgetter(2), scat), map(operator.itemgetter(1), scat), '.', label='Aftershock zone')
		#plt.plot([epicenter[0]], [epicenter[1]], 'ro', label='epicenter')
		plt.legend(loc=legendLoc, numpoints=1)
		if doSave: plt.savefig(saveName)
		if doShow: plt.show()
		
		return catmap
	
	def testMap(self):
		import pickle
		import time
		#
		fig=plt.figure()
		#
		t1 = time.clock()
		#m = Basemap(width=920000, height=1100000, resolution='f', projection='tmerc', lon_0=-4.2, lat_0=54.6)
		#m = Basemap(llcrnrlon=-11.0, llcrnrlat=45.0, urcrnrlon=3.0, urcrnrlat=59.0, resolution='f', projection='tmerc', lon_0=-4.2, lat_0=54.6)
		
		lllon=-115
		lllat=32
		urlon=-105
		urlat=42
		lon0=lllon + (urlon-lllon)/2.0
		lat0=lllat + (urlat-urlat)/2.0
		print("center: %f, %f" % (lon0, lat0))
		m = Basemap(llcrnrlon=lllon, llcrnrlat=lllat, urcrnrlon=urlon, urcrnrlat=urlat, resolution=self.mapres, projection='tmerc', lon_0=lon0, lat_0=lat0)
		m.drawcountries()
		m.drawrivers()
		print(time.clock()-t1,' secs to create original Basemap instance')

		# cPickle the class instance.
		pickle.dump(m,open('map.pickle','wb'),-1)

		# clear the figure
		plt.clf()
		# read cPickle back in and plot it again (should be much faster).
		t1 = time.clock()
		m2 = pickle.load(open('map.pickle','rb'))
		# draw coastlines and fill continents.
		m.drawcoastlines()
		# fill continents and lakes
		m.fillcontinents(color='coral',lake_color='aqua')
		# draw political boundaries.
		m.drawcountries(linewidth=1)
		# fill map projection region light blue (this will
		# paint ocean areas same color as lakes).
		m.drawmapboundary(fill_color='aqua')
		# draw major rivers.
		m.drawrivers(color='b')
		print(time.clock()-t1,' secs to plot using using a pickled Basemap instance')
		# draw parallels
		circles = np.arange(48,65,2).tolist()
		m.drawparallels(circles,labels=[1,1,0,0])
		# draw meridians
		meridians = np.arange(-12,13,2)
		m.drawmeridians(meridians,labels=[0,0,1,1])
		plt.title("High-Res British Isles",y=1.04)
		plt.show()
	
	def plotCatsMap(self, catalogses=None, maincat=0, doShow=True, doSave=False, saveName='catalogPlot.png', epicenter=None, legendLoc='upper left', maincatname='full cat'):
		# same as plotCatMap, but multiple catalogs. we assume the lat/lon range comes from the first catalog.
		# maincat is the "main catalog", the subcat we care about most. we assume the primary catalog is the broadest; maincat contains the epicenter, etc.
		if catalogses==None: catalogses=[maincatname, self.cat] + self.subcats

		#catalogs=[self.cat] + map(operator.itemgetter(1), self.subcats)
		#catnames=[maincatname] + map(operator.itemgetter(0), self.subcats)
		catalogs=list(map(operator.itemgetter(1), catalogses))
		catnames=list(map(operator.itemgetter(0), catalogses))
		#return [catalogs, catnames]
		catalog=catalogs[0]
		
		if epicenter==None:
			#mainshock=self.getMainEvent(catalog)
			mainshock=self.getMainEvent(catalogs[maincat+1])
			epicenter=[mainshock[2], mainshock[1]]
		#
		f0=plt.figure(0)	
		plt.clf()
		#		
		#set up map:
		llr=self.getLatLonRange(catalog)	# latLonRange
		#bulgeFactor=2.0
		llr[0][0]-=.1
		llr[0][1]-=.1
		llr[1][0]+=.1
		llr[1][1]+=.1
		
		print("setting up map prams")
		
		cntr=[float(llr[0][0])+(llr[1][0]-float(llr[0][0]))/2.0, float(llr[0][1])+(llr[1][1]-float(llr[0][1]))/2.0]
		print("create basmap object.")
		catmap=Basemap(llcrnrlon=llr[0][1], llcrnrlat=llr[0][0], urcrnrlon=llr[1][1], urcrnrlat=llr[1][0], resolution =self.mapres, projection='tmerc', lon_0=cntr[1], lat_0=cntr[0])
		print("bm object created...")
		canvas=FigureCanvas(f0)
		catmap.ax=f0.add_axes([0,0,1,1])
		#f0.set_figsize_inches((8/catmap.aspect,8.))
		
		#f0.set_figsize_inches((10/catmap.aspect,10.))
		#f0.set_size_inches((10/catmap.aspect,10.))
		f0.set_size_inches((10.,15.))
		#
		print("draw stuff on map...")
		catmap.drawcoastlines(color='gray')
		catmap.drawcountries(color='gray')
		catmap.fillcontinents(color='beige')
		#catmap.drawrivers(color='b')
		catmap.drawstates()
		catmap.drawmeridians(list(range(int(llr[0][1]-2.0), int(llr[1][1]+2.0))), color='k', labels=[1,1,1,1])
		catmap.drawparallels(list(range(int(llr[0][0]-2.0), int(llr[1][0]+2.0))), color='k', labels=[1, 1, 1, 1])
		#
		'''
		catmap.llcrnrlon=llr[0][1]+2.0
		catmap.llcrnrlat=llr[0][0]+2.0
		catmap.urcrnrlon=llr[1][1]-2.0
		catmap.urcrnrlat=llr[1][0]-2.0
		'''
		print("plot catalogs...")
		icat=0
		for ct in catalogs:
			xfull, yfull=catmap(list(map(operator.itemgetter(2), ct)), list(map(operator.itemgetter(1), ct)))
			catmap.plot(xfull, yfull, '.', label='%s' % catnames[icat], ms=2)
			icat+=1
		
		# now, plot all events m>m0 from the full catalog:
		bigmag=5.0
		for rw in catalog:
			if rw[3]<bigmag: continue
			thisx, thisy=catmap(rw[2], rw[1])
			catmap.plot(thisx, thisy, '*', label='%s, %s\n (%s, %s)' % (str(rw[3]), str(rw[0]), str(rw[2]), str(rw[1])), ms=15)
			
		epx, epy=catmap(epicenter[0], epicenter[1])
		catmap.plot(epx, epy, 'ro', label='epicenter')
		
		# this is how to draw an ellipse... obviously, this does not really belong in this part of the script;
		#  it was part of the learning process...
		#canvas.print_figure(saveName)
		from matplotlib.patches import Ellipse
		#f=plt.figure(0)
		#ax1=f0.gca()
		el = Ellipse([-120.5, 35.9], .8, .3, -40, facecolor='b', alpha=0.4)
		Xel, Yel = catmap(el.get_verts()[:,0],el.get_verts()[:,1])
		catmap.plot(Xel, Yel, '-r', lw=2)
		catmap.ax.fill(Xel, Yel, ec='r', fc='r', alpha=.4)
		###
		
		#ax1.add_artist(el)
		#catmap.ax.add_artist(el)
		#
		#ax=plt.gca()
		#el = Ellipse((self.tLon, self.tLat), 2.0*self.tA, 2.0*self.tB, -self.tTheta, facecolor='b', alpha=0.4)
		#catmap.ax.add_artist(el)
		#ax.add_artist(el)
		#
		#plt.plot(map(operator.itemgetter(2), self.fullCat), map(operator.itemgetter(1), self.fullCat), '+')
		#plt.plot(map(operator.itemgetter(2), self.shockCat), map(operator.itemgetter(1), self.shockCat), '.')
		#plt.plot(map(operator.itemgetter(2), fcat), map(operator.itemgetter(1), fcat), '+', label='Full Catalog')
		#plt.plot(map(operator.itemgetter(2), scat), map(operator.itemgetter(1), scat), '.', label='Aftershock zone')
		#plt.plot([epicenter[0]], [epicenter[1]], 'ro', label='epicenter')
		plt.legend(loc=legendLoc, numpoints=1)
		if doSave: plt.savefig('pltsave-%s' % saveName)
		
		canvas.print_figure(saveName)
		
		if doShow: plt.show()
		
		return None
	
	def setSpecialCatSQL(self, catname='parkfield'):
		#reload(yp)
		if catname in ['parkfield', 'pf', 'PF', 'park']:
			#theta=40.0, clat=35.9, clon=-120.5, ra=.4, rb=.15
			#self.setCatFromSQL(dtm.datetime(1969,1,1), dtm.datetime.now(), [34.9, 36.9], [-121.5, -119.5], 1.5, "Earthquakes", 523, 'asc')
			self.setCatFromSQL(dtm.datetime(1972,1,1), dtm.datetime.now(), [34.4, 37.4], [-121.11, -119.4], 1.5, "Earthquakes", 523, 'asc')
			self.addEllipCat('PFshock (.8 x .15)', self.cat, 40.0, 35.9, -120.5, 0.8, 0.15)
			self.addEllipCat('PFshock (.4 x .15)', self.cat, 40.0, 35.9, -120.5, 0.4, 0.15)
		if catname == 'PF5yr':
			#theta=40.0, clat=35.9, clon=-120.5, ra=.4, rb=.15
			#self.setCatFromSQL(dtm.datetime(1969,1,1), dtm.datetime.now(), [34.9, 36.9], [-121.5, -119.5], 1.5, "Earthquakes", 523, 'asc')
			self.setCatFromSQL(dtm.datetime(1999, 9, 28), dtm.datetime(2009,9,29), [34.4, 37.4], [-121.11, -119.4], 1.5, "Earthquakes", 523, 'asc')
			self.addEllipCat('PFshock (.8 x .15)', self.cat, 40.0, 35.9, -120.5, 0.8, 0.15)
			self.addEllipCat('PFshock (.4 x .15)', self.cat, 40.0, 35.9, -120.5, 0.4, 0.15)
		if catname in ['taiwan']:
			self.setCatFromSQL(dtm.datetime(1980,1,1), dtm.datetime(2010,6,1), [-90, 90], [-180, 180], 2.0, 'Earthquakes', 21)
			
	def setCatFromSQL(self, startDate=dtm.datetime(1999,9,28, 17,15,24), endDate=dtm.datetime(2009,9,28, 17,15,24), lats=[32.0, 37.0], lons=[-125.0, -115.0], minmag=3.0, catalogName='Earthquakes', catalogID=523, ordering='asc'):
		self.cat=self.getCatFromSQL(startDate, endDate, lats, lons, minmag, catalogName, catalogID, ordering)
		return None
	
	def getCatFromSQL(self, startDate=dtm.datetime(1999,9,28, 17,15,24), endDate=dtm.datetime(2009,9,28, 17,15,24), lats=[32.0, 37.0], lons=[-125.0, -115.0], minmag=2.0, catalogName='Earthquakes', catalogID=523, ordering='asc'):
		# return a catalog:
		if lats[0]>lats[1]: lats.reverse()
		if lons[0]>lons[1]: lons.reverse()
		#if yp.datetimeToFloat(startDate)>yp.datetimeToFloat(endDate):
		if startDate>endDate:
			middledate=startDate
			startDate=endDate
			endDate=middledate
			middledate=None
		if ordering not in ['asc', 'desc']: ordering='desc'
		
		import _mysql
		import MySQLdb
		#
		#sqlHost = 'localhost'
		sqlHost = self.sqlhost
		sqlUser = 'myoder'
		sqlPassword = 'yoda'
		sqlPort = self.sqlport
		sqlDB = 'QuakeData'
		con=MySQLdb.connect(host=sqlHost, user=sqlUser, passwd=sqlPassword, port=sqlPort, db=sqlDB)
		c1=con.cursor()
		sqlstr='select eventDateTime, lat, lon, mag from %s where catalogID=%d and lat between %f and %f and lon between %f and %f and mag>=%f and eventDateTime between \'%s\' and \'%s\' order by eventDateTime %s' % (catalogName, catalogID, lats[0], lats[1], lons[0], lons[1], minmag, str(startDate), str(endDate), ordering)
		catList=[]
		#print sqlstr
		#
		c1.execute(sqlstr)
		rw=c1.fetchone()
		while rw!=None:
		#	# spin through the cursor; write a catalog. note formatting choices...
			catList+=[[rw[0], float(rw[1]), float(rw[2]), float(rw[3])]]
			rw=c1.fetchone()
		#catList=self.fetchall()
		c1.close()
		con.close()
		# now we have a catalog of the parkfield area (note, it is partially defined by our "parkfieldquakes" MySQL view.
		#
		#makeShockCat(incat, outcat)
		#makeShockCat(fullcatout, shockcatout)
		return catList
		
	def plotGRdist(self, mags=None, doShow=True, fname='GRdist.png', plotTitle="Magnitude Distribution", fignum=0):
		# mags: a 1D array of magnitudes
		if mags==None: mags=list(map(operator.itemgetter(3), self.cat))
		# if mags rows are not scalar, assume a full standard type catalog has been passed.
		try:
			if len(mags[0])>=3: mags=list(map(operator.itemgetter(3), mags))
		except TypeError:
			# a list of scalars will throw a "can't get len." error. we should be able to skip without doing anything at all.
			# maybe a better approach is to test the type of mags[0] for list or tuple...
			dummyvar=None	# place-holder
		#
		mags.sort()
		# get rid of biggest event (probably a large off-GR earthquake):
		#mags.pop()
		#mags.reverse()
		#print mags
		#print len(mags)
		
		if doShow==True or fname!=None:
			# make a plot and show and/or save
			#Y=range(1, len(mags)+1)
			Y=frange(1, len(mags), -1)
			#print Y
			#print len(Y)
			plt.figure(fignum)
			plt.clf()
			plt.semilogy(mags, Y, '.-')
			plt.xlabel("Magnitude, m")
			plt.ylabel("Number of Events, n")
			plt.title(plotTitle)
			if fname!=None: plt.savefig(fname)
			if doShow: plt.show()
		
		return mags	

	def getIntervals(self, catList, winLen):
		catLen=len(catList)
		i=(catLen-1-winLen)	# start winLen positions from the end.
		thisInterval=0
		#N=1
		intervals=[]	# [[eventDateTime, totalInterval]]
		while i>=0:
			#
			thisInterval=datetimeToFloat(catList[i+winLen][0])-datetimeToFloat(catList[i][0])
			intervals+=[[catList[i+winLen][0], thisInterval]]
			i-=1
		
		#
		#return [intervals, catList]
		return intervals
	#
	def plotIntervals(self, intervals=[10, 100, 1000], minmag=2.0, catalog=None, fignum=0, dtmlatlonmagCols=[0,1,2,3], plotDates=[None, None], thisAxes=None):
		if type(plotDates).__name__!='list': plotDates=[None, None]
		while len(plotDates)<2: plotDates+=[None]
		#
		if catalog==None: catalog=self.cat
		#X = plotIntervals(intervals, minmag, catalog, fignum, dtmlatlonmagCols)
		#return X
		#zonedat=[35.9, -120.5, .4, .15, 40.0]
		cols=dtmlatlonmagCols	# for efficient notation
		#zonedat=[35.9, -120.5, .4, .05, 40.0]	# this will be done in advance of this function call, when the catalog is made.
		#minmag=2.0
		#dts=['1950-01-01', str(dtm.datetime.now())]
		#sqlcat="Earthquakes"
		#catid=523
	
		#
		plt.figure(fignum)
		if thisAxes==None:
			#plt.figure(fignum)
			plt.clf()
			ax0=plt.axes([.1,.1,.85, .35])
			plt.xlabel("time")
			plt.ylabel("mags")
			ax1=plt.axes([.1, .55, .85, .35], sharex=ax0)
			plt.ylabel("mean interval")
			plt.xlabel("")
			plt.title("Mean intervals, $m_c=%s$" % str(minmag))
		else:
			ax0=thisAxes[0]
			ax1=thisAxes[1]
	
		#dtms=map(operator.itemgetter(cols[0]), catalog)
		#lats=map(operator.itemgetter(cols[1]), catalog)
		#lons=map(operator.itemgetter(cols[2]), catalog)
		#mags=map(operator.itemgetter(cols[3]), catalog)
		mags=[]
		activecat=[]
		for rw in catalog:
			if rw[cols[3]]<minmag: continue
			mags+=[[rw[cols[0]], rw[cols[3]]]]
			activecat+=[rw]
		mags=vlinePadList(mags, minmag-abs(minmag)*.1)	# return the mags data padded for vertical line style plotting. this is just a trick to get width=1 histograms.
		#
		ax0.plot_date(list(map(operator.itemgetter(0), mags)), list(map(operator.itemgetter(1), mags)), '-')
		shockints=[]
		
		#print "plotdates: %s" % str(plotDates)
		for wlen in intervals:
			#print "plotting for wlen: %d" % wlen
			##
			#shockints+=[getIntervals(catalog, wlen)]
			shockints+=[self.getIntervals(activecat, wlen)]
			#
			# trim off max/min date ends for prettier plots:
			#print "mindt: %s" % str(shockints[-1][0])
			while (plotDates[1]!=None and plotDates[1]<shockints[-1][0][0]): a=shockints[-1].pop(0)
			while plotDates[0]!=None and plotDates[0]>shockints[-1][-1][0]: a=shockints[-1].pop()
			#
			#plt.plot(map(operator.itemgetter(0), shockints[-1]), scipy.array(map(operator.itemgetter(1), shockints[-1]))/float(wlen), '-', label='winLen=%d' % wlen)
			#
			X=list(map(operator.itemgetter(0), shockints[-1]))
			# pylab.date2num(dtm)
			#XX=date2num(X)
			ax1.plot(X, scipy.array(list(map(operator.itemgetter(1), shockints[-1])))/float(wlen), '-', label='$N=%d$' % wlen, lw=1.0)
			#ax1.semilogy(map(operator.itemgetter(0), shockints[-1]), scipy.array(map(operator.itemgetter(1), shockints[-1]))/float(wlen), '-', label='winLen=%d' % wlen)
			# fg.autofmt_xdate()
			
		
			#plt.plot(map(operator.itemgetter(0), shockints[-1]), scipy.array(map(operator.itemgetter(1), shockints[-1])), '-', label='winLen=%d' % wlen)
		#
		plt.legend(loc='upper left')
			
		#plt.legend(loc='lower left')
	
	
		plt.show()
	
		return shockints
		
	def plotInts(self, intervals=[10, 100, 1000], catalog=None, minmag=2.0, ax=None, dtmlatlonmagCols=[0,1,2,3], plotDates=[None, None]):
		# plot mean intervals only. having figured out how to put a bunch of independently generated plots onto a single canvas, we
		# split up some of these plots...
		#
		if type(plotDates).__name__!='list': plotDates=[None, None]
		while len(plotDates)<2: plotDates+=[None]
		#
		if catalog==None: catalog=self.cat
		cols=dtmlatlonmagCols	# for efficient notation
		activecat=[]
		for rw in catalog:
			if rw[cols[3]]>=minmag: activecat+=[rw]	# build active catalog of events m>mc
		#
		shockints=[]
		for wlen in intervals:
			shockints+=[self.getIntervals(activecat, wlen)]
			# trim off catalog elements outside min/max date range:
			while (plotDates[1]!=None and plotDates[1]<shockints[-1][0][0]): a=shockints[-1].pop(0)
			while plotDates[0]!=None and plotDates[0]>shockints[-1][-1][0]: a=shockints[-1].pop()
			#
			ax.plot(list(map(operator.itemgetter(0), shockints[-1])), scipy.array(list(map(operator.itemgetter(1), shockints[-1])))/float(wlen), '-', label='$N=%d$' % wlen, lw=1.0)
			#ax1.semilogy(map(operator.itemgetter(0), shockints[-1]), scipy.array(map(operator.itemgetter(1), shockints[-1]))/float(wlen), '-', label='winLen=%d' % wlen)
			
		
			#plt.plot(map(operator.itemgetter(0), shockints[-1]), scipy.array(map(operator.itemgetter(1), shockints[-1])), '-', label='winLen=%d' % wlen)
		#
		ax.legend(loc='best')
			
		return shockints
		
	def plotMags(self, catalog=None, minmag=2.0, ax=None, dtmlatlonmagCols=[0,1,2,3], plotDates=[None, None]):
		if type(plotDates).__name__!='list': plotDates=[None, None]
		while len(plotDates)<2: plotDates+=[None]
		#
		if catalog==None: catalog=self.cat
		cols=dtmlatlonmagCols	# for efficient notation
		#
		mags=[]
		activecat=[]
		for rw in catalog:
			if rw[cols[3]]>=minmag: mags+=[[rw[cols[0]], rw[cols[3]]]]
		mags=vlinePadList(mags, minmag-abs(minmag)*.1)	# return the mags data padded for vertical line style plotting. this is just a trick to get width=1 histograms.
		#
		ax.plot(list(map(operator.itemgetter(0), mags)), list(map(operator.itemgetter(1), mags)), '-')
		ax.legend(loc='best')
		return mags

