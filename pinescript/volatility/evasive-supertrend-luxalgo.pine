// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo

//@version=6
indicator("Evasive SuperTrend [LuxAlgo]", "LuxAlgo - Evasive SuperTrend", overlay = true, max_labels_count = 500)

//---------------------------------------------------------------------------------------------------------------------}
// Constants
//---------------------------------------------------------------------------------------------------------------------{
color BULL_COLOR            = #089981
color BEAR_COLOR            = #f23645

//---------------------------------------------------------------------------------------------------------------------}
// Inputs
//---------------------------------------------------------------------------------------------------------------------{
string ST_GROUP             = 'Supertrend Settings'
int lengthInput             = input.int(10, 'ATR Length', minval = 1, group = ST_GROUP)
float multiplierInput       = input.float(3.0, 'Base Multiplier', minval = 0.1, step = 0.1, group = ST_GROUP)

string NOISE_GROUP          = 'Noise Avoidance Logic'
float thresholdInput        = input.float(1.0, 'Noise Threshold (xATR)', minval = 0.1, step = 0.1, group = NOISE_GROUP, tooltip = 'If price gets closer to the band than this value, the band is pushed away.')
float alphaInput            = input.float(0.5, 'Expansion Alpha (xATR)', minval = 0, step = 0.1, group = NOISE_GROUP, tooltip = 'Distance (in ATRs) to push the band away when noise is detected.')

string VISUAL_GROUP         = 'Visualization'
bool showLabelsInput        = input.bool(true, 'Show Signal Labels', group = VISUAL_GROUP)
bool showFillsInput         = input.bool(true, 'Show Gradient Fills', group = VISUAL_GROUP)

//---------------------------------------------------------------------------------------------------------------------}
// Core Calculations
//---------------------------------------------------------------------------------------------------------------------{
// ATR Calculation
float atr = ta.atr(lengthInput)

// Supertrend Variables
var float stBand      = na
var int trend         = 1 // 1 for Bull, -1 for Bear

float src = hl2
float upperBase = src + multiplierInput * atr
float lowerBase = src - multiplierInput * atr

// Previous Band (needed for noise check)
float prevBand = nz(stBand[1], trend == 1 ? lowerBase : upperBase)

// Noise Avoidance Condition
// Logic: If price is closer to the band than (ATR * threshold), it's noisy
bool isNoisy = math.abs(close - prevBand) < (atr * thresholdInput)

// Band Calculation with Adaptive Expansion
if trend == 1
    // BULL TREND: If noisy, move band DOWN (away from price). 
    // This overrides the standard "only move up" math.max rule.
    if isNoisy
        stBand := prevBand - (atr * alphaInput)
    else
        stBand := math.max(lowerBase, prevBand)
    
    // Check for Trend Flip
    if close < stBand
        trend := -1
        stBand := upperBase
else
    // BEAR TREND: If noisy, move band UP (away from price).
    // This overrides the standard "only move down" math.min rule.
    if isNoisy
        stBand := prevBand + (atr * alphaInput)
    else
        stBand := math.min(upperBase, prevBand)
    
    // Check for Trend Flip
    if close > stBand
        trend := 1
        stBand := lowerBase

bool trendChanged = trend != trend[1]

//---------------------------------------------------------------------------------------------------------------------}
// Visuals
//---------------------------------------------------------------------------------------------------------------------{
color stColor = trend == 1 ? BULL_COLOR : BEAR_COLOR

// Switch Dot
plot(trendChanged ? stBand : na, "Trend Switch Dot", color = stColor, style = plot.style_circles, linewidth = 4, join = false)

// Main Band - Two plots used to handle conditional line styles (Solid vs Dotted)
// Invisible plot used as anchor for the gradient fill
plotId = plot(stBand, "Band for Fill", color = na)

// Solid Line (Normal mode) - style_linebr prevents gaps when switching to dotted
plot(isNoisy ? na : stBand, "Solid Band", color = stColor, linewidth = 2, style = plot.style_linebr)

// Dotted Line (Expansion/Noise mode)
plot(isNoisy ? stBand : na, "Dotted Band", color = stColor, linewidth = 2, style = plot.style_linebr, linestyle = plot.linestyle_dotted)

srcId  = plot(src, "Source", color = na)

// Gradient Fill (Strictly following: less transparent near price)
float topValue    = math.max(src, stBand)
float bottomValue = math.min(src, stBand)
color topFillColor    = trend == 1 ? color.new(BULL_COLOR, 50) : color.new(BEAR_COLOR, 100)
color bottomFillColor = trend == 1 ? color.new(BULL_COLOR, 100) : color.new(BEAR_COLOR, 50)

fill(plotId, srcId, topValue, bottomValue, topFillColor, bottomFillColor, 
     title   = "Trend Fill", 
     display = showFillsInput ? display.all : display.none)

// Signal Labels
if showLabelsInput and trendChanged
    label.new(bar_index, stBand, 
         text = trend == 1 ? "BULL" : "BEAR", 
         color = stColor, 
         textcolor = #FFFFFF, 
         style = trend == 1 ? label.style_label_up : label.style_label_down, 
         size = size.tiny)

//---------------------------------------------------------------------------------------------------------------------}
