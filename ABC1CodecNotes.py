# first 4B magic number
# next 4B len till next block in bytes
# start second timestamp 4B (timestamp all data is after)
# end second timestamp 4B (timestamp all data is before)
# 2B #of cols
# 1B per col datatype
    # 0 int 8
    # 1 int 16
    # 2 int 32
    # 3 int 64
    # 4 uint 8
    # 5 unit 16
    # 6 unit 32
    # 7 unit 64
    # 8 float16
    # 9 float32
    # 10 float64
    # 11-31: any weird float formats
    
    # we'll say n = 32
    # all timestamps are in UTC and 64 bits full precision
    # n ts 2^-7 128 sec (max power of 2 seconds that is perfectly divisible into a day)
    # ... ts ....
    # n+7 ts 2^0 1hz
    # n+13 ts 2^6 64hz
    # n+27 ts 2^20 1Mhz
    # n+37 ts 2^30 1Ghz
    # n+47 ts 2^40 1Thz

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


#new datatype list
    #uint 8-64
    #int 8-64
    #unix_ts-uint
    #unix_ts-int
    #dt64[ns]-u_delay_hz_-7 to dt64[ns]-u_delay_hz_10
    #dt64[ns]-afloat
    #float16-64-bounded_float
    #float16-64-afloat

#notes on floats
# start timestamps unsigned and regular, but can get large
    # u_delay_hz_XXXX
    # fractional part in units of the estimated amount/ the rounding amount
    # cont bit, delay bit 1, delay bit 2, delay bit 3

# end timestamps
    # not in order won't compress nearly as well
    # but should still compress alright
    # honeslty let's just store the differences as normal floats or ints

# unix timestamps
    # signed or unsigned ints

# quaternions and other unit vectors
    # bounded_floats - size 8 bits initially, 4 bit after
    # fractional part based on reading the bits as a binary decimal
    # cont bit, sign_bit, d msb 1, d msb 2, d msb 3, d msb 4, d msb 5, d msb 6

# general floats
    # afloat - size 8 bits initially, 4 bit after
    # same as quats but also has a bit to signify if there is an int attached
    # cont bit, sign_bit, int bit, d msb 1, d msb 2, d msb 3, d msb 4, d msb 5
        #finish reading all the decimal
        #if the int bit was 1 now read in a u_int, normal 4 bit starter