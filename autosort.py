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
import os.path
import re
import json

SCRIPT_NAME     = "autosort"
SCRIPT_AUTHOR   = "Maarten de Vries <maarten@de-vri.es>"
SCRIPT_VERSION  = "1.1"
SCRIPT_LICENSE  = "GPLv3"
SCRIPT_DESC     = "Automatically keeps buffers sorted just the way you want to."


options        = {}
rules          = []
group_irc      = True
case_sensitive = False
highest        = 0
default_rules  = json.dumps([
	('core',  0),
	('irc',   2),
	('[^.]+', 1),

	('irc[.]server',  1),
	('irc[.]irc_raw', 0),
])

def pad(sequence, length, padding = None):
	''' Pad a list until is has a certain length. '''
	return sequence + [padding] * max(0, (length - len(sequence)))


def log(message, buffer = 'NULL'):
	weechat.prnt(buffer, '[autosort] ' + str(message))


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

		# Buffer is merged with one we already have in the list, skip it.
		if number <= len(buffers):
			continue
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


def get_score(name, rules):
	''' Get the sort score of a partial name according to a rule list. '''
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
			result.append((get_score(name, rules), word if case_sensitive else word.lower()))
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


def parse_rules(blob):
	''' Parse rules from a string. '''
	result = []

	try:
		decoded = json.loads(blob)
	except Exception:
		log("Invalid rules: expected JSON encoded list of pairs, got \"" + blob + "\".")
		return [], 0

	highest = 0
	for rule in decoded:
		# Rules must be a regex,score pair.
		if len(rule) != 2:
			log("Invalid rule: expected [regex, score], got " + str(rule) + ". Rule ignored.")
			continue

		# Rules must have a valid regex.
		try:
			regex = re.compile('^' + rule[0] + '$')
		except Exception as error:
			log("Invalid regex: " + str(e) + " in \"" + rule[0] + "\". Rule ignored.")
			continue

		# Rules must have a valid score.
		try:
			score = int(rule[1])
		except Exception as error:
			log("Invalid score: expected an integer, got " + str(rule[1]) + ". Rule ignored.")
			continue

		highest = max(highest, score + 1)
		result.append((regex, score))

	return result, highest

def encode_rules(rules):
	''' Encode the rules for storage. '''
	return json.dumps(map(lambda x: (x[0].pattern[1:-1], x[1]),rules))


def init_config():
	''' Initialize the configuration. '''

	config_file = weechat.config_new('autosort', '', '')
	if not config_file:
		log('Failed to initialize configuration file. Got: ' + str(config_file))
	else:
		sorting_section = weechat.config_new_section(config_file, 'sorting', False, False, '', '', '', '', '', '', '', '', '', '')

		if not sorting_section:
			log("Failed to initialize section `sorting' of configuration file.")
			weechat.config_free(config_file)

		else:
			options['case_sensitive'] = weechat.config_new_option(config_file, sorting_section,
				'case_sensitive', 'boolean',
				'If this option is on, sorting is case sensitive.',
				'', 0, 0, 'off', 'off', 0,
				'', '', '', '', '', ''
			)

			options['group_irc'] = weechat.config_new_option(config_file, sorting_section,
				'group_irc', 'boolean',
				'If this option is on, the script pretends that IRC channel/private buffers are renamed to "irc.server.{network}.{channel}" rather than "irc.{network}.{channel}".' +
				'This ensures that thsee buffers are grouped with their respective server buffer.',
				'', 0, 0, 'on', 'on', 0,
				'', '', '', '', '', ''
			)

			options['rules'] = weechat.config_new_option(config_file, sorting_section,
				'rules', 'string',
				'An ordered list of sorting rules encoded as JSON. See /help autosort for commands to manipulate these rules.',
				'', 0, 0, default_rules, default_rules, 0,
				'', '', '', '', '', ''
			)

		if weechat.config_read(config_file) != weechat.WEECHAT_RC_OK:
			log('Failed to load configuration file.')

		if weechat.config_write(config_file) != weechat.WEECHAT_RC_OK:
			log('Failed to write configuration file.')


def load_config():
	''' Load configuration variables. '''
	global rules
	global group_irc
	global case_sensitive
	global highest

	case_sensitive = weechat.config_boolean(options['case_sensitive'])
	group_irc      = weechat.config_boolean(options['group_irc'])
	rules_blob     = weechat.config_string(options['rules'])

	rules, highest = parse_rules(rules_blob)

def save_rules(run_callback = True):
	''' Save the current rules to the configuration. '''
	weechat.config_option_set(options['rules'], encode_rules(rules), run_callback)


def call_command(data, buffer, old_command, args, subcommands):
	''' Call a subccommand from a dictionary. '''
	subcommand, tail = pad(args.split(' ', 1), 2, '')
	child            = subcommands.get(subcommand)
	command          = old_command + [subcommand]

	if isinstance(child, dict):
		return call_command(data, buffer, command, tail, child)
	elif callable(child):
		return child(data, buffer, command, tail)

	log(' '.join(command) + ": command not found");
	return weechat.WEECHAT_RC_ERROR


def split_args(args, expected):
	''' Split an argument string in the desired number of arguments. '''
	split = args.split(' ', expected - 1)
	if (len(split) != expected):
		raise ValueError('Expected exactly ' + expected + ' arguments, got ' + str(len(split)) + '.')
	return split


