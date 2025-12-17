https://pyinstaller.org/en/stable/installation.html#installed-commands
pip install --upgrade pyinstaller
pyinstaller --version
import sysconfig; print(sysconfig.get_path("scripts"))
import site; print(site.USER_BASE + "\\Scripts")
C:\Users\weihc\AppData\Roaming\Python\Python313\Scripts

pip install Pillow
pip install requests
pip install pyserial

cd C:\Code\HoloCubic_AIO\AIO_Tool\
pyinstaller --icon ./image/holo_256.ico -w -F CubicAIO_Tool.py

-------------------------------------------------------

pip install virtualenv

pip install esptool
pip uninstall esptool

pip install -e c:\Code\HoloCubic_AIO\AIO_Tool\esptool_v41

-------------------------------------------------------

https://github.com/astral-sh/uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

To add C:\Users\weihc\.local\bin to your PATH, either restart your shell or run:

uv self update
uv python list

cd C:\Code\HoloCubic_AIO\AIO_Tool\
uv python pin 3.13.5
uv venv
.venv\Scripts\activate

pip install ipython
pip install -e c:\Code\HoloCubic_AIO\AIO_Tool\esptool_v41

-------------------------------------------------------

Traceback (most recent call last):
  File "CubicAIO_Tool.py", line 14, in <module>
  File "pyimod02_importers.py", line 457, in exec_module
  File "page\download_debug.py", line 33, in <module>
  File "pyimod02_importers.py", line 457, in exec_module
  File "esptool_v41\esptool\__init__.py", line 42, in <module>
ModuleNotFoundError: No module named 'esptool'
