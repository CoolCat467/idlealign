# IDLEAlign
Python IDLE extension to align code by a regular expression

[![CI](https://github.com/CoolCat467/idlealign/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/CoolCat467/idlealign/actions/workflows/ci.yml)
<!-- BADGIE TIME -->

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

<!-- END BADGIE TIME -->

## What does this extension do?
This IDLE extension allows you to align a block of code by a regular
expression selecting the text you would like to have aligned and then
running Format -> Align Selection or `Alt+a` on default.
If `space wrap` is enabled in the dialog that appears, regular expression
match in selected text will have a single space added on both sides. If
disabled, this will not happen. This is very helpful for making large
blocks of assignment statements pretty or for making comments for
your ruff rules in pyproject.toml all match up.

## Installation (Without root permissions)
1) Go to terminal and install with `pip install idlealign[user]`.
2) Run command `idleuserextend; idlealign`. You should see the following
output: `Config should be good! Config should be good!`.
3) Open IDLE, go to `Options` -> `Configure IDLE` -> `Extensions`.
If everything went well, alongside `ZzDummy` there should be and
option called `idlealign`. This is where you can configure if
idlealign is enabled or not.

## Installation (Legacy, needs root permission)
1) Go to terminal and install with `pip install idlealign`.
2) Run command `idlealign`. You will likely see a message saying
`idlealign not in system registered extensions!`. Run the command
given to add lintcheck to your system's IDLE extension config file.
3) Again run command `idlealign`. This time, you should see the following
output: `Config should be good!`.
4) Open IDLE, go to `Options` -> `Configure IDLE` -> `Extensions`.
If everything went well, alongside `ZzDummy` there should be and
option called `idlealign`. This is where you can configure if
idlealign is enabled or not.
