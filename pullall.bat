@echo off

echo Checking out master/ main, and pulling all submodules!
git submodule foreach --recursive "(git checkout master || git checkout main)

echo.
echo This is the pull part...
git submodule foreach --recursive "(git pull; echo ___^^^)
