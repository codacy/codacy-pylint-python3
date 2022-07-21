##Patterns: E1003

class Animal:
    pass
class Tree:
    pass
class Cat(Animal):
    def __init__(self):
        ##Err: E1003
        super(Tree, self).__init__()  # [bad-super-call]
        super(Animal, self).__init__()