// This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) https://creativecommons.org/licenses/by-nc-sa/4.0/
// © LuxAlgo

//@version=6
indicator("Sweep Volume Index [LuxAlgo]", "LuxAlgo - Sweep Volume Index", format = format.volume)

//---------------------------------------------------------------------------------------------------------------------}
// Types
//---------------------------------------------------------------------------------------------------------------------{
type IntrabarData
    float h
    float l
    float v
//---------------------------------------------------------------------------------------------------------------------}
// Inputs
//---------------------------------------------------------------------------------------------------------------------{
int    pivotLenInput  = input.int(10,          "Pivot Length",         minval = 1, group = "Detection")
string lowerTfInput   = input.timeframe("1",  "Intrabar Timeframe",               group = "Calculation")

bool   useThreshold   = input.bool(true,       "Use ATR Threshold",                group = "Threshold")
int    atrLength      = input.int(200,         "ATR Length",          minval = 1,  group = "Threshold")
float  atrMult        = input.float(1.0,       "ATR Multiplier",      minval = 0,  group = "Threshold", step = 0.05)

float  alphaInput      = input.float(95,       "Envelope Alpha %",    minval = 0,  maxval = 100, group = "Envelopes")
color  upperEnvColor   = input.color(#089981,  "Upper Envelope Color",              group = "Envelopes")
color  lowerEnvColor   = input.color(#f23645,  "Lower Envelope Color",              group = "Envelopes")
bool   showLevelsInput = input.bool(true,      "Show Swing Levels",                 group = "Visuals")
bool   showOscFills    = input.bool(true,      "Show Oscillator Fills",              group = "Visuals")
color  bullColorInput  = input.color(#089981,  "Bullish Sweep Color",               group = "Visuals")
color  bearColorInput  = input.color(#f23645,  "Bearish Sweep Color",               group = "Visuals")
color  phLevelColor    = input.color(color.new(#089981, 50), "Pivot High Level Color",      group = "Visuals")
color  plLevelColor    = input.color(color.new(#f23645, 50), "Pivot Low Level Color",       group = "Visuals")
color  phZoneColor     = input.color(color.new(#089981, 85), "Pivot High Zone Color",       group = "Visuals")
color  plZoneColor     = input.color(color.new(#f23645, 85), "Pivot Low Zone Color",        group = "Visuals")


//---------------------------------------------------------------------------------------------------------------------}
// Calculation
//---------------------------------------------------------------------------------------------------------------------{
// Pivot High/Low detection
ph = ta.pivothigh(high, pivotLenInput, pivotLenInput)
pl = ta.pivotlow(low,   pivotLenInput, pivotLenInput)

// Store the most recent confirmed pivots
var float lastPH = na
var float lastPL = na

if not na(ph)
    lastPH := ph
if not na(pl)
    lastPL := pl

// Request intrabar data
intrabars = request.security_lower_tf(syminfo.tickerid, lowerTfInput, IntrabarData.new(high, low, volume))

// ATR for threshold calculation
atr = ta.atr(atrLength)
threshold = useThreshold ? atr * atrMult : 0.0

// Sweep volume variables
float bullSweepVol = 0.0
float bearSweepVol = 0.0

// Detection logic
float bodyMax = math.max(open, close)
float bodyMin = math.min(open, close)

if not na(lastPH) and high > lastPH and bodyMax <= lastPH + threshold
    if not na(intrabars) and array.size(intrabars) > 0
        for ib in intrabars
            if ib.h > lastPH
                bullSweepVol += ib.v

if not na(lastPL) and low < lastPL and bodyMin >= lastPL - threshold
    if not na(intrabars) and array.size(intrabars) > 0
        for ib in intrabars
            if ib.l < lastPL
                bearSweepVol += ib.v

// Envelope Calculation
var float upperEnv = 0.0
var float lowerEnv = 0.0

alpha = alphaInput / 100

// Detection of a new peak (for line cuts)
upperRise = bullSweepVol  > nz(upperEnv[1]) * alpha
lowerFall = -bearSweepVol < nz(lowerEnv[1]) * alpha

upperEnv := math.max(bullSweepVol,  nz(upperEnv[1]) * alpha)
lowerEnv := math.min(-bearSweepVol, nz(lowerEnv[1]) * alpha)

// Detection of changes for visuals
phChanged = ta.change(lastPH) != 0
plChanged = ta.change(lastPL) != 0
thChanged = ta.change(threshold) != 0

//---------------------------------------------------------------------------------------------------------------------}
// Visuals
//---------------------------------------------------------------------------------------------------------------------{
// --- Oscillator Pane ---
// We plot a 0-value series with no color to anchor fills without a visible line
pZero = plot(0, "Zero Anchor", color.new(chart.bg_color, 100))

// Plotting sweep volumes as columns
plot(bullSweepVol > 0 ? bullSweepVol : na,  "Bullish Sweep Volume", bullColorInput, style = plot.style_columns)
plot(bearSweepVol > 0 ? -bearSweepVol : na, "Bearish Sweep Volume", bearColorInput, style = plot.style_columns)

// Envelopes (Dotted with cuts on peak rise/fall)
pUpper = plot(upperEnv, "Upper Envelope", upperRise ? na : upperEnvColor, linestyle = plot.linestyle_dotted)
pLower = plot(lowerEnv, "Lower Envelope", lowerFall ? na : lowerEnvColor, linestyle = plot.linestyle_dotted)


// Envelope Fills (Fade to center)
fill(pUpper, pZero, upperEnv, 0, showOscFills ? color.new(upperEnvColor, 70) : na, color.new(upperEnvColor, 100), "Upper Env Fill")
fill(pLower, pZero, 0, lowerEnv, color.new(lowerEnvColor, 100), showOscFills ? color.new(lowerEnvColor, 70) : na, "Lower Env Fill")

// --- Main Chart Overlay ---
// Display swing levels and zones on chart with clear cuts
phC = phChanged ? na : phLevelColor
plC = plChanged ? na : plLevelColor

phLevelPlot = plot(showLevelsInput ? lastPH : na, "Pivot High Level", phC, style = plot.style_linebr, force_overlay = true)
plLevelPlot = plot(showLevelsInput ? lastPL : na, "Pivot Low Level",  plC, style = plot.style_linebr, force_overlay = true)

phThreshold = (showLevelsInput and useThreshold) ? lastPH + threshold : na
plThreshold = (showLevelsInput and useThreshold) ? lastPL - threshold : na

phZC = phChanged ? na : phZoneColor
plZC = plChanged ? na : plZoneColor


phZonePlot  = plot(phThreshold, "PH Threshold", phZC, style = plot.style_linebr, force_overlay = true)
plZonePlot  = plot(plThreshold, "PL Threshold", plZC, style = plot.style_linebr, force_overlay = true)

fill(phLevelPlot, phZonePlot, phChanged ? na : phZoneColor, "PH Zone Fill")
fill(plLevelPlot, plZonePlot, plChanged ? na : plZoneColor, "PL Zone Fill")

fill(phLevelPlot, phZonePlot, phChanged ? na : phZoneColor, "PH Zone Fill")
fill(plLevelPlot, plZonePlot, plChanged ? na : plZoneColor, "PL Zone Fill")

//---------------------------------------------------------------------------------------------------------------------}
