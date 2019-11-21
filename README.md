# Autosort

## Introduction
Autosort is a weechat script to automatically or manually keep your buffers sorted.
The sort order can be customized by defining your own sort rules,
but the default should be sane enough for most people.
It can also group IRC channel/private buffers under their server buffer if you like.

Autosort uses a stable sorting algorithm, meaning that you can manually move buffers
to change their relative order, if they sort equal with your rule set.

## Sort rules
Autosort evaluates a list of eval expressions (see /help eval) and sorts the buffers based on evaluated result.
Earlier rules will be considered first.
Only if earlier rules produced identical results is the result of the next rule considered for sorting purposes.

You can debug your sort rules with the `/autosort debug` command, which will print the evaluation results of each rule for each buffer.

NOTE: The sort rules for version 3 are not compatible with version 2 or vice versa.
You will have to manually port your old rules to version 3 if you have any.

## Helper variables
You may define helper variables for the main sort rules to keep your rules readable.
They can be used in the main sort rules as variables.
For example, a helper variable named `foo` can be accessed in a main rule with the string `${foo}`.

## Automatic or manual sorting
By default, autosort will automatically sort your buffer list whenever a buffer is opened, merged, unmerged or renamed.
This should keep your buffers sorted in almost all situations.
However, you may wish to change the list of signals that cause your buffer list to be sorted.
Simply edit the `autosort.sorting.signals` option to add or remove any signal you like.
If you remove all signals you can still sort your buffers manually with the `/autosort sort` command.
To prevent all automatic sorting, `autosort.sorting.sort_on_config_change` should also be set to off.

## Recommended settings
For the best visual effect, consider setting the following options:
```
/set irc.look.server_buffer independent
/set buffers.look.indenting on
```

The first setting allows server buffers to be sorted independently,
which is needed to create a hierarchical tree view of the server and channel buffers.
The second one indents channel and private buffers in the buffer list of the `buffers.pl` script.

If you are using the buflist plugin you could consider something like this:
```
/set buflist.format.indent "${color:237}${if:${buffer.next_buffer.local_variables.type}=~^(channel|private)$?├─:└─}"
```

This will use Unicode characters to draw a tree structure in the buflist.

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

## Info hooks
Autosort comes with a number of info hooks to add some extra functionality to regular weechat eval strings.
Info hooks can be used in eval strings in the form of `${info:some_hook,arguments}`.

Commas and backslashes in arguments to autosort info hooks (except for `${info:autosort_escape}`) must be escaped with a backslash.

```
${info:autosort_replace,pattern,replacement,source}
```
Replace all occurrences of `pattern` with `replacement` in the string `source`.
Can be used to ignore certain strings when sorting by replacing them with an empty string.

For example: `${info:autosort_replace,cat,dog,the dog is meowing}` expands to "`the cat is meowing`".

```
${info:autosort_order,value,option0,option1,option2,...}
```
Generate a zero-padded number that corresponds to the index of `value` in the list of options.
If one of the options is the special value `*`, then any value not explicitly mentioned will be sorted at that position.
Otherwise, any value that does not match an option is assigned the highest number available.
Can be used to easily sort buffers based on a manual sequence.

For example: `${info:autosort_order,${server},freenode,oftc,efnet}` will sort freenode before oftc, followed by efnet and then any remaining servers.
Alternatively, `${info:autosort_order,${server},freenode,oftc,*,efnet}` will sort any unlisted servers after freenode and oftc, but before efnet.

```
${info:autosort_escape,text}
```
Escape commas and backslashes in `text` by prepending them with a backslash.
This is mainly useful to pass arbitrary eval strings as arguments to other autosort info hooks.
Otherwise, an eval string that expands to something with a comma would be interpreted as multiple arguments.

For example, it can be used to safely pass buffer names to `${info:autosort_replace}` like so:
`${info:autosort_replace,##,#,${info:autosort_escape,${buffer.name}}}`.
