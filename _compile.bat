@echo off

echo Building Executable

pyinstaller --windowed --onefile ^
	--icon="dependencies\favicon.ico" ^
	--add-data="dependencies\*;dependencies" ^
	--version-file="file_version_info.txt" ^
	--name=password_injector ^
	main.py

echo ..................................................

echo Script End
pause