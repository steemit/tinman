from simple_steem_client.serializer.operation_variants import operation_variants

import math
import time
import datetime
import calendar
import types
import re

NIF_FLOAT_64 = 0xfff0000000000000
INF_FLOAT_64 = 0x7ff0000000000000
NAN_FLOAT_64 = 0x7ff8000000000000

UINT8_MAX    = 0xFF
UINT16_MAX   = 0xFFFF
UINT32_MAX   = 0xFFFFFFFF
UINT64_MAX   = 0xFFFFFFFFFFFFFFFF

BINARY64_RANGE = 2**53

class ArgumentError(Exception):
    pass

def twos(v, width):
  """Converts an integer into its representation in twos' complement.

  Args:
    v (int): The number to convert.
    width (int): The alignment of the integer. 1=8-bit, 2=16-bit, and so on.

  Returns:
    int: The two's complement of v.
  """
  assert(width in (1,2,4,8))
  if v >= 0:
    return v

  abs_v = abs(v)
  if width == 1:
    return UINT8_MAX-abs_v+1
  elif width == 2:
    return UINT16_MAX-abs_v+1
  elif width == 4:
    return UINT32_MAX-abs_v+1
  elif width == 8:
    return UINT64_MAX-abs_v+1

class Serializer:
  """Converts dicts and objects into sequences of bytes as required by the STEEM blockchain.

  STEEM uses a custom binary serialization format. All transactions on the blockchain must
  be signed, and the signatures must be taken over the binary serialization of the transaction.

  Some properties of the serialization format:
    - All fixed-width integers and floating-point values are serialized little-endian.
    - Variable-width integers follow Google's base-128 "varint" serialization.
    - Variable-length sequences such as text strings, arrays, and maps are prefixed with a varint
      indicating their length.
  """
  def __init__(self, size=65536):
    self._data = bytearray(size)
    self._pos = 0

  def _get_prop(self, value, prop):
    if type(value) is dict:
      return value.get(prop, None)
    else:
      return getattr(value, prop, None)

  def _get_serializer_fn(self, serializer_def):
    assert(type(serializer_def) in (types.FunctionType, str, tuple))
    if type(serializer_def) is types.FunctionType:
      return lambda v: serializer_def(self, v)
    elif type(serializer_def) is str:
      return getattr(self, serializer_def)
    elif type(serializer_def) is tuple:
      return lambda v: self.fields(v, serializer_def)

  def _write_byte(self, value):
    self._data[self._pos] = value
    self._pos += 1
    return 1

  def uint8(self, value):
    return self._write_byte(value)

  def uint16(self, value):
    return self.uint8(value & 0xff) + self.uint8((value >> 8) & 0xff) 

  def uint32(self, value):
    return self.uint16(value & 0xffff) + self.uint16((value >> 16) & 0xffff) 

  def uint64(self, value):
    return self.uint32(value & 0xffffffff) + self.uint32((value >> 32) & 0xffffffff)

  def int8(self, value):
    return self.uint8(twos(value, 1))

  def int16(self, value):
    return self.uint16(twos(value, 2))

  def int32(self, value):
    return self.uint32(twos(value, 4))

  def int64(self, value):
    return self.uint64(twos(value, 8)) 

  def binary64(self, value): 
    if math.isinf(value) and value < 0:
      encoded_value = NIF_FLOAT_64
    elif math.isinf(value):
      encoded_value = INF_FLOAT_64
    elif math.isnan(value):
      encoded_value = NAN_FLOAT_64
    else:
      # frontmost bit: sign, next 11 bits: exponent, next 52 bits: mantissa
      (mantissa_frac, exponent) = math.frexp(value)
      mantissa = int(abs(mantissa_frac) * BINARY64_RANGE)
      sign = 1 if value < 0 else 0
      # convert exponent offset to IEEE-754 standard
      exponent += 1022
      encoded_value = (sign << 63) | ((exponent & 0x7ff) << 52) | (mantissa & 0xfffffffffffff)
    return self.uint64(encoded_value)

  def uvarint(self, value):
    assert(value >= 0)
    count = 0
    while value > 127:
      self._write_byte(0x80 | (value & 0x7f))
      value = value >> 7
      count += 1 
    self._write_byte(value & 0x7f)
    return count + 1

  def svarint(self, value):
    return self.uvarint((value << 1) ^ (value >> 63))

  def boolean(self, value):
    assert(value in (True, False))
    encoded_value = 1 if value is True else 0
    return self.uint8(encoded_value)

  def raw_bytes(self, value):
    l = len(value)
    self._data[self._pos:self._pos+l] = value
    self._pos += l
    return l

  def raw_string(self, value):
    return self.raw_bytes(bytes(value, "utf8"))

  def string(self, value):
    return self.uvarint(len(value)) + self.raw_string(value)

  def hex_string(self, value):
    return self.raw_bytes(bytes.fromhex(value))

  def time_point_sec(self, value):
    if type(value) is time.struct_time:
      return self.uint32(calendar.timegm(value))
    elif type(value) is datetime.datetime:
      return self.time_point_sec(value.timetuple())
    elif type(value) is str:
      return self.time_point_sec(datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S"))
    else:
      raise ArgumentError("Cannot serialize to time_point_sec")

  def array(self, value, itemtype):
    bytes_written = self.uvarint(len(value))
    item_serializer = self._get_serializer_fn(itemtype)
    for item in value:
      bytes_written += item_serializer(item)
    return bytes_written
     
  def map(self, value, keytype, valuetype):
    """Serializes an object as an FC map.
  
    value can be either a dict or a list of (key, value) 2-tuples. The latter case
    is supported in case the objects for the map are unhashable by Python.
    """
    bytes_written = self.uvarint(len(value))
    key_serializer = self._get_serializer_fn(keytype)
    value_serializer = self._get_serializer_fn(valuetype)

    if type(value) is dict:
      iterator = value.items()
    elif type(value) is list:
      iterator = value
    else:
      raise ArgumentError("'map' serializer needs either a dict or a list of 2-tuples")

    for k, v in iterator:
      bytes_written += key_serializer(k) + value_serializer(v)
    return bytes_written

  def optional(self, value, underlyingtype):
    underlying_serializer = self._get_serializer_fn(underlyingtype)
    if value is None:
      return self.uint8(0)
    else:
      return self.uint8(1) + underlying_serializer(value)

  def field(self, value, name, fieldtype):
    field_val = self._get_prop(value, name)
    return self._get_serializer_fn(fieldtype)(field_val)

  def fields(self, value, pairs):
    return sum([ self.field(value, name, fieldtype) for (name, fieldtype) in pairs ])

  def public_key(self, value):
    """Serializes a public key.

    value must be either a bytes object containing the 65 bytes of a Bitcoin-type uncompressed public key,
    including the 1-byte header, or else it must implement the `format` method, which must accept a
    keyword argument `compressed` and should return the same. (This method signature is supplied by the
    PublicKey object in the coincurve library.)
    """
    if type(value) is bytes:
      return self.raw_bytes(value[1:])
    elif hasattr(value, "format"):
      return self.raw_bytes(value.format(compressed=False)[1:])

  def static_variant(self, value, variants):
    assert(type(value) in (list, tuple))
    assert(len(value) == 2)
    assert(type(variants) in (list, tuple))
    variant_select = value[0]
    for i, (variant_name, variant_def) in enumerate(variants):
      if variant_name == variant_select:
        return self.uvarint(i) + self._get_serializer_fn(variant_def)(value[1])
    raise ArgumentError("Unknown type for static variant (selector: %s)" % (value[0],))

  def extensions(self, value, variants):
    return self.array(value, lambda s, v: s.static_variant(v, variants))

  def void(self, value):
    assert(value is None)
    return 0

  _re_amount = re.compile(r"^([0-9]{0,19})[.]([0-9]{0,19}) (STEEM|SBD|VESTS|TESTS|TBD)$")
  _allowed_symbol_prec = set([
    ("STEEM", 3),
    ("SBD", 3),
    ("VESTS", 6),
    ("TESTS", 3),
    ("TBD", 3),
    ])

  def asset(self, value):
    # new asset JSON form as list, see https://github.com/steemit/steem/issues/1937

    assert(type(value) == str)

    m = self._re_amount.match(value)
    assert(m is not None)

    lamount, ramount, symbol = m.groups()

    prec = len(ramount)
    assert( (symbol, prec) in self._allowed_symbol_prec )

    encoded_symbol = bytearray(7)
    encoded_symbol[0:len(symbol)] = symbol.encode("utf8")

    amount = int(ramount) + (10**prec) * int(lamount)

    return self.uint64( amount ) + self.uint8( prec ) + self.raw_bytes( encoded_symbol )

  def authority(self, value):
    return self.fields(value, (
      ( "weight_threshold", "uint32" ),
      ( "account_auths", lambda s, v: s.map(v, "string", "uint16") ),
      ( "key_auths", lambda s, v: s.map(v, "public_key", "uint16") )
    ))

  def beneficiary(self, value):
    return self.fields(value, (
      ( "account", "string" ),
      ( "weight", "uint16" )
    ))

  def price(self, value):
    return self.fields(value, (
      ( "base", "asset" ),
      ( "quote", "asset" )
    ))

  def signed_block_header(self, value):
    return self.fields(value, (
      ( "previous", "raw_bytes" ),
      ( "timestamp", "time_point_sec" ),
      ( "witness", "string" ),
      ( "transaction_merkle_root", "raw_bytes" ),
      ( "extensions", lambda s, v: s.array(v, "void") ),
      ( "witness_signature", "raw_bytes" )
    ))

  def chain_properties(self, value):
    return self.fields(value, (
      ( "account_creation_fee", "asset" ),
      ( "maximum_block_size", "uint32" ),
      ( "sbd_interest_rate", "uint16" )
    ))

  def operation(self, value):
    return self.static_variant(value, operation_variants)

  _transaction_fields = (
      ( "ref_block_num", "uint16" ),
      ( "ref_block_prefix", "uint32" ),
      ( "expiration", "time_point_sec" ),
      ( "operations", lambda s, v: s.array(v, "operation") ),
      ( "extensions", lambda s, v: s.array(v, "string") )
    )

  _signed_transaction_fields = _transaction_fields + (
      ( "signatures", lambda s, v: s.array(v, "hex_string") ),
    )

  def transaction(self, value):
    return self.fields(value, self._transaction_fields)

  def signed_transaction(self, value):
    return self.fields(value, self._signed_transaction_fields)

  def flush(self):
    """Returns the serializer's output and resets the serializer.
    
    This method allocates a new `bytes` object. If you wish to manage memory directly
    you may prefer `flush_into`.

    Returns:
      bytes: The output of the serializer.
    """
    result = bytes(self._data[0:self._pos])
    self._pos = 0
    return result
  
  def flush_into(self, ba, offset=0):
    """Writes the serializer's output into `ba` and resets the serializer.

    Args:
      ba (bytearray): The buffer to write the serializer's output into.
      offset (int): The offset at which to start writing into `ba`. 
    """
    ba[offset:self._pos] = self._data[out_offset:self._pos]
    self._pos = 0

