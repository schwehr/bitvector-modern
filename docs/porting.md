# Porting Guide

The codebase has undergone a modernization and refactoring effort. As part of
this, many legacy method aliases and naming conventions from
[Avi Kak's original 3.5.0 version](https://engineering.purdue.edu/kak/dist/BitVector-3.5.0.html)
have been removed in favor of Python's standard `snake_case` conventions and
special dunder methods.

If you are migrating code that was written for the original `BitVector` 3.5.0 to
this modern fork, you will need to update your method calls.

## Breaking Changes from 3.5.0

- The methods `array.fromstring` and `array.tostring` are not supported since
  they were removed in Python 3.9 (as originally noted in the 3.5.0 release).
- The original `__add__` and `__iadd__` logic might differ slightly as it was
  updated in later versions of the original library. Ensure you test your logic
  when concatenating.

## Renamed Methods / Removed Aliases

The following aliases and camelCase methods were removed. You should update your
code to use the corresponding modern methods:

| Old Method / Alias                | New Modern Method                       |
| :-------------------------------- | :-------------------------------------- |
| `intValue()`                      | `int_val()` or `int(bv)`                |
| `isPowerOf2()`                    | `is_power_of_2()`                       |
| `isPowerOf2_sparse()`             | `is_power_of_2_sparse()`                |
| `getHexStringFromBitVector()`     | `get_bitvector_in_hex()`                |
| `getTextFromBitVector()`          | `get_bitvector_in_ascii()`              |
| `get_hex_string_from_bitvector()` | `get_bitvector_in_hex()`                |
| `get_text_from_bitvector()`       | `get_bitvector_in_ascii()`              |
| `gf_divide()`                     | `gf_divide_by_modulus()`                |
| `gen_rand_bits_for_prime()`       | `gen_random_bits()`                     |
| `setValue()`                      | `set_value()`                           |
| `write_bits_to_fileobject()`      | `write_bits_to_stream_object()`         |
| `length()`                        | `__len__()` or `len(bv)`                |
| `deep_copy()`                     | `__deepcopy__()` or `copy.deepcopy(bv)` |
