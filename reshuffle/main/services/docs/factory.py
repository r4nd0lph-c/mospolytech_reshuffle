import os
import shutil

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reshuffle.settings")

import django
from django.utils.translation import gettext_lazy as _

django.setup()
from reshuffle.settings import MEDIA_ROOT
from main.models import *
from uploader import FileUploader

import json
import openpyxl
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Font
import re
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

    __BASE_PATH = os.path.join(MEDIA_ROOT, "base", "sheets.xlsx")
    __WS_NAME = "blank"

    __BORDER_THIN = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    def __init__(self, custom_base_path: str = None) -> None:
        self.__wb_path = custom_base_path if custom_base_path else self.__BASE_PATH
        self.__wb = openpyxl.load_workbook(self.__wb_path)
        self.__ws = self.__wb[self.__WS_NAME]
        self.__sample_created = False

    def get_sample_created(self) -> bool:
        return self.__sample_created

    def sample(self, sbj_title: str, date: str, doc_header: str, unique_key: str, parts: list) -> None:
        # change sample_created flag
        self.__sample_created = True
        # init labels fields
        self.__ws.title = unique_key
        self.__ws["A1"] = re.sub(re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});"), "", doc_header)
        self.__ws["A4"] = f"{sbj_title} – " + _("Entrance exams")
        self.__ws["B7"] = str(_("Full name of applicant"))
        self.__ws["B9"] = _("Personnel file") + " №"
        self.__ws["D13"] = unique_key
        self.__ws["B14"] = _("Variant") + " №"
        self.__ws["P13"] = date
        self.__ws["N14"] = str(_("Exam date"))
        self.__ws["Z14"] = str(_("Signature of applicant"))
        self.__ws["A16"] = f"{sbj_title} – " + _("Answer sheet")
        self.__ws["A18"] = _("Variant") + f" № {unique_key}"
        self.__ws["A63"] = str(_("Correcting wrong marks"))
        self.__ws["A67"] = str(_("Results"))
        self.__ws["A70"] = str(_("Total number of\ncorrectly solved problems"))
        self.__ws["T70"] = str(_("Signature of examiner"))
        # split parts for correct render
        parts_splitted = []
        for part in parts:
            while part["task_count"] // Part.CAPACITIES[part["answer_type"]] > 0:
                parts_splitted.append(part.copy())
                parts_splitted[-1]["task_count"] = Part.CAPACITIES[part["answer_type"]]
                part["task_count"] -= Part.CAPACITIES[part["answer_type"]]
            if part["task_count"]:
                parts_splitted.append(part.copy())
        # init answer sheet
        r_init, c_init = 19, 1
        accum = 0
        for count, part in enumerate(parts_splitted):
            # update accum
            if count and part["title"] == parts_splitted[count - 1]["title"]:
                accum += Part.CAPACITIES[part["answer_type"]]
            else:
                accum = 0
            # render part [type 0: 15]
            if part["answer_type"] == 0:
                # answer nums
                for i in range(4):
                    for j in (1, 33):
                        self.__ws.cell(
                            row=r_init + 3 + 2 * i,
                            column=c_init + j,
                            value=str((i + 1))
                        ).font = Font(name="Gilroy", size=8, bold=True)
                # answer titles & cells
                for i in range(part["task_count"]):
                    self.__ws.cell(
                        row=r_init + 1,
                        column=c_init + 3 + 2 * i,
                        value=f"{part['title']}{i + 1 + accum}"
                    ).font = Font(name="Gilroy", size=8, bold=True)
                    for j in range(4):
                        self.__ws.cell(
                            row=r_init + 3 + 2 * j,
                            column=c_init + 3 + 2 * i
                        ).border = self.__BORDER_THIN
            # render part [type 1: 10]
            elif part["answer_type"] == 1:
                # answer titles & cells
                for i in range(part["task_count"]):
                    self.__ws.cell(
                        row=r_init + 1 + 2 * (i // 2),
                        column=c_init + 1 + (32 * (i % 2)),
                        value=f"{part['title']}{i + 1 + accum}"
                    ).font = Font(name="Gilroy", size=8, bold=True)
                    for j in range(13):
                        self.__ws.cell(
                            row=r_init + 1 + 2 * (i // 2),
                            column=c_init + 3 + (16 * (i % 2)) + j
                        ).border = self.__BORDER_THIN
            # move render window
            r_init += 11

    def reproduce(self, unique_key: str) -> None:
        # copy sample & change title
        self.__wb.copy_worksheet(self.__ws).title = unique_key
        # change labels fields
        self.__wb[unique_key]["D13"] = unique_key
        self.__wb[unique_key]["A18"] = _("Variant") + f" № {unique_key}"

    def save(self, path: str) -> None:
        if path != self.__wb_path:
            self.__wb.save(path)
        else:
            raise ValueError(
                f"The name of the destination file ({path}) "
                f"cannot be the same as the name of the source file ({self.__wb_path})."
            )


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
    __OUTPUT_JSON = "data.json"
    __OUTPUT_XLSX = "sheets.xlsx"

    def __init__(self, sbj_id: int, date: str) -> None:
        self.__sbj_id = sbj_id
        self.__sbj_title = Subject.objects.get(id=sbj_id).sbj_title
        self.__date = date

    def __create_folder(self) -> str:
        date = datetime.today().strftime("%d-%m-%Y_%H-%M-%S")
        folder = os.path.join(self.__OUTPUT_PATH, f"[{date}][{self.__sbj_title}]")
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

    def __collect_parts(self) -> list:
        # init result
        result = []
        # populate result with parts
        for part in Part.objects.filter(subject__id=self.__sbj_id):
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
            # add part's info & material to result
            result.append({"info": info, "material": material})
        # return populated result
        return result

    def generate(self, count: int) -> str:
        # create output folder
        folder = self.__create_folder()
        # init [JSON | XLSX]
        data = {
            "subject": self.__sbj_title,
            "date": self.__date,
            "doc_header": DocHeader.objects.filter(is_active=True)[0].content,
            "variants": []
        }
        gen_xlsx = GeneratorXLSX()
        # populate [JSON | XLSX]
        for unique_key in self.__get_unique_keys(count):
            data["variants"].append({"unique_key": unique_key, "parts": self.__collect_parts()})
            if not gen_xlsx.get_sample_created():
                gen_xlsx.sample(
                    data["subject"],
                    data["date"],
                    data["doc_header"],
                    unique_key,
                    [{
                        "title": p["info"]["title"],
                        "answer_type": p["info"]["answer_type"],
                        "task_count": p["info"]["task_count"]
                    } for p in data["variants"][0]["parts"]]
                )
            else:
                gen_xlsx.reproduce(unique_key)
        # save [JSON | XLSX]
        with open(os.path.join(folder, self.__OUTPUT_JSON), "w", encoding="UTF-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        gen_xlsx.save(os.path.join(folder, self.__OUTPUT_XLSX))
        # archive & delete output folder
        result = self.__archive_folder(folder)
        return result


if __name__ == "__main__":
    dg = DocumentPackager(sbj_id=3, date="20.01.2024")
    file_path = dg.generate(3)
    print(file_path)
    fu = FileUploader()
    fu.upload(file_path.split("\\")[-1], file_path)
