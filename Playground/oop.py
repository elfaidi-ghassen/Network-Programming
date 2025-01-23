# __init__ is a "dundar" or "magic method"
# you can use any name, it doesn't have to be "this"
# in Python you don't need "new" keyword
# print(dir(Person))
# obj.__class__ => what class it is
# attributes not in __init__ are called class attributes
# @classmethod
# def show_class_into(cls): # and not self!

# @classmethod vs @staticmethod
# so bascially staticmethod knows nothing about the class, it doesn't get cls as a param
# use it when you find a method that doesn't need anything from the class, but
# it logically belongs to it
# classmethod takes cls as a param, so it can use the class attributes if needed



class Person:
    total = 0
    def __init__(self, name):
        self.name = name
        Person.total += 1

    def get_name(self):
        return self.name

person1 = Person("Ghassen")
print(person1.total)


# IMPORTANT
print(person1.get_name())
# this is what Python does under the hood
print(Person.get_name(person1))

name = "Mohammed"
print(name.upper())
print(str.upper(name))

print(dir(int))

class Test:
    def __init__(self):
        pass
    
    def __str__(self): # like toString in Java
        return "some string"
    
    def __len__(self): # so it works when someone uses the built-in len() function
        return 0 
    
    

# class Subclass(Superclass):
#...
# Superclass.__init__(self, ...) <=> super().__init__(...)
# class Subclass(SC1, SC2)
# sc.mro() => method resolution order

# python doesn't have protected, but in Python, you add _ before the method/attr name
# to tell devs please don't use outside the class or subclass!
## __ => private, it cannot be accessed outside

# @property decorator is nice