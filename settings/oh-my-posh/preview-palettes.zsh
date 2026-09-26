#!/bin/zsh
# Render the prompt once per palette in gaurav-custom.omp.json, to compare them side by side.
# Run it in the terminal you want to judge the colours in:
#   zsh ~/.config/oh-my-posh/preview-palettes.zsh [palette ...]
config=${0:A:h}/gaurav-custom.omp.json
palettes=(${@:-$(python3 -c 'import json, sys; print(*json.load(open(sys.argv[1]))["palettes"]["list"])' $config)})

omp() {
  env -u POSH_SESSION_ID POSH_PALETTE=$palette \
    oh-my-posh print "$@" --config $config --shell zsh --pwd $PWD --terminal-width $COLUMNS
}

for palette in $palettes; do
  print -P "\n%B== $palette ==%b"
  print -P "$(omp transient --status 0)ls"
  print -P "$(omp transient --status 1)false"
  print -P "$(omp primary --execution-time 130000 --status 1)"
  print -P "$(omp primary --execution-time 450 --status 0)"
done
print "\nTo live with one: export POSH_PALETTE=<name> (unset it to go back to the default)."
