---
title: Pandoc-theoremnos Demo
theoremnos-cleveref: True
theoremnos-names:
- id: thm
  name: Theorem
- id: dfn
  name: Definition
...

[]{#dfn:good}
: This is my definition of good.

[Pythagorean theorem]{#thm:pythagorean}

: For a right triangle, if $c$ denotes the length of the hypotenuse
and $a$ and $b$ denote the lengths of the other two sides, we have

$$a^2 + b^2 = c^2$$


*@thm:pythagorean is very popular and is unrelated to @dfn:good.


And this is a normal definition list:

Day
: When the sun is above the horizon.

Night
: When it is not day.
