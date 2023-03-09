#Patterns: W0199
##Warn: W0199
assert (1 == 1, 2 == 2), "no error"
##Warn: W0199
assert (1 == 1, 2 == 2)
##Warn: W0199
assert 1 == 1, "no error"
##Warn: W0199
assert (1 == 1,), "no error"
##Warn: W0199
assert (1 == 1,)
##Warn: W0199
assert (1 == 1, 2 == 2, 3 == 5), "no error"
##Warn: W0199
assert (True, 'error msg')