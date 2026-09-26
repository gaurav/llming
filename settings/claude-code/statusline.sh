#!/bin/bash
# Claude Code status line: git branch, context use, quota left, and model. See README.md.
# Reads the statusline JSON payload from stdin (see Claude Code docs).

input=$(cat)

# ---- colours (dim-friendly; terminal theme handles the dimming) ----
c_reset=$'\033[0m'
c_dim=$'\033[2m'
c_green=$'\033[32m'
c_yellow=$'\033[33m'
c_orange=$'\033[91m'
c_red=$'\033[1;31m'
c_cyan=$'\033[36m'
c_opus=$'\033[38;2;232;106;160m'
c_sonnet=$'\033[38;2;98;164;230m'
c_fable=$'\033[38;2;150;150;235m'
c_sep=$'\033[97m'

diamond=$'\xE2\x99\xA6'  # ♦ U+2666 BLACK DIAMOND SUIT
sep="${c_sep} ${diamond} ${c_reset}"

arrow_up=$'\xE2\x87\xA1'    # ⇡ U+21E1 UPWARDS DASHED ARROW (unpushed commits)
arrow_down=$'\xE2\x87\xA3'  # ⇣ U+21E3 DOWNWARDS DASHED ARROW (commits behind)

now=$(date +%s)

fmt_duration() {
  # seconds -> "Xd Yh" / "Xh Ym" / "Xm"
  local secs=$1
  if [ -z "$secs" ] || [ "$secs" -lt 0 ] 2>/dev/null; then
    echo "now"
    return
  fi
  local d=$((secs / 86400))
  local h=$(((secs % 86400) / 3600))
  local m=$(((secs % 3600) / 60))
  if [ "$d" -gt 0 ]; then
    printf '%dd %dh' "$d" "$h"
  elif [ "$h" -gt 0 ]; then
    printf '%dh %dm' "$h" "$m"
  else
    printf '%dm' "$m"
  fi
}

fmt_clock() {
  # epoch -> "3:05pm" (short form)
  local epoch=$1
  local t
  t=$(date -r "$epoch" '+%I:%M%p' 2>/dev/null | sed 's/AM$/am/; s/PM$/pm/')
  # strip a leading zero on the hour
  echo "${t#0}"
}

fmt_clock_day() {
  # epoch -> "Fri 3am"
  local epoch=$1
  local t
  t=$(date -r "$epoch" '+%a %I%p' 2>/dev/null | sed 's/AM$/am/; s/PM$/pm/')
  echo "$t" | sed -E 's/ 0/ /'
}

pct_color() {
  # 4-ish step green -> yellow -> orange -> red
  local pct=$1
  awk -v p="$pct" -v g="$c_green" -v y="$c_yellow" -v o="$c_orange" -v r="$c_red" \
    'BEGIN {
      if (p+0 < 50) print g;
      else if (p+0 < 75) print y;
      else if (p+0 < 90) print o;
      else print r;
    }'
}

pace_color() {
  # yellow when the quota's used_percentage is running more than 10 points ahead of how much
  # of the window has elapsed (the margin keeps early-window noise, e.g. 3% used 5 minutes in,
  # from flagging as burning); dim otherwise, including when resets_at is missing or past.
  local used=$1 resets_at=$2 window=$3
  if [ -z "$resets_at" ]; then
    echo "$c_dim"
    return
  fi
  awk -v used="$used" -v resets_at="$resets_at" -v window="$window" -v now="$now" \
    -v y="$c_yellow" -v d="$c_dim" \
    'BEGIN {
      remaining = resets_at - now;
      if (remaining < 0) { print d; exit }
      elapsed = window - remaining;
      if (elapsed < 0) elapsed = 0;
      if (elapsed > window) elapsed = window;
      elapsed_pct = elapsed * 100 / window;
      if (used + 0 > elapsed_pct + 10) print y;
      else print d;
    }'
}

# ---- branch, coloured by git state ----
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
status_output=$(git -C "$cwd" --no-optional-locks status --porcelain=v2 --branch 2>/dev/null)
git_rc=$?

