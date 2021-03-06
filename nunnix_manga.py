from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QVariant
from PyQt5.QtQml import QQmlApplicationEngine, QQmlEngine
from requests.exceptions import ConnectionError, ReadTimeout
from PyQt5.QtGui import QGuiApplication, QIcon
from threading import Thread
from pathlib import Path
from tools import tools
from time import sleep
from scrapers import *
import scrapers
import json
import sys
import os
import re


# Manga searcher.
class Searcher(QObject):
    search_manga_data = pyqtSignal(list, str, arguments=["dataSearch", "error"])
    search_manga_controls = pyqtSignal(str, arguments=["jsonControls"])

    def __init__(self):
        QObject.__init__(self)

    # Allows change source.
    @pyqtSlot(str, str)
    def change_manga_source(self, manga_source_name, alias):
        global manga_source
        manga_source = eval(manga_source_name)  # New manga source.

        # Write the config file.
        tools.config_writer("scrapers", "current", value=manga_source_name)
        tools.config_writer("scrapers", "current_alias", value=alias)

        # Reads and sends to QML.
        config_file_read = tools.config_file()
        context.setContextProperty("configFile", config_file_read)

        self.emit_controls()

    # Search manga thread.
    @pyqtSlot(str, int)
    def search_manga(self, parameter_list, page):
        data = Thread(target=self.search_manga_thread, args=[parameter_list, page])
        data.start()

    # Download thumbnail thread.
    @pyqtSlot(str, str)
    def download_thumbnail(self, link, image_name):
        data = Thread(target=tools.download_image, args=[link, thumbnail_dir, image_name])
        data.start()

    # Allows search.
    def search_manga_thread(self, parameter_list, page):
        data = manga_source.search_manga(**json.loads(parameter_list), page=page)

        if type(data) == ConnectionError:
            self.search_manga_data.emit([], "ConnectionError")
        elif type(data) == ReadTimeout:
            self.search_manga_data.emit([], "ReadTimeout")
        elif type(data) == str:
            self.search_manga_data.emit([], data)
        else:
            data = self.check_thumbnail(data)
            self.search_manga_data.emit(data, "")

    # Emit advanced search controls.
    @pyqtSlot()
    def emit_controls(self):
        controls = manga_source.get_search_controls()
        self.search_manga_controls.emit(controls)

    # Check if the thumbnail already exists.
    def check_thumbnail(self, data):
        for thumbnail in data:
            name = re.search(r"[^/]\w+\..{3,4}$", thumbnail["thumbnail"]).group()
            if Path(thumbnail_dir + name).exists():
                thumbnail["thumbnail"] = Path(thumbnail_dir + name).as_uri()

        return data


# TODO: Parse data through Python
# Manga viewer (data)
class Viewer(QObject):
    manga_data = pyqtSignal("QVariant", "QVariant", str, str, bool, arguments=["mangaData", "source", "error", "saved"])

    def __init__(self):
        QObject.__init__(self)

    # Set manga data thread
    @pyqtSlot(str, str, str, bool)
    def set_manga_data(self, url, source, name, forced):
        data = Thread(target=self.set_manga_data_thread, args=[url, source, name, forced])
        data.start()

    @pyqtSlot(str, str, str)
    def save_manga(self, data, source, name):
        name = re.sub(windows_expr, "", name)  # Windows folders support.
        source_config_dir = Path(manga_config_dir, source, name)

        # If the manga config does not exists
        if not Path(source_config_dir).exists():
            os.makedirs(Path(source_config_dir).absolute())

        with open(str(Path(source_config_dir, name)) + ".json", "w") as config:
            json.dump(json.loads(data), config, indent=4, ensure_ascii=False)

    # Set manga data
    def set_manga_data_thread(self, url, source, name, forced):
        name = re.sub(windows_expr, "", name)

        config_manga_file = str(Path(manga_config_dir, source, name, name)) + ".json"
        data_saved = {}

        if Path(config_manga_file).exists():
            with open(config_manga_file) as f:
                data = json.load(f)
                saved = True

            if forced:
                data_saved = data
                data = manga_source.get_manga_data(url)
                saved = False
        else:
            data = manga_source.get_manga_data(url)
            saved = False

        if type(data) == ConnectionError:
            self.manga_data.emit({}, {}, "", "ConnectionError", False)
        elif type(data) == ReadTimeout:
            self.manga_data.emit({}, {}, "", "ReadTimeout", False)
        elif type(data) == str:
            self.manga_data.emit({}, {}, "", data, False)
        else:
            self.manga_data.emit(data, data_saved, manga_source.name, "", saved)

    @pyqtSlot(str, str, str)
    def delete_manga(self, source, name, chapter):
        # Windows folders support.
        chapter = re.sub(windows_expr, "", chapter)
        name = re.sub(windows_expr, "", name)

        chapter_dir = Path(downloads_dir, source, name, chapter)
        chapter_config_dir = Path(config_dir, "manga", source, name, "chapters", chapter)
        chapter_config = str(chapter_config_dir) + ".json"

        for image in os.walk(chapter_dir.absolute()):
            images_name = image[2]

            for image_name in images_name:
                image_path = Path(image[0], image_name)
                os.remove(image_path)

        if os.path.exists(chapter_config):
            os.remove(chapter_config)


