// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © KINSKI

//@version=5
indicator('KINSKI Volume Regression Trend', shorttitle='Volume Regression Trend', timeframe='', overlay=false)



//************  Colors
color colorUpTrendStrong = #00FF11
color colorUpTrend = #00ab0b
color colorUpTrendWeak = #007a08

color colorDownTrendStrong = #FF0004
color colorDownTrend = #a30002
color colorDownTrendWeak = #750001

color colorTrendNeutral = color.gray

color valColorsBearColor = color.red
color valColorsBullColor = color.green

color valColorsTextColor = color.white
color valColorsNaColor = color.new(color.white, 100)



//********** Functions
// Calculate Buy/Sell Volume
_funcRate(_cond, _cwT, _cwB, _cwBody) =>
    _tmp = 0.5 * (_cwT + _cwB + (_cond ? 2 * _cwBody : 0)) / (_cwT + _cwB + _cwBody)
    _tmp := na(_tmp) ? 0.5 : _tmp
    _tmp

// Calculate Regression Slope for Buy/Sell Volumes
_funcTrend(_len, _cwT, _cwB, _cwBody) =>
    _tmpUp = volume * _funcRate(open <= close, _cwT, _cwB, _cwBody)
    _tmpDown = volume * _funcRate(open > close, _cwT, _cwB, _cwBody)

    volumeUp = ta.linreg(_tmpUp, _len, 0) - ta.linreg(_tmpUp, _len, 1)
    volumeDown = ta.linreg(_tmpDown, _len, 0) - ta.linreg(_tmpDown, _len, 1)
    [volumeUp, volumeDown]

// Smoothed Moving Average (SMMA)
_funcSMMA(_src, _len) =>
    tmpSMA = ta.sma(_src, _len)
    tmpVal = 0.0
    tmpVal := na(tmpVal[1]) ? tmpSMA : (tmpVal[1] * (_len - 1) + _src) / _len
    return_1 = tmpVal
    return_1

// Triple EMA (TEMA)
_funcTEMA(_src, _len) =>
    ema1 = ta.ema(_src, _len)
    ema2 = ta.ema(ema1, _len)
    ema3 = ta.ema(ema2, _len)
    return_1 = 3 * (ema1 - ema2) + ema3
    return_1

// Double Expotential Moving Average (DEMA)
_funcDEMA(_src, _len) =>
    return_2 = 2 * ta.ema(_src, _len) - ta.ema(ta.ema(_src, _len), _len)
    return_2

// Hull Moving Average (HMA)
_funcHMA(_src, _len) =>
    tmpVal = math.max(2, _len)
    return_3 = ta.wma(2 * ta.wma(_src, tmpVal / 2) - ta.wma(_src, tmpVal), math.round(math.sqrt(tmpVal)))
    return_3

// Exponential Hull Moving Average (EHMA)
_funcEHMA(_src, _len) =>
    tmpVal = math.max(2, _len)
    return_4 = ta.ema(2 * ta.ema(_src, tmpVal / 2) - ta.ema(_src, tmpVal), math.round(math.sqrt(tmpVal)))
    return_4

// Kaufman's Adaptive Moving Average (KAMA)
_funcKAMA(_src, _len) =>
    tmpVal = 0.0
    sum_1 = math.sum(math.abs(_src - _src[1]), _len)
    sum_2 = math.sum(math.abs(_src - _src[1]), _len)
    tmpVal := nz(tmpVal[1]) + math.pow((sum_1 != 0 ? math.abs(_src - _src[_len]) / sum_2 : 0) * (0.666 - 0.0645) + 0.0645, 2) * (_src - nz(tmpVal[1]))
    return_5 = tmpVal
    return_5

