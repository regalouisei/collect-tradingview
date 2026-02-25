//@version=5
indicator("Numbers Renko 数字練行足", overlay=true, max_bars_back=5000, max_labels_count=500, max_lines_count=500)

// ———————————————————— Inputs {
string Numberfontsize = input.string(size.normal,                 "Font size",            inline = "00", group = "Numbers Renko General Settings", options = [size.small, size.normal, size.large])
float  Yspacing       = input.float(0.0,                          "  Y-axis Spacing",     inline = "00", group = "Numbers Renko General Settings")
float  divisor        = input.float(0.01,                         "Volume Divisor",       inline = "01", group = "Numbers Renko General Settings", minval = 0)
bool   onlyLvol       = input.bool(false,                         "Show Only Large Renko Volume", inline = "01", group = "Numbers Renko General Settings")
float  tdivisor       = input.float(1,                            "Time Divisor  ",       inline = "02", group = "Numbers Renko General Settings", minval = 0)
string TimeInput      = input.string("None",                      " 　  Show Renko Time", inline = "02", group = "Numbers Renko General Settings", options = ["All Renko Time","Only Large Renko Time","None"])
int    emaPeriod      = input.int(5,                              "EMA period for Calculation", inline = "03", group = "Numbers Renko General Settings", minval = 1)
bool   usesma         = input.bool(false,                         "Use SMA",              inline = "03", group = "Numbers Renko General Settings")