# TODO: Advanced Manga reader
class Reader(QObject):
    def __init__(self):
        QObject.__init__(self)


class Library(QObject):
    set_save_manga = pyqtSignal(str, str, str, arguments=["thumbnail", "title", "link"])

    def __init__(self):
        QObject.__init__(self)

    @pyqtSlot()
    def get_saved_mangas(self):
        depth = 2

        for files in tools.walklevel(str(Path(config_dir, "manga")), depth):
            manga_config_path = Path(files[0], "".join(files[2]))

            if manga_config_path.is_file():
                with open(manga_config_path) as f:
                    file = json.load(f)
                if file["bookmarked"]:
                    self.set_save_manga.emit(file["thumbnail"], file["title"], file["link"])


class Downloader(QObject):
    set_images = pyqtSignal(str, int, int, str, int, arguments=[
        "image", "imgWidth", "imgHeight", "url", "_totalPages"])
    downloaded = pyqtSignal(str, arguments="buttonLink")
    download_progress = pyqtSignal(int, int, str, arguments=["nImages", "nDownloads", "mangaID"])

    def __init__(self):
        QObject.__init__(self)
        self.cancel_download = False
        self.pause = False

    # Set images thread
    @pyqtSlot(str, str, str, str)
    def download_manga(self, url, source, name, chapter):
        data = Thread(target=self.download_manga_thread, args=[url, source, name, chapter])
        data.start()

    # Read manga thread
    @pyqtSlot(str, str, str, str, bool)
    def read_manga(self, url, source, name, chapter, downloaded):
        data = Thread(target=self.read_manga_thread, args=[url, source, name, chapter, downloaded])
        data.start()

    @pyqtSlot()
    def cancel_manga(self):
        self.cancel_download = True

    @pyqtSlot()
    def toggle_pause(self):
        self.pause = not self.pause

    @pyqtSlot(str, str, int)
    def set_downloaded(self, name, source, n_chapter):
        name = re.sub(windows_expr, "", name)

        config_manga_file = Path(manga_config_dir, source, name, name + ".json")

        with open(config_manga_file) as config:
            read_config = json.load(config)
            read_config["chapters"]["chapter_" + str(n_chapter)]["downloaded"] = True
            read_config["chapters"]["chapter_" + str(n_chapter)]["downloading"] = False

        with open(config_manga_file, "w") as config:
            json.dump(read_config, config, indent=4, ensure_ascii=False)

    @pyqtSlot(str, str, int, bool)
    def set_queued(self, name, source, n_chapter, queued):
        name = re.sub(windows_expr, "", name)

        config_manga_file = Path(manga_config_dir, source, name, name + ".json")

        with open(config_manga_file) as config:
            read_config = json.load(config)
            read_config["chapters"]["chapter_" + str(n_chapter)]["queued"] = queued

        with open(config_manga_file, "w") as config:
            json.dump(read_config, config, indent=4, ensure_ascii=False)

    @pyqtSlot(str, str, int, bool)
    def set_downloading(self, name, source, n_chapter, downloading):
        name = re.sub(windows_expr, "", name)

        config_manga_file = Path(manga_config_dir, source, name, name + ".json")

        with open(config_manga_file) as config:
            read_config = json.load(config)
            read_config["chapters"]["chapter_" + str(n_chapter)]["downloading"] = downloading

        with open(config_manga_file, "w") as config:
            json.dump(read_config, config, indent=4, ensure_ascii=False)

    @pyqtSlot(str)
    def download_manga_thread(self, url, source, name, chapter):
        mangaID = url + source + name + chapter  # MangaID

        # Windows folders support.
        name = re.sub(windows_expr, "", name)
        chapter = re.sub(windows_expr, "", chapter)

        # Setting the image size.
        images_size = {}
        images_config_path = Path(manga_config_dir, source, name, "chapters")
        if not images_config_path.exists():
            os.makedirs(images_config_path)

        images = manga_source.get_chapters_images(url)
        chapter_dir = Path(downloads_dir, source, name, chapter)

        n_images = len(images)

        # If the chapter directory does not exists.
        if not chapter_dir.exists():
            os.makedirs(chapter_dir)

        # Iterate through images.
        for i in range(n_images):
            while self.pause:  # Sleep for 1 second while self.pause is True
                sleep(1)

            image_name = str(i) + re.search(r"\..{3,4}$", images[i]).group()
            image_config = str(Path(images_config_path, chapter)) + ".json"

            image_path = Path(chapter_dir, image_name)

            image = tools.download_image(images[i], chapter_dir, image_name)
            while not image:
                image = tools.download_image(images[i], chapter_dir, image_name)

            if self.cancel_download:
                self.cancel_download = False
                return None

            if os.path.exists(image_config):
                with open(image_config) as f:
                    config_length = len(json.load(f))
            else:
                config_length = 0

            # If the configuration image exists and it's complete.
            if os.path.exists(image_config) and images_size == {} and config_length == n_images:
                pass
            # Else, create it.
            else:
                width, height = tools.get_image_size(image_path)
                images_size[image_name] = [width, height]
                with open(image_config, "w") as f:
                    json.dump(images_size, f, indent=4)

            self.download_progress.emit(n_images, i + 1, mangaID)  # MangaID

    # Read manga
    def read_manga_thread(self, url, source, name, chapter, downloaded):
        # Windows folders support.
        name = re.sub(windows_expr, "", name)
        chapter = re.sub(windows_expr, "", chapter)

        # Setting the image size.
        images_size = {}
        images_config_path = Path(manga_config_dir, source, name, "chapters")
        image_config = str(Path(images_config_path, chapter)) + ".json"
        if not images_config_path.exists():
            os.makedirs(images_config_path)

        chapter_dir = Path(downloads_dir, source, name, chapter)

        # If the chapter is downloaded.
        if downloaded:
            images = [str(Path(chapter_dir, image)) for image in os.listdir(chapter_dir)]
            images.sort(key=lambda x: int(re.search(r"(\d+)\..{3,4}$", x).groups()[0]))

            for image in images:
                image_name = re.search(r"\w+\..{3,4}$", image).group()

                with open(image_config) as f:
                    sizes = json.load(f)
                    width, height = sizes[image_name]
                self.set_images.emit(Path(image).as_uri(), width, height, url, len(images))
        else:
            pass