def parse_rule_arg(arg):
	''' Parse a rule argument. '''
	stripped = arg.strip();
	match = parse_rule_arg.regex.match(stripped)
	if not match:
		raise ValueError('Invalid rule: expected "regex = score", got "' + stripped + '".')

	regex = '^' + match.group(1).strip() + '$'
	score = match.group(2).strip()

	try:
		score = int(score)
	except Exception:
		raise ValueError('Invalid score: expected integer, got "' + score + '".')

	try:
		regex = re.compile(regex)
	except Exception as e:
		raise ValueError('Invalid regex: ' + str(e) + ' in "' + regex + '".')

	return (regex, score)

parse_rule_arg.regex = re.compile(r'^(.*)=\s*([+-]?\d+)$')

def parse_index_arg(arg):
	''' Parse an index argument. '''
	stripped = arg.strip()
	try:
		return int(stripped)
	except ValueError:
		raise ValueError('Invalid index: expected integer, got "' + stripped + '".')


def command_rule_list(data, buffer, command, args):
	''' Show the list of sorting rules. '''
	global rules

	output = 'Sorting rules:\n'
	for i, rule in enumerate(rules):
		output += '    ' + str(i) + ": " + str(rule[0].pattern[1:-1]) + ' = ' + str(rule[1]) + '\n'
	log(output, buffer)

	return weechat.WEECHAT_RC_OK


def command_rule_add(data, buffer, command, args):
	''' Add a rule to the rule list. '''
	global rules
	rule = parse_rule_arg(args)

	rules.append(rule)
	save_rules()
	command_rule_list('', buffer, command, '')

	return weechat.WEECHAT_RC_OK


def command_rule_insert(data, buffer, command, args):
	''' Insert a rule at the desired position in the rule list. '''
	global rules
	index, rule = split_args(args, 2)
	index = parse_index_arg(index)
	rule  = parse_rule_arg(rule)

	rules.insert(index, rule)
	save_rules()
	command_rule_list('', buffer, command, '')
	return weechat.WEECHAT_RC_OK


def command_rule_update(data, buffer, command, args):
	''' Update a rule in the rule list. '''
	global rules
	index, rule = split_args(args, 2)
	index = parse_index_arg(index)
	rule  = parse_rule_arg(rule)

	if not 0 <= index < len(rules):
		raise ValueError('Index out of range: expected between 0 and {}, got {}.'.format(len(rules), index))

	rules[index] = rule
	save_rules()
	command_rule_list('', buffer, command, '')
	return weechat.WEECHAT_RC_OK



def command_rule_delete(data, buffer, command, args):
	''' Delete a rule from the rule list. '''
	global rules
	index = args.strip()
	index = parse_index_arg(index)

	if not 0 <= index < len(rules):
		raise ValueError('Index out of range: expected between 0 and {}, got {}.'.format(len(rules), index))

	rules.pop(index)
	save_rules()
	command_rule_list('', buffer, command, '')
	return weechat.WEECHAT_RC_OK


def command_rule_move(data, buffer, command, args):
	''' Move a rule to a new position. '''
	global rules
	index_a, index_b = split_args(args, 2)
	index_a = parse_index_arg(index_a)
	index_b = parse_index_arg(index_b)
	rule = rules[index_a]

	if not 0 <= index_a < len(rules):
		raise ValueError('Index out of range: expected between 0 and {}, got {}.'.format(len(rules), index_a))

	if not 0 <= index_b < len(rules):
		raise ValueError('Index out of range: expected between 0 and {}, got {}.'.format(len(rules), index_b))

	rules.insert(index_b, rules.pop(index_a))
	save_rules()
	command_rule_list('', buffer, command, '')
	return weechat.WEECHAT_RC_OK


def command_rule_swap(data, buffer, command, args):
	''' Swap two rules. '''
	global rules
	index_a, index_b = split_args(args, 2)
	index_a = parse_index_arg(index_a)
	index_b = parse_index_arg(index_b)

	if not 0 <= index_a < len(rules):
		raise ValueError('Index out of range: expected between 0 and {}, got {}.'.format(len(rules), index_a))

	if not 0 <= index_b < len(rules):
		raise ValueError('Index out of range: expected between 0 and {}, got {}.'.format(len(rules), index_b))

	rules[index_a], rules[index_b] = rules[index_b], rules[index_a]
	save_rules()
	command_rule_list('', buffer, command, '')
	return weechat.WEECHAT_RC_OK


commands = {
	'rule': {
		'list':   command_rule_list,
		'add':    command_rule_add,
		'insert': command_rule_insert,
		'update': command_rule_update,
		'delete': command_rule_delete,
		'move':   command_rule_move,
		'swap':   command_rule_swap,
	}
}


def on_buffers_changed(*args, **kwargs):
	''' Called whenever the buffer list changes. '''
	apply_buffer_order(sort_buffers(get_buffers(), rules))
	return weechat.WEECHAT_RC_OK


def on_config_changed(*args, **kwargs):
	''' Called whenever the configuration changes. '''
	load_config()
	on_buffers_changed()
	return weechat.WEECHAT_RC_OK


def on_autosort_command(data, buffer, args):
	''' Called when the autosort command is invoked. '''
	try:
		return call_command(data, buffer, ['/autosort'], args, commands)
	except ValueError as e:
		log(e, buffer)
		return weechat.WEECHAT_RC_ERROR


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
	init_config()

	weechat.hook_signal('buffer_opened',   'on_buffers_changed', '')
	weechat.hook_signal('buffer_merged',   'on_buffers_changed', '')
	weechat.hook_signal('buffer_unmerged', 'on_buffers_changed', '')
	weechat.hook_signal('buffer_renamed',  'on_buffers_changed', '')
	weechat.hook_config('autosort.*',      'on_config_changed',  '')
	weechat.hook_command('autosort', '', '', '', '', 'on_autosort_command', 'NULL')
	on_config_changed()
