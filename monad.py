#!/usr/bin/env python3
"""Monads in Python — Maybe, Either, IO, State, List, Reader, Writer.

Implements monadic bind (>>=), return, map, and common transformations.
Each monad follows the three laws: left identity, right identity, associativity.

Usage: python monad.py [--test]
"""

import sys
from functools import reduce

# --- Maybe ---
class Maybe:
    def __init__(self, value, is_nothing=False):
        self._value = value
        self._nothing = is_nothing
    
    @staticmethod
    def just(x): return Maybe(x)
    
    @staticmethod
    def nothing(): return Maybe(None, True)
    
    @staticmethod
    def unit(x): return Maybe.just(x)
    
    def bind(self, f):
        if self._nothing: return Maybe.nothing()
        return f(self._value)
    
    def map(self, f):
        return self.bind(lambda x: Maybe.just(f(x)))
    
    def or_else(self, default):
        return default if self._nothing else self._value
    
    @property
    def value(self): return self._value
    @property
    def is_nothing(self): return self._nothing
    
    def __repr__(self):
        return "Nothing" if self._nothing else f"Just({self._value})"
    def __eq__(self, other):
        if not isinstance(other, Maybe): return False
        if self._nothing and other._nothing: return True
        return not self._nothing and not other._nothing and self._value == other._value

# --- Either ---
class Either:
    def __init__(self, value, is_left):
        self._value = value
        self._is_left = is_left
    
    @staticmethod
    def left(x): return Either(x, True)
    
    @staticmethod
    def right(x): return Either(x, False)
    
    @staticmethod
    def unit(x): return Either.right(x)
    
    def bind(self, f):
        if self._is_left: return self
        return f(self._value)
    
    def map(self, f):
        return self.bind(lambda x: Either.right(f(x)))
    
    def map_left(self, f):
        if self._is_left: return Either.left(f(self._value))
        return self
    
    @property
    def value(self): return self._value
    @property
    def is_left(self): return self._is_left
    
    def __repr__(self):
        return f"Left({self._value})" if self._is_left else f"Right({self._value})"
    def __eq__(self, other):
        return isinstance(other, Either) and self._is_left == other._is_left and self._value == other._value

# --- List Monad ---
class ListM:
    def __init__(self, values):
        self._values = list(values)
    
    @staticmethod
    def unit(x): return ListM([x])
    
    def bind(self, f):
        results = []
        for v in self._values:
            results.extend(f(v)._values)
        return ListM(results)
    
    def map(self, f):
        return ListM([f(v) for v in self._values])
    
    @property
    def values(self): return self._values
    
    def __repr__(self): return f"ListM({self._values})"
    def __eq__(self, other):
        return isinstance(other, ListM) and self._values == other._values

# --- State Monad ---
class State:
    def __init__(self, run_fn):
        self._run = run_fn  # state -> (value, new_state)
    
    @staticmethod
    def unit(x): return State(lambda s: (x, s))
    
    def bind(self, f):
        def run(s):
            val, s2 = self._run(s)
            return f(val)._run(s2)
        return State(run)
    
    def map(self, f):
        return self.bind(lambda x: State.unit(f(x)))
    
    def run(self, initial_state):
        return self._run(initial_state)
    
    @staticmethod
    def get(): return State(lambda s: (s, s))
    
    @staticmethod
    def put(s): return State(lambda _: (None, s))
    
    @staticmethod
    def modify(f): return State(lambda s: (None, f(s)))

# --- Reader Monad ---
class Reader:
    def __init__(self, run_fn):
        self._run = run_fn  # env -> value
    
    @staticmethod
    def unit(x): return Reader(lambda _: x)
    
    def bind(self, f):
        return Reader(lambda env: f(self._run(env))._run(env))
    
    def map(self, f):
        return Reader(lambda env: f(self._run(env)))
    
    def run(self, env):
        return self._run(env)
    
    @staticmethod
    def ask(): return Reader(lambda env: env)

