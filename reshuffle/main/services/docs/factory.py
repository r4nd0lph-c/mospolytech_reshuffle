import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reshuffle.settings")

import django
django.setup()

from random import choice, choices
from main.models import *


class UniqueKey:
    __BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, length) -> None:
        self.length = length

    def generate(self) -> str:
        return "".join(choices(self.__BASE36, k=self.length))


class DocsGenerator:
    __UNIQUE_KEY_LENGTH = 6

    def __init__(self, subject: int, date: str) -> None:
        self.subject = subject
        self.date = date

    def __get_unique_keys(self, count: int) -> set[str]:
        uk = UniqueKey(self.__UNIQUE_KEY_LENGTH)
        result = [uk.generate() for _ in range(count)]
        while len(result) != len(set(result)):
            result.append(uk.generate())
        return set(result)

    def __collect_data(self) -> dict:
        parts = Part.objects.filter(subject__id=self.subject)
        result = {
            "subject": Subject.objects.get(id=self.subject).sbj_title,
            "parts": []
        }
        for part in parts:
            info = {
                "id": part.id,
                "title": Part.TITLES[part.title],
                "answer_type": part.answer_type,
                "task_count": part.task_count,
                "total_difficulty": part.total_difficulty,
                "inst_content": part.inst_content
            }
            material = []
            for position in range(1, part.task_count + 1):
                # TODO: add difficulty sampling for tasks
                tasks = Task.objects.filter(part=part, position=position, is_active=True)
                if tasks:
                    task = choice(tasks)
                    options = Option.objects.filter(task=task).order_by("?")
                    material.append({
                        "id": task.id,
                        "position": f"{Part.TITLES[part.title]}{position}",
                        "difficulty": task.difficulty,
                        "content": task.content,
                        "options": [{"id": o.id, "content": o.content, "is_answer": o.is_answer} for o in options]
                    })
            result["parts"].append({"info": info, "material": material})
        return result

    def generate(self, count: int) -> None:
        unique_keys = self.__get_unique_keys(count)
        for unique_key in unique_keys:
            data = ({
                        "unique_key": unique_key,
                        "date": self.date,
                        "doc_header": DocHeader.objects.filter(is_active=True)[0].content
                    } | self.__collect_data())
            # print(f"\n{data}")


class DocsPackager:

    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    dg = DocsGenerator(subject=19, date="16.01.2024")
    dg.generate(1)
