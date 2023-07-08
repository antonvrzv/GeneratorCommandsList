#!/usr/bin/env python3

import os
import sys
import getopt
from shutil import copy, rmtree
import xml.etree.ElementTree as ET

CURRENT_DIR = './'
CURRENT_WORKING_DIR = './xmls'
PATH_TO_DIR_WITH_TYPES = CURRENT_WORKING_DIR + '/types_xmls'
PATH_TO_DIR_WITH_COMMANDS = CURRENT_WORKING_DIR + '/commands_xmls'

PARAM_TAG   = 'PARAM'
COMMAND_TAG = 'COMMAND'
PTYPE_TAG   = 'PTYPE'
VIEW_TAG    = 'VIEW'

board_types = ('esr1000', 'esr1200', 'esr15', 'esr15xx', 'esr1700', 'esr1x', 'esr200', 'esr2x', 'esr3100', 'esr3200', 'esr3300', 'esr3x', 'vesr', 'wlc30')

# Класс, отвечающий за генерацию списка имен файлов, удовлетворяющих заданному условию
class GeneratorCommandList(object):
	def __init__(self, set_of_ptypes):
		self.set_of_ptypes = set_of_ptypes

	#read only properties	
	@property
	def commands_list_name(self):
		return 'commands.list'

	def __write_string_to_file(self, string):
		path_to_commands_list = CURRENT_DIR + self.commands_list_name
		with open(path_to_commands_list, "w") as f:
			f.write(string)
		print(f"'{path_to_commands_list} file is ready")
		print("Generating commands list done\n")

	def __prepare_string_of_commands(self, dict_of_commands):
		commands_string = 'Список xml-файлов и команды, которые содержатcя в этих файлах.\n'
		commands_string += "Команды отфильтрованы по заданной подстроке('[1-2]/' или '[1-2]\\/' - с экранированием и без), которая содержится в паттерне ptype'а команды.\n\n"
		for file_name, set_of_commands in dict_of_commands.items():
			commands_string += f'{file_name}:\n'
			for command in set_of_commands:
				commands_string += f'\t{command}\n'

		return commands_string


	def __prepare_set_of_commands(self, set_of_commands, parent_node, tag, command_name):
		if tag == PARAM_TAG and \
		   parent_node.find(PARAM_TAG) is None:
				return

		for node in parent_node.findall(tag):
			# Если мы встретили нужный ptype,
			# то нет смысла обрабатывать другие параметры команды,
			# т.к. мы уже добавили эту команду в список, ptype которой удовлетворяет требованию,
			# просто возвращаем управление и переходим к следущей команде.
			# Алгоритм повторяется до тех пор, пока не будут обработаны все команды в рамках xml-файла
			if tag == PARAM_TAG and \
			   command_name in set_of_commands:
				return

			if tag == COMMAND_TAG:
			   command_name = node.attrib.get('name')

			attr_ptype = node.attrib.get('ptype')
			if attr_ptype is not None and \
			   attr_ptype in self.set_of_ptypes:
					set_of_commands.add(command_name)

					if tag == COMMAND_TAG:
						# Если мы встретили нужный ptype у команды(что маловеротяно, т.к. они обычно указываются у параметров),
						# то это значит мы нашли, то что хотели(команду), просто переходим к следующей команде.
						continue
					elif tag == PARAM_TAG:
						# Если мы встретили нужный ptype у параметра,
						# то это значит мы нашли, то что хотели(команду), просто возвращаем управление в цикл обработки следующей команды.
						return

			# Приватный метод, который подготавливает множество(для дальнейшей генерации в файл), состоящее из имен команд,
			# которые удовлетворяют требованию. Множество set_of_commands, содержит команды, описанные в рамках одного,
			# конкретного xml-файла
			self.__prepare_set_of_commands(set_of_commands, node, PARAM_TAG, command_name)

	# Публичный метод, который выполняет генерацию списка команд, удовлетворящих требованию, в файл commands.list
	def generate_command_list(self):
		print("Generating commands list...")
		set_of_commands = set()

		# Словарь, содержащий пары ключ-значение.
		# Ключ - имя файла, в котором были найдены команды.
		# Значение - множестово всех найденных комманд в рамках одного xml-файла.
		# Используется для генерации списка комманд в файл commands.list
		dict_of_commands = dict()

		# Обрабатываем все xml-файлы с командами
		for file in os.scandir(PATH_TO_DIR_WITH_COMMANDS):
			xml_file = file.path

			xml_tree = ET.parse(xml_file)
			clish_module = xml_tree.getroot()
			view = clish_module.find(VIEW_TAG)

			self.__prepare_set_of_commands(set_of_commands, view, COMMAND_TAG, None)

			dict_of_commands[file.name] = set_of_commands.copy()
			set_of_commands.clear()

		# Подготавливаем форматированную строку со списком имен файлов и найденых команд внутри них.
		commands_string = self.__prepare_string_of_commands(dict_of_commands)
		# Записываем строку в файл commands.list.
		self.__write_string_to_file(commands_string)

	# Деинициализатор, который удаляет рабочую директорию после освобождения экземляра класса из памяти(по факту завершение программы после генерации)
	def __del__(self):
		if os.path.exists(CURRENT_WORKING_DIR):
			rmtree(CURRENT_WORKING_DIR)
			print(f"Current working directory '{CURRENT_WORKING_DIR}' was deleted")
		

