import re
import sys
import time

from PIL import Image
from io import BytesIO
from getpass import getpass

from selenium.webdriver.firefox.options import Options
from seleniumrequests import Firefox


class ControlEstudios():
	def __init__(self):
		options = Options()
		options.headless = False

		self.driver = Firefox(options=options)
		self.control_alumnos_url = "https://control.unet.edu.ve/control/alumnos"
		self.oper_funciones_url = self.control_alumnos_url + "/oper_funciones.php"

	def solve_captcha(self):
		captcha   = ''
		tries     = 1

		container = self.driver.find_element_by_id("iseg")
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
		image.show()

		user.send_keys(input('Username: '))
		passwd.send_keys(getpass('Password: '))
		captcha = input('Captcha: ')
		captcha = re.sub('[^A-Z]+', '', captcha)

		print("Tries: {} Captcha solved: {}".format(tries, captcha))

		self.driver.execute_script("arguments[0].value = '{}';".format(captcha), captch)
		submit.click()

	def open(self):
		self.driver.get("https://control.unet.edu.ve/sec/inicioNuevo.php")
		self.solve_captcha()

	def close(self):
		self.driver.close()

	def get_page(self, page, code):
		data = {'xajax': 'enviar', 'xajaxr': int(time.time()), 'xajaxargs[]': [page, code]}
		response = self.driver.request("POST", self.oper_funciones_url, data=data)
		if response.status_code == 200 and len(response.content) > 0:
			self.driver.execute_script("window.location.href='{}/{}'".format(self.control_alumnos_url, page))
		time.sleep(1)

	def get_notas_parciales(self):
		self.get_page('Alum_0019.php', '12')
		return [
			[td.text for td in tr.find_elements_by_tag_name('td')] 
			for tr in self.driver.find_elements_by_class_name('textos')
		][4:]
		
	def get_materias_inscritas(self):
		self.get_page('Alum_0008.php', '8')
		table = self.driver.find_elements_by_xpath("//table[@class='textos']")
		return [
			[td for td in tr.find_elements_by_tag_name('td')] 
			for tr in table.find_elements_by_tag_name('tr')
		]


	
control = ControlEstudios()
control.open()
#control.get_notas_parciales()
control.get_materias_inscritas()
control.close()

 
# Datos Academicos   ['Alum_0017.php','7'] 
# Datos Personales   ['Alum_0011.php','6'] 
# Expediente Digital ['../asuntos/archivo_muestra1.php','443'] 
# Informacion De Mat ['Alum_0009.php','126'] 
# Informe Academico  ['Alum_InfReg.php','9'] 
# Materias Inscritas ['Alum_0008.php','8'] 
# Notas Parciales    ['Alum_0019.php','12'] 
# Record Academico   ['Alum_0007.php','11'] 