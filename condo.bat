@echo off

echo CONDO.bat ... getting all submodules from 'condo40', and update them

git submodule update --init --recursive condo40
git submodule foreach --recursive "(git remote -v ; git checkout master; git pull; echo ___^; echo ...)"
git submodule foreach --recursive git fetch --all
git submodule foreach git pull

rem # temp/contactos
