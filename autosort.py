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
import fnmatch

SCRIPT_NAME     = "autosort"
SCRIPT_AUTHOR   = "Maarten de Vries <maarten@de-vri.es>"
SCRIPT_VERSION  = "1.1"
SCRIPT_LICENSE  = "GPLv3"
SCRIPT_DESC     = "Automatically keeps buffers grouped by server and sorted by name."
CONFIG_PREFIX   = "plugins.var.python." + SCRIPT_NAME

priorities = None
group_irc  = True

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
		buffers.append(Buffer(weechat.infolist_string(buffer_list, 'full_name')))

	weechat.infolist_free(buffer_list)
	return buffers


def process_info(buffer):
	'''
	Get a processes list of buffer name components.
	This function modifies IRC buffers to group them under their server buffer if group_irc is set.
	'''
	result = list(buffer.info)
	if group_irc and len(buffer.info) == 3 and buffer.info[0] == 'irc' and buffer.info[1] != 'server':
		result.insert(1, 'server')
	return result;


def get_priority(word, priorities):
	''' Get the priority of a word according to a priority list. '''
	if priorities == None:
		return None, None

	highest = 0
	for i, (pattern, priority, children) in enumerate(priorities):
		highest = max(highest, priority)
		if fnmatch.fnmatchcase(word, pattern):
			return priority, children

	return highest + 1, None


def sort_key(priorities_):
	''' Create a sort key function for a priority list. '''

	''' Get the sort key for a buffer. '''
	def key(buffer):
		priorities = priorities_
		result  = []
		for word in process_info(buffer):
			priority, priorities = get_priority(word, priorities)
			result.append((priority, word))

		weechat.prnt('NULL', buffer.full_name + ': ' + str(result) + '  --  ' + str(priorities_))
		return result
	return key


def sort_buffers(buffers, priorities):
	'''
	Sort a buffer list by name, grouped by server.
	Buffers without a server are sorted after the rest.
	'''

	return sorted(buffers, key=sort_key(priorities))


def apply_buffer_order(buffers):
	''' Sort the buffers in weechat according to the order in the input list.  '''
	i = 1
	for buf in buffers:
		weechat.command('', '/buffer swap {} {}'.format(buf.full_name, i))
		i += 1

def get_config_string(name):
	return weechat.config_get_plugin(name)

def get_config_bool(name):
	return weechat.config_get_plugin(name) == 'on'

def get_config_int(name):
	return int(weechat.config_get_plugin(name))

def get_config_order(prefix):
	if not weechat.config_is_set_plugin(prefix):
		return None

	result  = []
	for entry in get_config_string(prefix).split(' '):
		try:
			pattern, priority = entry.rsplit(':', 2)
			priority = int(priority)
			result.append((pattern, priority, get_config_order(prefix + '.' + pattern)))
		except Exception:
			raise RuntimeError("Invalid pattern `" + entry + "' in configuration option autosort." + prefix + ".")

	return result


def parse_order_pattern(pattern):
	components = rsplit(':', 2)
	if len(components) != 2: raise RuntimeError("invalid pattern `" + pattern + "'")
	return tuple(components)

def do_sort_buffers(*args, **kwargs):
	''' Callback called whenever the buffer list changes. '''
	weechat.prnt('NULL', 'Configured priorities: ' + str(priorities))
	buffers = get_buffers()
	apply_buffer_order(sort_buffers(buffers, priorities))
	return weechat.WEECHAT_RC_OK


def reload_configuration(*args, **kwargs):
	global priorities
	global group_irc
	init_configuration()
	priorities = get_config_order('order')
	group_irc  = get_config_bool('group_irc')
	do_sort_buffers()
	return weechat.WEECHAT_RC_OK


def init_configuration():
	defaults = {
		'order':     'core:0 irc:1',
		'order.irc': 'server:0',
		'group_irc': 'on',
	}

	for option, default in defaults.items():
		if not weechat.config_is_set_plugin(option):
			weechat.config_set_plugin(option, default)


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
	weechat.hook_signal("buffer_opened",   "do_sort_buffers", "")
	weechat.hook_signal("buffer_merged",   "do_sort_buffers", "")
	weechat.hook_signal("buffer_unmerged", "do_sort_buffers", "")
	weechat.hook_signal("buffer_renamed",  "do_sort_buffers", "")
	weechat.hook_config(CONFIG_PREFIX + ".*", "reload_configuration", "")
	reload_configuration()