config_file = tools.config_file()
scale_factor = config_file["system"]["scale_factor"]
current_scraper = config_file["scrapers"]["current"]

thumbnail_dir, cache_save_dir, downloads_dir, config_dir, manga_config_dir = tools.get_dirs()

scraper_data = {}
manga_source = getattr(__import__("scrapers"), current_scraper)

for scraper in scrapers.__all__:
    scraper_data[getattr(__import__("scrapers"), scraper).name] = scraper

windows_expr = re.compile(r"[\\/:*?\"<>|]")


os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
os.environ["QT_QUICK_CONTROLS_MATERIAL_VARIANT"] = "Dense"
os.environ["QT_SCALE_FACTOR"] = str(scale_factor)

application = QGuiApplication(sys.argv)
application.setWindowIcon(QIcon("resources/icon.png"))

manga_searcher = Searcher()
manga_viewer = Viewer()
manga_reader = Reader()
manga_library = Library()
manga_downloader = Downloader()
engine = QQmlApplicationEngine()

# Pass variables to QML
context = engine.rootContext()
context.setContextProperty("MangaSearcher", manga_searcher)
context.setContextProperty("MangaViewer", manga_viewer)
context.setContextProperty("MangaReader", manga_reader)
context.setContextProperty("MangaLibrary", manga_library)
context.setContextProperty("MangaDownloader", manga_downloader)
context.setContextProperty("configFile", config_file)
context.setContextProperty("scraperData", scraper_data)
context.setContextProperty("thumbnailDir", thumbnail_dir)
context.setContextProperty("os", sys.platform)

engine.load("gui/nunnix_manga.qml")
sys.exit(application.exec_())
