class Test():
    def __init__(self):
        self.a = 0

    def modify_a(self):
        self.a += 1

    def get_a(self):
        print("get_a: self.a is: "+str(self.a))

    def run(self):
        print("running")
        print("self.a is: "+str(self.a))
        self.modify_a()
        self.get_a()
