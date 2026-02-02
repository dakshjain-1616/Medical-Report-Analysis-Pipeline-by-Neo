#!/bin/bash

# Configuration
PROJECT_ROOT="/root/MedicalReportAnalysis"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"

echo "medical report analysis pipeline - by Neo"
echo "Starting Pipeline Execution..."

# 1. Check Port 8000
PORT_PID=$(lsof -t -i:8000 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    echo "Cleaning up existing process on port 8000 (PID: $PORT_PID)..."
    kill -9 $PORT_PID
fi

# 2. Setup environment
mkdir -p "$LOG_DIR"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 3. Start API Server
echo "Launching Secure API Server..."
cd "$PROJECT_ROOT"
export PYTHONUNBUFFERED=1
nohup "$VENV_PATH/bin/python3" api.py > "$LOG_DIR/api_server.log" 2>&1 &
API_PID=$!

# Wait for server and check if it stayed alive
echo "Initializing (15s)..."
sleep 15
if ! ps -p $API_PID > /dev/null; then
    echo "ERROR: API Server failed to start. Last log entries:"
    tail -n 10 "$LOG_DIR/api_server.log"
    exit 1
fi

# 4. Run study processing
echo "Processing Pending Studies (solver.py)..."
"$VENV_PATH/bin/python3" "$PROJECT_ROOT/solver.py"
SOLVER_EXIT=$?

# 5. Run final validation
echo "Running Final Verification..."
"$VENV_PATH/bin/python3" "$PROJECT_ROOT/final_verify.py"
VERIFY_EXIT=$?

# 6. Final Cleanup
echo "Shutting down API server..."
kill $API_PID

if [ $SOLVER_EXIT -eq 0 ] && [ $VERIFY_EXIT -eq 0 ]; then
    echo "Full Pipeline Execution SUCCESSFUL."
    exit 0
else
    echo "Pipeline Execution FAILED (Solver: $SOLVER_EXIT, Verify: $VERIFY_EXIT)"
    exit 1
fi