// Variable Index Dynamic Average (VIDYA)
_funcVIDYA(_src, _len) =>
    _diff = ta.change(_src)
    _uppperSum = math.sum(_diff > 0 ? math.abs(_diff) : 0, _len)
    _lowerSum = math.sum(_diff < 0 ? math.abs(_diff) : 0, _len)
    _chandeMomentumOscillator = (_uppperSum - _lowerSum) / (_uppperSum + _lowerSum)
    _factor = 2 / (_len + 1)
    tmpVal = 0.0
    tmpVal := _src * _factor * math.abs(_chandeMomentumOscillator) + nz(tmpVal[1]) * (1 - _factor * math.abs(_chandeMomentumOscillator))
    return_6 = tmpVal
    return_6

// Coefficient of Variation Weighted Moving Average (COVWMA)
_funcCOVWMA(_src, _len) =>
    _coefficientOfVariation = ta.stdev(_src, _len) / ta.sma(_src, _len)
    _cw = _src * _coefficientOfVariation
    tmpVal = math.sum(_cw, _len) / math.sum(_coefficientOfVariation, _len)
    return_7 = tmpVal
    return_7

// Fractal Adaptive Moving Average (FRAMA)
_funcFRAMA(_src, _len) =>
    _coefficient = -4.6
    _n3 = (ta.highest(high, _len) - ta.lowest(low, _len)) / _len
    _hd2 = ta.highest(high, _len / 2)
    _ld2 = ta.lowest(low, _len / 2)
    _n2 = (_hd2 - _ld2) / (_len / 2)
    _n1 = (_hd2[_len / 2] - _ld2[_len / 2]) / (_len / 2)
    _dim = _n1 > 0 and _n2 > 0 and _n3 > 0 ? (math.log(_n1 + _n2) - math.log(_n3)) / math.log(2) : 0
    _alpha = math.exp(_coefficient * (_dim - 1))
    _sc = _alpha < 0.01 ? 0.01 : _alpha > 1 ? 1 : _alpha
    tmpVal = _src
    tmpVal := ta.cum(1) <= 2 * _len ? _src : _src * _sc + nz(tmpVal[1]) * (1 - _sc)
    return_8 = tmpVal
    return_8

// Karobein
_funcKarobein(_src, _len) =>
    tmpMA = ta.ema(_src, _len)
    tmpUpper  = ta.ema(tmpMA < tmpMA[1] ? tmpMA/tmpMA[1] : 0, _len)
    tmpLower  = ta.ema(tmpMA > tmpMA[1] ? tmpMA/tmpMA[1] : 0, _len)
    tmpRescaleResult  = (tmpMA/tmpMA[1]) / (tmpMA/tmpMA[1] + tmpLower)
    (2*((tmpMA/tmpMA[1]) / (tmpMA/tmpMA[1] + tmpRescaleResult * tmpUpper)) - 1) * 100

// RSX based Noise Remover based Noise Remover
_funcRemoveNoise(_src, _len) =>
    f8 = 100 * _src
    f10 = nz(f8[1])
    v8 = f8 - f10

    f18 = 3 / (_len + 2)
    f20 = 1 - f18

    f28 = 0.0
    f28 := f20 * nz(f28[1]) + f18 * v8

    f30 = 0.0
    f30 := f18 * f28 + f20 * nz(f30[1])
    vC = f28 * 1.5 - f30 * 0.5

    f38 = 0.0
    f38 := f20 * nz(f38[1]) + f18 * vC

    f40 = 0.0
    f40 := f18 * f38 + f20 * nz(f40[1])
    v10 = f38 * 1.5 - f40 * 0.5

    f48 = 0.0
    f48 := f20 * nz(f48[1]) + f18 * v10

    f50 = 0.0
    f50 := f18 * f48 + f20 * nz(f50[1])
    v14 = f48 * 1.5 - f50 * 0.5

    f58 = 0.0
    f58 := f20 * nz(f58[1]) + f18 * math.abs(v8)

    f60 = 0.0
    f60 := f18 * f58 + f20 * nz(f60[1])
    v18 = f58 * 1.5 - f60 * 0.5

    f68 = 0.0
    f68 := f20 * nz(f68[1]) + f18 * v18

    f70 = 0.0
    f70 := f18 * f68 + f20 * nz(f70[1])
    v1C = f68 * 1.5 - f70 * 0.5

    f78 = 0.0
    f78 := f20 * nz(f78[1]) + f18 * v1C

    f80 = 0.0
    f80 := f18 * f78 + f20 * nz(f80[1])
    v20 = f78 * 1.5 - f80 * 0.5

    f88_ = 0.0
    f90_ = 0.0

    f88 = 0.0
    f90_ := nz(f90_[1]) == 0 ? 1 : nz(f88[1]) <= nz(f90_[1]) ? nz(f88[1]) + 1 : nz(f90_[1]) + 1
    f88 := nz(f90_[1]) == 0 and _len - 1 >= 5 ? _len - 1 : 5

    f0 = f88 >= f90_ and f8 != f10 ? 1 : 0
    f90 = f88 == f90_ and f0 == 0 ? 0 : f90_

    v4_ = f88 < f90 and v20 > 0 ? (v14 / v20 + 1) * 50 : 50
    tmpRsx = v4_ > 100 ? 100 : v4_ < 0 ? 0 : v4_

    tmpRsx

