import json
from importlib_resources import files


def read_with_id(file_id):
    """
    :param file_id: the name you use to refer to your json file
    :return: the contents of the file, read as a Python object
    """
    with open(files('resources').joinpath(file_id), 'r', encoding="utf-8") as f_read:
        return json.load(f_read)


if __name__ == "__main__":
    print(read_with_id("skills.json"))
