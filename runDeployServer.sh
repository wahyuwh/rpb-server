# Create deployment .spec files
python ../programming/pyinstaller-2.0/pyinstaller.py --noconsole  -n RadPlanBio-server ./server/httpsServer.py

# Build distibution
../programming/pyinstaller-2.0/pyinstaller.py RadPlanBio-server.spec

# Copy configuration files
cp ./server/logging.ini ./dist/RadPlanBio-server/
cp ./server/radplanbio-server.cfg ./dist/RadPlanBio-server/
cp ./server/server.pem ./dist/RadPlanBio-server/

# Build and the DICOM correction utility for the server
python ../programming/pyinstaller-2.0/pyinstaller.py --noconsole  -n RadPlanBio-correct ./server/correct/mainCorrect.py
python ../programming/pyinstaller-2.0/pyinstaller.py RadPlanBio-correct.spec

# Copy configuration files
cp ./server/correct/logging.ini ./dist/RadPlanBio-correct/

# Add correction utility to the server
mkdir ./dist/RadPlanBio-server/correct
# Copy correction utility
cp ./server/correct/rle2img ./dist/RadPlanBio-server/correct/
cp -r ./dist/RadPlanBio-correct/* ./dist/RadPlanBio-server/correct/

# Create necessary folders
mkdir ./dist/RadPlanBio-server/temp/
mkdir ./dist/RadPlanBio-server/corrected/
mkdir ./dist/RadPlanBio-server/downloaded/
mkdir ./dist/RadPlanBio-server/unzipped/
