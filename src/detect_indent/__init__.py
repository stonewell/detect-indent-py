'''
 Detect either spaces or tabs but not both to properly handle tabs
 for indentation and spaces for alignment
'''
import os
import sys
import re
import logging

INDENT_REGEX = r'^(?:( )+|\t+)'

INDENT_TYPE_SPACE = 'space'
INDENT_TYPE_TAB = 'tab'
'''
Make a Map that counts how many indents/unindents have occurred for a given size and how many lines follow a given indentation.
The key is a concatenation of the indentation type (s = space and t = tab) and the size of the indents/unindents.
```
indents = {
	t3: [1, 0],
	t4: [1, 5],
	s5: [1, 0],
	s12: [1, 0],
}
```
'''


def __is_empty_line(l):
  if len(l) == 0:
    return True

  return re.fullmatch('^\\s*$', l, flags=re.MULTILINE) is not None


def __make_indents_map(lines, ignore_simple_space):
  indents = {}

  previous_size = 0
  previous_indent_type = None

  for line in lines:
    if __is_empty_line(line):
      logging.debug('skip empty line')
      continue

    match = re.match(INDENT_REGEX, line)

    if not match:
      previous_size = 0
      previous_indent_type = None
      logging.debug('skip no indent line')
      continue

    indent = len(match.group(0))
    indent_type = INDENT_TYPE_SPACE if match.group(1) else INDENT_TYPE_TAB

    if ignore_simple_space and indent_type == INDENT_TYPE_SPACE and indent == 1:
      continue

    if indent_type != previous_indent_type:
      previous_size = 0

    previous_indent_type = indent_type

    use = 1
    weight = 0

    indent_diff = abs(indent - previous_size)

    logging.debug('indent:%d, indent_type:%s, p:%d, pt:%s, diff:%d line:%s',
                  indent, indent_type, previous_size, previous_indent_type,
                  indent_diff, line)

    previous_size = indent

    if indent_diff == 0:
      use = 0
      weight = 1
    else:
      key = f'{"s" if indent_type == INDENT_TYPE_SPACE else "t"}{indent_diff}'

    try:
      cur_use, cur_weight = indents[key]
      indents[key] = (cur_use + use, cur_weight + weight)
    except KeyError:
      indents[key] = (1, 0)

    logging.debug('save indent, key:%s, v:%s', key, indents[key])

  return indents


def __get_most_used_key(indents):
  result = None
  max_used = 0
  max_weight = 0

  for key, value in indents.items():
    used, weight = value

    if used > max_used or (used == max_used and weight > max_weight):
      max_used = used
      max_weight = weight
      result = key

  return result


def detect_indent(lines):
  '''
  Detect the indent for lines
  '''
  indents = __make_indents_map(lines, True)

  if len(indents) == 0:
    indents = __make_indents_map(lines, False)

  logging.debug('indents:%s', indents)

  key = __get_most_used_key(indents)

  if key is None:
    return None

  return (int(key[1:]), ' ' if key[0] == 's' else '\t')


if __name__ == '__main__':
  logging.getLogger('').setLevel(logging.DEBUG)

  with open(sys.argv[1], 'r', encoding='utf-8') as f:
    print(detect_indent(f))
