#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inkex
import simplestyle, math

# Function for calculating a point from the origin when you know the distance 
# and the angle
def calculatePoint(angle, distance):
	if angle < 0 or angle > 360:
		return None
	else:
		return [distance*math.cos(math.radians(angle)),
				distance*math.sin(math.radians(angle))]

class EncoderDiskGenerator(inkex.Effect):
		
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("--diameter",
				        action="store", type="float",
						dest="diameter", default=0.0,
				        help="Diameter of the encoder disk")
		self.OptionParser.add_option("--hole_diameter",
				        action="store", type="float", 
				        dest="hole_diameter", default=0.0,
				        help="Diameter of the center hole")
		self.OptionParser.add_option("--segments",
				        action="store", type="int", 
				        dest="segments", default=0,
				        help="Number of segments")
		self.OptionParser.add_option("--outer_encoder_diameter",
				        action="store", type="float", 
				        dest="outer_encoder_diameter", default=0.0,
				        help="Diameter of the outer encoder disk")
		self.OptionParser.add_option("--outer_encoder_width",
				        action="store", type="float", 
				        dest="outer_encoder_width", default=0.0,
				        help="Width of the outer encoder disk")
		self.OptionParser.add_option("--inner_encoder_diameter",
				        action="store", type="float", 
				        dest="inner_encoder_diameter", default=0.0,
				        help="Diameter of the inner encoder disk")
		self.OptionParser.add_option("--inner_encoder_width",
				        action="store", type="float", 
				        dest="inner_encoder_width", default=0.0,
				        help="Width of the inner encoder disk")
		self.OptionParser.add_option("--bits",
				        action="store", type="int", 
				        dest="bits", default=1,
				        help="Number of bits/tracks")
		self.OptionParser.add_option("--encoder_diameter",
				        action="store", type="float", 
				        dest="encoder_diameter", default=0.0,
				        help="Outer diameter of the last track")
		self.OptionParser.add_option("--track_width",
				        action="store", type="float", 
				        dest="track_width", default=0.0,
				        help="Width of one track")
		self.OptionParser.add_option("--track_distance",
				        action="store", type="float", 
				        dest="track_distance", default=0.0,
				        help="Distance between tracks")

	# This function just concatenates the point and the command and returns
	# the data string
	def parsePathData(self, command, point):
		path_data = command + ' %f ' %point[0] + ' %f ' %point[1] 
		return path_data
	
	# This function creates a gray code of size bits (n >= 1) in the format of a list
	def createGrayCode(self, bits):

		gray_code = [[False], [True]]

		if bits == 1:
			return gray_code

		for i in range(bits-1):
			temp = []
			# Reflect values
			for j in range(len(gray_code[0]), 0, -1):
				for k in range(0, len(gray_code)):
					if j == len(gray_code[0]):
						temp.append([gray_code[k][-j]])
					else:
						temp[k].append(gray_code[k][-j])
			while temp:
				gray_code.append(temp.pop())
			# Add False to the "old" values and true to the new ones
			for j in range(0, len(gray_code)):
				if j < len(gray_code)/2:
					gray_code[j].insert(0, False)
				else:
					gray_code[j].insert(0, True)
			temp = []

		return gray_code

	def drawGrayEncoder(self, bits, encoder_diameter, track_width, track_distance):
		gray_code = self.createGrayCode(bits)

		segments = []
		segment_size = 0
		start_angle_position = 0
		index = 0
		current_encoder_diameter = encoder_diameter
		previous_item = False
		position_size = 360.0/(2**bits)

		for i in range(len(gray_code[0])-1, 0, -1):
			for j in gray_code:
				if j[i] == True:
					segment_size += 1
					if segment_size == 1:
						start_angle_position = index
					previous_item = True
				elif j[i] == False and previous_item == True:
					segments.append(self.drawSegment(line_style, start_angle_position*position_size, segment_size*position_size, current_encoder_diameter, track_width))
					segment_size = 0
					previous_item = False
					start_angle_position = 0
				index += 1

			if previous_item == True:
				segments.append(self.drawSegment(line_style, start_angle_position*position_size, segment_size*position_size, current_encoder_diameter, track_width))
				segment_size = 0
				previous_item = False
				start_angle_position = 0
			current_encoder_diameter -= 2*track_distance
			index = 0

	# This function creates the path for one single segment
	def drawSegment(self, line_style, angle, segment_angle, outer_diameter, width):

		path = {'style' : simplestyle.formatStyle(line_style)}
		path['d'] = ''
		outer_radius = outer_diameter/2

		# Go to the first point in the segment
		path['d'] += self.parsePathData('M', calculatePoint(angle, outer_radius-width))

		# Go to the second point in the segment
		path['d'] += self.parsePathData('L', calculatePoint(angle, outer_radius))

		# Go to the third point in the segment, draw an arc
		point = calculatePoint(angle+segment_angle, outer_radius)
		path['d'] += self.parsePathData('A', [outer_radius, outer_radius]) + \
					'0 0 1' + self.parsePathData(' ', point)

		# Go to the fourth point in the segment
		point = calculatePoint(angle+segment_angle, outer_radius-width)
		path['d'] += self.parsePathData('L', point)

		# Go to the beginning in the segment, draw an arc
		point = calculatePoint(angle, outer_radius-width)
		# 'Z' closes the path
		path['d'] += self.parsePathData('A', [outer_radius-width, outer_radius-width])\
					 + '0 0 0' + self.parsePathData(' ', point) + ' Z'

		# Return the path
		return path

	# This function adds an element to the document
	def addElement(self, element_type, group, element_attributes):
		self.current_layer.append(inkex.etree.SubElement(group, 
		inkex.addNS(element_type,'svg'), element_attributes))

	def effect(self):

		# Group to put all the elements in, center set in the middle of the view
		group = inkex.etree.SubElement(self.current_layer, 'g', {
			inkex.addNS('label', 'inkscape'):'Encoder disk', 
			'transform':'translate' + str(self.view_center)
		})

		# Attributes for the center hole, then create it, if diameter is 0, dont
		# create it
		attributes = {
			'style'     : simplestyle.formatStyle({'stroke':'none', 'fill':'black'}),
			'r'         : str(self.options.hole_diameter/2)
		}
		if self.options.hole_diameter > 0:
			self.addElement('circle', group, attributes)

		# Attributes for the guide hole in the center hole, then create it
		attributes = {
			'style'     : simplestyle.formatStyle({'stroke':'white','fill':'white'}),
			'r'         : '1'
		}
		self.addElement('circle', group, attributes)

		# Attributes for the outer rim, then create it
		attributes = {
			'style'     : simplestyle.formatStyle({'stroke':'black', 'stroke-width':'1', 'fill':'none'}),
			'r'         : str(self.options.diameter/2)
		}
		if self.options.diameter > 0:
			self.addElement('circle', group, attributes)

		# Line style for the encoder segments
		line_style   = { 
			'stroke'		: 	'black',
			'stroke-width'	:	'1',
			'fill'			:	'black'
		}

		# Angle of one single segment
		segment_angle = 360.0/(self.options.segments*2)

