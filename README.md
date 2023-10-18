# IDLEAlign
Python IDLE extension to align code by a regular expression

<!-- BADGIE TIME -->

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![code style: black](https://img.shields.io/badge/code_style-black-000000.svg)](https://github.com/psf/black)

<!-- END BADGIE TIME -->

## Installation (Without root permissions)
1) Go to terminal and install with `pip install idlealign[user]`.
2) Run command `idleuserextend; idlealign`. You should see the following
output: `Config should be good! Config should be good!`.
3) Open IDLE, go to `Options` -> `Configure IDLE` -> `Extensions`.
If everything went well, alongside `ZzDummy` there should be and
option called `idlealign`. This is where you can configure how
idlealign works.

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
