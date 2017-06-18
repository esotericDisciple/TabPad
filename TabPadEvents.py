#!/usr/bin/python3

import subprocess
import time
import evdev
import threading
from evdev import ecodes
from decimal import Decimal
from TabPadConfig import *

class newThread (threading.Thread):
	def __init__(self, threadID, name, touch_panel, screen_width, screen_height):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.daemon = True
		self.touch_panel = touch_panel
		self.no_device_found = True
		self.screen_width = screen_width
		self.screen_height= screen_height
		self.min_x, self.max_x = None, None
		self.min_y, self.max_y = None, None
		self.res_x, self.res_y = None, None
		self.devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
		# print (self.devices)
		self.inputsetup()

	def run(self):
		print ("Starting " + self.name)
		self.eventloop()

	def inputsetup(self):
		for d in self.devices:
			# print(d.fn, d.name, device.phys)
			# print (d.name)
			if (d.name == self.touch_panel):
				input_node = d.fn
				self.no_device_found = False
				self.min_x, self.max_x = d.capabilities()[3][0][1][1], d.capabilities()[3][0][1][2]
				self.min_y, self.max_y = d.capabilities()[3][1][1][1], d.capabilities()[3][1][1][2]
				self.res_x, self.res_y = d.capabilities()[3][0][1][-1], d.capabilities()[3][1][1][-1]

		if self.no_device_found == True:
			print ("No touch input detected.")
			print ("Please make sure you have entered correct touch panel name in user settings.")
			print ("And that you are running the app with root access.")
			print ("Quitting in 10 seconds.")
			time.sleep(10)
			quit()
			sys.exit(1)

		self.device = evdev.InputDevice(input_node)

	def eventloop(self):
		touch_time = None
		lift_time = None
		x_abs_val = None
		y_abs_val = None
		finger0_coords = None
		finger1_coords = None
		for ev in self.device.read_loop():
			# print (evdev.util.categorize(ev))
			if ev.code == 330 and ev.value == 1:
				touch_time = Decimal(str(ev.sec) + "." + str(ev.usec))
				# print touch_time

			if ev.code == 330 and ev.value == 0:
				lift_time = Decimal(str(ev.sec) + "." + str(ev.usec))
				# print lift_time
			else:
				lift_time = None

			if ev.code == 53:
				if ev.value > 0:
					x_abs_val = ev.value
			if ev.code == 54:
				if ev.value > 0:
					y_abs_val = ev.value

			# if x_abs_val != None and y_abs_val != None and ev.code == 47:
			# 	if ev.value == 0:
			# 		finger0_coords = (x_abs_val, y_abs_val)
			# 	if ev.value == 1:
			# 		finger1_coords = (x_abs_val, y_abs_val)
			# if (finger0_coords and finger1_coords) != None:
			# 	if finger0_coords != finger1_coords:
			# 		print ("finger0: ", finger0_coords)
			# 		print ("finger1: ", finger1_coords)

			if lift_time != None and x_abs_val != None and y_abs_val != None:
				self.compare_coords(*(self.convert_absolute_values((x_abs_val, y_abs_val))))

	def percentconvertor(self, val, dimension):
		val = int(round((dimension * val)/100))
		return val

	def compare_coords(self, actual_x, actual_y):
		l = []
		button_area = self.circle_points(actual_x, actual_y, 10)
		for k, v in button_layout.items():
			self.x_start_pos = self.percentconvertor(v[0], overlay_width)
			self.x_end_pos = self.x_start_pos + v[4][0]
			self.y_start_pos = self.percentconvertor(v[1], overlay_height)
			self.y_end_pos = self.y_start_pos + v[4][1] 
			for c in button_area:
				if c[0] >= self.x_start_pos and c[0] <= self.x_end_pos:
					if c[1] >= self.y_start_pos and c[1] <= self.y_end_pos:
						l.append(v[2])
		l = self.remove_duplicates_in_array(l)
		self.command_executor(l)

	def command_executor(self, command_array):
		if command_array:
			for c in command_array:
				if c:
					subprocess.Popen(c, stdout=subprocess.PIPE)

	def circle_points(self, xcenter, ycenter, radius):
		r = radius
		xc = xcenter
		yc = ycenter
		points_array = []
		for x in range(xc-r, xc+1):
			for y in range(yc-r, yc+1):
				if ((x - xc)*(x - xc) + (y - yc)*(y - yc)) <= r*r:
					xcord = xc - (x - xc)
					ycord = yc - (y - yc)
					points_array.append((xcord, ycord))
		return points_array

	def remove_duplicates_in_array(self, array):
		array = sorted(array)
		a = [array[i] for i in range(len(array)) if i == 0 or array[i] != array[i-1]]
		return a

	def convert_absolute_values(self, value):
		cmnd = "xrandr -q|grep -v dis|grep con|awk '{print $5}'"
		output = self.get_bash_output(cmnd)

		if coord_hack:
			if self.current_ctm() == [1, 0, 0, 0, 1, 0, 0, 0, 1] or output == "normal":
				xc = value[0]
				yc = value[1]
			elif self.current_ctm() == [-1, 0, 1, 0, -1, 1, 0, 0, 1] or output == "inverted":
				xc = abs(self.max_x - value[0])
				yc = abs(self.max_y - value[1])
			elif self.current_ctm() == [0, -1, 1, 1, 0, 0, 0, 0, 1] or output == "left":
				xc = abs(self.max_x - value[1])
				yc = value[0]
			elif self.current_ctm() == [0, 1, 0, -1, 0, 1, 0, 0, 1] or output == "right":
				xc = value[1]
				yc = abs(self.max_y - value[0])
			else:
				xc = value[0]
				yc = value[1]
		else:
			xc = value[0]
			yc = value[1]

		xc = (xc - self.min_x) * self.screen_width / (self.max_x - self.min_x + 1)
		yc = (yc - self.min_y) * self.screen_height / (self.max_y - self.min_y + 1)
		xc = int(round(xc))
		yc = int(round(yc))

		if overlay_x_position < self.screen_width:
			xc = xc - overlay_x_position
			if xc < 0:
				xc = 0
		if overlay_y_position < self.screen_height:
			yc = yc - overlay_y_position
			if yc < 0:
				yc = 0
		# print (xc, yc)
		return (xc, yc)

	def current_ctm(self):
		c = "echo $(xinput list-props '" + self.touch_panel \
		+ "'| grep 'Coordinate Transformation Matrix' | sed 's/.*://')"
		output = self.get_bash_output(c)
		output = output.split(", ")
		output = [int(float(i)) for i in output]
		return output

	def convert_coords_asper_ctm(self, coords, matrix):
		x = coords[0]
		y = coords[1]
		a, b, c, d, e, f, g, h, i = matrix
		w = (g*x + h*y + i)
		x = (a*x + b*y + c) / w
		y = (d*x + e*y + f) / w
		x = int(round(x))
		y = int(round(y))
		return x, y	  

	def get_bash_output(self, cmnd):
		output = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell = True ).communicate()
		output = str(output[0]).strip("\\n'")
		output = output.strip("'b")
		return output