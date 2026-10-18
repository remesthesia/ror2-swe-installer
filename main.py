import os
import shutil
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib import request
from urllib.request import urlretrieve, urlopen
from zipfile import ZipFile

import vdf

BEPINEX_URL = "https://thunderstore.io/package/download/bbepis/BepInExPack/{version}/"
BEPINEX_VERSION = "5.4.2122"

DEPOT_DOWNLOADER_URL = "https://github.com/SteamRE/DepotDownloader/releases/download/DepotDownloader_{version}/DepotDownloader-{platform}-x64.zip"
DEPOT_DOWNLOADER_VERSION = "3.4.0"

ROR2_APP_ID = "632360"
ROR2_DEPOT_ID = "632361"
LEGACY_ROR2_MANIFEST_ID = "2538203695974683966"

STEAM_ROOT_PATH = Path.home().joinpath(".steam/steam").resolve()


def install_depot_downloader() -> Path:
    depot_downloader_archive_path: Path = Path(f"{tempfile.gettempdir()}/depot_downloader-{DEPOT_DOWNLOADER_VERSION}.zip")
    depot_downloader_directory_path: Path = Path(f"{tempfile.gettempdir()}/depot_downloader-{DEPOT_DOWNLOADER_VERSION}")

    depot_downloader_executable_path = ""

    if sys.platform == "win32":
        urlretrieve(DEPOT_DOWNLOADER_URL.format(version=DEPOT_DOWNLOADER_VERSION, platform="windows"), depot_downloader_archive_path)
        depot_downloader_executable_path = depot_downloader_directory_path.joinpath("DepotDownloader.exe")
    elif sys.platform == "linux":
        urlretrieve(DEPOT_DOWNLOADER_URL.format(version=DEPOT_DOWNLOADER_VERSION, platform="linux"), depot_downloader_archive_path)
        depot_downloader_executable_path = depot_downloader_directory_path.joinpath("DepotDownloader")
    else:
        quit()

    with ZipFile(depot_downloader_archive_path, "r") as archive:
        archive.extractall(depot_downloader_directory_path)

    if sys.platform == "linux":
        os.chmod(depot_downloader_executable_path, 0o755)

    return depot_downloader_executable_path


def install_legacy_ror2(depot_downloader_executable_path: Path) -> tuple[str, Path]:
    legacy_ror2_path = f"{tempfile.gettempdir()}/ror2-{ROR2_DEPOT_ID}-{LEGACY_ROR2_MANIFEST_ID}"

    steam_username = input("Enter account username for Steam: ")
    subprocess.run([
        str(depot_downloader_executable_path),
        "-username", steam_username,
        "-remember-password",
        "-app", ROR2_APP_ID,
        "-depot", ROR2_DEPOT_ID,
        "-manifest", LEGACY_ROR2_MANIFEST_ID,
        "-dir", legacy_ror2_path
    ])

    if sys.platform == "linux":
        steam_root_path = Path.home().joinpath(".steam/steam").resolve()
    if sys.platform == "windows":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software/Valve/Steam") as k:
            steam_root_path = Path(winreg.QueryValueEx(k, "SteamPath")[0])
    else:
        quit()

    with open(f"{steam_root_path}/steamapps/libraryfolders.vdf", encoding="utf-8") as f:
        libs = vdf.load(f)["libraryfolders"]

    steam_path = [Path(v["path"]) for v in libs.values()][0]

    manifest = Path(f"{steam_path}/steamapps/appmanifest_{ROR2_APP_ID}.acf")
    if manifest.exists():
        with open(manifest, encoding="utf-8") as f:
            name = vdf.load(f)["AppState"]["installdir"]
        ror2_path = steam_path.joinpath(f"steamapps/common/{name}")
    else:
        quit()

    for item in Path(ror2_path).iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()

    shutil.copytree(legacy_ror2_path, ror2_path, dirs_exist_ok=True)

    return steam_username, Path(ror2_path)

def install_bepinex(steam_username: str, ror2_path: Path) -> Path:
    temp_bepinex_path = f"{tempfile.gettempdir()}/BepInEx-{BEPINEX_VERSION}"
    req = request.Request(BEPINEX_URL.format(version=BEPINEX_VERSION), headers={"User-Agent": "ror2-swe-installer/1.0"})
    with urlopen(req) as response:
        with ZipFile(BytesIO(response.read())) as archive:
            archive.extractall(temp_bepinex_path)

    shutil.copytree(f"{temp_bepinex_path}/BepInExPack", ror2_path, dirs_exist_ok=True)

    if sys.platform == "linux":
        with open(f"{STEAM_ROOT_PATH}/config/loginusers.vdf", encoding="utf-8") as f:
            for id, info in dict(vdf.load(f)["users"]).items():
                if steam_username == info["AccountName"]:
                    steam_id = int(id) - 76561197960265728

        with open(f"{STEAM_ROOT_PATH}/userdata/{steam_id}/config/localconfig.vdf", encoding="utf-8") as f:
            data = vdf.load(f)

        node = data
        for part in ["UserLocalConfigStore", "Software", "Valve", "Steam", "apps", ROR2_APP_ID]:
            node = node[part]

        node["LaunchOptions"] = "WINEDLLOVERRIDES=\"winhttp=n,b\" %command%"

    return Path(f"{temp_bepinex_path}/BepInExPack")

def main() -> None:
    steam_username, ror2_path = install_legacy_ror2(install_depot_downloader())
    install_bepinex(steam_username, ror2_path)

if __name__ == '__main__':
    main()