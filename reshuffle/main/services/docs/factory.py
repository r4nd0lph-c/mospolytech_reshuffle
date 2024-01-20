import os
import shutil
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reshuffle.settings")

import django
django.setup()
from reshuffle.settings import MEDIA_ROOT
from main.models import *

import json
import openpyxl
from datetime import datetime
from random import shuffle, choice, choices


class UniqueKey:
    """
    ...
    """

    __BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, length: int) -> None:
        self.length = length

    def create(self) -> str:
        return "".join(choices(self.__BASE36, k=self.length))


class GeneratorXLSX:
    """
    ...
    """

    def __init__(self) -> None:
        pass


class GeneratorDOCX:
    """
    ...
    """

    def __init__(self) -> None:
        pass


class DocumentPackager:
    """
    ...
    """

    __UNIQUE_KEY_LENGTH = 6
    __OUTPUT_PATH = os.path.join(MEDIA_ROOT, "docs")
    __OUTPUT_DATA = "data.json"

    def __init__(self, subject: int, date: str) -> None:
        self.subject = subject
        self.date = date

    def __create_folder(self) -> str:
        date = datetime.today().strftime("%d-%m-%Y_%H-%M-%S")
        folder = os.path.join(self.__OUTPUT_PATH, f"[{Subject.objects.get(id=self.subject).sbj_title}][{date}]")
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    @staticmethod
    def __archive_folder(folder: str, delete: bool = True) -> str:
        archive_format = "zip"
        shutil.make_archive(folder, archive_format, folder)
        if delete:
            shutil.rmtree(folder)
        return f"{folder}.{archive_format}"

    def __get_unique_keys(self, count: int) -> set[str]:
        uk = UniqueKey(self.__UNIQUE_KEY_LENGTH)
        result = [uk.create() for _ in range(count)]
        while len(result) != len(set(result)):
            result.append(uk.create())
        return set(result)

    def __collect_data(self) -> dict:
        # init result
        result = {"subject": Subject.objects.get(id=self.subject).sbj_title, "parts": []}
        # populate result with parts
        for part in Part.objects.filter(subject__id=self.subject):
            # create part's info
            info = {
                "id": part.id,
                "title": str(Part.TITLES[part.title]),
                "answer_type": part.answer_type,
                "task_count": part.task_count,
                "difficulty_total": part.total_difficulty,
                "difficulty_generated": 0,
                "inst_content": part.inst_content
            }
            # calculate part's difficulty distribution
            difficulties = list(DIFFICULTIES.keys())
            distribution = [choice(difficulties) for _ in range(part.task_count)]
            while sum(distribution) != part.total_difficulty:
                if sum(distribution) > part.total_difficulty:
                    i = distribution.index(choice(list(set(difficulties[1:]) & set(distribution))))
                    distribution[i] -= 1
                else:
                    i = distribution.index(choice(list(set(difficulties[:-1]) & set(distribution))))
                    distribution[i] += 1
            shuffle(distribution)
            # create part's material
            material = []
            for position in range(1, part.task_count + 1):
                tasks = Task.objects.filter(part=part, position=position, is_active=True)
                if tasks:
                    tasks_filtered = tasks.filter(difficulty=distribution[position - 1])
                    task = choice(tasks_filtered) if tasks_filtered else choice(tasks)
                    options = Option.objects.filter(task=task).order_by("?")
                    info["difficulty_generated"] += task.difficulty  # <-- update info "difficulty_generated" field
                    material.append({
                        "id": task.id,
                        "position": f"{Part.TITLES[part.title]}{position}",
                        "difficulty": task.difficulty,
                        "content": task.content,
                        "options": [{"id": o.id, "content": o.content, "is_answer": o.is_answer} for o in options]
                    })
            # add info & material to result's parts
            result["parts"].append({"info": info, "material": material})
        # return populated result
        return result

    def generate(self, count: int) -> str:
        # create output folder
        folder = self.__create_folder()
        # init JSON data
        data = {"date": self.date, "doc_header": DocHeader.objects.filter(is_active=True)[0].content, "variants": []}
        # populate JSON data
        for unique_key in self.__get_unique_keys(count):
            data["variants"].append({"unique_key": unique_key} | self.__collect_data())
        # save JSON data
        with open(os.path.join(folder, self.__OUTPUT_DATA), "w", encoding="UTF-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # archive & delete output folder
        result = self.__archive_folder(folder)
        return result


if __name__ == "__main__":
    dg = DocumentPackager(subject=19, date="20.01.2024")
    print(dg.generate(3))
