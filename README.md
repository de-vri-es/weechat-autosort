# Autosort

## Introduction
Autosort is a weechat script to automatically keep your buffers sorted.
The sort order can be customized by defining your own sort rules,
but the default should be sane enough for most people.
It can also group IRC channel/private buffers under their server buffer if you like.

Autosort first turns buffer names into a list of their components by splitting on them on the period character.
For example, the buffer name `irc.server.freenode` is turned into `['irc', 'server', 'freenode']`
The buffers are then lexicographically sorted.

To facilitate custom sort orders, it is possible to assign a score to each component individually before the sorting is done.
Any name component that did not get a score assigned will be sorted after those that did receive a score.
Components are always sorted on their score first and on their name second.
Lower scores are sorted first.

### Sort rules
You can assign scores to name components by defining sort rules.
The first rule that matches a component decides the score.
Further rules are not examined.
Sort rules use the following syntax:
```
<glob-pattern> = <score>
```
You can use the `/autosort rule` command to show and manipulate the list of sort rules.


Allowed special characters in the glob patterns are:

Pattern | Meaning
--------|:-------
*       | Matches a sequence of any characters except for periods.
?       | Matches a single character, but not a period.
[a-z]   | Matches a single character in the given regex-like character class.
[^ab]   | A negated regex-like character class.
\\*     | A backslash escapes the next characters and removes its special meaning.
\\\\    | A literal backslash.


### Grouping IRC buffers
In weechat, IRC channel/private buffers are named `irc.<network>.<#channel>`,
and IRC server buffers are named `irc.server.<network>`.
This does not work very well with lexicographical sorting if you want all buffers for one network grouped together.
That is why autosort comes with the `autosort.sorting.group_irc` option,
which secretly pretends IRC channel/private buffers are called `irc.server.<network>.<#channel>`.
The buffers are not actually renamed, autosort simply pretends they are for sorting purposes.


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
```
/autosort list
```
Print the list of sort rules.

```
/autosort add <pattern> = <score>
```
Add a new rule at the end of the rule list.

```
/autosort insert <index> <pattern> = <score>
```
Insert a new rule at the given index in the rule list.

```
/autosort update <index> <pattern> = <score>
```
Update a rule in the list with a new pattern and score.

```
/autosort delete <index>
```
Delete a rule from the list.

```
/autosort move <index_from> <index_to>
```
Move a rule from one position in the list to another.

```
/autosort swap <index_a> <index_b>
```
Swap two rules in the list
