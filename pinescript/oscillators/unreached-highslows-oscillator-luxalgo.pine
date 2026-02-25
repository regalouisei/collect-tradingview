// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo

//@version=6
indicator('Unreached Highs/Lows Oscillator [LuxAlgo]','LuxAlgo - UHLO')
//---------------------------------------------------------------------------------------------------------------------}
//CONSTANTS & STRINGS & INPUTS
//---------------------------------------------------------------------------------------------------------------------{
GREEN                   = #089981
RED                     = #F23645
SILVER                  = #B2B5BE 

STYLE_GROUP             = 'Style'

EM_SPACE                = ' '
EN_SPACE                = ' '
FOUR_PER_EM_SPACE       = ' '

topThresholdTag         = 'Top Threshold'+EM_SPACE+EN_SPACE+FOUR_PER_EM_SPACE

lengthInput             = input.int(    20,     'Length')

bullishColorInput       = input.color(  GREEN,  'Bullish',          group = STYLE_GROUP)
bearishColorInput       = input.color(  RED,    'Bearish',          group = STYLE_GROUP)

topThresholdInput       = input.int(    80,     topThresholdTag,    group = STYLE_GROUP, inline = 'top', minval = 50, maxval = 100)
topColorInput           = input.color(  SILVER, '',                 group = STYLE_GROUP, inline = 'top')
topColorAutoInput       = input.bool(   true,   'Auto',             group = STYLE_GROUP, inline = 'top')

bottomThresholdInput    = input.int(    20,     'Bottom Threshold', group = STYLE_GROUP, inline = 'bottom', maxval = 50, minval = 0)
bottomColorInput        = input.color(  SILVER, '',                 group = STYLE_GROUP, inline = 'bottom')
bottomColorAutoInput    = input.bool(   true,   'Auto',             group = STYLE_GROUP, inline = 'bottom')

//---------------------------------------------------------------------------------------------------------------------}
//DATA STRUCTURES & VARIABLES
//---------------------------------------------------------------------------------------------------------------------{
type extremes
    int highs
    int lows

var extremes unreached  = extremes.new(0,0)
var int baseLevel       = 50

//---------------------------------------------------------------------------------------------------------------------}
//USER-DEFINED FUNCTIONS
//---------------------------------------------------------------------------------------------------------------------{
gatherData() =>
    var highs     = array.new_float(0)
    high_removals = array.new_float(0)

    var lows      = array.new_float(0)
    lows_removals = array.new_float(0)

    if array.size(highs) != 0
        for h in highs
            if high > h
                array.push(high_removals, h)
        
        for element in high_removals
            array.remove(highs, array.indexof(highs, element))

    if array.size(lows) != 0
        for l in lows
            if low < l
                array.push(lows_removals, l)
        
        for element in lows_removals
            array.remove(lows, array.indexof(lows, element))
            
    if array.size(highs) > lengthInput
        array.pop(highs)

    if array.size(lows) > lengthInput
        array.pop(lows)

    unreached.highs := 100 * array.size(highs) / lengthInput
    unreached.lows  := 100 * array.size(lows) / lengthInput

    array.unshift(highs, high)
    array.unshift(lows, low)

//---------------------------------------------------------------------------------------------------------------------}
//MUTABLE VARIABLES & EXECUTION
//---------------------------------------------------------------------------------------------------------------------{
gatherData()

highsPlot   = plot(unreached.highs, 'Unreached Highs',  bearishColorInput)
lowsPlot    = plot(unreached.lows,  'Unreached Lows',   bullishColorInput)
basePlot    = plot(baseLevel,       'Base line', chart.fg_color, linestyle = plot.linestyle_dotted, display = display.pane)
plot(topThresholdInput,     'Top Threshold',  topColorAutoInput ? chart.fg_color : topColorInput, linestyle = plot.linestyle_dotted, display = display.pane)
plot(bottomThresholdInput,  'Bottom Threshold', bottomColorAutoInput ? chart.fg_color : bottomColorInput, linestyle = plot.linestyle_dotted, display = display.pane)

fill(lowsPlot,basePlot,100,baseLevel,unreached.lows > baseLevel ? color.new(bullishColorInput,50) : color(na),unreached.lows > baseLevel ? color.new(bullishColorInput,100) : color(na))
fill(highsPlot,basePlot,100,baseLevel,unreached.highs > baseLevel ? color.new(bearishColorInput,50) : color(na),unreached.highs > baseLevel ? color.new(bearishColorInput,100) : color(na))

//---------------------------------------------------------------------------------------------------------------------}