# --- Writer Monad ---
class Writer:
    def __init__(self, value, log=None):
        self._value = value
        self._log = log or []
    
    @staticmethod
    def unit(x): return Writer(x, [])
    
    def bind(self, f):
        result = f(self._value)
        return Writer(result._value, self._log + result._log)
    
    def map(self, f):
        return Writer(f(self._value), self._log)
    
    @staticmethod
    def tell(msg): return Writer(None, [msg])
    
    @property
    def value(self): return self._value
    @property
    def log(self): return self._log

# --- IO Monad (simulated) ---
class IO:
    def __init__(self, effect_fn):
        self._effect = effect_fn  # () -> value
    
    @staticmethod
    def unit(x): return IO(lambda: x)
    
    def bind(self, f):
        def run():
            val = self._effect()
            return f(val)._effect()
        return IO(run)
    
    def map(self, f):
        return IO(lambda: f(self._effect()))
    
    def run(self):
        return self._effect()

# --- Utility ---
def chain(*monadic_fns):
    """Chain monadic functions: f >>= g >>= h."""
    def compose(m, f):
        return m.bind(f)
    return lambda m: reduce(compose, monadic_fns, m)

# --- Tests ---

def test_maybe_laws():
    f = lambda x: Maybe.just(x + 1)
    g = lambda x: Maybe.just(x * 2)
    # Left identity: unit(a) >>= f == f(a)
    assert Maybe.unit(5).bind(f) == f(5)
    # Right identity: m >>= unit == m
    m = Maybe.just(5)
    assert m.bind(Maybe.unit) == m
    # Associativity: (m >>= f) >>= g == m >>= (x -> f(x) >>= g)
    assert m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))

def test_maybe_nothing():
    assert Maybe.nothing().bind(lambda x: Maybe.just(x + 1)) == Maybe.nothing()
    assert Maybe.just(5).map(lambda x: x * 2) == Maybe.just(10)
    assert Maybe.nothing().or_else(0) == 0
    assert Maybe.just(42).or_else(0) == 42

def test_either():
    assert Either.right(5).map(lambda x: x + 1) == Either.right(6)
    assert Either.left("err").map(lambda x: x + 1) == Either.left("err")
    
    def safe_div(a, b):
        return Either.left("div/0") if b == 0 else Either.right(a / b)
    assert safe_div(10, 2) == Either.right(5.0)
    assert safe_div(10, 0).is_left

def test_list_monad():
    m = ListM([1, 2, 3])
    assert m.bind(lambda x: ListM([x, x*10])) == ListM([1, 10, 2, 20, 3, 30])
    # Left identity
    assert ListM.unit(5).bind(lambda x: ListM([x, x+1])) == ListM([5, 6])

def test_state_monad():
    # Counter
    inc = State.modify(lambda s: s + 1).bind(lambda _: State.get())
    val, state = inc.run(0)
    assert state == 1
    
    # Chained state
    prog = State.get().bind(lambda x: State.put(x + 10).bind(lambda _: State.get()))
    val, state = prog.run(5)
    assert val == 15

def test_reader():
    # Dependency injection
    get_name = Reader.ask().map(lambda env: env["name"])
    greeting = get_name.map(lambda n: f"Hello, {n}!")
    assert greeting.run({"name": "World"}) == "Hello, World!"

def test_writer():
    def logged_add(x):
        return Writer(x + 1, [f"added 1 to {x}"])
    
    result = Writer.unit(0).bind(logged_add).bind(logged_add).bind(logged_add)
    assert result.value == 3
    assert len(result.log) == 3

def test_io():
    captured = []
    io = IO(lambda: 42).map(lambda x: x + 1).bind(lambda x: IO(lambda: captured.append(x) or x))
    result = io.run()
    assert result == 43
    assert captured == [43]

def test_chain():
    f = lambda x: Maybe.just(x + 1)
    g = lambda x: Maybe.just(x * 2)
    chained = chain(f, g)
    assert chained(Maybe.just(5)) == Maybe.just(12)

if __name__ == "__main__":
    if "--test" in sys.argv or len(sys.argv) == 1:
        test_maybe_laws()
        test_maybe_nothing()
        test_either()
        test_list_monad()
        test_state_monad()
        test_reader()
        test_writer()
        test_io()
        test_chain()
        print("All tests passed!")
