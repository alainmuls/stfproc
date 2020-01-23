dSigType = {
 0: 'GPS_L1-CA',
 1: 'GPS_L1-P(Y)',
 2: 'GPS_L2-P(Y)',
 3: 'GPS_L2C',
 4: 'GPS_L5',
 5: 'Reserved',
 6: 'Reserved',
 7: 'Reserved',
 8: 'GLO_L1-CA',
 9: 'GLO_L1-P',
 10: 'GLO_L2-P',
 11: 'GLO_L2-CA',
 12: 'Reserved',
 13: 'Reserved',
 14: 'Reserved',
 15: 'Reserved',
 16: 'GAL_L1A',
 17: 'GAL_L1BC',
 18: 'GAL_E6A',
 19: 'GAL_E6BC',
 20: 'GAL_E5a',
 21: 'GAL_E5b',
 22: 'GAL_E5',
 23: 'Reserved',
 24: 'GEO_L1CA',
 25: 'Reserved',
 26: 'Reserved',
 27: 'Reserved',
 28: 'Reserved',
 29: 'Reserved',
 30: 'Reserved',
 31: 'Reserved'}


dFrontEnd = {
 0: 'GPS/SBAS/Galileo L1',
 1: 'GLONASS L1',
 2: 'Galileo E6',
 3: 'GPS L2',
 4: 'GLONASS L2',
 5: 'GPS/SBAS/Galileo L5/E5a',
 6: 'Galileo E5b',
 7: 'Galileo E5 (a+b)',
 8: 'unknown am',
 9: 'unknown am'
}

dPVTErrorCode = {
    0: 'no error.',
    1: 'not enough meas',
    2: 'not enough ephem',
    3: 'DOP too large',
    4: 'squared residuals too large',
    5: 'no convergence',
    6: 'not enough measurements after outlier rejection',
    7: 'position output prohibited due to export laws',
    8: 'not enough differential corrections available',
    9: 'base station coordinates unavailable',
    127: 'PNT actively suppressed'
}


def isPowerOfTwo(n: int) -> bool:
    """
    A utility function to check whether n is power of 2 or not.
    """
    return (True if(n > 0 and ((n & (n - 1)) > 0)) else False)


def findPosition(n):
    """
    Returns position of the only set bit in 'n'
    """
    if (isPowerOfTwo(n) is True):
        return -1

    i = 1
    pos = 0

    # Iterate through bits of n till we find a set bit
    # i&n will be non-zero only when 'i' and 'n' have a set bit at same position
    while ((i & n) == 0):

        # Unset current bit and set the next bit in 'i'
        i = i << 1

        # increment position
        pos += 1

        print('i = {:d}  pos = {:d}'.format(i, pos))

    return pos


def findAllSetBits(n: int, nr1Bits: int) -> list:
    """
    Function to get location of all set bits in binary representation of positive integer n
    """
    i = 1
    pos = 0
    lstPosn = []

    while len(lstPosn) < nr1Bits:
        # check whether the LSB bit is set
        # print('... i = {:d}  pos = {:d}  n = {:d}  i&n = {:d}  2<<pos = {:d}'.format(i, pos, n, i & n, (2 << pos)))
        if n & (2 << pos):
            lstPosn.append(pos+1)
        # Unset current bit and set the next bit in 'i'
        i = i << 1
        # increment position
        pos += 1

    return lstPosn


def countSetBits(n: int) -> int:
    """
    Function to get no of set bits in binary representation of positive integer n
    """
    count = 0
    while (n):
        count += n & 1
        # print('count = {:d}  n = {:d}  n&1 = {:d}'.format(count, n, n&1))
        n >>= 1
    return count