def usage():
	print('Use the following options and arguments: \n')
	print('-h      : print this help message and exit (also --help)')
	print('--path  : path to project xml directory (build/apps/clish/xml-files)\n')


def prepare_working_dir_with_xmls(path_to_project_xmls_dir):
	print("Preparing working directory...")
	# Дополнительный слой защиты, на случай, если что-то пойдет не так и рабочая директория не удалится
	if os.path.exists(CURRENT_WORKING_DIR):
		rmtree(CURRENT_WORKING_DIR)

	os.makedirs(PATH_TO_DIR_WITH_TYPES)
	print(f"Directory '{PATH_TO_DIR_WITH_TYPES}' was created")
	os.makedirs(PATH_TO_DIR_WITH_COMMANDS)
	print(f"Directory '{PATH_TO_DIR_WITH_COMMANDS}' was created")

	for address_dir, sub_dirs, sub_files in os.walk(path_to_project_xmls_dir):
		name_dir = address_dir.split('/')[-1]
		if name_dir in board_types:
			for file in os.scandir(address_dir):
				if file.name.startswith('types-'):
					copy(file.path, PATH_TO_DIR_WITH_TYPES)
		elif name_dir == 'common':
			copy(address_dir + '/types.xml', PATH_TO_DIR_WITH_TYPES)
			for file in os.scandir(address_dir):
				if not file.name.startswith('types'):
					copy(file.path, PATH_TO_DIR_WITH_COMMANDS)

	print("Preparing working directory done\n")


# Создает множество с типами, паттерн которых содержит заданную подстроку
# Используется при обработки комманд - ptype команды проверяется на наличие в этом множестве,
# Если ptype команды является элементом этого множества, то команда попадает в список.
def create_set_of_ptypes():
	search_substring = '[1-2]/'
	search_substring_with_escaping = '[1-2]\\/'

	set_of_result_ptypes = set()
	for file in os.scandir(PATH_TO_DIR_WITH_TYPES):
		xml_file = file.path

		xml_tree = ET.parse(xml_file)
		clish_module = xml_tree.getroot()

		set_of_ptypes = set()
		for node in clish_module.findall(PTYPE_TAG):
			attr_pattern = node.attrib.get('pattern')

			if attr_pattern is not None:
				if search_substring in attr_pattern or \
					search_substring_with_escaping in attr_pattern:
						set_of_ptypes.add(node.attrib.get('name'))

		set_of_result_ptypes = set_of_result_ptypes.union(set_of_ptypes)

	return set_of_result_ptypes


def validate_path(path):
	if not os.path.exists(path):
		print(f"error: - path to '{path}' is not exist")
		sys.exit(1)


def main(argv):
	try:
		opts, args = getopt.getopt(argv, 'h',['path='])
	except getopt.GetoptError:
		usage()
		sys.exit(1)

	if len(opts) == 0:
		usage()
		sys.exit(0)

	path_to_project_xmls_dir = ''

	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit(0)
		if opt == '--path':
			path_to_project_xmls_dir = arg
			if len(path_to_project_xmls_dir) == 0:
				print("Option '--path' must have an argument")
				sys.exit(1)

	validate_path(path_to_project_xmls_dir)

	prepare_working_dir_with_xmls(path_to_project_xmls_dir)
	set_of_ptypes = create_set_of_ptypes()

	generatorCommandList = GeneratorCommandList(set_of_ptypes)
	generatorCommandList.generate_command_list()


if __name__ == '__main__':
	main(sys.argv[1:])
