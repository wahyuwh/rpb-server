python C:\Users\toskrip\Desktop\PyInstaller-2.1\PyInstaller-2.1\pyinstaller.py -n RadPlanBio-server .\server\httpsServer.py

python C:\Users\toskrip\Desktop\PyInstaller-2.1\PyInstaller-2.1\pyinstaller.py RadPlanBio-server.spec

copy .\server\logging.ini .\dist\RadPlanBio-server\
copy .\server\radplanbio-server.cfg .\dist\RadPlanBio-server\
copy .\server\server.pem .\dist\RadPlanBio-server\