left=""
if [ "$git_rc" -eq 0 ]; then
  branch=$(printf '%s\n' "$status_output" | awk '/^# branch\.head /{print $3}')
  ahead=$(printf '%s\n' "$status_output" | awk '/^# branch\.ab /{gsub("\\+","",$3); print $3}')
  behind=$(printf '%s\n' "$status_output" | awk '/^# branch\.ab /{gsub("-","",$4); print $4}')

  if [ -n "$branch" ]; then
    if printf '%s\n' "$status_output" | grep -q '^[^#]'; then
      branch_color="$c_yellow"  # uncommitted changes: staged, unstaged or untracked
    else
      branch_color="$c_cyan"    # clean tree
    fi
    left="${branch_color}${branch}${c_reset}"

    arrows=""
    [ -n "$ahead" ] && [ "$ahead" != "0" ] && arrows="${arrows}${arrow_up}${ahead}"
    [ -n "$behind" ] && [ "$behind" != "0" ] && arrows="${arrows}${arrow_down}${behind}"
    [ -n "$arrows" ] && left="${left} ${c_sep}${arrows}${c_reset}"
  fi
else
  # not a git repo (or lookup failed): fall back to worktree metadata
  branch=$(echo "$input" | jq -r '.worktree.branch // empty')
  [ -n "$branch" ] && left="${c_cyan}${branch}${c_reset}"
fi
[ -z "$left" ] && left="${c_dim}no branch${c_reset}"

# ---- context window ----
ctx_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
ctx_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')

ctx_seg=""
if [ -n "$ctx_used" ]; then
  ctx_color=$(pct_color "$ctx_used")
  ctx_k_used=$(awk -v v="$ctx_in" 'BEGIN{printf "%.0f", v/1000}')
  ctx_seg=$(printf '%sctx%s %s%.0f%%%s %s(%sk)%s' \
    "$c_sep" "$c_reset" "$ctx_color" "$ctx_used" "$c_reset" "$c_dim" "$ctx_k_used" "$c_reset")
fi

# ---- rate limits (5h / 7d) ----
five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
week_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

quota_seg=""
if [ -n "$five_pct" ]; then
  five_color=$(pct_color "$five_pct")
  five_remaining=$(awk -v p="$five_pct" 'BEGIN{printf "%.0f", 100 - p}')
  five_left=$(fmt_duration $((five_reset - now)))
  five_clock=$(fmt_clock "$five_reset")
  five_pace=$(pace_color "$five_pct" "$five_reset" 18000)
  quota_seg="${c_sep}5h:${c_reset} ${five_color}${five_remaining}%${c_reset} ${c_dim}until ${five_clock} ${c_reset}${five_pace}(${five_left})${c_reset}"
fi
if [ -n "$week_pct" ]; then
  week_color=$(pct_color "$week_pct")
  week_remaining=$(awk -v p="$week_pct" 'BEGIN{printf "%.0f", 100 - p}')
  week_left=$(fmt_duration $((week_reset - now)))
  week_clock=$(fmt_clock_day "$week_reset")
  week_pace=$(pace_color "$week_pct" "$week_reset" 604800)
  week_seg="${c_sep}7d:${c_reset} ${week_color}${week_remaining}%${c_reset} ${c_dim}until ${week_clock} ${c_reset}${week_pace}(${week_left})${c_reset}"
  if [ -n "$quota_seg" ]; then
    quota_seg="${quota_seg}${sep}${week_seg}"
  else
    quota_seg="$week_seg"
  fi
fi

# ---- model / effort ----
model=$(echo "$input" | jq -r '.model.display_name // empty')
effort=$(echo "$input" | jq -r '.effort.level // empty')
model_seg=""
if [ -n "$model" ]; then
  # colour by model family, so a glance confirms which model is running
  model_lc=$(echo "$model" | tr '[:upper:]' '[:lower:]')
  case "$model_lc" in
    *opus*) model_color="$c_opus" ;;
    *sonnet*) model_color="$c_sonnet" ;;
    *fable*) model_color="$c_fable" ;;
    *haiku*) model_color="" ;;  # plain, undimmed default text
    *) model_color="$c_dim" ;;
  esac
  model_seg="${model_color}${model}${c_reset}"

  if [ -n "$effort" ]; then
    if [ "$effort" = "high" ]; then
      # the usual setting: calm, same colour as the model name
      effort_color="$model_color"
    else
      # anything else (low/medium/xhigh/max/unrecognised): stand out
      effort_color="$c_sep"
    fi
    model_seg="${model_seg} ${effort_color}[${effort}]${c_reset}"
  fi
fi

# ---- assemble ----
parts=()
[ -n "$left" ] && parts+=("$left")
[ -n "$ctx_seg" ] && parts+=("$ctx_seg")
[ -n "$quota_seg" ] && parts+=("$quota_seg")
[ -n "$model_seg" ] && parts+=("$model_seg")

out=""
for p in "${parts[@]}"; do
  if [ -z "$out" ]; then
    out="$p"
  else
    out="${out}${sep}${p}"
  fi
done

printf '%s' "$out"
