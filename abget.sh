adb start-server

root=sdcard/Android/data/com.YoStarEN.AzurLane/files/AssetBundles/

adb pull --sync -a $root"dependencies" AssetBundles
adb pull --sync -a $root"painting" AssetBundles
adb pull --sync -a $root"paintingface" AssetBundles
adb pull --sync -a $root"paintings" AssetBundles
