from wsgic.handlers.files import FileSystemStorage
from pathlib import Path

appdir = FileSystemStorage(directory=str(Path(__file__).parent.absolute()))

class Dict:
    __data = {}
    __grouped = {}

    @property
    def grouped(self):
        return self.__grouped
    
    @property
    def data(self):
        return self.__data

    def get(self, name, default=None):
        if name in self.__data:
            return self.__data.get(name)
        return self.find_group(name)
    
    def set(self, name, item, group=False):
        if group:
            if group in self.__grouped:
                self.__grouped[group][name] = item
            else:
                self.__grouped[group] = {name: item}
        else:
            self.__data[name] = item
        return
    
    def get_group(self, name, default=None):
        return self.__grouped.get(name, default)
    
    def find_group(self, name):
        for item in self.__grouped:
            if name in self.__grouped[item]:
                return self.__grouped[item][name]
        return None
