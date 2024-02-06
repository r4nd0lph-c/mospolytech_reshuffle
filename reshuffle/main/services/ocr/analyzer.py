import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reshuffle.settings")
import django

django.setup()

from os import path
import json
from math import ceil
import numpy as np
from numpy import ndarray
import cv2
import pytesseract
from reshuffle.settings import TESSERACT_ROOT
from main.models import Part


class Analyzer:
    """
    ...
    """

    __A4_W = 210  # scan width (mm)
    __A4_H = 297  # scan height (mm)

    __A4_W_CELL = 38  # scan width (cell)
    __A4_H_CELL = 71  # scan height (cell) (!) cells have different height (px)

    __CHECKBOX_W = 20  # base checkbox width (px)
    __CHECKBOX_H = 20  # base checkbox height (px)
    __CHECKBOX_ATOL = 0.2  # checkbox aspect ratio = __CHECKBOX_W / __CHECKBOX_H +- __CHECKBOX_ATOL

    __TOLERANCE_PERCENTAGE = 0.1  # same line = line +- (__CHECKBOX_W + __CHECKBOX_H) / 2 * __TOLERANCE_PERCENTAGE
    __FILLED_PERCENTAGE = 0.5  # if filled area / total area >= __FILLED_PERCENTAGE -> checkbox is marked

    __CHECKBOX_CORRECTION_LEN = 4  # length of one checkbox correction field

    __ANSWER_TYPE_0_ANSWERS_N = 4  # amount of answers for task with answer_type = 0
    __ANSWER_TYPE_1_ANSWERS_LEN = 13  # max length of answers for task with answer_type = 1

    __UNIQUE_KEY_BOXES_N = 3  # amount of boxes that looks like box for variant unique key

    def __init__(self) -> None:
        pytesseract.pytesseract.tesseract_cmd = path.join(TESSERACT_ROOT, "tesseract.exe")
        self.__pytesseract_config = f"--tessdata-dir '{path.join(TESSERACT_ROOT, 'tessdata')}'"

    def resize(self, img: ndarray, k: float) -> ndarray:
        (h, w) = img.shape[:2]
        return cv2.resize(img, (round(w / k), round(h / k)))

    def grayscale(self, img: ndarray) -> ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def invert(self, img: ndarray) -> ndarray:
        return 255 - img

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

    def restore_perspective(self, img: ndarray) -> ndarray:  # <-- TODO: add detection if rotate-90 / mirror is needed
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

    def find_mask(self, img: ndarray, l_1: int = 1, l_2: int = 40) -> ndarray:
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

    def check_mark(self, img: ndarray, box: ndarray, margin: int = 0) -> bool:
        x, y, w, h, area = box
        check_area = img[y - margin:y + h + margin, x - margin:x + w + margin]
        check_area = self.invert(check_area)
        enhanced = self.dilate(check_area, iterations=2)
        filled = cv2.countNonZero(enhanced)
        return filled / area >= self.__FILLED_PERCENTAGE

    def get_stats(self, img: ndarray) -> ndarray:
        mask = self.find_mask(img)
        _, _, stats, _ = cv2.connectedComponentsWithStats(~mask, connectivity=8, ltype=cv2.CV_32S)
        return stats

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
        stats = stats[(stats[:, 2] / stats[:, 3]).argsort()[::-1]][:self.__UNIQUE_KEY_BOXES_N]
        # sort by y-axis and get first
        unique_key_box = stats[stats[:, 1].argsort()][0]
        # detect text
        x, y, w, h, area = unique_key_box
        unique_key = pytesseract.image_to_string(img[y:y + h, x:x + w], config=self.__pytesseract_config, lang="eng")
        unique_key = unique_key.split(" ")[-1].strip()
        # check if detected text in data["variants"] & return result
        if unique_key in [item["unique_key"] for item in data["variants"]]:
            return unique_key
        return None

    def get_fields(self, img: ndarray, stats: ndarray, data: dict) -> None:
        # filter stats for checkboxes only
        stats = stats[2:]
        stats = stats[np.isclose(
            stats[:, 2] / stats[:, 3],
            self.__CHECKBOX_W / self.__CHECKBOX_H,
            atol=self.__CHECKBOX_ATOL
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
        # create fields_correction [list]
        checkboxes_correction = checkboxes_correction[checkboxes_correction[:, 0].argsort()]
        fields_correction = []
        i = 0
        while i < len(checkboxes_correction):
            c = checkboxes_correction[i:i + self.__CHECKBOX_CORRECTION_LEN]
            fields_correction.append([c[0][0], min(c[:, 1]), c[-1][0] + c[-1][2] - c[0][0], max(c[:, 3])])
            i += self.__CHECKBOX_CORRECTION_LEN
        # create fields_answers [dict]
        fields_answers = {}
        for part in data["variants"][0]["parts"]:
            # get part info
            title = part["info"]["title"]
            answer_type = part["info"]["answer_type"]
            task_count = part["info"]["task_count"]
            # iterate throw parts
            if answer_type == 0:
                # if tasks with answer choice [0]
                part_answers = np.full((self.__ANSWER_TYPE_0_ANSWERS_N, task_count), False)
                n = ceil(task_count / Part.CAPACITIES[0])
                y_set = set(checkboxes_answers[:, 1])
                k = -1
                for i in range(self.__ANSWER_TYPE_0_ANSWERS_N * n):
                    y_min = min(y_set)
                    if i % self.__ANSWER_TYPE_0_ANSWERS_N == 0:
                        k += 1
                    checkboxes_answers_row = checkboxes_answers[
                        np.isclose(checkboxes_answers[:, 1], y_min, atol=tolerance)
                    ]
                    for j in range(len(checkboxes_answers_row)):
                        new_i = i % self.__ANSWER_TYPE_0_ANSWERS_N
                        new_j = j + k * Part.CAPACITIES[0]
                        part_answers[new_i][new_j] = self.check_mark(img, checkboxes_answers_row[j])
                    checkboxes_answers_row = checkboxes_answers_row[checkboxes_answers_row[:, 0].argsort()]
                    y_set = y_set - set(checkboxes_answers_row[:, 1])
                fields_answers[title] = {"answer_type": answer_type, "material": part_answers.T}
            elif answer_type == 1:
                # if tasks with short answer writing [1]
                pass
        print(fields_answers)

        # debug
        detected = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for i, (x, y, w, h, area) in enumerate(stats):
            # print(f"{(x, y), (x + w, y + h), w / h}\n")
            cv2.rectangle(detected, (x, y), (x + w, y + h), [(255, 0, 0), (0, 255, 0), (0, 0, 255)][i % 3], 5)
        cv2.imshow("detected", self.resize(img=detected, k=4))
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    img_base = cv2.imread("test_1.png")
    with open("data_hs.json", "r", encoding="UTF-8") as f:
        data_base = json.load(f)
    a = Analyzer()
    img_grayscale = a.grayscale(img_base)
    img_restore_perspective = a.restore_perspective(img_grayscale)
    img_threshold = a.threshold(img_restore_perspective)
    img_mask = a.find_mask(img_threshold)

    s = a.get_stats(img_threshold)

    uk = a.get_unique_key(img_threshold, s, data_base)
    print(uk)

    # a.get_fields(img_threshold, s, data_base)

    # cv2.imshow("img_base", a.resize(img=img_base, k=4))
    # cv2.imshow("threshold_invert", a.resize(img=a.invert(img_threshold), k=4))
    # cv2.imshow("mask", a.resize(img=img_mask, k=4))

    cv2.imwrite("threshold.png", img_threshold)
    cv2.imwrite("mask.png", img_mask)

    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
