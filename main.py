import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile



DEPOT_DOWNLOADER_URL = "https://github.com/SteamRE/DepotDownloader/releases/download/DepotDownloader_{version}/DepotDownloader-{platform}-x64.zip"
DEPOT_DOWNLOADER_VERSION = "3.4.0"

LEGACY_ROR2_APP_ID = "632360"
LEGACY_ROR2_DEPOT_ID = "632361"
LEGACY_ROR2_MANIFEST_ID = "2538203695974683966"

def get_platform_name():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "linux":
        return "linux"
    else:
        return "unknown"

def install():
    depot_downloader_archive_path = tempfile.gettempdir() + "/depot_downloader" + DEPOT_DOWNLOADER_VERSION + ".zip"
    depot_downloader_path = tempfile.gettempdir() + "/depot_downloader-" + DEPOT_DOWNLOADER_VERSION

    if get_platform_name() == "windows":
        depot_downloader = depot_downloader_path + "/DepotDownloader.exe"
    elif get_platform_name() == "linux":
        depot_downloader = depot_downloader_path + "/DepotDownloader"
    else:
        quit()

    legacy_ror2_path = tempfile.gettempdir() + "/ror2-" + LEGACY_ROR2_MANIFEST_ID + "-" + LEGACY_ROR2_APP_ID

    urlretrieve(DEPOT_DOWNLOADER_URL.format(version=DEPOT_DOWNLOADER_VERSION, platform=get_platform_name()), depot_downloader_archive_path)
    with ZipFile(depot_downloader_archive_path, "r") as archive:
        archive.extractall(depot_downloader_path)

    if get_platform_name() == "linux":
        os.chmod(depot_downloader, 0o755)

    username = input("Enter account username for Steam: ")
    subprocess.run([
        depot_downloader,
        "-username", username,
        "-app", LEGACY_ROR2_APP_ID,
        "-depot", LEGACY_ROR2_DEPOT_ID,
        "-manifest", LEGACY_ROR2_MANIFEST_ID,
        "-dir", legacy_ror2_path
    ])

    ror2_executable_path = input("Enter path to Risk of Rain 2 executable: ")
    if not ror2_executable_path.endswith("Risk of Rain 2.exe"):
        quit()

    ror2_path = Path(ror2_executable_path).parent
    for item in Path(ror2_path).iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()

    shutil.copytree(legacy_ror2_path, ror2_path, dirs_exist_ok=True)



install()