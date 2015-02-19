# Autosort

## Introduction
Autosort is a weechat script to automatically or manually keep your buffers sorted.
The sort order can be customized by defining your own sort rules,
but the default should be sane enough for most people.
It can also group IRC channel/private buffers under their server buffer if you like.

For the best effect, you may want to consider setting the option `irc.look.server_buffer` to `independent` and `buffers.look.indenting` to `on`.

Autosort first turns buffer names into a list of their components by splitting on them on the period character.
For example, the buffer name `irc.server.freenode` is turned into `['irc', 'server', 'freenode']`
The buffers are then lexicographically sorted.

To facilitate custom sort orders, it is possible to assign a score to each component individually before the sorting is done.
Any name component that did not get a score assigned will be sorted after those that did receive a score.
Components are always sorted on their score first and on their name second.
Lower scores are sorted first.

### Automatic or manual sorting
By default, autosort will automatically sort your buffer list whenever a buffer is opened, merged, unmerged or renamed.
This should keep your buffers sorted in almost all situations.
However, you may wish to change the list of signals that cause your buffer list to be sorted.
Simply edit the `autosort.sorting.signals` option to add or remove any signal you like.
If you remove all signals you can still sort your buffers manually with the `/autosort sort` command.
To prevent all automatic sorting, `autosort.sorting.sort_on_config_change` should also be set to off.

### Grouping IRC buffers
In weechat, IRC channel/private buffers are named `irc.<network>.<#channel>`,
and IRC server buffers are named `irc.server.<network>`.
This does not work very well with lexicographical sorting if you want all buffers for one network grouped together.
That is why autosort comes with the `autosort.sorting.group_irc` option,
which secretly pretends IRC channel/private buffers are called `irc.server.<network>.<#channel>`.
The buffers are not actually renamed, autosort simply pretends they are for sorting purposes.

### Replacement patterns
Sometimes you may want to ignore some characters for sorting purposes.
On Freenode for example, you may wish to ignore the difference between channels starting with a double or a single hash sign.
To do so, simply add a replacement pattern that replaces ## with # with the following command:
```
/autosort replacements add ## #
```

Replacement patterns do not support wildcards or special characters at the moment.

### Sort rules
You can assign scores to name components by defining sort rules.
The first rule that matches a component decides the score.
Further rules are not examined.
Sort rules use the following syntax:
```
<glob-pattern> = <score>
```
You can use the `/autosort rules` command to show and manipulate the list of sort rules.


Allowed special characters in the glob patterns are:

Pattern | Meaning
--------|:-------
*       | Matches a sequence of any characters except for periods.
?       | Matches a single character, but not a period.
[a-z]   | Matches a single character in the given regex-like character class.
[^ab]   | A negated regex-like character class.
\\*     | A backslash escapes the next characters and removes its special meaning.
\\\\    | A literal backslash.


### Example
As an example, consider the following rule list:
```
0: core            = 0
1: irc             = 2
2: *               = 1

3: irc.server.*.#* = 1
4: irc.server.*.*  = 0
```

Rule 0 ensures the core buffer is always sorted first.
Rule 1 sorts IRC buffers last and rule 2 puts all remaining buffers in between the two.

Rule 3 and 4 would make no sense with the group_irc option off.
With the option on though, these rules will sort private buffers before regular channel buffers.
Rule 3 matches channel buffers and assigns them a higher score,
while rule 4 matches the buffers that remain and assigns them a lower score.
The same effect could also be achieved with a single rule:
```
irc.server.*.[^#]* = 0
```

## Commands

### Miscellaneous
```
/autosort sort
```
Manually trigger the buffer sorting.


### Sorting rules
```
/autosort rules list
```
Print the list of sort rules.

```
/autosort rules add <pattern> = <score>
```
Add a new rule at the end of the list.

```
/autosort rules insert <index> <pattern> = <score>
```
Insert a new rule at the given index in the list.

```
/autosort rules update <index> <pattern> = <score>
```
Update a rule in the list with a new pattern and score.

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


### Replacement patterns
```
/autosort replacements list
```
Print the list of replacement patterns.

```
/autosort replacements add <pattern> <replacement>
```
Add a new replacement pattern at the end of the list.

```
/autosort replacements insert <index> <pattern> <replacement>
```
Insert a new replacement pattern at the given index in the list.

```
/autosort replacements update <index> <pattern> <replacement>
```
Update a replacement pattern in the list.

```
/autosort replacements delete <index>
```
Delete a replacement pattern from the list.

```
/autosort replacements move <index_from> <index_to>
```
Move a replacement pattern from one position in the list to another.

```
/autosort replacements swap <index_a> <index_b>
```
Swap two replacement pattern in the list
