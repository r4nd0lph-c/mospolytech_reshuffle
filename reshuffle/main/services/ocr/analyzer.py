import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reshuffle.settings")
import django

django.setup()

import json
import re
from math import ceil
import numpy as np
from numpy import ndarray
import cv2
import easyocr
from main.models import Part
from main.services.docs.factory import UniqueKey


class Analyzer:
    """
    ...
    """

    __A4_W = 210  # scan width (mm)
    __A4_H = 297  # scan height (mm)

    __A4_W_CELL = 38  # scan width (cell)
    __A4_H_CELL = 71  # scan height (cell) (!) cells have different height (px)

    __UNIQUE_KEY_SIMILAR_BOXES_N = 3  # amount of boxes that looks like box for variant unique key

    __CHECKBOX_W = 20  # base checkbox width (px)
    __CHECKBOX_H = 20  # base checkbox height (px)
    __CHECKBOX_ATOL = 0.2  # checkbox aspect ratio = __CHECKBOX_W / __CHECKBOX_H +- __CHECKBOX_ATOL

    __TOLERANCE_PERCENTAGE = 0.1  # same line = line +- (__CHECKBOX_W + __CHECKBOX_H) / 2 * __TOLERANCE_PERCENTAGE
    __FILLED_PERCENTAGE = 0.3  # if filled area / total area >= __FILLED_PERCENTAGE -> checkbox is marked

    __CHECKBOX_CORRECTION_N = 28  # count of checkboxes correction field
    __CHECKBOX_CORRECTION_LEN = 4  # length of one checkbox correction field

    __TYPE_0_ANSWERS_N = 4  # amount of answers for task with answer_type = 0

    __TYPE_1_ANSWERS_N = 2  # amount of answers for tasks with answer_type = 1 per one line
    __TYPE_1_ANSWERS_LEN = 13  # max length of answers for task with answer_type = 1

    def __init__(self) -> None:
        self.__reader = easyocr.Reader(["en", "ru"])

    def resize(self, img: ndarray, k: float) -> ndarray:
        (h, w) = img.shape[:2]
        return cv2.resize(img, (round(w * k), round(h * k)))

    def invert(self, img: ndarray) -> ndarray:
        return 255 - img

    def grayscale(self, img: ndarray) -> ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def blur(self, img: ndarray, kernel: tuple = (5, 5), sigma: float = 1) -> ndarray:
        return cv2.GaussianBlur(img, kernel, sigma)

    def canny(self, img: ndarray, threshold1: float = 100, threshold2: float = 200) -> ndarray:
        if img.shape == 3:
            img = self.grayscale(img)
        return cv2.Canny(self.blur(img), threshold1, threshold2)

    def threshold(self, img: ndarray, thresh: float = 85, maxval: float = 255) -> ndarray:
        return cv2.threshold(img, thresh, maxval, cv2.THRESH_BINARY)[1]

    def dilate(self, img: ndarray, kernel: ndarray = np.ones((5, 5)), iterations: int = 1) -> ndarray:
        return cv2.dilate(img, kernel, iterations=iterations)

    def erode(self, img: ndarray, kernel: ndarray = np.ones((5, 5)), iterations: int = 1) -> ndarray:
        return cv2.erode(img, kernel, iterations=iterations)

    # TODO: add detection if rotate-90 / mirror is needed
    def restore_perspective(self, img: ndarray) -> ndarray:
        # detect edges
        restored = img.copy()
        img = self.canny(img)
        img = self.dilate(img, iterations=2)
        img = self.erode(img)
        # find the biggest target contour
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        target_contour = np.array([])
        max_area = 0
        for c in contours:
            area = cv2.contourArea(c)
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if area > max_area and len(approx) == 4:
                target_contour = approx
                max_area = area
        # reorder points in target contour
        target_contour = target_contour.reshape((4, 2))
        reordered_target_contour = np.zeros((4, 1, 2), dtype=np.int32)
        add = target_contour.sum(1)
        diff = np.diff(target_contour, axis=1)
        reordered_target_contour[0] = target_contour[np.argmin(add)]
        reordered_target_contour[1] = target_contour[np.argmin(diff)]
        reordered_target_contour[2] = target_contour[np.argmax(diff)]
        reordered_target_contour[3] = target_contour[np.argmax(add)]
        # prepare point for warp
        (h, w) = restored.shape[:2]
        w = round(h * self.__A4_W / self.__A4_H)
        points_1 = np.float32(reordered_target_contour)
        points_2 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        matrix = cv2.getPerspectiveTransform(points_1, points_2)
        # restore perspective
        restored = cv2.warpPerspective(restored, matrix, (w, h))
        # return result
        return restored

    def find_mask(self, img: ndarray) -> ndarray:
        # define constants
        l_1 = 1
        l_2 = round((img.shape[1] / self.__A4_W_CELL) * 0.75)
        # define vertical and horizontal kernels
        kernel_1_h = np.ones((1, l_1), np.uint8)
        kernel_1_v = np.ones((l_1, 1), np.uint8)
        kernel_2_h = np.ones((1, l_2), np.uint8)
        kernel_2_v = np.ones((l_2, 1), np.uint8)
        # detect horizontal lines
        img_h = cv2.morphologyEx(~img, cv2.MORPH_CLOSE, kernel_1_h)
        img_h = cv2.morphologyEx(img_h, cv2.MORPH_OPEN, kernel_2_h)
        # detect vertical lines
        img_v = cv2.morphologyEx(~img, cv2.MORPH_CLOSE, kernel_1_v)
        img_v = cv2.morphologyEx(img_v, cv2.MORPH_OPEN, kernel_2_v)
        # merge lines
        mask = self.dilate(img_h | img_v)
        # return result
        return self.threshold(mask, maxval=255)

    def calc_stats(self, img: ndarray) -> ndarray:
        mask = self.find_mask(img)
        _, _, stats, _ = cv2.connectedComponentsWithStats(~mask, connectivity=8, ltype=cv2.CV_32S)
        return stats

    def recognize(self, img: ndarray, box: ndarray | list, m: int = 0, allowlist: str = None) -> str:
        x, y, w, h, _ = box
        result = self.__reader.readtext(img[y - m:y + h + m, x - m:x + w + m], detail=0, allowlist=allowlist)
        return " ".join(result)

    def check_mark(self, img: ndarray, box: ndarray, m: int = 0) -> bool:
        x, y, w, h, area = box
        check_area = img[y - m:y + h + m, x - m:x + w + m]
        check_area = self.invert(check_area)
        enhanced = self.dilate(check_area, iterations=2)
        filled = cv2.countNonZero(enhanced)
        return filled / area >= self.__FILLED_PERCENTAGE

    def get_unique_key(self, img: ndarray, stats: ndarray, data: dict) -> str | None:
        # calc w_max & tolerance
        stats = stats[2:]
        w_max = max(stats[:, 2])
        tolerance = w_max / self.__A4_W_CELL
        # get all wide boxes
        stats = stats[np.isclose(stats[:, 2], w_max, atol=tolerance)]
        # exclude boxes with large deviation
        stats = stats[stats[:, 2] / stats[:, 3] < w_max / 2]
        # sort by w / h and get only __UNIQUE_KEY_BOXES_N count
        stats = stats[(stats[:, 2] / stats[:, 3]).argsort()[::-1]][:self.__UNIQUE_KEY_SIMILAR_BOXES_N]
        # sort by y-axis and get first
        box = stats[stats[:, 1].argsort()][0]
        # detect text
        x, y, w, h, _ = box
        unique_key = self.recognize(img=img, box=box, allowlist=UniqueKey.BASE)
        unique_key = unique_key.split(" ")[-1].strip()
        # check if detected text in data["variants"] & return result
        if unique_key in [item["unique_key"] for item in data["variants"]]:
            return unique_key
        return None

    def get_fields(self, img: ndarray, stats: ndarray, variant: dict) -> tuple[dict, ndarray]:
        # filter stats for checkboxes only
        stats = stats[2:]
        stats = stats[np.isclose(
            stats[:, 2] / stats[:, 3], self.__CHECKBOX_W / self.__CHECKBOX_H, atol=self.__CHECKBOX_ATOL
        )]
        # calc tolerance
        _, _, w, h, _ = stats[0]
        tolerance = round((w + h) / 2 * self.__TOLERANCE_PERCENTAGE)
        # categorize checkboxes
        y_set = set(stats[:, 1])
        y_max = max(y_set)
        checkboxes_correction = stats[np.isclose(stats[:, 1], y_max, atol=tolerance)]
        y_set = y_set - set(checkboxes_correction[:, 1])
        y_max = max(y_set)
        checkboxes_answers = stats[stats[:, 1] <= y_max]
        # create fields_correction [ndarray]
        checkboxes_correction = checkboxes_correction[checkboxes_correction[:, 0].argsort()]
        checkboxes_correction[:, 3] = max(checkboxes_correction[:, 3])
        checkboxes_correction = checkboxes_correction.reshape(
            (self.__CHECKBOX_CORRECTION_N // self.__CHECKBOX_CORRECTION_LEN, self.__CHECKBOX_CORRECTION_LEN, 5)
        )
        fields_correction = np.empty(
            (self.__CHECKBOX_CORRECTION_N // self.__CHECKBOX_CORRECTION_LEN,),
            dtype=f"<U{self.__CHECKBOX_CORRECTION_LEN}"
        )
        m = 1
        allowlist = "0123456789" + "".join([str(t) for t in list(Part.TITLES.values())])
        for i, box in enumerate(checkboxes_correction):
            cut_area = np.concatenate(
                [img[y - m:y + h + m, x - m:x + w + m] for (x, y, w, h, _) in box], axis=1
            )
            fields_correction[i] = self.recognize(
                img=cut_area, box=[0, 0, cut_area.shape[1], cut_area.shape[0], _], allowlist=allowlist
            )
        # create fields_answers [dict]
        fields_answers = {}
        y_set = set(checkboxes_answers[:, 1])
        for part in variant["parts"]:
            # get part info
            title = part["info"]["title"]
            answer_type = part["info"]["answer_type"]
            task_count = part["info"]["task_count"]
            # iterate throw parts
            if answer_type == 0:
                # if tasks with answer choice [0]
                part_answers = np.full((self.__TYPE_0_ANSWERS_N, task_count), False)
                n = ceil(task_count / Part.CAPACITIES[0])
                k = -1
                for i in range(self.__TYPE_0_ANSWERS_N * n):
                    y_min = min(y_set)
                    if i % self.__TYPE_0_ANSWERS_N == 0:
                        k += 1
                    checkboxes_answers_row = checkboxes_answers[
                        np.isclose(checkboxes_answers[:, 1], y_min, atol=tolerance)
                    ]
                    checkboxes_answers_row = checkboxes_answers_row[checkboxes_answers_row[:, 0].argsort()]
                    y_set = y_set - set(checkboxes_answers_row[:, 1])
                    for j in range(len(checkboxes_answers_row)):
                        new_i = i % self.__TYPE_0_ANSWERS_N
                        new_j = j + k * Part.CAPACITIES[0]
                        part_answers[new_i][new_j] = self.check_mark(img, checkboxes_answers_row[j])
                fields_answers[title] = {"answer_type": answer_type, "material": part_answers.T}
            elif answer_type == 1:
                # if tasks with short answer writing [1]
                part_answers = np.empty((task_count,), dtype=f"<U{self.__TYPE_1_ANSWERS_LEN}")
                for i in range(ceil(task_count / self.__TYPE_1_ANSWERS_N)):
                    y_min = min(y_set)
                    checkboxes_answers_row = checkboxes_answers[
                        np.isclose(checkboxes_answers[:, 1], y_min, atol=tolerance)
                    ]
                    checkboxes_answers_row = checkboxes_answers_row[checkboxes_answers_row[:, 0].argsort()]
                    y_set = y_set - set(checkboxes_answers_row[:, 1])
                    splitted_row = checkboxes_answers_row.reshape(
                        (self.__TYPE_1_ANSWERS_N, self.__TYPE_1_ANSWERS_LEN, 5)
                    )
                    m = 1
                    for j, answer in enumerate(splitted_row):
                        answer[:, 3] = max(answer[:, 3])
                        cut_area = np.concatenate(
                            [img[y - m:y + h + m, x - m:x + w + m] for (x, y, w, h, _) in answer], axis=1
                        )
                        allowlist = ""
                        if len(part["material"]) > i * self.__TYPE_1_ANSWERS_N + j:
                            for o in part["material"][i * self.__TYPE_1_ANSWERS_N + j]["options"]:
                                clean = re.sub(
                                    re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});"), "", o["content"]
                                )
                                allowlist += "".join({*clean})
                        part_answers[i * self.__TYPE_1_ANSWERS_N + j] = self.recognize(
                            img=cut_area,
                            box=[0, 0, cut_area.shape[1], cut_area.shape[0], _],
                            allowlist=allowlist if allowlist else None
                        )
                fields_answers[title] = {"answer_type": answer_type, "material": part_answers}
        # return result
        return fields_answers, fields_correction


if __name__ == "__main__":
    img_base = cv2.imread("test_5.png")
    with open("data_it.json", "r", encoding="UTF-8") as f:
        data_base = json.load(f)
    a = Analyzer()
    img_grayscale = a.grayscale(img_base)
    img_restore_perspective = a.restore_perspective(img_grayscale)
    img_threshold = a.threshold(img_restore_perspective)
    img_mask = a.find_mask(img_threshold)

    cv2.imwrite("threshold.png", img_threshold)
    cv2.imwrite("mask.png", img_mask)

    st = a.calc_stats(img_threshold)

    uk = a.get_unique_key(img_threshold, st, data_base)
    print(uk)
    if not uk:
        uk = "FDOMC8"  # FDOMC8 P548X0
    filtered = list(filter(lambda v: v["unique_key"] == uk, data_base["variants"]))
    v = filtered[0] if filtered else data_base["variants"][0]
    f_answers, f_correction = a.get_fields(img_threshold, st, v)
    print(f_answers, "\n", f_correction)
