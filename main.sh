# Clone Upstream
mkdir -p ./apx-subsystem-settings
cp -rvf ./* ./apx-subsystem-settings || echo
cd ./apx-subsystem-settings

# Get build deps
apt-get build-dep ./ -y

# Build package
dpkg-buildpackage

# Move the debs to output
cd ../
mkdir -p ./output
mv ./*.deb ./output/
