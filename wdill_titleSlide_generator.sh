#!/bin/bash

convert -size 1024x768 xc:"#EEEEEE" \
    \( -pointsize 50 -background "#EEEEEE" -gravity center -geometry +0-100 -fill black label:"What Did" \) -composite \
    \( icon.png -resize 150x150 -compose over -gravity north -geometry +0+70 \) -composite \
    "$4"

convert "$4" -pointsize 50 -background "#EEEEEE" -gravity center -fill blue -annotate +0+5 "$1" "$4"

convert "$4" -pointsize 50 -background "#EEEEEE" -gravity center -fill black -annotate +0+125 "Look Like From $2 To $3?" "$4"

#convert "$4" -pointsize 50 -background "#EEEEEE" -gravity center -fill black -annotate +0+150 "From $2 - $3?" "$4"

convert "$4" -pointsize 50 -undercolor "#0008" -gravity south -fill white -font "LiberationSerif.ttf" -annotate +0+70 "#whatdiditlooklike" "$4"