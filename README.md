# Result.py

A Result type much like Rust's, featuring generics and lovely combinators.

## Error Handling with Result

The `Result` type is meant to be used to facilitate error handling.  This type is designed to provide as similar an interface as possible to that of [Rust's Result type](https://doc.rust-lang.org/nightly/std/result/enum.Result.html).  The motivation behind this approach is reasonably summarized by saying that the use of a Result type rather than exceptions makes it easier to reason about code, due to the complexity caused by the way that exceptions affect a program's control flow.  The Result type's methods make it easy to compose actions together.

## Representing successful and failed computations

This module exports two constructor functions for producing instances of `Result`.  The `Ok` constructor takes a single value and returns a `Result` containing that value, indicating the successful completion of a computation.  The `Err` constructor takes a single value which must be either an instance of `Exception` or a class that inherits `Exception`, such as `TypeError`, `RuntimeError`, `OSError`, etc.  Before considering subclassing `Exception` yourself, take a moment to see if there is a [built-in Exception](https://docs.python.org/3/library/exceptions.html) that meets your needs.

```python
from result import Ok, Err

successful_comp = Ok(32)
print(successful_comp.is_ok())
print(successful_comp.ok())

error_comp = Err(RuntimeError('Something bad happened.'))
print(error_comp.is_err())
print(error_comp.err())

## Output ##
# True
# 32
# True
# Something bad happened.
```

Also note that, since `Err` values are literally just instances of exceptions, if you ever find yourself in a situation where you *need* to throw an exception, you can still do that.

```python
my_error = Err(RuntimeError('Made-up error'))
raise my_error.err()
```

## Handling Errors

As seen in the above section, `Result` provides two methods-- `result.is_ok()` and `result.is_err()`-- that we can use to determine whether a computation succeed or failed.  The `result.ok()` and `result.err()` methods are used to unwrap the underlying value in their respective cases.  Note that if `result.is_ok()` is `True` and `result.err()` is called, `None` will be returned.  The same is true when `result.is_err()` is `True` and `result.ok()` is called.

`result.ok()` and `result.err()`  enable us to unwrap values from their `Result` container to handle them explicitly.  It is important to note that unwrapping a `Result` like this makes it impossible to chain further operations on the `Result` using `Result`'s other convenient methods, so this should only be done at the time at which one is ready to consume the value of a `Result` and either handle the error or value.

The rest of this document will explore each of `Result`'s other methods, providing examples of the kind of scenarios where each should be used.  In general, since most functions are not going to want to unwrap and handle errors themselves, but rather propagate those errors until they reach a part of the program that can handle those errors, the methods discussed from here should be strongly preferred to unwrapping `Result`s.

## Result[T, E] Methods

From this point on, the type variable `T` will refer to the generic type parameter that is contained by a `Result` created by the `Ok` constructor function, and `E` wil refer to the `Exception` type parameter contained by a `Result` created by the `Err` constructor.

### result.is_ok(self) -> bool

Determines if a given `Result` represents a successful computation or not.  If the `Result` was created by calling `Ok`, this method will return `True`. Otherwise, it returns `False`.  This method should be called before unwrapping a `Result` to ensure that we'll end up dealing with the correct value.

```python
if my_result.is_ok():
    handle_ok_value(my_result.ok())
else:
    handle_err(my_result.err())
```

### result.is_err(self) -> bool

This method determines if a given `Result` represents a failed computation.  If the `Result` was created by calling `Err`, this method will return `True`. Otherwise, it returns `False`.

### result.ok(self) -> Optional[T]

Unwraps the underlying value of the `Result`, assuming it represents a successful computation.  If the `Result` represents a failed computation, `None` will be returned.  However, since `None` is a valid type for `T` to take, this method returning `None` does *not* necessarily imply that `result.is_err()` is `True`.

### result.err(self) -> Optional[E]

Unwraps the underlying error contained in a `Result`, assuming it represents a failed computation.  If this method returns `None` and your code type checks correctly, then this suggests that `result.is_ok()` is `True`, since `E` should be either `Exception` or a subclass thereof.

### result.map(self, f: Callable[[T], U]) -> Result[U, E]

Apply a function to transform the value contained by a `Result` representing a successful computation.  Its argument is a function that takes a value of type `T` and returns a new value of some type `U` (which could practically be the same as `T`).  If the result contains `Ok(value)`, the function will be applied to that underlying value, leaving us with a `Result` containing `Ok(f(value))`.  This method should be used any time we want to transform a value contained by a `Result` rather than, for example, returning that value.  Any time you might write something like the following:

```python
my_result = thing_that_might_fail()
if my_result.is_ok():
    good_value = my_result.ok()
    return Ok(transformation(good_value))
else:
    return my_result
```

you almost certainly should, instead, write:

```python
return thing_that_might_fail().map(transformation)
```

### result.map_err(self, f: Callable[[E], F]) -> Result[T, F]

Apply a function to transform the error contained by a `Result` representing a failed computation.  Its argument is a function that takes an exception instance of type `E` and returns a new exception instance of some type `F` (which could be the same as `E`).  If the result contains `Err(error)`, the function will be applied to the underlying error leaving us with a `Result` containing `Err(f(error))`.   The use case is similar to `result.map`.

A common practical example of where `result.map_err` is used is for transforming an error type in order to achieve consistency with a function's type signature.  Suppose we had two functions with the following signatures:

```python
http_post(url: str, data: Dict[str, Any]) -> Result[Response, ConnectionError]
upload_results(results: List[Dict[str, Any]]) -> Result[UploadResponse, C2Error]
```

If `upload_results` wanted to call `http_post` and return its result after converting the `Response` type into an `UploadResponse`, we would get a type error because `upload_results` expects an error type of `C2Error`, not `ConnectionError`. This issue can be remedied with a call to `result.map_err`.

```python
def upload_results(results: List[Dict[str, Any]]) -> Result[UploadResponse, C2Error]:
    return http_post(C2_ADDRESS() + '/results', {'results': results})\
        .map_err(lambda conn_err: C2Error('Failed to upload results.', cause=conn_err))\
        .map(lambda response: UploadResponse(**response.json()))
```

### result.and_then(self, f: Callable[[T], Result[U, E]]) -> Result[U, E]

Apply a function which itself returns a `Result` to the value contained in `Ok(value)`, and return a new `Result` produced by the evaluation of `f(value)`.  Whereas `result.map` is used to transform values using functions that do *not* return `Result`s (i.e. cannot fail), `result.and_then` is used to chain operations that *can* fail, negating the need to unwrap values.  Consider the following example.

```python
return detect_env_proxy(env_variable_name)\
    .and_then(lambda proxy: make_http_client(C2_ADDRESS(), proxy))\
    .and_then(lambda request_fn: cmdctrl.authenticate(request_fn, api_key, secret_key))
```

### result.or_else(self, f: Callable[[E], Result[T, F]]) -> Result[T, F]

Apply a function which itself returns a `Result` to the error contained in `Err(error)`, and return a new `Result` produced by the evaluation of `f(error)`.  Whereas `result.map_err` is used to transform values using function that do *not* return `Result`s (i.e. cannot fail), `result.or_else` is used to chain operations that *can* fail, negating the need to unwrap errors.  `result.or_else` is useful to call in cases where we want to try to recover from an error.  Consider the following example which, failing to detect a system-configured proxy, attempts to recover by detecting a usable proxy given by an environment variable.

```python
return detect_system_proxy()\
    .or_else(lambda _: detect_env_proxy(env_variable_name))\
    .and_then(lambda proxy: make_http_client(C2_ADDRES(), proxy))\
    .and_then(lambda request_fn: cmdctrl.authenticate(request_fn, api_key, secret_key))
```

Note that, because `result.or_else` calls a function to transform a contained error, it is suitable for use in cases where we only want to call a function if a former computation failed, resulting in extra work being done only if a failure occurs.

### result.conjunct(self, res: Result[U, E]) -> Result[U, E]

Since Python won't let us name methods or functions using reserved keywords, we had to forego calling this method `result.and`, the way Rust does, and instead used a shortened form of the word "conjunction", meaning effectively the same thing.  `result.conjunct` behaves similarly to how the logical operator `and` does.  Consider the following code:

```python
[1, 2, 3] and 8
# >>> 8
```

The above expression evaluates to `8` becaue Python treats both values as "truthy," and the `and` operator tests that both of its operands are truthy, evaluating to the latter of the two.  `result.conjunct` behaves in much the same way, such that

```python
first_result.conjunct(second_result)
```

returns `second_result` if `first_result` contains an `Ok` value.  Otherwise, it returns `first_result`, which will contain an `Err` error.  `result.conjunct` should be used when you want to verify that one computation succeeded and, if it did, get the result of a second computation, or else handle the first error encountered.  Suppose you were parsing some input that could parse to one of two possible abstract syntax trees, with one receiving preference over the other.  You might write the following code to handle such a situation:

```python
tree1 = parse_tree1(_input)
tree2 = parse_tree2(_input)
tree1\
    .conjunct(tree2)\
    .and_then(process_ast)
```

### result.disjunct(self, res: Result[U, E]) -> Result[U, E]

`result.disjunct` behaves very similarly to `result.conjunct` except that, instead of behaving like the logical `and` operator, it behaves like logical `or`.  In other words, much like how the following code will evaluate to the first of the two if it is "truthy" or else the second, `result.disjunct` will similarly return the first result if it contains an `Ok` value, or else the second result.

```python
None or 32
# >>> 32
```

## Useful Patterns

The `Result` type's methods lend themselves very well to a functional style of programming and, following from that, makes some pretty elegant patterns possible.

### Taking the last Ok value or first Err of a list of results

Suppose that you had a list of `Result`s and wanted to either take the last `Ok` result or the first `Err` in the list.  This would be similar to calling Python's `all` function on a list of boolean values.  You could write code such as the following to accomplish this.

```python
results = [Ok(32), Ok(101), Err(ValueError('not an int')), Ok(-2)]
last = reduce(lambda r1, r2: r2.conjunct(r2), results)
print(last.err())
# >>> not an int

results = [Ok(32), Ok(101), Ok(-2)]
last = reduce(lambda r1, r2: r1.conjunct(r2), results)
print(last.ok())
# >>> -2
```

### Taking the first Ok value of a list of results

Suppose that you had a list of `Result`s and you wanted to take the first result that has an `Ok` value in it.  This might be very similar to calling Python's `any` function on a list of boolean values.  You could write code such as the following to accomplish this.

```python
results = [Ok(32), Ok(101), Err(ValueError('not an int')), Ok(-2)]
first = reduce(lambda r1, r2: r1.disjunct(r2), results)

print(first.ok())
# >>> 32
```

### Converting a list of results to a result of a list

JavaScript's `Promise` type has a static method, `Promise.all` that takes a list of promises and returns a promise containing a list of each promise's resolved value, or an error if any of those promises reject.  We can do something similar with `Result`s, converting a list of `Result`s into a Result containing a list of `Ok` values or else the first `Err` in the list. Warning. Black magic ahead.

```python
results = [Ok(32), Ok(101), Err(ValueError('not an int')), Ok(-2)]
ls_result = reduce(lambda r1, r2: r1.and_then(lambda ls: r2.map(lambda x: ls + [x])), results, Ok([]))
print(ls_result.err())
# >>> not an int

results = [Ok(32), Ok(101), Ok(-2)]
ls_result = reduce(lambda r1, r2: r1.and_then(lambda ls: r2.map(lambda x: ls + [x])), results, Ok([]))
print(ls_result.ok())
# >>> [32, 101, -2]
```
