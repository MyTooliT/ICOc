def testRampDim(MaxValue, FirstDim, SecondDim, fRecalc):
    ramp = []

    u64Quantisation = MaxValue / (FirstDim * SecondDim - 1)
    if None != fRecalc:
        for i in range(0, FirstDim * SecondDim):
            ramp.append(fRecalc(int(u64Quantisation * i)))
    else:
        for i in range(0, FirstDim * SecondDim):
            ramp.append(int(u64Quantisation * i))
    return ramp
