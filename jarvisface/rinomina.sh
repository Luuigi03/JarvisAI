#!/bin/bash

contatore=1

# Fase 1: Rinomina con prefisso temporaneo
for file in *; do
  if [[ -f "$file" && ! "$file" == .* && "$file" != "$(basename "$0")" ]]; then
    estensione="${file##*.}"
    if [[ "$file" == *.* ]]; then
      mv "$file" "temp_$contatore.$estensione"
    else
      mv "$file" "temp_$contatore"
    fi
    ((contatore++))
  fi
done

# Fase 2: Rimuove il prefisso temporaneo
for file in temp_*; do
  if [[ -f "$file" ]]; then
    mv "$file" "${file#temp_}"
  fi
done