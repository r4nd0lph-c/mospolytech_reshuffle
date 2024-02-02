import cv2
import numpy as np
from numpy import ndarray


class Analyzer:
    """
    ...
    """

    __A4_W = 210
    __A4_H = 297

    def __init__(self) -> None:
        pass

    def __resize(self, img: ndarray, k: float) -> ndarray:
        (h, w) = img.shape[:2]
        return cv2.resize(img, (round(w / k), round(h / k)))

    def __grayscale(self, img: ndarray) -> ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def __invert(self, img: ndarray) -> ndarray:
        return 255 - img

    def __blur(self, img: ndarray, kernel: tuple = (5, 5), sigma: float = 1) -> ndarray:
        return cv2.GaussianBlur(img, kernel, sigma)

    def __canny(self, img: ndarray, threshold1: float = 100, threshold2: float = 200) -> ndarray:
        if img.shape == 3:
            img = self.__grayscale(img)
        return cv2.Canny(self.__blur(img), threshold1, threshold2)

    def __threshold(self, img: ndarray, thresh: float = 85, maxval: float = 255) -> ndarray:
        return cv2.threshold(img, thresh, maxval, cv2.THRESH_BINARY)[1]

    def __dilate(self, img: ndarray, kernel: ndarray = np.ones((5, 5)), iterations: int = 1) -> ndarray:
        return cv2.dilate(img, kernel, iterations=iterations)

    def __erode(self, img: ndarray, kernel: ndarray = np.ones((5, 5)), iterations: int = 1) -> ndarray:
        return cv2.erode(img, kernel, iterations=iterations)

    def __restore_perspective(self, img: ndarray) -> ndarray:
        # detect edges
        restored = img.copy()
        img = self.__canny(img)
        img = self.__dilate(img, iterations=2)
        img = self.__erode(img)
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

    def __find_mask(self, img: ndarray, l_1: int = 1, l_2: int = 40) -> ndarray:
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
        mask = self.__dilate(img_h | img_v)
        # return result
        return self.__threshold(mask, maxval=255)

    def analyze(self, img: ndarray, data: dict) -> None:
        img_grayscale = self.__grayscale(img)
        img_restore_perspective = self.__restore_perspective(img_grayscale)
        img_threshold = self.__threshold(img_restore_perspective)
        img_mask = self.__find_mask(img_threshold)

        cv2.imshow("img_base", self.__resize(img=img, k=4))
        cv2.imshow("threshold_invert", self.__resize(img=self.__invert(img_threshold), k=4))
        cv2.imshow("mask", self.__resize(img=img_mask, k=4))

        cv2.imwrite("threshold.png", img_threshold)
        cv2.imwrite("mask.png", img_mask)

        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    Analyzer().analyze(img=cv2.imread("test_1.png"), data={})
