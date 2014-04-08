# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2013 Maarten de Vries <maarten@de-vri.es>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import weechat
import re
import os.path

SCRIPT_NAME     = "autosort"
SCRIPT_AUTHOR   = "Maarten de Vries <maarten@de-vri.es>"
SCRIPT_VERSION  = "1.1"
SCRIPT_LICENSE  = "GPLv3"
SCRIPT_DESC     = "Automatically keeps buffers grouped by server and sorted by name."
CONFIG_PREFIX   = "plugins.var.python.autosort"

rules          = []
group_irc      = True
case_sensitive = False
highest        = 0

def log(message):
	weechat.prnt('NULL', '[autosort] ' + str(message))

class Buffer:
	''' Represents a buffer in Weechat. '''

	def __init__(self, name):
		''' Construct a buffer from a buffer name. '''
		self.full_name = name
		self.info = name.split('.')

	def __str__(self):
		''' Get a string representation of the buffer. '''
		return self.full_name


def get_buffers():
	''' Get a list of all the buffers in weechat. '''
	buffers = []

	buffer_list = weechat.infolist_get("buffer", "", "")

	while weechat.infolist_next(buffer_list):
		name   = weechat.infolist_string (buffer_list, 'full_name')
		number = weechat.infolist_integer(buffer_list, 'number')
		buffers.append(Buffer(name))

	weechat.infolist_free(buffer_list)
	return buffers


def process_info(buffer):
	'''
	Get a processes list of buffer name components.
	This function modifies IRC buffers to group them under their server buffer if group_irc is set.
	'''
	result = list(buffer.info)
	if group_irc and len(result) >= 2 and buffer.info[0] == 'irc' and buffer.info[1] not in ('server', 'irc_raw'):
		result.insert(1, 'server')
	return result;


def get_priority(name, rules):
	''' Get the sort priority of a partial name according to a rule list. '''
	for rule in rules:
		if rule[0].match(name): return rule[1]
	return highest


def sort_key(rules):
	''' Create a sort key function for a rule list. '''
	def key(buffer):
		result  = []
		name    = ""
		for word in process_info(buffer):
			name += ("." if name else "") + word
			result.append((get_priority(name, rules), word if case_sensitive else word.lower()))

		weechat.prnt('NULL', buffer.full_name + ': ' + str(result))
		return result
	return key


def sort_buffers(buffers, rules):
	'''
	Sort a buffer list according to a rule list.
	'''

	return sorted(buffers, key=sort_key(rules))


def apply_buffer_order(buffers):
	''' Sort the buffers in weechat according to the order in the input list.  '''
	i = 1
	for buf in buffers:
		weechat.command('', '/buffer swap {} {}'.format(buf.full_name, i))
		i += 1

def get_config_string(name):
	return weechat.config_get_plugin(name)

def get_config_bool(name):
	return weechat.config_string_to_boolean(weechat.config_get_plugin(name))

def get_config_int(name):
	return int(weechat.config_get_plugin(name))

def resolve_path(path):
	return os.path.join(weechat.info_get('weechat_dir', 'NULL'), path)


def parse_order_rule(rule):
	''' Parse an order rule '''
	match = parse_order_rule.regex.match(rule)
	if not match:
		raise RuntimeError("Invalid rule: expected `{regex} = {priority}'\", got `" + rule + "'")
	try:
		return re.compile('^' + match.group(1).strip() + '$'), int(match.group(2)) if match else None
	except Exception as e:
		raise RuntimeError("Invalid regex: " + str(e) +  " in rule `" + rule + "'")

parse_order_rule.regex = re.compile('^(.*)\\s*=\\s*([+-]?\\d+)$')


def read_order_rules(filename):
	''' Read order rules from a file. '''
	result = []

	highest = 0
	with open(resolve_path(filename)) as file:
		i = -1
		for line in file:
			i += 1

			line = line.strip()
			if not line or line[0] == '#':
				continue

			try:
				rule = parse_order_rule(line)
			except Exception as e:
				log(filename + ":" + str(i) + ": " + str(e) + ". Rule ignored.")
				continue
			highest = max(highest, rule[1])
			result.append(rule)

	return result, highest


def write_default_rules(filename):
	''' Write default order rules to a file. '''
	with open(filename, 'w+') as file:
		file.write(''
			+ '# Sort core buffer first, then non-IRC buffers, then IRC buffers.\n'
			+ 'core  = 0\n'
			+ 'irc   = 2\n'
			+ '[^.]+ = 1\n'
			+ '\n'
			+ '# Sort irc_raw buffer first, then server buffers, then rest.\n'
			+ 'irc.irc_raw = 0\n'
			+ 'irc.server  = 1\n'
		)


def init_configuration():
	''' Initialize the configuration with default values. '''

	defaults = {
		'rules_file':     'autosort_rules.txt',
		'group_irc':      'on',
		'case_sensitive': 'off',
	}

	# Set defaults for unset options.
	for option, default in defaults.items():
		if not weechat.config_is_set_plugin(option):
			weechat.config_set_plugin(option, default)

	# Write default rules file.
	rules_file = resolve_path(get_config_string('rules_file'))
	if not os.path.exists(rules_file): write_default_rules(rules_file)


def load_configuration():
	''' Load configuration variables. '''
	global rules
	global group_irc
	global case_sensitive
	global highest

	init_configuration()

	group_irc      = get_config_bool('group_irc')
	rules_file     = get_config_string('rules_file')
	case_sensitive = get_config_bool('case_sensitive')
	rules, highest = read_order_rules(rules_file)


def on_buffers_changed(*args, **kwargs):
	''' Called whenever the buffer list changes. '''
	apply_buffer_order(sort_buffers(get_buffers(), rules))


def on_config_changed(*args, **kwargs):
	''' Called whenever the configuration changes. '''
	try:
		load_configuration()
	except Exception as e:
		log(e)
		return weechat.WEECHAT_RC_ERROR

	on_buffers_changed()
	return weechat.WEECHAT_RC_OK


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
	weechat.hook_signal("buffer_opened",   "on_buffers_changed", "")
	weechat.hook_signal("buffer_merged",   "on_buffers_changed", "")
	weechat.hook_signal("buffer_unmerged", "on_buffers_changed", "")
	weechat.hook_signal("buffer_renamed",  "on_buffers_changed", "")
	weechat.hook_config(CONFIG_PREFIX + ".*", "on_config_changed", "")
	on_config_changed()
