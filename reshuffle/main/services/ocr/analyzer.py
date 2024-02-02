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

    def resize(self, img: ndarray, k: float) -> ndarray:
        (h, w) = img.shape[:2]
        return cv2.resize(img, (round(w / k), round(h / k)))

    def grayscale(self, img: ndarray) -> ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def blur(self, img: ndarray, kernel: tuple = (5, 5), sigma: int = 1) -> ndarray:
        return cv2.GaussianBlur(img, kernel, sigma)

    def canny(self, img: ndarray, threshold1: float = 100, threshold2: float = 200) -> ndarray:
        return cv2.Canny(self.blur(self.grayscale(img)), threshold1, threshold2)

    def dilate(self, img: ndarray, kernel: ndarray = np.ones((5, 5)), iterations: int = 1) -> ndarray:
        return cv2.dilate(img, kernel, iterations=iterations)

    def erode(self, img: ndarray, kernel: ndarray = np.ones((5, 5)), iterations: int = 1) -> ndarray:
        return cv2.erode(img, kernel, iterations=iterations)

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
        return restored


if __name__ == "__main__":
    a = Analyzer()
    img_base = cv2.imread("test_3.png")
    result = a.restore_perspective(img_base)

    cv2.imshow("img_base", a.resize(img=img_base, k=4))
    cv2.imshow("restore_perspective", a.resize(img=result, k=4))

    cv2.waitKey(0)
    cv2.destroyAllWindows()
