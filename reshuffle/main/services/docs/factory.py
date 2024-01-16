from random import choices


class UniqueKey:
    __BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, length):
        self.length = length

    def generate(self):
        return "".join(choices(self.__BASE36, k=self.length))


class DocsGenerator:

    def __init__(self):
        pass


class DocsPackager:

    def __init__(self):
        pass


if __name__ == "__main__":
    pass
