#!/bin/bash
# VigilHome Monitor Control Script

PID_FILE="/tmp/vigilhome_monitor.pid"
LOG_FILE="/tmp/vigilhome_monitor.out"
MONITOR_SCRIPT="/Users/augustosilva/clawd/projects/video-surveillance-rnd/src/realtime_monitor.py"
VENV="/Users/augustosilva/clawd/venv-vigilhome/bin/activate"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
      echo "Monitor is already running (PID: $(cat $PID_FILE))"
      exit 1
    fi
    
    echo "Starting VigilHome Monitor..."
    source "$VENV" && cd ~/clawd/projects/video-surveillance-rnd
    nohup python "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Monitor started with PID: $!"
    sleep 2
    tail -20 "$LOG_FILE"
    ;;
    
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping monitor (PID: $PID)..."
        kill "$PID"
        rm "$PID_FILE"
        echo "Monitor stopped"
      else
        echo "Monitor not running (stale PID file)"
        rm "$PID_FILE"
      fi
    else
      echo "Monitor is not running (no PID file)"
    fi
    ;;
    
  restart)
    $0 stop
    sleep 1
    $0 start
    ;;
    
  status)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Monitor is running (PID: $PID)"
        echo ""
        echo "Recent activity:"
        tail -15 "$LOG_FILE" 2>/dev/null | grep -E "(Person|Alert|Status)" | tail -8
      else
        echo "❌ Monitor is not running (stale PID file)"
      fi
    else
      echo "❌ Monitor is not running"
    fi
    ;;
    
  logs)
    tail -f "$LOG_FILE"
    ;;
    
  stats)
    echo "=== VigilHome Monitor Statistics ==="
    if [ -f "$LOG_FILE" ]; then
      echo ""
      echo "Person Detections:"
      grep -c "Person detected" "$LOG_FILE" 2>/dev/null || echo "0"
      echo ""
      echo "Alerts Sent:"
      grep -c "Alert sent successfully" "$LOG_FILE" 2>/dev/null || echo "0"
      echo ""
      echo "Recent Detections by Camera:"
      grep "Person detected in" "$LOG_FILE" 2>/dev/null | tail -10
    else
      echo "No log file found"
    fi
    ;;
    
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|stats}"
    exit 1
    ;;
esac
