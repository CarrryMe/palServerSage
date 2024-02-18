fileName="Saved_$(date '+%Y-%m-%d_%H.%M.%S')"
#复制原始目录
cp -r ~/Steam/steamapps/common/PalServer/Pal/Saved ~/palBack/Temp/$fileName
#删除配置文件
rm -f ~/palBack/Temp/$fileName/Config/LinuxServer/PalWorldSettings.ini
#重新给出默认配置文件
cp ~/Steam/steamapps/common/PalServer/DefaultPalWorldSettings.ini ~/palBack/Temp/$fileName/Config/LinuxServer/PalWorldSettings.ini
#进入临时文件夹并压缩至download目录下
cd ~/palBack/Temp
zip -r ~/palBack/download/$fileName.zip $fileName
#删除临时目录
rm -rf ~/palBack/Temp/$fileName
#清理一天之前的文件
find ~/palBack/download -name "Saved_*.zip" -mtime +0 -delete
