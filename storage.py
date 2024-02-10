from os import path, makedirs


def get_workdir() -> str:
    """ Находим рабочий каталог """
    home_dir = path.expanduser("~")
    workdir = path.join(home_dir, 'Sensor_data')
    return path.normpath(workdir)


def ensure_dir_exists(dirpath: str) -> bool:
    if not path.exists(dirpath):
        try:
            makedirs(dirpath)
            return True
        except Exception as ex:
            ex_repr = str(ex)[:100].replace('\n', ' | ')
            print(f"Не удалось содать каталог {dirpath}: {ex_repr}")
            return False
    else:
        return True