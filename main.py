import re
import sys
import time

from PIL import Image
from io import BytesIO
from solver import try_to_solve_captcha

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException


class PregradoException(Exception):
	description = ("Something wrong has occured.")


class WrongFrameException(Exception):
	description = ("You are in the wrong frame")


class ControlEstudios():
	def __init__(self):
		options = Options()
		options.headless = False

		self.driver = webdriver.Firefox(options=options)
		self.notas = []
		self.route = self.get_current_route()
		self.depth = 0

	def solve_captcha(self, solve):
		captcha   = ''
		tries     = 0

		while len(captcha) != 2:
			self.driver.get("https://control.unet.edu.ve/sec/inicioNuevo.php")

			container = self.driver.find_element_by_id("iseg")
			# image_src = container.find_element_by_tag_name("img").get_attribute('src')
			image_tes = container.find_element_by_tag_name("img")
			self.driver.execute_script("arguments[0].width = '50';", image_tes)
			self.driver.execute_script("arguments[0].height = '24';", image_tes)

			user   = self.driver.find_element_by_id("usuario")
			passwd = self.driver.find_element_by_id("clave")
			captch = self.driver.find_element_by_id("imagen")
			submit = self.driver.find_element_by_id("Submit")

			user.clear()
			passwd.clear()
			captch.clear()

			self.driver.execute_script("arguments[0].type = 'hidden';", captch)

			image_loc = container.location
			image_siz = container.size

			png    = self.driver.get_screenshot_as_png()
			image  = Image.open(BytesIO(png))
			left   = image_loc['x']
			top    = image_loc['y']
			right  = image_loc['x'] + 50
			bottom = image_loc['y'] + 24

			image = image.crop((left, top, right, bottom))

			tries   = tries + 1
			if not solve:
				image.show()
				captcha = input('Captcha: ')
			else:
				captcha = try_to_solve_captcha(image)
			captcha = re.sub('[^A-Z]+', '', captcha)

		print("Tries: {} Captcha solved: {}".format(tries, captcha))

		user.send_keys("FILL")
		passwd.send_keys("FILL")
		self.driver.execute_script("arguments[0].value = '{}';".format(captcha), captch)
		submit.click()
		try:
			self.route = self.get_current_route()
		except UnexpectedAlertPresentException:
			print("Retrying")
			self.solve_captcha(solve)
		except Exception as e:
			raise e
		
	def get_current_route(self, url=''):
		current_url = url if url != '' else self.driver.current_url
		return "/".join(current_url.split('/')[-2:]).lower()
	
	def select_menu(self, text_menu, find_type, option, child=None):
		if find_type == 'class':
			options = self.driver.find_elements_by_class_name(option)
		elif find_type == 'tag':
			options = self.driver.find_elements_by_tag_name(option)
		else: 
			raise PregradoException("Type not specified")

		for option in options:
			if child:
				option = option.find_element_by_tag_name(child)
			if text_menu in option.text.lower():
				option.click()

		self.route = self.get_current_route()

	def switch_to_iframe(self, iframe_name, find_type):
		self.driver.switch_to.default_content()

		if find_type == 'id':
			frame = self.driver.find_element_by_id('cargar')
		else:
			raise PregradoException("Type not specified")
		
		self.route = self.get_current_route(frame.get_attribute('src'))
		self.driver.switch_to.frame(frame)

	def save_notas(self):
		if self.route == 'alumnos/alum_notice.php':
			self.notas = [
				[td.text for td in tr.find_elements_by_tag_name('td')] 
				for tr in self.driver.find_elements_by_class_name('textos')
			][4:]
		else:
			raise WrongFrameException

	def get_notas(self):
		self.select_menu('notas', 'tag', 'li')
		self.switch_to_iframe('cargar', 'id')

		try:
			WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'textos')))
			self.save_notas()
		except TimeoutException:
			print("Timeout Exception")
			time.sleep(1)
			self.depth = self.depth + 1
			if self.depth < 5:
				self.get_notas()
		except Exception:
			print("General exception > get_notas")
				
		if (len("".join("".join(nota) for nota in self.notas)) == 0) and self.depth < 5:
			time.sleep(1)
			self.depth = self.depth + 1
			self.get_notas()
		
		self.depth = 0
		return self.notas

	def open_informacion_academica(self):
		try:
			WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'menu1')))
			if self.route == 'alumnos/menualum.php':
				self.select_menu('academica', 'class', 'subOpcion', 'span')
			else:
				raise WrongFrameException
		except TimeoutException:
			print("Timeout Exception > open_informacion_academica")
			time.sleep(1)
			self.depth = self.depth + 1
			if self.depth < 5:
				self.open_informacion_academica()
		except Exception as e:
			print("General Exception > open_informacion_academica", e)

		self.depth = 0

	def open(self, solve=True):
		self.solve_captcha(solve)

		if self.route == 'adm_usuarios/menuppal.php':
			self.select_menu('pregrado', 'class', 'subOpcion')
			
		self.open_informacion_academica()
		
		self.get_notas()

	def close(self):
		self.driver.close()


control = ControlEstudios()
control.open(solve=False)
from pprint import pprint
pprint(control.get_notas())
control.close()