bool   usetime        = input.bool(false,                         "Use Renko Time for Number Color", inline = "04", group = "Numbers Renko Coloring")
color  Upclr1         = input.color(#333333,                      "Up Candle Number  0",  inline = "a", group = "Numbers Renko Coloring")
color  Upclr2         = input.color(color.gray,                   "0.5",                  inline = "a", group = "Numbers Renko Coloring")
color  Upclr3         = input.color(color.white,                  "┆L→ 1",                inline = "a", group = "Numbers Renko Coloring")
color  Upclr4         = input.color(#BAFF8C,                      "1.5",                  inline = "a", group = "Numbers Renko Coloring")
color  Upclr5         = input.color(#66FF00,                      "2",                    inline = "a", group = "Numbers Renko Coloring")
color  Dnclr1         = input.color(#333333,                      "Dn Candle Number  0",  inline = "b", group = "Numbers Renko Coloring")
color  Dnclr2         = input.color(color.gray,                   "0.5",                  inline = "b", group = "Numbers Renko Coloring")
color  Dnclr3         = input.color(color.white,                  "┆L→ 1",                inline = "b", group = "Numbers Renko Coloring")
color  Dnclr4         = input.color(#FF8298,                      "1.5",                  inline = "b", group = "Numbers Renko Coloring")
color  Dnclr5         = input.color(#FF0230,                      "2",                    inline = "b", group = "Numbers Renko Coloring")

bool  isShowbody      = input.bool(false,                         "Show Candle Body  ",   inline = "05", group = "Numbers Renko Coloring")
bool  usetime2        = input.bool(false,                         "Use Renko Time for Candle Body Color", inline = "06", group = "Numbers Renko Coloring")
bool  isShowclrborder = input.bool(false,                         "Reflect Candle Body Color on Border and Wick", inline = "07", group = "Numbers Renko Coloring")
color Upclr1b         = input.color(color.new(#333333, 50),       "Up Candle Body     0", inline = "c", group = "Numbers Renko Coloring")
color Upclr2b         = input.color(color.new(color.gray, 50),    "0.5",                  inline = "c", group = "Numbers Renko Coloring")
color Upclr3b         = input.color(color.new(color.white, 50),   "┆L→ 1",                inline = "c", group = "Numbers Renko Coloring")
color Upclr4b         = input.color(color.new(#BAFF8C, 50),       "1.5",                  inline = "c", group = "Numbers Renko Coloring")
color Upclr5b         = input.color(color.new(#66FF00, 50),       "2",                    inline = "c", group = "Numbers Renko Coloring")
color Dnclr1b         = input.color(color.new(#333333, 50),       "Dn Candle Body     0", inline = "d", group = "Numbers Renko Coloring")
color Dnclr2b         = input.color(color.new(color.gray, 50),    "0.5",                  inline = "d", group = "Numbers Renko Coloring")
color Dnclr3b         = input.color(color.new(color.white, 50),   "┆L→ 1",                inline = "d", group = "Numbers Renko Coloring")
color Dnclr4b         = input.color(color.new(#FF8298, 50),       "1.5",                  inline = "d", group = "Numbers Renko Coloring")
color Dnclr5b         = input.color(color.new(#FF0230, 50),       "2",                    inline = "d", group = "Numbers Renko Coloring")

bool  isShowHollowCandle = input.bool(true,                       "Show Hollow Candle    ", inline = "11", group = "Numbers Renko Coloring")
color Upbarclr        = input.color(color.new(color.green, 60),   "Up",                   inline = "11", group = "Numbers Renko Coloring")
color Dnbarclr        = input.color(color.new(color.red, 60),     "Dn",                   inline = "11", group = "Numbers Renko Coloring")
bool  isShowline      = input.bool(false,                         "Show Renko Line         ", inline = "12", group = "Numbers Renko Coloring")
color colorlineUp     = input.color(color.new(color.green, 50),   "Up",                   inline = "12", group = "Numbers Renko Coloring")
color colorlineDn     = input.color(color.new(color.red, 50),     "Dn",                   inline = "12", group = "Numbers Renko Coloring")

string WWVfontsize    = input.string(size.large,                  "WWV Font size",        inline = "13", group = "Weis Wave Volume",  options = [size.small, size.normal, size.large])
bool  reverselabel    = input.bool(false,                         "Invert the line of the label above", inline = "13", group = "Weis Wave Volume")
bool  cumulTimeInput  = input.bool(false,                         "Show Wave Time  ",     inline = "14", group = "Weis Wave Volume")
bool  EvsRInput       = input.bool(false,                         "Show Effort vs Result", inline = "15", group = "Weis Wave Volume")
float noResult        = input.float(1.5,                          "       No Result Ratio ", inline = "15", group = "Weis Wave Volume")
bool  reVolInput      = input.bool(false,                         "Show Comparison Marks", inline = "16", group = "Weis Wave Volume")
float hivol           = input.float(1.5,                          "   Large WWV Ratio",   inline = "16", group = "Weis Wave Volume")
color colorUpWaveVol  = input.color(color.green,                  "Up WWV",               inline = "17", group = "Weis Wave Volume")
color colorDnWaveVol  = input.color(color.red,                    "  Down WWV",           inline = "17", group = "Weis Wave Volume")
color colorhiWaveVol  = input.color(color.yellow,                 "  Large WWV",          inline = "17", group = "Weis Wave Volume")
// } 

// ———————————————————— Global data {
O = open
H = high
L = low
C = close

vol =  volume * divisor// not var float
wks = weekofyear(time[1]) > weekofyear(time) ? weekofyear(time) : weekofyear(time) - weekofyear(time[1])
tm  = math.round(((time - time[1]) / 60000.0 - 2880.0 * wks)*tdivisor)

var float cumulVol = 0
var float cumulTime = 0
var int  cumulRenko = 0
string arrow1 = na
string arrow2 = na
string arrow3 = na
string arrow4 = na
string relativeVol = na
string EvsR = na
string labelcumulTime = na

var float [] prevol = array.new_float(5, na)// not varip
var float [] vp = array.new_float(5, na)// not varip

color barclr       = color(na)
color candleColor  = color(na)
color NumberClr    = na
// }

// ———————————————————— Functions {
// —————— Numbers Renko Coloring —————————
G = C > O
barclr := isShowHollowCandle ? G ? Upbarclr : Dnbarclr : na
isUp = close > open

//time 
timeFraction = usesma ? tm / ta.sma(tm, emaPeriod) : tm / ta.ema(tm, emaPeriod)

string Renkotime = str.tostring(tm)
string RenkotimeL = timeFraction > 1 ? str.tostring(tm) : na

//volume
volumeFraction =  usesma ? volume / ta.sma(volume, emaPeriod) : volume / ta.ema(volume, emaPeriod) 

string Renkovolume = str.tostring(vol)
string RenkovolumeL = volumeFraction > 1 ? str.tostring(math.round(vol, 0)) : na
string labelRenkovolume = onlyLvol ? RenkovolumeL : str.tostring(math.round(vol, 0))

// Coloring
colortypeN = usetime ? timeFraction : volumeFraction
colortypeC = usetime2 ? timeFraction : volumeFraction


if isUp
    NumberClr := colortypeN > 2 ? Upclr5 : colortypeN > 1.5 ? Upclr4 : colortypeN > 1 ? Upclr3 : colortypeN > 0.5 ? Upclr2 : Upclr1 
    candleColor := colortypeC > 2 ? Upclr5b : colortypeC > 1.5 ? Upclr4b : colortypeC > 1 ? Upclr3b : colortypeC > 0.5 ? Upclr2b : Upclr1b
else
    NumberClr := colortypeN > 2 ? Dnclr5 : colortypeN > 1.5 ? Dnclr4 : colortypeN > 1 ? Dnclr3 : colortypeN > 0.5 ? Dnclr2 : Dnclr1 
    candleColor := colortypeC > 2 ? Dnclr5b : colortypeC > 1.5 ? Dnclr4b : colortypeC > 1 ? Dnclr3b : colortypeC > 0.5 ? Dnclr2b : Dnclr1b
    
barclr := isShowclrborder ? candleColor : barclr
    
// ——————— Weis Wave Volume ——————————
direction = int(na)
direction:= close > close[1] ? 1 : close < close[1] ? -1 : nz(direction[1])
directionHasChanged = ta.change(direction) != 0
directionIsUp = direction > 0
directionIsDown = direction < 0

renkoblockcount = int(na)
renkoblockcount := not directionHasChanged[1] ? renkoblockcount[1] : 1

var label currentWaveLabel = na
var color labelColor = color.silver
var color textColor = color.silver
var string labelText = ""
labelStyle = label.style_none
xloc = bar_index
yloc = yloc.abovebar
fontsize = size.normal
// }

// ———————————————————— Plots {
plotcandle(O, H, L, C, "Renko Bar", color=isShowbody ? candleColor : na, wickcolor=barclr, bordercolor=barclr)

if TimeInput == "All Renko Time"
    label.new(bar_index, isUp ? open + Yspacing : close + Yspacing, labelRenkovolume + "\n" + Renkotime, xloc.bar_index, yloc.price, NumberClr, label.style_none, NumberClr, Numberfontsize)
else if TimeInput == "Only Large Renko Time"
    label.new(bar_index, isUp ? open + Yspacing : close + Yspacing, labelRenkovolume + "\n" + RenkotimeL, xloc.bar_index, yloc.price, NumberClr, label.style_none, NumberClr, Numberfontsize)
else
    label.new(bar_index, isUp ? open + Yspacing: close + Yspacing, labelRenkovolume, xloc.bar_index, yloc.price, NumberClr, label.style_none, NumberClr, Numberfontsize)


label.delete(currentWaveLabel)

// Reprint the confirmed high/low     //from Weis Wave Volume Numbers by the_MarketWhisperer 
if directionHasChanged and directionIsDown
    cumulVol := vol
    cumulTime := tm
    cumulRenko := renkoblockcount
    array.push(prevol, cumulVol[1])
    array.push(vp, cumulVol[1]/cumulRenko[1])
    arrow1 := cumulVol[1] > array.get(prevol, array.size(prevol) - 3) ? "↑" : "↓"
    arrow2 := cumulVol[1] > array.get(prevol, array.size(prevol) - 3) ? cumulVol[1] > array.get(prevol, array.size(prevol) - 2) ? "" : "⌄" : cumulVol[1] > array.get(prevol, array.size(prevol) - 2) ? "^" : ""
    arrow3 := cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(prevol) - 3) ? "↑" : "↓"
    arrow4 := cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 3) ? cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 2) ? "" : "⌄" : cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 2) ? "^" : ""
    relativeVol := reVolInput ? arrow1 + str.tostring(math.round(cumulVol[1])) + arrow2 : str.tostring(math.round(cumulVol[1]))
    EvsR := EvsRInput ? reVolInput ? "[" + arrow3 + str.tostring(math.round(cumulVol[1] / cumulRenko[1], 1)) + arrow4 + "]" : "[" + str.tostring(math.round(cumulVol[1] / cumulRenko[1], 1)) + "]": na
    labelcumulTime := cumulTimeInput ? "\n" + str.tostring(cumulTime[1]) : na
    labelText := reverselabel ? EvsR + labelcumulTime + "\n" + relativeVol : relativeVol + labelcumulTime + "\n" + EvsR 
    labelStyle := (array.get(vp, array.size(vp) - 1) + array.get(vp, array.size(vp) - 2) + array.get(vp, array.size(vp) - 3) + array.get(vp, array.size(vp) - 4) + array.get(vp, array.size(vp) - 5)) / 5 * noResult < cumulVol[1]/cumulRenko[1] ? label.style_square : label.style_none
    textColor := (array.get(prevol, array.size(prevol) - 1) + array.get(prevol, array.size(prevol) - 2) + array.get(prevol, array.size(prevol) - 3) + array.get(prevol, array.size(prevol) - 4) + array.get(prevol, array.size(prevol) - 5)) / 5 * hivol < cumulVol[1] ? colorhiWaveVol : colorUpWaveVol
    xloc := bar_index[1]
    yloc := yloc.abovebar
    fontsize := WWVfontsize
    label.new(xloc, close, yloc=yloc, textcolor=textColor, color=color.new(colorhiWaveVol, 50), style=labelStyle, text=labelText, size = fontsize)
    //Show developing volume (cumulVol) of the current bar
    arrow1 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? "↓" : "↑"
    arrow2 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? cumulVol > array.get(prevol, array.size(prevol) - 1) ? "" : "^" : cumulVol > array.get(prevol, array.size(prevol) - 1) ? "⌄" : ""
    arrow3 := cumulVol > array.get(vp, array.size(vp) - 2) ? "↓" : "↑"
    arrow4 := cumulVol > array.get(vp, array.size(vp) - 2) ? cumulVol > array.get(vp, array.size(vp) - 1) ? "" : "^" : cumulVol > array.get(vp, array.size(vp) - 1) ? "⌄" : ""
    relativeVol := reVolInput ? arrow1 + str.tostring(math.round(cumulVol)) + arrow2 : str.tostring(math.round(cumulVol))
    string rabelcumulVol = EvsRInput ? reVolInput ? "["+ arrow3 + str.tostring(math.round(cumulVol)) + arrow4 + "]" : "[" + str.tostring(math.round(cumulVol)) + "]" : na
    labelcumulTime := cumulTimeInput ? "\n" + str.tostring(cumulTime) : na
    labelStyle := (cumulVol + array.get(vp, array.size(vp) - 1) + array.get(vp, array.size(vp) - 2) + array.get(vp, array.size(vp) - 3) + array.get(vp, array.size(vp) - 4)) / 5 * noResult < cumulVol ? label.style_square : label.style_none
    labelText := relativeVol + str.tostring("_") + labelcumulTime + "\n" + rabelcumulVol
    textColor := (cumulVol + array.get(prevol, array.size(prevol) - 1) + array.get(prevol, array.size(prevol) - 2) + array.get(prevol, array.size(prevol) - 3) + array.get(prevol, array.size(prevol) - 4)) / 5 * hivol < cumulVol ? colorhiWaveVol : colorDnWaveVol
    currentWaveLabel := label.new(bar_index, close, yloc=yloc.belowbar, textcolor=textColor, color=color.new(colorhiWaveVol, 50), style=labelStyle, text=labelText, size = fontsize)
else if directionHasChanged and directionIsUp
    cumulVol := vol
    cumulTime := tm
    cumulRenko := renkoblockcount
    array.push(prevol, cumulVol[1])
    array.push(vp, cumulVol[1]/cumulRenko[1])
    arrow1 := cumulVol[1] > array.get(prevol, array.size(prevol) - 3) ? "↓" : "↑"
    arrow2 := cumulVol[1] > array.get(prevol, array.size(prevol) - 3) ? cumulVol[1] > array.get(prevol, array.size(prevol) - 2) ? "" : "^" : cumulVol[1] > array.get(prevol, array.size(prevol) - 2) ? "⌄" : ""
    arrow3 := cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 3) ? "↓" : "↑"
    arrow4 := cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 3) ? cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 2) ? "" : "^" : cumulVol[1]/cumulRenko[1] > array.get(vp, array.size(vp) - 2) ? "⌄" : ""
    relativeVol := reVolInput ? arrow1 + str.tostring(math.round(cumulVol[1])) + arrow2 : str.tostring(math.round(cumulVol[1]))
    EvsR := EvsRInput ? reVolInput ? "[" + arrow3 + str.tostring(math.round(cumulVol[1] / cumulRenko[1], 1)) + arrow4 + "]" : "[" + str.tostring(math.round(cumulVol[1] / cumulRenko[1], 1)) + "]": na
    labelcumulTime := cumulTimeInput ? "\n" + str.tostring(cumulTime[1]) : na
    labelText := relativeVol + labelcumulTime + "\n" + EvsR 
    labelStyle := (array.get(vp, array.size(vp) - 1) + array.get(vp, array.size(vp) - 2) + array.get(vp, array.size(vp) - 3) + array.get(vp, array.size(vp) - 4) + array.get(vp, array.size(vp) - 5)) / 5 * noResult < cumulVol[1]/cumulRenko[1] ? label.style_square : label.style_none
    textColor := (array.get(prevol, array.size(prevol) - 1) + array.get(prevol, array.size(prevol) - 2) + array.get(prevol, array.size(prevol) - 3) + array.get(prevol, array.size(prevol) - 4) + array.get(prevol, array.size(prevol) - 5)) / 5 * hivol < cumulVol[1] ? colorhiWaveVol : colorDnWaveVol
    xloc := bar_index[1]
    yloc := yloc.belowbar
    fontsize := WWVfontsize
    label.new(xloc, close, yloc=yloc, textcolor=textColor, color=color.new(colorhiWaveVol, 50), style=labelStyle, text=labelText, size = fontsize)
    //Show developing volume (cumulVol) of the current bar
    arrow1 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? "↑" : "↓"
    arrow2 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? cumulVol > array.get(prevol, array.size(prevol) - 1) ? "" : "⌄" : cumulVol > array.get(prevol, array.size(prevol) - 1) ? "^" : ""
    arrow3 := cumulVol > array.get(vp, array.size(vp) - 2) ? "↑" : "↓"
    arrow4 := cumulVol > array.get(vp, array.size(vp) - 2) ? cumulVol > array.get(vp, array.size(vp) - 1) ? "" : "⌄" : cumulVol > array.get(vp, array.size(vp) - 1) ? "^" : ""
    relativeVol := reVolInput ? arrow1 + str.tostring(math.round(cumulVol)) + arrow2 : str.tostring(math.round(cumulVol))
    string rabelcumulVol = EvsRInput ? reVolInput ? "["+ arrow3 + str.tostring(math.round(cumulVol)) + arrow4 + "]" : "[" + str.tostring(math.round(cumulVol)) + "]" : na
    labelcumulTime := cumulTimeInput ? "\n" + str.tostring(cumulTime) : na
    labelStyle := (cumulVol + array.get(vp, array.size(vp) - 1) + array.get(vp, array.size(vp) - 2) + array.get(vp, array.size(vp) - 3) + array.get(vp, array.size(vp) - 4)) / 5 * noResult < cumulVol ? label.style_square : label.style_none
    labelText := reverselabel ? rabelcumulVol + labelcumulTime + "\n" + relativeVol + str.tostring("_") : relativeVol + str.tostring("_") + labelcumulTime + "\n" + rabelcumulVol
    textColor := (cumulVol + array.get(prevol, array.size(prevol) - 1) + array.get(prevol, array.size(prevol) - 2) + array.get(prevol, array.size(prevol) - 3) + array.get(prevol, array.size(prevol) - 4)) / 5 * hivol < cumulVol ? colorhiWaveVol : colorUpWaveVol
    currentWaveLabel := label.new(bar_index, close, yloc=yloc.abovebar, textcolor=colorUpWaveVol, color=color.new(colorhiWaveVol, 50), style=labelStyle, text=labelText, size = fontsize)
    // and not directionHasChanged
else if directionIsDown  // add current volume to cumulative volume
    cumulVol += vol
    cumulTime += tm
    cumulRenko += 1
    arrow1 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? "↓" : "↑"
    arrow2 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? cumulVol > array.get(prevol, array.size(prevol) - 1) ? "" : "^" : cumulVol > array.get(prevol, array.size(prevol) - 1) ? "⌄" : ""
    arrow3 := cumulVol/cumulRenko > array.get(vp, array.size(vp) - 2) ? "↓" : "↑"
    arrow4 := cumulVol/cumulRenko > array.get(vp, array.size(vp) - 2) ? cumulVol/cumulRenko > array.get(vp, array.size(vp) - 1) ? "" : "^" : cumulVol/cumulRenko > array.get(vp, array.size(vp) - 1) ? "⌄" : ""
    relativeVol := reVolInput ? arrow1 + str.tostring(math.round(cumulVol)) + arrow2 : str.tostring(math.round(cumulVol))
    labelcumulTime := cumulTimeInput ? "\n" + str.tostring(cumulTime) : na
    EvsR := EvsRInput ? reVolInput ? "[" + arrow3 + str.tostring(math.round(cumulVol / cumulRenko, 1)) + arrow4 + "]" : "[" + str.tostring(math.round(cumulVol / cumulRenko, 1)) + "]" : na
    labelText := relativeVol + str.tostring("_") + labelcumulTime + "\n" + EvsR
    labelStyle := ((cumulVol / cumulRenko) + array.get(vp, array.size(vp) - 1) + array.get(vp, array.size(vp) - 2) + array.get(vp, array.size(vp) - 3) + array.get(vp, array.size(vp) - 4)) / 5 * noResult < cumulVol/cumulRenko ? label.style_square : label.style_none
    textColor := (cumulVol + array.get(prevol, array.size(prevol) - 1) + array.get(prevol, array.size(prevol) - 2) + array.get(prevol, array.size(prevol) - 3) + array.get(prevol, array.size(prevol) - 4)) / 5 * hivol < cumulVol ? colorhiWaveVol : colorDnWaveVol
    xloc := bar_index
    yloc := yloc.belowbar
    fontsize := WWVfontsize
    currentWaveLabel := label.new(xloc, close, yloc=yloc, textcolor=textColor, color=color.new(colorhiWaveVol, 50), style=labelStyle, text=labelText, size = fontsize)
    // and not directionHasChanged
else if directionIsUp  // add current volume to cumulative volume
    cumulVol += vol
    cumulTime += tm
    cumulRenko += 1
    arrow1 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? "↑" : "↓"
    arrow2 := cumulVol > array.get(prevol, array.size(prevol) - 2) ? cumulVol > array.get(prevol, array.size(prevol) - 1) ? "" : "⌄" : cumulVol > array.get(prevol, array.size(prevol) - 1) ? "^" : ""
    arrow3 := cumulVol/cumulRenko > array.get(vp, array.size(vp) - 2) ? "↑" : "↓"
    arrow4 := cumulVol/cumulRenko > array.get(vp, array.size(vp) - 2) ? cumulVol/cumulRenko > array.get(vp, array.size(vp) - 1) ? "" : "⌄" : cumulVol/cumulRenko > array.get(vp, array.size(vp) - 1) ? "^" : ""
    relativeVol := reVolInput ? arrow1 + str.tostring(math.round(cumulVol)) + arrow2 : str.tostring(math.round(cumulVol))
    labelcumulTime := cumulTimeInput ? "\n" + str.tostring(cumulTime) : na
    EvsR := EvsRInput ? reVolInput ? "[" + arrow3 + str.tostring(math.round(cumulVol / cumulRenko, 1)) + arrow4 + "]" : "[" + str.tostring(math.round(cumulVol / cumulRenko, 1)) + "]" : na
    labelText := reverselabel ? EvsR + labelcumulTime + "\n" + relativeVol + str.tostring("_") : relativeVol + str.tostring("_")  + labelcumulTime + "\n" + EvsR
    labelStyle := ((cumulVol / cumulRenko) + array.get(vp, array.size(vp) - 1) + array.get(vp, array.size(vp) - 2) + array.get(vp, array.size(vp) - 3) + array.get(vp, array.size(vp) - 4)) / 5 * noResult < cumulVol/cumulRenko ? label.style_square : label.style_none
    textColor := (cumulVol + array.get(prevol, array.size(prevol) - 1) + array.get(prevol, array.size(prevol) - 2) + array.get(prevol, array.size(prevol) - 3) + array.get(prevol, array.size(prevol) - 4)) / 5 * hivol < cumulVol ? colorhiWaveVol : colorUpWaveVol
    xloc := bar_index
    yloc := yloc.abovebar
    fontsize := WWVfontsize
    currentWaveLabel := label.new(xloc, close, yloc=yloc, textcolor=textColor, color=color.new(colorhiWaveVol, 50), style=labelStyle, text=labelText, size = fontsize)

// if barstate.isrealtime and directionHasChanged[1]
//     array.shift(prevol)
//     array.shift(vp)

// Renko Line
var line renkoline = na
var line renkoline2 = na
var x1 = bar_index
var y1 = close[1]
linecolor = isUp ? colorlineUp : colorlineDn

x1 := directionHasChanged ? bar_index : x1
y1 := directionHasChanged ? open[1] : y1
x2 = bar_index
y2 = open

if isShowline
    if not directionHasChanged
        line.delete(renkoline)
    if directionHasChanged
        renkoline2 := line.new(bar_index[1], open[1], bar_index, open[1], color=linecolor)
    renkoline := line.new(x1, y1, x2, y2, extend=extend.none, color=linecolor)
// }