// calculate the moving average with the transferred settings
_funcCalcMA(_type, _src, _len) =>
    float ma = switch _type
        "COVWMA" => _funcCOVWMA(_src, _len)
        "DEMA" => _funcDEMA(_src, _len)
        "EMA" => ta.ema(_src, _len)
        "EHMA" => _funcEHMA(_src, _len)
        "HMA" => _funcHMA(_src, _len)
        "KAMA" => _funcKAMA(_src, _len)
        "RMA" => ta.rma(_src, _len)
        "RSX based Noise Remover" => _funcRemoveNoise(_src, _len)
        "SMA" => ta.sma(_src, _len)
        "SMMA" => _funcSMMA(_src, _len)
        "TEMA" => _funcTEMA(_src, _len)
        "FRAMA" => _funcFRAMA(_src, _len)
        "VWMA" => ta.vwma(_src, _len)
        "VIDYA" => _funcVIDYA(_src, _len)
        "WMA" => ta.wma(_src, _len)
        "Karobein" => _funcKarobein(_src, _len)
        =>
            float(na)

_funcRange(_cond, _minLookbackRange, _maxLookbackRange) =>
    bars = ta.barssince(_cond == true)
    _minLookbackRange <= bars and bars <= _maxLookbackRange

_funcPivot(_src, _pivotLookbackLeft, _pivotLookbackRight, _pivotLookbackRangeMin, _pivotLookbackRangeMax) =>
    // Pivot
    tmpPivotLowFound = na(ta.pivotlow(_src, _pivotLookbackLeft, _pivotLookbackRight)) ? false : true
    tmpPivotHighFound = na(ta.pivothigh(_src, _pivotLookbackLeft, _pivotLookbackRight)) ? false : true

    // Regular Bullish
    // Oscillator Higher Low
    tmpOscillatorHigherLow = _src[_pivotLookbackRight] > ta.valuewhen(tmpPivotLowFound, _src[_pivotLookbackRight], 1) and _funcRange(tmpPivotLowFound[1], _pivotLookbackRangeMin, _pivotLookbackRangeMax)
    // Price: Lower Low
    tmpPriceLowerLow = low[_pivotLookbackRight] < ta.valuewhen(tmpPivotLowFound, low[_pivotLookbackRight], 1)
    tmpBullishCondition = tmpPriceLowerLow and tmpOscillatorHigherLow and tmpPivotLowFound

    // Regular Bearish
    // Oscillator Lower High
    tmpOscillatorLowerHigh = _src[_pivotLookbackRight] < ta.valuewhen(tmpPivotHighFound, _src[_pivotLookbackRight], 1) and _funcRange(tmpPivotHighFound[1], _pivotLookbackRangeMin, _pivotLookbackRangeMax)
    // Price: Higher High
    tmpPriceHigherHigh = high[_pivotLookbackRight] > ta.valuewhen(tmpPivotHighFound, high[_pivotLookbackRight], 1)
    tmpBearishCondition = tmpPriceHigherHigh and tmpOscillatorLowerHigh and tmpPivotHighFound

    [tmpPivotLowFound, tmpPivotHighFound, tmpOscillatorHigherLow, tmpPriceLowerLow, tmpBullishCondition, tmpOscillatorLowerHigh, tmpPriceHigherHigh, tmpBearishCondition]



