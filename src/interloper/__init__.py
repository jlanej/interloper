"""interloper: positive identification of non-human DNA in human sequencing.

A read is called foreign only when a named genome explains it better than the human genome does; an organism is
called present only when the sample's reads cover its genome; a candidate variant is called foreign only when the
reads it rests on are. Everything else is reported as what it is: human, ambiguous, or unexplained.

This version is the groundwork: the design (docs/design.md), the prior work it builds on (docs/prior-art.md), the
validation plan on public 1000 Genomes data (docs/validation.md) and a container with the tools the method needs.
The one command that does something is `interloper doctor`, which checks those tools.
"""
__version__ = "0.0.1"
