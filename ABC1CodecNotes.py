# first 4B magic number
# next 4B len till next block
# start second timestamp 4B
# end second timestamp 4B
# 5b log base 2 of the update rate
# 3b log base 2 of the full precision of each col
# 2B #of cols

# start data 
# #ofCols * full precision length

# start diffs
#for each diff
    # read the timedelta, scale described in the header
    # read 4 bit chunks
    # if msb = 0 then the last 3 bits is the value
    # else keep on appending the last 3 bits of each 4 bit chunk as the most significant bits
    # calc the timedelta by reading the bits as an unsigned int and multiplying by the scale
    
    #for each column
    # read 4 bit chunks
    # if msb = 0 then the last 2 bits is the value, bit 1 is the sign
    # else keep on appending the last 3 bits of each 4 bit chunk as the most significant bits
    # for ints just decode the whole set of bits as a signed int
    
    # honestly there may be more than just 1 datatype i'm interested in
    # I could just read in the sign, exponent, and fraction as seperate blocs
    # min 2 blocks if we put the sign and exponent together which should be alright
    # the real question will be encoding the number of min fractions
    # how should we decide the min fraction?
    # normally it's 2^the number of bits in the mantissa over 1
    # but the number of blocks wouldn't be very variable

    # how about we just do the exponential golomb and 
    
    # calc the delta by using