"""
		gray_code_bits = 5
		gray_code = self.createGrayCode(gray_code_bits)
		inkex.errormsg(gray_code)

		segment_size = 0
		start_angle_position = 0
		index = 0
		previous_item = False
		encoder_diameter = 100.0
		for i in range(len(gray_code[0])):
			inkex.errormsg("Bit: " + str(i))
			for j in gray_code:
				if j[i] == True:
					segment_size += 1
					if segment_size == 1:
						start_angle_position = index
					previous_item = True
				elif j[i] == False and previous_item == True:
					segment = self.drawSegment(line_style, start_angle_position*(360.0/(2**gray_code_bits)), segment_size*(360.0/(2**gray_code_bits)), encoder_diameter, self.options.outer_encoder_width)
					self.addElement('path', group, segment)
					inkex.errormsg("Segment size: " +str(segment_size) + " start angle position: " + str(start_angle_position))
					segment_size = 0
					previous_item = False
					start_angle_position = 0
				index += 1

			if previous_item == True:
				segment = self.drawSegment(line_style, start_angle_position*(360.0/(2**gray_code_bits)), segment_size*(360.0/(2**gray_code_bits)), self.options.outer_encoder_diameter, self.options.outer_encoder_width)
				self.addElement('path', group, segment)
				inkex.errormsg("Segment size: " +str(segment_size) + " start angle position: " + str(start_angle_position))
				segment_size = 0
				previous_item = False
				start_angle_position = 0
			encoder_diameter += 40
			index = 0
"""
		segments = drawGrayEncoder(self.options.bits, self.options.encoder_diameter, self.options.track_width, self.options.track_distance)
		for item in segments:
			self.addElement('path', group, item)

		#inkex.errormsg("Gray code: " +str(self.createGrayCode(4)))
"""
		for segment_number in range(0, self.options.segments):

			angle = segment_number*(segment_angle*2)

			if 	self.options.outer_encoder_width > 0 and \
				self.options.outer_encoder_diameter > 0 and \
				self.options.outer_encoder_diameter/2 > self.options.outer_encoder_width:

				segment = self.drawSegment(line_style, angle, segment_angle,
					self.options.outer_encoder_diameter, self.options.outer_encoder_width)
				self.addElement('path', group, segment)

			# If the inner encoder diameter is something else than 0; create it
			if 	self.options.outer_encoder_width > 0 and \
				self.options.inner_encoder_diameter > 0 and \
				self.options.inner_encoder_diameter/2 > self.options.inner_encoder_width:

				# The inner encoder must be half an encoder segment ahead of the outer one
				segment = self.drawSegment(line_style, angle+(segment_angle/2), segment_angle,
					self.options.inner_encoder_diameter, self.options.inner_encoder_width)
				self.addElement('path', group, segment)
"""
if __name__ == '__main__':
	# Run the effect
	effect = EncoderDiskGenerator()
	effect.affect()
