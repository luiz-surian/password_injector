@echo off

echo Building Executable

pyinstaller --windowed --onefile ^
	--icon="dependencies\images\bradesco.ico" ^
	--add-data="dependencies\images\*;dependencies\images" ^
	--version-file="file_version_info.txt" ^
	--name=password_injector ^
	main.py

echo ..................................................

echo Script End
pause