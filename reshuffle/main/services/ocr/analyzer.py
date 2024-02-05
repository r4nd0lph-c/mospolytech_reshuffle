import json
import numpy as np
from numpy import ndarray
import cv2


class Analyzer:
    """
    ...
    """

    __A4_W = 210  # scan width (mm)
    __A4_H = 297  # scan height (mm)

    __CHECKBOX_W = 20  # base checkbox width (px)
    __CHECKBOX_H = 20  # base checkbox height (px)

    __CHECKBOX_ATOL = 0.2  # checkbox aspect ratio = __CHECKBOX_W / __CHECKBOX_H +- __CHECKBOX_ATOL
    __TOLERANCE_PERCENTAGE = 0.1  # same line = line +- (__CHECKBOX_W + __CHECKBOX_H) / 2 * __TOLERANCE_PERCENTAGE

    __CHECKBOX_CORRECTION_LEN = 4  # length of one checkbox correction field

    def __init__(self) -> None:
        pass

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

    def analyze(self, img: ndarray, data: dict) -> None:
        # get stats about all rectangles
        mask = self.find_mask(img)
        _, _, stats, _ = cv2.connectedComponentsWithStats(~mask, connectivity=8, ltype=cv2.CV_32S)
        # filter stats for checkboxes only
        stats = stats[2:]
        stats = stats[np.isclose(
            stats[:, 2] / stats[:, 3],
            self.__CHECKBOX_W / self.__CHECKBOX_H,
            atol=self.__CHECKBOX_ATOL
        )]
        # calc tolerance
        _, _, w, h, _ = stats[0]
        tolerance = (w + h) / 2 * self.__TOLERANCE_PERCENTAGE
        # categorize checkboxes
        y_set = set(stats[:, 1])
        y_max = max(y_set)
        checkboxes_correction = stats[np.isclose(stats[:, 1], y_max, atol=tolerance)]
        y_set = y_set - set(checkboxes_correction[:, 1])
        y_max = max(y_set)
        checkboxes_answers = stats[stats[:, 1] <= y_max]
        # create fields_correction
        checkboxes_correction = checkboxes_correction[checkboxes_correction[:, 0].argsort()]
        fields_correction = []
        i = 0
        while i < len(checkboxes_correction):
            c = checkboxes_correction[i:i + self.__CHECKBOX_CORRECTION_LEN]
            fields_correction.append([c[0][0], min(c[:, 1]), c[3][0] + c[-1][2] - c[0][0], max(c[:, 3])])
            i += self.__CHECKBOX_CORRECTION_LEN
        # create fields_answers
        # ...

        # debug 1
        detected = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for i, (x, y, w, h) in enumerate(fields_correction):
            cv2.rectangle(detected, (x, y), (x + w, y + h), [(255, 0, 0), (0, 255, 0), (0, 0, 255)][i % 3], 5)
        cv2.imshow("detected", a.resize(img=detected, k=4))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # debug 2
        detected = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for i, (x, y, w, h, area) in enumerate(stats):
            # print(f"{(x, y), (x + w, y + h), w / h}\n")
            cv2.rectangle(detected, (x, y), (x + w, y + h), [(255, 0, 0), (0, 255, 0), (0, 0, 255)][i % 3], 5)
        cv2.imshow("detected", a.resize(img=detected, k=4))
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    img_base = cv2.imread("test_5.png")
    with open("data_it.json", "r", encoding="UTF-8") as f:
        data_base = json.load(f)
    a = Analyzer()
    img_grayscale = a.grayscale(img_base)
    img_restore_perspective = a.restore_perspective(img_grayscale)
    img_threshold = a.threshold(img_restore_perspective)
    img_mask = a.find_mask(img_threshold)

    a.analyze(img_threshold, data_base)

    # cv2.imshow("img_base", a.resize(img=img_base, k=4))
    # cv2.imshow("threshold_invert", a.resize(img=a.invert(img_threshold), k=4))
    # cv2.imshow("mask", a.resize(img=img_mask, k=4))

    cv2.imwrite("threshold.png", img_threshold)
    cv2.imwrite("mask.png", img_mask)

    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