//********** Templates: settings

// Precise
int tpl_precise_Length = 4
string tpl_precise_SmoothingFactorType = 'DISABLED'
int tpl_precise_SmoothingFactorLength = 1

// Smooth
int tpl_smooth_Length = 4
string tpl_smooth_SmoothingFactorType = 'RMA'
int tpl_smooth_SmoothingFactorLength = 2

// Long Term
int tpl_longterm_Length = 20
string tpl_longterm_SmoothingFactorType = 'DISABLED'
int tpl_longterm_SmoothingFactorLength = 1



//********** Inputs
string inputTemplate = input.string(title='Template', group='Default', defval='Precise', options=['DISABLED', 'Precise', 'Smooth', 'Long Term'])

inputSource = input(title='Calculation Source', group='Default', defval=close)
int inputLength = input.int(title='Period', group='Default', minval=1, maxval=999, defval=4, step=1)

string inputSmoothingFactorType = input.string(title='Smoothing Factor: Type', group='Smoothing Factor', defval='DISABLED', options=['DISABLED', 'COVWMA', 'DEMA', 'EMA', 'EHMA', 'FRAMA', 'HMA', 'KAMA', 'Karobein', 'RMA', 'RSX based Noise Remover', 'SMA', 'SMMA', 'TEMA', 'VIDYA', 'VWMA', 'WMA'])
int inputSmoothingFactorLength = input.int(title='Smoothing Factor: Period', group='Smoothing Factor', minval=1, maxval=1000, defval=2)

// Divergence Identification
bool inputPivotEnable = input.bool(title='Divergence: On/Off', group='Divergence Identification', defval=true)
int inputPivotLookbackLeft = input.int(title='Divergence: Pivot Lookback Left', group='Divergence Identification', defval=5)
int inputPivotLookbackRight = input.int(title='Divergence: Pivot Lookback Right', group='Divergence Identification', defval=5)
int inputPivotLookbackRangeMin = input.int(title='Divergence: Min Lookback Range', group='Divergence Identification', defval=5)
int inputPivotLookbackRangeMax = input.int(title='Divergence: Max Lookback Range', group='Divergence Identification', defval=18)

// Styles
string inputStyle = input.string(title='Style Type', group='Styles', defval='Columns', options=['Columns', 'Histogram', 'Area', 'Line', 'Stepline'])

color input_colorUpTrendStrong = input(title='Color: Strong Uptrend', group='Styles', defval=colorUpTrendStrong)
color input_colorUpTrend = input(title='Color: Uptrend', group='Styles', defval=colorUpTrend)
color input_colorUpTrendWeak = input(title='Color: Weak Uptrend', group='Styles', defval=colorUpTrendWeak)

color input_colorDownTrendStrong = input(title='Color: Strong Downtrend', group='Styles', defval=colorDownTrendStrong)
color input_colorDownTrend = input(title='Color: Downtrend', group='Styles', defval=colorDownTrend)
color input_colorDownTrendWeak = input(title='Color: Weak Downtrend', group='Styles', defval=colorDownTrendWeak)

color input_colorTrendNeutral = input(title='Color: Neutral', group='Styles', defval=colorTrendNeutral)



//************  set final settings
int valFinalLength = inputTemplate == 'Precise' ? tpl_precise_Length : inputTemplate == 'Smooth' ? tpl_smooth_Length : inputTemplate == 'Long Term' ? tpl_longterm_Length : inputLength

