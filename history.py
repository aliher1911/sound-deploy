class History:
    def __init__(self, histfile='relocate.hist'):
        self.history = set()
        try:
            with open('relocate.hist', 'r') as source:
                for line in source:
                    self.history.add(line.strip())
            self.file = open('relocate.hist', 'a')
        except IOError:
            self.file = open('relocate.hist', 'w')

    def has(self, name):
        return name in self.history

    def remember(self, name):
        self.history.add(name)
        self.file.write(name + '\n')
        # self.file.flush()

    def close(self):
        self.file.close()

class NoHistory:
    def has(self, file):
        return False
    def remember(self, file):
        pass
    def close(self):
        pass
