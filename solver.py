import os, requests, pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO
from subprocess import check_output

def try_to_solve_captcha(image):
	# image = Image.open(BytesIO(requests.get(url).content)).convert("RGB").rotate(-7)
	image = image.convert("RGB").rotate(-7)
	cropped_image = image.crop((0, 0, 50, 24))
	# cropped_image.show()
	color_format  = '%02x%02x%02x'
	pixel_matrix = cropped_image.load()

	rgb_colors_on_img = list(set([pixel_matrix[row, col] for col in range(0, cropped_image.height) for row in range(0, cropped_image.width)]))
	rgb_colors_on_img.sort()

	rgb_red    = (135, 0, 0)
	rgb_blank  = (255, 255, 255)
	rgb_gray   = rgb_colors_on_img[1]

	if (rgb_red in rgb_colors_on_img):
		rgb_colors_on_img.pop(rgb_colors_on_img.index(rgb_red))

	hex_colors_on_img = [color_format % color for color in rgb_colors_on_img[:4]]

	for col in range(0, cropped_image.height):
		for row in range(0, cropped_image.width):
			current_hex_color = color_format % pixel_matrix[row, col]
			if current_hex_color == '000000':
				pixel_matrix[row, col] = rgb_blank
			if current_hex_color == '870000':
				occurrences = 0

				upper_row  = row - 1
				bottom_row = row + 1
				left_col   = col - 1
				right_col  = col + 1

				if upper_row  >= 0:
					occurrences += 1 if color_format % pixel_matrix[upper_row,  col] in hex_colors_on_img else 0
				if left_col   >= 0:
					occurrences += 1 if color_format % pixel_matrix[row,   left_col] in hex_colors_on_img else 0
				if right_col  <= cropped_image.height - 1:
					occurrences += 1 if color_format % pixel_matrix[row,  right_col] in hex_colors_on_img else 0
				if bottom_row <= cropped_image.width  - 1:
					occurrences += 1 if color_format % pixel_matrix[bottom_row, col] in hex_colors_on_img else 0

				if upper_row >= 0 and left_col >= 0:
					occurrences += 1 if color_format % pixel_matrix[upper_row,   left_col] in hex_colors_on_img else 0
				if upper_row >= 0 and right_col <= cropped_image.height - 1:
				 	occurrences += 1 if color_format % pixel_matrix[upper_row,  right_col] in hex_colors_on_img else 0
				if bottom_row <= cropped_image.width  - 1 and right_col <= cropped_image.height - 1:
					occurrences += 1 if color_format % pixel_matrix[bottom_row, right_col] in hex_colors_on_img else 0
				if bottom_row <= cropped_image.width  - 1 and left_col >= 0:
					occurrences += 1 if color_format % pixel_matrix[bottom_row,  left_col] in hex_colors_on_img else 0

				pixel_matrix[row, col] = rgb_gray if occurrences > 1 else rgb_blank

	cropped_image.convert('L')
	cropped_image = cropped_image.filter(ImageFilter.MedianFilter(3))
	cropped_image = ImageEnhance.Contrast(cropped_image)
	cropped_image = cropped_image.enhance(2)
	cropped_image = cropped_image.convert('1')
	cropped_image.save('temp.jpg')

	check_output(['convert', 'temp.jpg', '-resample', '600', 'temp.jpg'])
	img = Image.open('temp.jpg')
	text = pytesseract.image_to_string(img)

	return text
