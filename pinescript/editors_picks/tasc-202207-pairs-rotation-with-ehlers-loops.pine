//  TASC Issue: July 2022 - Vol. 40, Issue 8
//     Article: Pairs Rotation With Ehlers Loops
//              Part 2 - Charting The Rotation
//  Article By: John F. Ehlers
//    Language: TradingView's Pine Script™ v5
// Provided By: PineCoders, for tradingview.com

//@version=5
indicator("TASC 2022.07 Pairs Rotation With Ehlers Loops",
       "PRWEL", max_lines_count=300, max_labels_count=300)

pairedSym = input.symbol("SP:SPX", "Referenced Symbol")
periodLP  = input.int( 20,           "Low-Pass Period", minval= 7)
periodHP  = input.int(125,          "High-Pass Period", minval=20)
periodRMS = input.int( 80,                "RMS Period",   step=10)
colorLoop = input.color(#FF0000,          "Loop Color")
barScale  = input.int( 40,                "Bar Scale:",   step= 5)
offset    = input.int(125,          "X Axis Position:",   step= 5)
segments  = input.int( 50,            "Loop Segments:", minval=10)


//== 2 Pole Butterworth Highpass Filter ==//
butterworthHP(float Series, float Period) =>
    var float ALPHA =  math.pi * math.sqrt(2.0) / Period
    var float BETA  =  math.exp(-ALPHA )
    var float COEF2 = -math.pow(BETA, 2)
    var float COEF1 =  math.cos( ALPHA ) * 2.0 * BETA
    var float COEF0 =  (1.0 + COEF1 - COEF2) * 0.25
    float tmp    = nz(Series[1],  Series)
    float whiten =    Series + nz(Series[2], tmp) - 2.0 * tmp 
    float smooth = na, smooth := COEF0 *     whiten     +
                                 COEF1 *  nz(smooth[1]) +
                                 COEF2 *  nz(smooth[2])

//===== 2 Pole Super Smoother Filter =====//
superSmoother(float Series, float Period) =>
    var float ALPHA =  math.pi * math.sqrt(2.0) / Period
    var float BETA  =  math.exp(-ALPHA )
    var float COEF2 = -math.pow(BETA, 2)
    var float COEF1 =  math.cos( ALPHA ) * 2.0 * BETA
    var float COEF0 =  1.0 - COEF1 - COEF2
    float sma2   = math.avg(Series, nz(Series[1], Series))
    float smooth = na, smooth := COEF0 *      sma2      +
                                 COEF1 *  nz(smooth[1]) +
                                 COEF2 *  nz(smooth[2])

//===== Faster Root Mean Square =====//
fastRMS(float Series, float Period) =>
    if Period < 1
        runtime.error("Err: fastRMS(Period=) is less than 1")
    var float COEF0 = 2.0 / (Period + 1)
    var float COEF1 = 1.0 -  COEF0
    float pow = math.pow(Series, 2)
    float ema = na, ema := COEF0 *    pow +
                           COEF1 * nz(ema[1], pow)
    nz(Series / math.sqrt(ema))

//===== RMS Scaled Bandpass Filter =====//
scaledFilt(int periodHP, int periodLP, int periodRMS) =>
    float HP       = butterworthHP(close, periodHP )
    float BPF      = superSmoother(   HP, periodLP )
    float priceRMS =       fastRMS(  BPF, periodRMS)

//===== Draws a Vertical Line Segment =====/
vline(int X, color Color) =>
    if barstate.islast
        var zero = line.new(X, -3.0, X, 3.0, color=Color,
                       style=line.style_dotted,  width=1)
        line.set_x1(zero, X + 1)
        line.set_x2(zero, X)

//======= Draws Various Deviation Boxes =======//
drawDeviationBox(float Width, int Offset, float Height,
                          int Deviations, color  Color) =>
    if barstate.islast
        var Box = box.new(
          bar_index, Height * 0.5, bar_index, Height * -0.5,
         border_color=Color, border_style=line.style_dotted,
         bgcolor=color.new(Color, 96), text_size=size.small,
           text=str.tostring(Deviations)   +  " deviations",
           text_color=Color,  text_valign=text.align_bottom)
        width = int(Width)
        box.set_left( Box, int(bar_index - width) + Offset)
        box.set_right(Box, int(bar_index + width) + Offset)

//===== Draws the Ehlers Loop =====/
drawLoop(float xPosition, float yPosition, color  Color,
           int  Segments,   int  BarScale,   int Offset) =>
    if barstate.islast
        var aSegments = array.new<line> (Segments    )
        var aNodes    = array.new<label>(Segments + 1)
        for i=0 to Segments
            float Y2 =     nz(yPosition[  i  ])
            int   X2 = int(nz(xPosition[  i  ]) * BarScale)
            int   X1 = int(nz(xPosition[1 + i]) * BarScale)
            float Y1 =     nz(yPosition[1 + i])
            X2 := math.min(500, X2 + Offset) + bar_index
            X1 := math.min(500, X1 + Offset) + bar_index
            if i < Segments
                width = int(4 * (Segments - i) / Segments + 1)
                line.delete(array.get(aSegments, i))
                segment= line.new(X1, Y1, X2, Y2, color=Color,
                         style=line.style_solid,  width=width)
                array.set( aSegments, i, segment)
            nodeSize = i==0 ? size.large : size.normal
            nodeChar = i==0 ? "⦿" : i==Segments ? "✕":"◆"
            label.delete(array.get(aNodes, i))
            node = label.new(X2, Y2, nodeChar,  size=nodeSize,
                             color=#00000000, textcolor=Color,
                              style=label.style_label_center)
            array.set(aNodes, i, node)

expression = scaledFilt(periodHP, periodLP, periodRMS)

var  CHART_TICKER = ticker.new(syminfo.prefix, syminfo.ticker)
var PAIRED_SYMBOL = ticker.new(syminfo.prefix(pairedSym),
                               syminfo.ticker(pairedSym))
PriceRMS_1 = request.security( CHART_TICKER, timeframe.period,
                       expression, ignore_invalid_symbol=true)
PriceRMS_2 = request.security(PAIRED_SYMBOL, timeframe.period,
                       expression, ignore_invalid_symbol=true)

plot(PriceRMS_1,      "Chart Symbol", color=#FF5555)
plot(PriceRMS_2, "Referenced Symbol", color=#5555FF)
hline( 0.0, "Zero", #808000, hline.style_dotted)

vline(        math.min(500, offset) + bar_index, #808000)
drawDeviationBox(3.0 * barScale, offset, 6.0, 3, #FF0000)
drawDeviationBox(2.0 * barScale, offset, 4.0, 2, #FF6600)
drawDeviationBox(      barScale, offset, 2.0, 1, #FFCC00)
drawLoop(PriceRMS_2, PriceRMS_1, colorLoop,
           segments,   barScale,    offset)
