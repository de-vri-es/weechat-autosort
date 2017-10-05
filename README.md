# Autosort

## Introduction
Autosort is a weechat script to automatically or manually keep your buffers sorted.
The sort order can be customized by defining your own sort rules,
but the default should be sane enough for most people.
It can also group IRC channel/private buffers under their server buffer if you like.

For the best effect, you may want to consider setting the option `irc.look.server_buffer` to `independent` and `buffers.look.indenting` to `on`.

### Sort rules
Autosort evaluates a list of eval expressions (see /help eval) and sorts the buffers based on evaluated result.
Earlier rules will be considered first.
Only if earlier rules produced identical results is the result of the next rule considered for sorting purposes.

You can debug your sort rules with the `/autosort debug` command, which will print the evaluation results of each rule for each buffer.

NOTE: The sort rules for version 3 are not compatible with version 2 or vice versa.
You will have to manually port your old rules to version 3 if you have any.

### Helper variables
You may define helper variables for the main sort rules to keep your rules readable.
They can be used in the main sort rules as variables.
For example, a helper variable named `foo` can be accessed in a main rule with the string `${foo}`.

## Replacing substrings
There is no default method for replacing text inside eval expressions.
However, autosort adds a `replace` info hook that can be used inside eval expressions: `${info:autosort_replace,from,to,text}`.
For example, `${info:autosort_replace,#,,${buffer.name}}` will evaluate to the buffer name with all hash signs stripped.

### Automatic or manual sorting
By default, autosort will automatically sort your buffer list whenever a buffer is opened, merged, unmerged or renamed.
This should keep your buffers sorted in almost all situations.
However, you may wish to change the list of signals that cause your buffer list to be sorted.
Simply edit the `autosort.sorting.signals` option to add or remove any signal you like.
If you remove all signals you can still sort your buffers manually with the `/autosort sort` command.
To prevent all automatic sorting, `autosort.sorting.sort_on_config_change` should also be set to off.

## Commands

### Miscellaneous
```
/autosort sort
```
Manually trigger the buffer sorting.

```
/autosort debug
```
Show the evaluation results of the sort rules for each buffer.


### Sorting rules
```
/autosort rules list
```
Print the list of sort rules.

```
/autosort rules add <expression>
```
Add a new rule at the end of the list.

```
/autosort rules insert <index> <expression>
```
Insert a new rule at the given index in the list.

```
/autosort rules update <index> <expression>
```
Update a rule in the list with a new expression.

```
/autosort rules delete <index>
```
Delete a rule from the list.

```
/autosort rules move <index_from> <index_to>
```
Move a rule from one position in the list to another.

```
/autosort rules swap <index_a> <index_b>
```
Swap two rules in the list


### Helper variables
```
/autosort helpers list
```
Print the list of helpers variables.

```
/autosort helpers set <name> <expression>
```
Add or update a helper variable.

```
/autosort helpers delete <name>
```
Delete a helper variable.

```
/autosort helpers rename <old_name> <new_name>
```
Rename a helper variable.

```
/autosort helpers swap <name_a> <name_b>
```
Swap the expressions of two helper variables in the list.