string valFinalSmoothingFactorType = inputTemplate == 'Precise' ? tpl_precise_SmoothingFactorType : inputTemplate == 'Smooth' ? tpl_smooth_SmoothingFactorType : inputTemplate == 'Long Term' ? tpl_longterm_SmoothingFactorType : inputSmoothingFactorType

int valFinalSmoothingFactorLength = inputTemplate == 'Precise' ? tpl_precise_SmoothingFactorLength : inputTemplate == 'Smooth' ? tpl_smooth_SmoothingFactorLength : inputTemplate == 'Long Term' ? tpl_longterm_SmoothingFactorLength : inputSmoothingFactorLength



//************  Calculation

// determine the price of the regression slope
slopePrice = ta.linreg(inputSource, valFinalLength, 0) - ta.linreg(inputSource, valFinalLength, 1)
slopePriceFinal = valFinalSmoothingFactorType == 'DISABLED' ? slopePrice : _funcCalcMA(valFinalSmoothingFactorType, slopePrice, valFinalSmoothingFactorLength)

// get sizes of the candles
candleWidthTop = high - math.max(open, close)
candleWidthBottom = math.min(open, close) - low
candleWidthBody = math.abs(close - open)

// determine upward and downward movement of the regression slope
[volumeUp, volumeDown] = _funcTrend(valFinalLength, candleWidthTop, candleWidthBottom, candleWidthBody)

valFinalVol = slopePriceFinal * valFinalLength

// Pivot
[valVolPivotLowFound, valVolPivotHighFound, valVolPivotOscillatorHigherLow, valVolPivotPriceLowerLow, valVolPivotBullishCondition, valVolPivotOscillatorLowerHigh, valVolPivotPriceHigherHigh, valVolPivotBearishCondition] = _funcPivot(valFinalVol, inputPivotLookbackLeft, inputPivotLookbackRight, inputPivotLookbackRangeMin, inputPivotLookbackRangeMax)




//************ coloring
color colOsc = slopePriceFinal > 0 ? volumeUp > 0 ? volumeUp > volumeDown ? input_colorUpTrendStrong : input_colorUpTrend : input_colorUpTrendWeak : slopePriceFinal < 0 ? volumeDown > 0 ? volumeUp < volumeDown ? input_colorDownTrendStrong : input_colorDownTrend : input_colorDownTrendWeak : input_colorTrendNeutral

plotStyle = inputStyle == 'Columns' ? plot.style_columns : inputStyle == 'Histogram' ? plot.style_histogram : inputStyle == 'Area' ? plot.style_area : inputStyle == 'Line' ? plot.style_line : inputStyle == 'Stepline' ? plot.style_stepline : plot.style_columns




//************ Plotting
plot(valFinalVol, color=colOsc, style=plotStyle)

plot(inputPivotEnable and valVolPivotLowFound ? valFinalVol[inputPivotLookbackRight] : na, offset=-inputPivotLookbackRight, title='Regular Bullish', linewidth=3, color=valVolPivotBullishCondition ? valColorsBullColor : valColorsNaColor)

plotshape(inputPivotEnable and inputPivotEnable and valVolPivotBullishCondition ? valFinalVol[inputPivotLookbackRight] : na, offset=-inputPivotLookbackRight, title='Regular Bullish Label', text='Bull', style=shape.labelup, location=location.absolute, color=color.new(valColorsBullColor, 0), textcolor=color.new(valColorsTextColor, 0))

plot(inputPivotEnable and valVolPivotHighFound ? valFinalVol[inputPivotLookbackRight] : na, offset=-inputPivotLookbackRight, title='Regular Bearish', linewidth=3, color=valVolPivotBearishCondition ? valColorsBearColor : valColorsNaColor)

plotshape(inputPivotEnable and inputPivotEnable and valVolPivotBearishCondition ? valFinalVol[inputPivotLookbackRight] : na, offset=-inputPivotLookbackRight, title='Regular Bearish Label', text='Bear', style=shape.labeldown, location=location.absolute, color=color.new(valColorsBearColor, 0), textcolor=color.new(valColorsTextColor, 0))
