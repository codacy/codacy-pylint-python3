##Patterns: E0110

import abc

class Animal(abc.ABC):
    @abc.abstractmethod
    def make_sound(self):
        pass

##Err: E0110
sheep = Animal() 