import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reshuffle.settings")

import django
django.setup()

from random import shuffle, choice, choices
from main.models import *


class UniqueKey:
    """
    ...
    """

    __BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, length: int) -> None:
        self.length = length

    def generate(self) -> str:
        return "".join(choices(self.__BASE36, k=self.length))


class DocsGenerator:
    """
    ...
    """

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
        result = {"subject": Subject.objects.get(id=self.subject).sbj_title, "parts": []}
        for part in parts:
            info = {
                "id": part.id,
                "title": str(Part.TITLES[part.title]),
                "answer_type": part.answer_type,
                "task_count": part.task_count,
                "difficulty_total": part.total_difficulty,
                "difficulty_generated": 0,
                "inst_content": part.inst_content
            }
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
            material = []
            for position in range(1, part.task_count + 1):
                tasks = Task.objects.filter(part=part, position=position, is_active=True)
                if tasks:
                    tasks_filtered = tasks.filter(difficulty=distribution[position - 1])
                    task = choice(tasks_filtered) if tasks_filtered else choice(tasks)
                    options = Option.objects.filter(task=task).order_by("?")
                    info["difficulty_generated"] += task.difficulty
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
        doc_header = DocHeader.objects.filter(is_active=True)[0].content
        unique_keys = self.__get_unique_keys(count)
        for unique_key in unique_keys:
            data = {"unique_key": unique_key, "date": self.date, "doc_header": doc_header} | self.__collect_data()
            print(f"\n{data}")


class DocsPackager:
    """
    ...
    """

    def __init__(self) -> None:
        pass


if __name__ == "__main__":
    pass
