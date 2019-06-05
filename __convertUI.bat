@echo off

echo ##############################
echo #     Convert .ui to .py     #
echo ##############################
echo.

del graphical_interface.py

for %%f in (./*.ui) do (
	echo Converting %%~nf
	pyuic5 %%f -o %%~nf.py
	echo ------------------------------
)

echo Generating .py file
echo ------------------------------
forfiles /S /M ui_*.py /C "cmd /c type @file >> graphical_interface.tmp"
del ui_*.py
ren graphical_interface.tmp graphical_interface.py

echo Done
pause
