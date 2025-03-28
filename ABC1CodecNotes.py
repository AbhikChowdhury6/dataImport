# first 4B magic number
# next 4B len till next block in bytes
# start second timestamp 4B
# end second timestamp 4B
# 5b log base 2 of the update rate
# 3b data type
    # 0 int8
    # 1 int32
    # 2 int64
    # 3 float16
    # 4 float32
# 2B #of cols

# start data 
# #ofCols * full precision length

#for each diff
    # read the timedelta, scale described in the header
    # read 4 bit chunks
    # if msb = 0 then the last 3 bits is the value
    # else keep on appending the last 3 bits of each 4 bit chunk as the most significant bits
    # calc the timedelta by reading the bits as an unsigned int and multiplying by the scale and adding to the current time
    
    #for each column  
        # for ints
        # read 4 bit chunks
        # if msb = 0 then the last 2 bits is the value, bit 1 is the sign
        # else keep on appending the last 3 bits of each 4 bit chunk as the most significant bits
        # just decode the whole set of bits as a signed int and add it to the current value
        
        # for floats
        # read first 4 bits
        # 1st is continuation, 2nd is sign, 3 and 4 are the lsb of exponent
        # if cont = 1 keep on appending the last 3 bits of each 4 bit chunk as the most significant bits
        # after exponent is done reading
        # keep reading in 4 bit chinks with the 1st bit being for continuation
        # insert bits and convert to a float32 or 16 and add to the current value

# 4b padding of 0's if needed, for neatness

#32B per 1KB of len reed solomon coding bits
#4B CRC check



#usage notes
#pack blocks till their around 200kb or one second or 5 minutes
#store in files around 2MB about 10 blocks or 5 minutes