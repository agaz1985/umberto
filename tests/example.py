class A:
    pass

class B(A):
    pass

class C(B):
    pass

class D(C):
    pass  # This class exceeds max depth of 3 if max_depth=3
