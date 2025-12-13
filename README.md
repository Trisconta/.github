# Trisconta
All your accounts into one.

## Introduction
This is located at github [(here)](https://github.com/Trisconta/.github)
+ To checkout, do:
  * `git clone git@github.com:Trisconta/.github.git`
  * ...or, as read-only: `https://github.com/Trisconta/.github.git`

+ To update submodules, except a few ones we do not care:
  * Linux:
    1. `git submodule update --init --recursive $(git config --file .gitmodules --get-regexp path | awk '{print $2}' | grep -v -E 'ext/cpython|deep/diplomacy')`
  * Windows:
    1. `git submodule update --init --recursive condo40`, and for each submodule.
    1. Or, recurse all and then:
       + `git submodule deinit -f ext/cpython`

## Purpose
...

## Credits
- [markdown](https://daringfireball.net/projects/markdown/syntax)

* * *
