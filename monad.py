#!/usr/bin/env python3
"""monad - Maybe, Either, and IO monads for Python."""
import sys

class Maybe:
    def __init__(self, value=None, is_nothing=False):
        self._value = value
        self._nothing = is_nothing or (value is None and not isinstance(value, int))

    @staticmethod
    def just(value):
        return Maybe(value, False)

    @staticmethod
    def nothing():
        return Maybe(is_nothing=True)

    def bind(self, fn):
        if self._nothing:
            return Maybe.nothing()
        return fn(self._value)

    def map(self, fn):
        if self._nothing:
            return Maybe.nothing()
        return Maybe.just(fn(self._value))

    def get_or(self, default):
        return default if self._nothing else self._value

    def is_nothing(self):
        return self._nothing

    def __repr__(self):
        return "Nothing" if self._nothing else f"Just({self._value!r})"

class Either:
    def __init__(self, value, is_right=True):
        self._value = value
        self._right = is_right

    @staticmethod
    def right(value):
        return Either(value, True)

    @staticmethod
    def left(value):
        return Either(value, False)

    def bind(self, fn):
        if not self._right:
            return self
        return fn(self._value)

    def map(self, fn):
        if not self._right:
            return self
        return Either.right(fn(self._value))

    def get_or(self, default):
        return self._value if self._right else default

    def is_right(self):
        return self._right

    def __repr__(self):
        return f"Right({self._value!r})" if self._right else f"Left({self._value!r})"

class IO:
    def __init__(self, effect):
        self._effect = effect

    def run(self):
        return self._effect()

    def bind(self, fn):
        return IO(lambda: fn(self._effect()).run())

    def map(self, fn):
        return IO(lambda: fn(self._effect()))

    @staticmethod
    def pure(value):
        return IO(lambda: value)

def test():
    r = Maybe.just(5).map(lambda x: x * 2).map(lambda x: x + 1)
    assert r.get_or(0) == 11
    r2 = Maybe.nothing().map(lambda x: x * 2)
    assert r2.is_nothing()
    assert r2.get_or(42) == 42
    def safe_div(x):
        return Maybe.nothing() if x == 0 else Maybe.just(10 // x)
    assert Maybe.just(2).bind(safe_div).get_or(0) == 5
    assert Maybe.just(0).bind(safe_div).is_nothing()
    r3 = Either.right(10).map(lambda x: x * 2)
    assert r3.get_or(0) == 20
    r4 = Either.left("error").map(lambda x: x * 2)
    assert r4.get_or(0) == 0
    assert not r4.is_right()
    io = IO.pure(42).map(lambda x: x + 1)
    assert io.run() == 43
    print("All tests passed!")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("monad: Maybe/Either/IO monads. Use --test")
